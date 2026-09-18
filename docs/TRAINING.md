# Training Notes

## Dataset

Surprise Party Fiddlesticks Turkish voice dataset.

- Final usable utterances: 123
- Sample rate: 22050 Hz
- Channels: mono
- Piper base: tr_TR DFKI medium
- Precision: FP32
- Batch size: 16
- Validation split: 0
- MRD: disabled

## Training

Initial fine-tuning used the Turkish DFKI medium Piper checkpoint.

Major test points:

- 6500 epochs
- 10000 epochs
- 12000 epochs
- 13600 epochs
- 15000 epochs

Voice similarity improved strongly with training.
Robotic prosody progressively decreased.

At epoch 10000 the optimizer learning rate had decayed to approximately:

5.73e-05

A controlled second phase was continued around 5e-05.

Current next target:

20000 epochs

Milestone checkpoints are intended at:

16000
17000
18000
19000
20000

## Long sentence synthesis

Best current long-form strategy:

- approximately 40 phonemes per chunk
- BOS at the beginning of every chunk
- no EOS between intermediate chunks
- EOS only on the final chunk
- trim artificial edge silence
- 70 ms equal-power crossfade

This produces substantially more natural speech than feeding one long
phoneme sequence into the model.
