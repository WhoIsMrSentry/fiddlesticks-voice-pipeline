# Surprise Party Fiddlesticks Turkish Piper Pipeline

Training and dataset preparation pipeline for a Turkish Piper TTS voice
based on Surprise Party Fiddlesticks.

This repository contains pipeline code only.

The dataset and trained model are maintained separately on Hugging Face.

## Pipeline

1. Extract voice clips
2. Filter non-verbal clips
3. Generate Whisper draft transcripts
4. Manually review audio and transcripts
5. Normalize audio to 22050 Hz mono
6. Generate Piper metadata
7. Fine-tune from the Turkish DFKI medium Piper checkpoint
8. Export ONNX
9. Use phoneme-aware chunked synthesis for long text

## Long-form synthesis

Current preferred strategy:

- ~40 phonemes per chunk
- BOS for every chunk
- no intermediate EOS
- EOS only on final chunk
- edge silence trimming
- 70 ms equal-power crossfade

See `docs/TRAINING.md`.

## Repository contents

- `scripts/` dataset, training and inference utilities
- `patches/` local Piper training changes
- `docs/` experiment and training notes

Audio files, datasets, checkpoints and ONNX models are intentionally
excluded from this Git repository.
