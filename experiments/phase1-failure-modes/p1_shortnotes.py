"""Phase 1 — short notes (duration sweep) + sharp/flat directionality.
(a) A 5-note scale synthesized at shrinking note durations: when do notes stop being
    detected/measured? (b) Detune distinct notes ±10/20/30¢ and confirm the SIGN reads
    correctly (sharp -> +, flat -> -)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from synth1 import build_signal
from pipeline import analyze

print("=== (a) note-duration sweep (5-note scale, all in tune) ===")
FIVE = ["D4","E4","F#4","G4","A4"]
print(f"{'dur(s)':>7} {'detected':>9} {'mean|¢|':>8}")
for dur in [1.5, 1.0, 0.5, 0.3, 0.2, 0.15, 0.10]:
    rows = analyze(build_signal([(n,0) for n in FIVE], dur=dur, gap=0.4))
    mc = f"{np.mean([abs(r[5]) for r in rows]):.1f}" if rows else "—"
    print(f"{dur:>7} {len(rows):>7}/5 {mc:>8}")

print("\n=== (b) sharp/flat directionality (sign check) ===")
specs = [("C4",-30),("D4",-20),("E4",-10),("G4",+10),("A4",+20),("B4",+30)]
rows = analyze(build_signal(specs))
print(f"{'intended':>9} {'reads':>8} {'sign OK?':>9}")
for (n,c), r in zip(specs, rows):
    ok = "yes" if (np.sign(r[5])==np.sign(c) or c==0) else "NO"
    print(f"{n}{c:>+4}¢ {r[5]:>+7.1f}¢ {ok:>9}")
