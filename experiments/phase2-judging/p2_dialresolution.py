"""Phase 2 follow-up — does the strictness dial actually do anything?

p2_demo showed pass rate identical at 10/15/20¢. This isolates why: pYIN's default
resolution snaps every reading to a 10¢ bin (Entry 002), so a threshold can only change
a verdict when it crosses a bin edge. Between edges the dial is dead.

Three parts:
  A. fine-grained threshold sweep (1..30¢ in 1¢ steps) on the mock performance
  B. the same sweep on the TRUE cents (what a perfect ruler would have measured)
  C. the Just 3rd / 6th at default vs fine resolution — does the ET penalty survive?
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from synth1 import build_signal, synth_tone
from phase2 import get_notes, cents_under_ref, threshold_sweep, hz_to_cents
from pipeline import analyze

SCALE = ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"]
HUMAN = [-8, +3, +18, -22, +5, -12, +2, +9]      # the 'playing' error
OFFSET = +10                                      # instrument near A=442.5
TRUE = [h + OFFSET for h in HUMAN]                # ground truth, exactly known

print("=== A. what the tool reads vs what is actually there ===")
notes = get_notes(build_signal([(n, t) for n, t in zip(SCALE, TRUE)]))
read = cents_under_ref([n[2] for n in notes], 440.0)
print(f"{'note':>6} {'true¢':>7} {'read¢':>7} {'err':>6}")
for n, t, r in zip(SCALE, TRUE, read):
    print(f"{n:>6} {t:>+7.1f} {r:>+7.1f} {r-t:>+6.1f}")
print(f"  mean |error| = {np.mean([abs(r-t) for r, t in zip(read, TRUE)]):.1f}¢ "
      f"(pure 10¢-bin snapping)\n")

print("=== B. strictness dial, 1¢ steps: measured vs ground truth ===")
print(f"{'±¢':>4} {'pass (measured)':>16} {'pass (true)':>13}")
prev = None
dead = 0
for t in range(1, 31):
    pm = 100.0 * sum(abs(c) <= t for c in read) / len(read)
    pt = 100.0 * sum(abs(c) <= t for c in TRUE) / len(TRUE)
    flag = ""
    if prev is not None and pm == prev:
        dead += 1
    else:
        flag = "  <- verdict changes here"
    prev = pm
    print(f"{t:>3}¢ {pm:>14.0f}% {pt:>12.0f}%{flag}")
print(f"  the measured dial changes verdicts at only {30-dead} of 30 settings; "
      f"the rest are dead steps\n")

print("=== C. the Just 3rd and 6th: default (10¢) vs fine (1¢) resolution ===")
print("  A perfectly played just-intonation interval. Does it read as an error?")
print(f"{'degree':>8} {'true¢':>7} {'@0.1 (10¢ bins)':>17} {'@0.01 (1¢)':>13}")
for label, true_c, ratio, base in [
        ("3rd (E)", -13.7, 5/4, "D4"),
        ("6th (B)", -15.6, 5/3, "D4")]:
    import librosa
    hz = librosa.note_to_hz(base) * ratio
    tone = synth_tone(hz, dur=0.7)
    coarse = analyze(tone, resolution=0.1)
    fine = analyze(tone, resolution=0.01)
    cc = coarse[0][5] if coarse else float("nan")
    fc = fine[0][5] if fine else float("nan")
    vc = "OFF" if abs(cc) > 15 else "OK"
    vf = "OFF" if abs(fc) > 15 else "OK"
    print(f"{label:>8} {true_c:>+7.1f} {cc:>+11.1f} [{vc:>3}] {fc:>+8.1f} [{vf:>3}]")
print("  if the coarse column says OK and the fine column says OFF, the ruler is")
print("  forgiving an error the scorer was designed to catch.")
