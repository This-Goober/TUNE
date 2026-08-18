"""Phase 1 — vibrato-width degradation curve.
Synthetic tone with SYMMETRIC sinusoidal vibrato (rate 6 Hz). True center pitch = f0
(0 error by construction). Question: as vibrato widens, does maestro's median-per-note
reading stay in tune, and does the verdict flip? Also report the per-FRAME spread — what
a naive frame-by-frame scorer would see and penalize."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, librosa
from synth1 import synth_vibrato, SYN_SR
from pipeline import pyin_track, SR
import audio_v0 as av

WIDTHS = [0, 10, 20, 30, 40, 50, 75, 100]   # peak cents deviation
RATE, DUR = 6.0, 2.0

def frame_cents(sig, f0):
    y = librosa.resample(sig, orig_sr=SYN_SR, target_sr=SR)
    t, pitch, per = pyin_track(y)
    m = (per > 0.5) & (pitch > 0)
    v = pitch[m]
    n_total = int(m.size)
    if len(v) < 5:
        return None
    cents = 1200 * np.log2(v / f0)                 # per-frame cents vs true center
    med = float(np.median(cents))
    # what maestro actually reports = median hz -> hz_to_note cents (snapped)
    name, octv, rep = av.hz_to_note(float(np.median(v)))
    voiced_frac = len(v) / n_total
    return dict(med=med, rep=rep, name=f"{name}{octv}",
                std=float(np.std(cents)), lo=float(np.percentile(cents,5)),
                hi=float(np.percentile(cents,95)), vfrac=voiced_frac, n=len(v))

for note in ["A4", "A5"]:
    f0 = librosa.note_to_hz(note)
    print(f"\n=== vibrato sweep @ {note} ({f0:.1f} Hz), rate {RATE} Hz, dur {DUR}s ===")
    print(f"{'width±¢':>8} {'reported¢':>9} {'verdict':>7} {'frame_med':>9} "
          f"{'frame_std':>9} {'frame 5–95%':>14} {'voiced%':>8}")
    for w in WIDTHS:
        sig = synth_vibrato(f0, w, RATE, DUR)
        r = frame_cents(sig, f0)
        if r is None:
            print(f"{w:>7}± {'LOST (unvoiced)':>40}"); continue
        verdict = "OK" if abs(r['rep']) <= 15 else "OFF"
        print(f"{w:>7}± {r['rep']:>+9.1f} {verdict:>7} {r['med']:>+9.1f} "
              f"{r['std']:>9.1f} {r['lo']:>+6.0f}..{r['hi']:>+5.0f} {100*r['vfrac']:>7.0f}%")
