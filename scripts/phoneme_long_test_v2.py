from pathlib import Path
import sys
import wave
import numpy as np

from piper.voice import PiperVoice
from piper.const import BOS, EOS, PAD


MODEL = Path(sys.argv[1])
OUT = Path(sys.argv[2])

TEXT = (
    "Bu gece ışıklar söndüğünde kimse nereye saklandığını hatırlamayacak, "
    "çünkü kahkahalar duvarların arasından yükselirken ben çoktan yanı başınızda olacağım; "
    "o zaman perde açılacak, gösteri başlayacak ve gecenin sonunda "
    "kimin gerçekten güldüğünü hep birlikte öğreneceğiz."
)

MAX_PHONEMES = 40

# Aradaki fiziksel birleşme.
CROSSFADE_MS = 70

# Her bloktan kalan yapay sessizlikten sadece bu kadar bırak.
EDGE_KEEP_MS = 15


voice = PiperVoice.load(MODEL)
sample_rate = voice.config.sample_rate
id_map = voice.config.phoneme_id_map

OUT.mkdir(parents=True, exist_ok=True)


def flatten_phonemes(text):
    return [
        p
        for sentence in voice.phonemize(text)
        for p in sentence
    ]


def phoneme_count(text):
    return len(flatten_phonemes(text))


def split_text(text, maximum):
    words = text.split()

    chunks = []
    current = []

    for word in words:
        candidate = " ".join(current + [word])

        if current and phoneme_count(candidate) > maximum:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(" ".join(current))

    return chunks


def make_ids(phonemes, add_bos=True, add_eos=True):
    ids = []

    pad_ids = list(id_map[PAD])

    if add_bos:
        ids.extend(id_map[BOS])
        ids.extend(pad_ids)

    for phoneme in phonemes:
        pids = id_map.get(phoneme)

        if not pids:
            continue

        ids.extend(pids)
        ids.extend(pad_ids)

    if add_eos:
        ids.extend(id_map[EOS])

    return ids


def synth_ids(ids):
    audio = voice.phoneme_ids_to_audio(ids)
    return np.asarray(audio, dtype=np.float32)


def trim_edge_silence(audio):
    if len(audio) == 0:
        return audio

    peak = float(np.max(np.abs(audio)))

    if peak <= 0:
        return audio

    # Yaklaşık -36 dB relatif eşik.
    threshold = max(
        peak * 0.015,
        0.001,
    )

    win = max(
        1,
        int(sample_rate * 0.010)
    )

    power = np.convolve(
        audio * audio,
        np.ones(win, dtype=np.float32) / win,
        mode="same",
    )

    rms = np.sqrt(power)

    active = np.where(rms > threshold)[0]

    if len(active) == 0:
        return audio

    keep = int(
        sample_rate * EDGE_KEEP_MS / 1000
    )

    start = max(
        0,
        int(active[0]) - keep
    )

    end = min(
        len(audio),
        int(active[-1]) + keep + 1
    )

    return audio[start:end]


def equal_power_join(parts):
    if not parts:
        return np.zeros(
            0,
            dtype=np.float32
        )

    result = parts[0]

    requested = int(
        sample_rate
        * CROSSFADE_MS
        / 1000
    )

    for part in parts[1:]:
        n = min(
            requested,
            len(result),
            len(part),
        )

        if n <= 0:
            result = np.concatenate(
                [result, part]
            )
            continue

        theta = np.linspace(
            0.0,
            np.pi / 2.0,
            n,
            dtype=np.float32,
        )

        fade_out = np.cos(theta)
        fade_in = np.sin(theta)

        overlap = (
            result[-n:] * fade_out
            + part[:n] * fade_in
        )

        result = np.concatenate([
            result[:-n],
            overlap,
            part[n:],
        ])

    return result


def save_wav(path, audio):
    audio = np.clip(
        audio,
        -1.0,
        1.0
    )

    pcm = (
        audio * 32767.0
    ).astype(np.int16)

    with wave.open(
        str(path),
        "wb"
    ) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(
            pcm.tobytes()
        )


chunks = split_text(
    TEXT,
    MAX_PHONEMES
)

print("CHUNKS:", len(chunks))


# =====================================================
# VARIANT A
#
# Her chunk BOS ile başlıyor.
# SADECE SON chunk EOS alıyor.
#
# Bu, modele alışık olduğu başlangıç tokenını verir
# ama ara bloklarda "cümle bitti" dememiş oluruz.
# =====================================================

audio_a = []

for i, chunk in enumerate(chunks):
    phonemes = flatten_phonemes(chunk)

    ids = make_ids(
        phonemes,
        add_bos=True,
        add_eos=(i == len(chunks) - 1),
    )

    audio = synth_ids(ids)
    audio = trim_edge_silence(audio)

    audio_a.append(audio)

    print(
        f"A chunk {i+1:02d}:",
        len(phonemes),
        "phonemes",
        round(len(audio) / sample_rate, 3),
        "sec",
    )


joined_a = equal_power_join(audio_a)

save_wav(
    OUT / "01_40phon_keep_BOS_no_mid_EOS.wav",
    joined_a,
)


# =====================================================
# VARIANT B
#
# BOS sadece ilk chunkta.
# EOS sadece son chunkta.
#
# Tüm bloklar sanki tek uzun fonem dizisinin parçalarıymış
# gibi davranıyor.
# =====================================================

audio_b = []

for i, chunk in enumerate(chunks):
    phonemes = flatten_phonemes(chunk)

    ids = make_ids(
        phonemes,
        add_bos=(i == 0),
        add_eos=(i == len(chunks) - 1),
    )

    audio = synth_ids(ids)
    audio = trim_edge_silence(audio)

    audio_b.append(audio)

    print(
        f"B chunk {i+1:02d}:",
        len(phonemes),
        "phonemes",
        round(len(audio) / sample_rate, 3),
        "sec",
    )


joined_b = equal_power_join(audio_b)

save_wav(
    OUT / "02_40phon_outer_BOS_EOS_only.wav",
    joined_b,
)


# =====================================================
# Bilgi dosyası
# =====================================================

report = []

for i, chunk in enumerate(chunks, 1):
    phonemes = flatten_phonemes(chunk)

    report.append(
        f"""CHUNK {i}
PHONEMES: {len(phonemes)}
TEXT: {chunk}
IPA: {''.join(phonemes)}

"""
    )

(OUT / "chunks.txt").write_text(
    "\n".join(report),
    encoding="utf-8",
)


print()
print("DONE")
print("OUTPUT:", OUT)
