from pathlib import Path
import json
import html

ROOT = Path.home() / "piper_rex" / "fiddle_tr"
RAW = ROOT / "raw"
JSONL = ROOT / "transcripts" / "fiddle_raw.jsonl"
OUT = ROOT / "review"

OUT.mkdir(parents=True, exist_ok=True)

rows = [
    json.loads(line)
    for line in JSONL.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

parts = []

for r in rows:
    idx = int(r["index"])
    filename = r["filename"]
    text = r["text"]

    src = RAW / filename
    dst_name = f"{idx:03d}.wav"
    dst = OUT / dst_name

    if not dst.exists():
        dst.write_bytes(src.read_bytes())

    parts.append(f"""
    <div class="row" data-index="{idx}" data-file="{html.escape(filename)}">
      <div class="num">{idx:03d}</div>

      <div class="audio">
        <audio controls preload="none" src="{dst_name}"></audio>
      </div>

      <div class="file">{html.escape(filename)}</div>

      <textarea id="text-{idx}">{html.escape(text)}</textarea>

      <label class="reject">
        <input type="checkbox" id="reject-{idx}">
        REJECT
      </label>
    </div>
    """)

page = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>Fiddlesticks TR Dataset Review</title>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 20px;
  background: #111;
  color: #eee;
}

h1 {
  margin-bottom: 5px;
}

.info {
  color: #aaa;
  margin-bottom: 20px;
}

.toolbar {
  position: sticky;
  top: 0;
  background: #111;
  padding: 10px 0;
  z-index: 100;
}

button {
  padding: 10px 16px;
  margin-right: 8px;
  cursor: pointer;
}

.row {
  border: 1px solid #444;
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 8px;
}

.num {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 7px;
}

.file {
  color: #888;
  font-size: 11px;
  margin: 6px 0;
  word-break: break-all;
}

audio {
  width: 100%;
  max-width: 650px;
}

textarea {
  width: 100%;
  min-height: 65px;
  box-sizing: border-box;
  font-size: 16px;
  padding: 8px;
  background: #222;
  color: #fff;
  border: 1px solid #555;
  border-radius: 5px;
}

.reject {
  display: inline-block;
  margin-top: 8px;
  color: #ff9090;
  font-weight: bold;
}
</style>
</head>

<body>

<h1>Surprise Party Fiddlesticks TR</h1>
<div class="info">
Dinle → metni düzelt → anlamsız ses ise REJECT işaretle.
</div>

<div class="toolbar">
  <button onclick="exportCSV()">CSV indir</button>
  <button onclick="saveProgress()">İlerlemeyi tarayıcıda kaydet</button>
  <button onclick="loadProgress()">Kaydı geri yükle</button>
</div>

__ROWS__

<script>
function collect() {
  const rows = [];

  document.querySelectorAll(".row").forEach(row => {
    const i = row.dataset.index;

    rows.push({
      index: Number(i),
      filename: row.dataset.file,
      text: document.getElementById("text-" + i).value.trim(),
      reject: document.getElementById("reject-" + i).checked
    });
  });

  return rows;
}

function saveProgress() {
  localStorage.setItem("fiddle_review", JSON.stringify(collect()));
  alert("Kaydedildi.");
}

function loadProgress() {
  const raw = localStorage.getItem("fiddle_review");

  if (!raw) {
    alert("Kayıt bulunamadı.");
    return;
  }

  const rows = JSON.parse(raw);

  rows.forEach(r => {
    const t = document.getElementById("text-" + r.index);
    const c = document.getElementById("reject-" + r.index);

    if (t) t.value = r.text;
    if (c) c.checked = r.reject;
  });
}

function esc(s) {
  return '"' + String(s).replaceAll('"', '""') + '"';
}

function exportCSV() {
  const rows = collect();

  let csv = "index,filename,text,reject\n";

  for (const r of rows) {
    csv += [
      r.index,
      esc(r.filename),
      esc(r.text),
      r.reject ? "1" : "0"
    ].join(",") + "\n";
  }

  const blob = new Blob([csv], {
    type: "text/csv;charset=utf-8"
  });

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "fiddle_review.csv";
  a.click();

  URL.revokeObjectURL(a.href);
}
</script>

</body>
</html>
"""

page = page.replace("__ROWS__", "\n".join(parts))

(OUT / "index.html").write_text(page, encoding="utf-8")

print("Review hazir:")
print(OUT / "index.html")
print("Kayit:", len(rows))
