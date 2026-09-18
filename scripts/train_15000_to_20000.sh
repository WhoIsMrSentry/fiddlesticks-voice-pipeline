#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/piper_rex"
PIPER="$ROOT/piper1-gpl"
DS="$ROOT/fiddle_tr/final_dataset_fiddle_tr_v1"
TRAIN="$ROOT/piper_train"
RUN="$TRAIN/fiddle_gladosstyle_long"

cd "$PIPER"
source .venv/bin/activate

CKPT="$(
    find "$RUN" -type f -name 'last.ckpt' -printf '%T@ %p\n' \
    | sort -nr \
    | head -1 \
    | cut -d' ' -f2-
)"

echo "Resume checkpoint:"
echo "$CKPT"

python - "$CKPT" <<'PY'
import sys
import torch

c = torch.load(
    sys.argv[1],
    map_location="cpu",
    weights_only=False,
)

print("epoch:", c.get("epoch"))
print("training epoch:", (c.get("epoch") or 0) + 1)
print("global_step:", c.get("global_step"))

for i, opt in enumerate(c.get("optimizer_states", [])):
    print(
        "optimizer",
        i,
        "lr:",
        [g.get("lr") for g in opt.get("param_groups", [])]
    )
PY

python -m piper.train fit \
  --ckpt_path "$CKPT" \
  --weights_only false \
  --trainer.accelerator gpu \
  --trainer.devices 1 \
  --trainer.precision 32-true \
  --trainer.max_epochs 20000 \
  --trainer.max_steps -1 \
  --trainer.log_every_n_steps 5 \
  --trainer.default_root_dir "$RUN" \
  --data.voice_name fiddle_tr \
  --data.csv_path "$DS/metadata.piper.csv" \
  --data.audio_dir "$DS/wavs" \
  --model.sample_rate 22050 \
  --data.espeak_voice tr \
  --data.cache_dir "$TRAIN/cache_fiddle" \
  --data.config_path "$TRAIN/model/tr_TR-fiddle.onnx.json" \
  --data.batch_size 16 \
  --data.validation_split 0.0 \
  --data.num_test_examples 0 \
  --data.num_workers 4 \
  --model.use_mrd false \
  --model.learning_rate 0.00005 \
  --model.learning_rate_d 0.00005 \
  --model.betas "[0.8,0.99]" \
  --model.betas_d "[0.8,0.99]" \
  --model.lr_decay 0.999875 \
  --model.lr_decay_d 0.999875 \
  --model.mos_metric none \
  2>&1 | tee -a "$TRAIN/fiddle_gladosstyle_long_phase4.log"
