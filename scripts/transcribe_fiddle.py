from pathlib import Path
from faster_whisper import WhisperModel
import json
import csv

ROOT = Path.home() / "piper_rex" / "fiddle_tr"
AUDIO = ROOT / "raw"
OUT = ROOT / "transcripts"

OUT.mkdir(parents=True, exist_ok=True)

jsonl_path = OUT / "fiddle_raw.jsonl"
tsv_path = OUT / "fiddle_raw.tsv"

files = sorted(AUDIO.glob("*.wav"))

print(f"Toplam WAV: {len(files)}")
print("Model yukleniyor: large-v3 / CUDA / float16")

model = WhisperModel(
    "large-v3",
    device="cuda",
    compute_type="float16",
)

with (
    jsonl_path.open("w", encoding="utf-8") as jf,
    tsv_path.open("w", encoding="utf-8", newline="") as tf,
):
    writer = csv.writer(tf, delimiter="\t")
    writer.writerow([
        "index",
        "filename",
        "text",
        "avg_logprob",
        "no_speech_prob",
    ])

    for i, wav in enumerate(files, 1):
        segments, info = model.transcribe(
            str(wav),
            language="tr",
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
            word_timestamps=False,
        )

        segments = list(segments)

        text = " ".join(
            s.text.strip()
            for s in segments
            if s.text.strip()
        ).strip()

        if segments:
            weights = [max(s.end - s.start, 0.001) for s in segments]
            total_weight = sum(weights)

            avg_logprob = sum(
                s.avg_logprob * w
                for s, w in zip(segments, weights)
            ) / total_weight

            no_speech_prob = sum(
                s.no_speech_prob * w
                for s, w in zip(segments, weights)
            ) / total_weight
        else:
            avg_logprob = None
            no_speech_prob = None

        row = {
            "index": i,
            "filename": wav.name,
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
            "avg_logprob": avg_logprob,
            "no_speech_prob": no_speech_prob,
        }

        jf.write(json.dumps(row, ensure_ascii=False) + "\n")
        jf.flush()

        writer.writerow([
            i,
            wav.name,
            text,
            "" if avg_logprob is None else f"{avg_logprob:.4f}",
            "" if no_speech_prob is None else f"{no_speech_prob:.4f}",
        ])
        tf.flush()

        print(f"[{i:03d}/{len(files):03d}] {wav.name}")
        print(f"    {text!r}")

print()
print("Bitti.")
print("JSONL:", jsonl_path)
print("TSV  :", tsv_path)
