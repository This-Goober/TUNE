"""Phase 2 knobs — demonstration on a MOCK imperfect performance.
Stands in for the real recording so the rig is proven before audio lands. The mock: a D
major scale with hand-set human-ish errors, plus a uniform +10¢ (instrument tuned ~442-443).
Replace `sig` with get_notes('yourfile.wav') when the recording arrives — nothing else changes.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from synth1 import build_signal, build_tuned_scale, JUST_MAJOR
from phase2 import (get_notes, hz_to_cents, graded_score, score_summary,
                    threshold_sweep, cents_under_ref, detect_offset, cents_vs_just)

SCALE = ["D4","E4","F#4","G4","A4","B4","C#5","D5"]
HUMAN = [-8, +3, +18, -22, +5, -12, +2, +9]     # per-note 'playing' error (what the ear rates)
OFFSET = +10                                     # whole instrument ~+10¢ (near 442-443)
specs = [(n, h + OFFSET) for n, h in zip(SCALE, HUMAN)]

notes = get_notes(build_signal(specs))
hzs = [n[2] for n in notes]
cents440 = cents_under_ref(hzs, 440.0)
print(f"detected {len(notes)} notes (of {len(SCALE)})\n")

print("=== KNOB 1: hard pass/fail  vs  graded partial-credit ===")
print(f"{'note':>6} {'reads¢':>7} {'hard@15':>8} {'graded':>7}")
for (n, c) in zip(SCALE, cents440):
    hard = "OK" if abs(c) <= 15 else "OFF"
    print(f"{n:>6} {c:>+7.1f} {hard:>8} {graded_score(c):>6.0f}")
hard, graded = score_summary(cents440)
print(f"  overall:  hard pass/fail = {hard:.0f}%   graded = {graded:.0f}/100")
print("  (pass/fail throws away 'how off'; graded keeps it)\n")

print("=== KNOB 2: strictness dial (threshold sweep) ===")
print(f"{'±cents':>7} {'pass rate':>10}")
for t, p, n, pct in threshold_sweep(cents440):
    print(f"{t:>6}¢ {pct:>8.0f}%  ({p}/{n})")
print("  (is ±15¢ special, or just a line someone drew?)\n")

print("=== KNOB 3: reference pitch + offset reporter ===")
med, a4 = detect_offset(hzs)
print(f"  uniform offset detected: {med:+.1f}¢  ->  suggests A4 ≈ {a4:.1f} Hz")
print(f"  {'note':>6} {'@A=440':>7} {'@A=443':>7}")
for n, c440, c443 in zip(SCALE, cents440, cents_under_ref(hzs, 443.0)):
    print(f"{n:>6} {c440:>+7.1f} {c443:>+7.1f}")
print("  (set your real reference and the whole-scale offset stops counting as 'error')\n")

print("=== KNOB 4: equal temperament vs just intonation ===")
print("  (clean demo: a PERFECT just-intonation scale, judged both ways)")
just_notes = get_notes(build_tuned_scale("D4", JUST_MAJOR))
just_hz = [n[2] for n in just_notes]
print(f"  {'deg':>4} {'vs ET':>7} {'vs Just':>8}")
off_et = off_just = 0
for i, (et, ju) in enumerate(cents_vs_just(just_hz, "D4"), 1):
    ve = "OFF" if abs(et) > 15 else "OK"
    vj = "—" if ju is None else ("OFF" if abs(ju) > 15 else "OK")
    off_et += ve == "OFF"; off_just += (vj == "OFF")
    juf = "  —  " if ju is None else f"{ju:>+5.1f}"
    print(f"  {i:>4} {et:>+6.1f} {juf:>8}  [{ve} / {vj}]")
print(f"  OFF under ET = {off_et}   OFF under Just = {off_just}   "
      f"(expressive intonation stops reading as mistakes)")
