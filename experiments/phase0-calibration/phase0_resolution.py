"""Phase 0 — pYIN resolution comparison: 10¢ bins (default) vs 1¢ bins.
Demonstrates the accuracy/speed tradeoff that motivates CREPE.
WARNING: resolution=0.01 is ~360x slower; keep the signal short.
Run:  python experiments/phase0-calibration/phase0_resolution.py"""
import sys, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import numpy as np, librosa
from synth import synth_tone, target_hz, SYN_SR
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "Maestro" / "scripts"))
import audio_v0 as av

# single sustained tone, E5 detuned +25¢ (snaps to +30 at coarse resolution)
y = librosa.resample(synth_tone(target_hz("E5", 25), dur=0.7), orig_sr=SYN_SR, target_sr=av.SR)
for res in [0.1, 0.01]:
    t0 = time.time()
    f0, vf, vp = librosa.pyin(y, sr=av.SR, fmin=librosa.note_to_hz("G3"),
                             fmax=librosa.note_to_hz("E7"),
                             frame_length=2048, hop_length=256, resolution=res)
    p = np.nan_to_num(f0, nan=0.0)
    hz = float(np.median(p[p > 0][2:-2]))
    n, o, c = av.hz_to_note(hz)
    print(f"resolution={res} ({int(res*100)}¢ bins): read {n}{o} {c:+.1f}¢ "
          f"(true +25.0¢, err {c-25:+.1f}¢)  [{time.time()-t0:.1f}s]")
# Observed 2026-07-02: 0.1 -> +30.0¢ err +5.0 [0.2s];  0.01 -> +26.0¢ err +1.0 [72.5s]
