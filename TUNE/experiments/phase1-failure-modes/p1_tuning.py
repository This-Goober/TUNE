"""Phase 1 — the equal-temperament penalty.
Synthesize a PERFECTLY played major scale in Just and Pythagorean intonation (tonic on
the ET grid). maestro scores against the nearest A=440 equal-tempered semitone. Count how
many notes read OFF purely because of the tuning system — not because of any error."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from synth1 import (build_tuned_scale, ratio_cents_vs_et, JUST_MAJOR, PYTHAG_MAJOR,
                    ET_STEPS, DEGREE_NAMES)
from pipeline import analyze

TONIC = "D4"
SYSTEMS = {"Equal (control)": [2**(s/12) for s in ET_STEPS],
           "Just":            JUST_MAJOR,
           "Pythagorean":     PYTHAG_MAJOR}

for name, ratios in SYSTEMS.items():
    print(f"\n=== {name} major scale on {TONIC} (perfectly in that system) ===")
    rows = analyze(build_tuned_scale(TONIC, ratios))
    truth = [ratio_cents_vs_et(r, s) for r, s in zip(ratios, ET_STEPS)]
    print(f"{'degree':>9} {'true vs ET':>11} {'maestro reads':>13} {'verdict':>8}")
    off = 0
    for i, (deg, tru) in enumerate(zip(DEGREE_NAMES, truth)):
        if i < len(rows):
            rep = rows[i][5]
            v = "OK" if abs(rep) <= 15 else "OFF"
            off += (v == "OFF")
            print(f"{deg:>9} {tru:>+10.1f}¢ {rep:>+12.1f}¢ {v:>8}")
        else:
            print(f"{deg:>9} {tru:>+10.1f}¢ {'(not detected)':>13}")
    n = min(len(rows), len(DEGREE_NAMES))
    print(f"  -> {off}/{n} notes flagged OFF by the ±15¢ ET rule "
          f"(a perfect {name.split()[0]} performance)")
