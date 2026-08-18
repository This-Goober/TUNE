"""Phase 1 — noise / SNR robustness.
Clean, perfectly-in-tune D-major scale (8 distinct notes). Add white (and pink) noise at
known SNRs; find where note detection and cents readings break down."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from synth1 import build_signal, add_noise_snr, add_pink_snr
from pipeline import analyze

SCALE = ["D4","E4","F#4","G4","A4","B4","C#5","D5"]
clean = build_signal([(n, 0) for n in SCALE])
SNRS = [None, 40, 30, 20, 10, 5, 0]

def run(sig):
    rows = analyze(sig)
    if not rows: return 0, None, None
    cents = [abs(r[5]) for r in rows]
    acc = 100 * sum(abs(r[5]) <= 15 for r in rows) / len(rows)
    return len(rows), acc, float(np.mean(cents))

for label, adder in [("WHITE", add_noise_snr), ("PINK", add_pink_snr)]:
    print(f"\n=== {label} noise (scale = 8 clean D-major notes) ===")
    print(f"{'SNR(dB)':>8} {'detected':>9} {'accuracy':>9} {'mean|¢|':>8}")
    for snr in SNRS:
        sig = clean if snr is None else adder(clean, snr, seed=0)
        n, acc, mc = run(sig)
        lab = "clean" if snr is None else f"{snr}"
        accs = f"{acc:.0f}%" if acc is not None else "—"
        mcs = f"{mc:.1f}" if mc is not None else "—"
        print(f"{lab:>8} {n:>7}/8 {accs:>9} {mcs:>8}")
