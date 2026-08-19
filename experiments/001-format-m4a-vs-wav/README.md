# Experiment 001 — m4a vs WAV (Entry 001)

Tests whether lossy AAC changes the intonation reading vs lossless WAV.
Finding: **identical** for a real same-take pair; the codec is transparent for
sustained-note intonation (median over the note averages out codec noise).

## Run
Uses the paired recording in [`audio/reference-2026-06/`](../../audio/reference-2026-06/)
— `scale_notvib.wav` and `scale_notvib.m4a`, the same take in both formats. From the repo root:
```
python format_test.py
```
Requires the maestro deps (librosa, numpy, soundfile) and ffmpeg.
