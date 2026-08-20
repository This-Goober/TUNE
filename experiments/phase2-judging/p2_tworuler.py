"""Phase 2 — is the strictness dial real, and does a fine ruler need CREPE?

Two questions, one rig:

  A. CALIBRATION. Measure known detunings with (1) the standing setup — pYIN at default
     resolution over the full G3-E7 search range — and (2) a two-pass refinement: locate the
     note coarsely, then re-run at 1c resolution over a +/-3 semitone band around it.
     Entry 002 measured fine resolution as ~360x slower and wrote it off. That number came
     from searching the WHOLE range at 1c. Constrain the band and the cost mostly vanishes.

  B. THE DIAL. Sweep the pass/fail threshold from 5 to 30c on the same mock performance,
     scored three ways: coarse readings, two-pass readings, and the true cents we synthesized.
     If the ruler is coarser than the dial, whole ranges of the dial do nothing.

Synthetic throughout: the true cents are known exactly, so every error here is the tool's.
"""
import warnings; warnings.filterwarnings("ignore")
import time
import numpy as np
import librosa
import audio_v0 as av
from pipeline import SR, SYN_SR
from synth1 import synth_tone

WIDE = (librosa.note_to_hz("G3"), librosa.note_to_hz("E7"))
BAND_SEMITONES = 3          # +/- this much around the located note for the fine pass
                            # (must span >= ~5 semitones at 0.01 or librosa's filter errors)


def _pyin(y, resolution, fmin, fmax):
    f0, _, _ = librosa.pyin(y, sr=SR, fmin=fmin, fmax=fmax, frame_length=2048,
                            hop_length=256, resolution=resolution)
    hz = np.nan_to_num(f0, nan=0.0)
    hz = hz[hz > 0]
    return float(np.median(hz)) if len(hz) else float("nan")


def read_coarse(y):
    """The standing setup: default 10c bins, full search range."""
    return av.hz_to_note(_pyin(y, 0.1, *WIDE))[2]


def read_twopass(y):
    """Locate coarsely, then refine at 1c over a narrow band around the located pitch.
    Needs no prior knowledge of what note was played."""
    rough = _pyin(y, 0.1, *WIDE)
    lo = rough * 2 ** (-BAND_SEMITONES / 12)
    hi = rough * 2 ** (BAND_SEMITONES / 12)
    return av.hz_to_note(_pyin(y, 0.01, lo, hi))[2]


def tone(note, cents, dur=0.7):
    hz = librosa.note_to_hz(note) * 2 ** (cents / 1200)
    return librosa.resample(synth_tone(hz, dur=dur), orig_sr=SYN_SR, target_sr=SR)


# ------------------------------------------------------------------ A. calibration
OFFSETS = [0, -5, -8, -12, -15, -16, -20, -25, +7, +13, +18]

print("=== A. two rulers on known detunings (A4, 0.7s tones) ===")
print(f"{'true':>6} {'coarse':>8} {'err':>6} {'two-pass':>10} {'err':>6}")
ec, ef, tc, tf = [], [], 0.0, 0.0
for off in OFFSETS:
    y = tone("A4", off)
    t0 = time.time(); c = read_coarse(y);  tc += time.time() - t0
    t0 = time.time(); f = read_twopass(y); tf += time.time() - t0
    ec.append(abs(c - off)); ef.append(abs(f - off))
    print(f"{off:>+6.0f} {c:>+8.1f} {c-off:>+6.1f} {f:>+10.1f} {f-off:>+6.1f}")
print(f"  mean |error|:  coarse {np.mean(ec):.2f}c   two-pass {np.mean(ef):.2f}c")
print(f"  cost per tone: coarse {tc/len(OFFSETS):.2f}s   two-pass {tf/len(OFFSETS):.2f}s "
      f"({tf/tc:.1f}x, not 360x)\n")

# ------------------------------------------------------------------ B. the dial
SCALE = ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"]
HUMAN = [-8, +3, +18, -22, +5, -12, +2, +9]     # per-note playing error
OFFSET = +10                                     # instrument sitting near A=442.5
TRUE = [h + OFFSET for h in HUMAN]

coarse = [read_coarse(tone(n, t, dur=1.5)) for n, t in zip(SCALE, TRUE)]
fine = [read_twopass(tone(n, t, dur=1.5)) for n, t in zip(SCALE, TRUE)]

print("=== B. the same performance, read by each ruler ===")
print(f"{'note':>6} {'true':>6} {'coarse':>8} {'two-pass':>10}")
for n, t, c, f in zip(SCALE, TRUE, coarse, fine):
    print(f"{n:>6} {t:>+6.0f} {c:>+8.1f} {f:>+10.1f}")

print("\n=== B. strictness dial, 1c steps ===")
print(f"{'+/-c':>5} {'coarse':>8} {'two-pass':>10} {'truth':>8}")
prev_c = prev_f = None
dead_c = dead_f = 0
for t in range(5, 31):
    pc = 100.0 * sum(abs(c) <= t for c in coarse) / len(coarse)
    pf = 100.0 * sum(abs(c) <= t for c in fine) / len(fine)
    pt = 100.0 * sum(abs(c) <= t for c in TRUE) / len(TRUE)
    if prev_c is not None and pc == prev_c: dead_c += 1
    if prev_f is not None and pf == prev_f: dead_f += 1
    prev_c, prev_f = pc, pf
    print(f"{t:>4}c {pc:>7.0f}% {pf:>9.0f}% {pt:>7.0f}%")
n = 30 - 5
print(f"\n  dead steps (settings that change nothing): coarse {dead_c}/{n}, two-pass {dead_f}/{n}")
print("  A dial finer than the ruler underneath it is not a dial.")
