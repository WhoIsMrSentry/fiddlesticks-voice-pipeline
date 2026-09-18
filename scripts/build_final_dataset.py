from pathlib import Path
import csv
import subprocess
import shutil

ROOT = Path.home() / "piper_rex" / "fiddle_tr"

CSV_PATH = ROOT / "fiddle_review.csv"
RAW = ROOT / "raw"

OUT = ROOT / "final_dataset_fiddle_tr_v1"
WAVS = OUT / "wavs"
META = OUT / "metadata.piper.csv"
MAP = OUT / "source_map.tsv"

if OUT.exists():
    shutil.rmtree(OUT)

WAVS.mkdir(parents=True, exist_ok=True)

rows = []

with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        reject = str(row["reject"]).strip().lower()

        if reject in {"1", "true", "yes"}:
            continue

        text = row["text"].strip()
        filename = row["filename"].strip()

        if not text:
            print("SKIP EMPTY:", filename)
            continue

        src = RAW / filename

        if not src.exists():
            raise FileNotFoundError(src)

        rows.append((filename, text))

print("KEEP:", len(rows))

with (
    META.open("w", encoding="utf-8", newline="") as mf,
    MAP.open("w", encoding="utf-8", newline="") as mapf,
):
    map_writer = csv.writer(mapf, delimiter="\t")
    map_writer.writerow(["dataset_file", "source_file", "text"])

    for i, (filename, text) in enumerate(rows, 1):
        dst_name = f"fiddle_{i:04d}.wav"
        dst = WAVS / dst_name
        src = RAW / filename

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", str(src),
            "-ac", "1",
            "-ar", "22050",
            "-c:a", "pcm_s16le",
            str(dst),
        ]

        subprocess.run(cmd, check=True)

        mf.write(f"{dst_name}|{text}\n")
        map_writer.writerow([dst_name, filename, text])

        print(f"[{i:03d}/{len(rows):03d}] {dst_name} | {text}")

print()
print("DONE")
print("dataset:", OUT)
print("metadata:", META)
