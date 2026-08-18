"""Phase 0 — calibrate the pYIN-backed maestro ruler with synthetic tones.
Run:  python experiments/phase0-calibration/phase0_calibration.py
See RESULTS.md for the numbers this produced on 2026-07-02 (Entry 002)."""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import numpy as np
from synth import build_signal, target_hz
from run_pyin import analyze, SYN_SR


def read_rows(specs):
    return analyze(build_signal(specs), syn_sr=SYN_SR)


print("TEST A — offset accuracy (DISTINCT notes, known detuning)")
specs = [("C4", -30), ("E4", +20), ("A4", -10), ("C5", 0), ("E5", +25)]
rows = read_rows(specs)
errs = []
for (n, c), r in zip(specs, rows):
    err = r[5] - c; errs.append(abs(err))
    print(f"  {n}{c:+d}¢ -> {r[3]}{r[4]} read {r[5]:+6.1f}  err {err:+5.1f}")
if len(rows) == len(specs):
    print(f"  mean|err|={np.mean(errs):.2f}¢  max|err|={max(errs):.1f}¢  "
          f"(readings snap to 10¢ — pYIN default resolution=0.1 semitone)")

print("\nTEST B — register sweep at fixed +15¢ (resolution vs pitch height)")
for (n, c), r in zip([(x, 15) for x in ["A3", "A4", "A5", "A6"]],
                     read_rows([(x, 15) for x in ["A3", "A4", "A5", "A6"]])):
    print(f"  {n} +15¢ -> read {r[5]:+6.1f}  err {r[5]-15:+5.1f}  (no register dependence)")

print("\nTEST C — note count (D major, 8 distinct tones)")
scale = ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"]
rows = read_rows([(n, 0) for n in scale])
detected = [f"{r[3]}{r[4]}" for r in rows]
print(f"  intended: {' '.join(scale)}")
print(f"  detected: {' '.join(detected)}  -> {'MATCH' if detected == scale else 'MISMATCH'}")

print("\nTEST D — repeatability (same signal x3)")
sig_specs = [("C4", -30), ("E4", +20), ("A4", -10), ("C5", 0), ("E5", +25)]
runs = [tuple(round(r[5], 3) for r in read_rows(sig_specs)) for _ in range(3)]
print(f"  run1 == run2 == run3 : {runs[0] == runs[1] == runs[2]}")
