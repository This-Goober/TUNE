"""Phase 2 — 'the judging': the verdict knobs, made visible and adjustable.

These operate on the SAME pitch measurements Phases 0-1 validated; they only change how
the tool *judges*. Every knob is an explicit, legible setting — the tool surfaces what it's
doing rather than silently adapting. Works on synthetic tones now and on a real audio file
(pass a path to get_notes) the moment a recording lands.

Knobs:
  1. graded_score      — partial credit instead of hard pass/fail
  2. threshold_sweep   — strictness as a dial, not a hidden ±15¢ constant
  3. reference pitch + detect_offset — A=440/442/443 setting, and REPORT a uniform offset
  4. cents_vs_just     — judge against equal temperament OR just intonation
"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, librosa
import audio_v0 as av
from pipeline import pyin_track, SR, SYN_SR

NOTE_NAMES = av.NOTE_NAMES


# ---------- shared: pitch -> note/cents under a chosen reference pitch ----------
def hz_to_cents(hz, a4=440.0):
    """Nearest-semitone name + signed cents, on a grid anchored at the given A4."""
    midi = 12 * np.log2(hz / a4) + 69
    nearest = int(round(midi))
    cents = (midi - nearest) * 100
    return NOTE_NAMES[nearest % 12], nearest // 12 - 1, float(cents)


def get_notes(source, syn_sr=SYN_SR):
    """source = audio file path (str/Path) OR raw synthetic ndarray.
    Returns per-note [(start, end, hz)] using the validated maestro pipeline (pYIN,
    onset segmentation, median-per-note, octave-fix, merge). Reference-independent: we
    keep raw Hz so any knob can re-judge under any reference/intonation."""
    if isinstance(source, (str, Path)):
        y = av.load_audio(Path(source))
    else:
        y = librosa.resample(np.asarray(source, dtype=float), orig_sr=syn_sr, target_sr=SR)
    times, pitch, per = pyin_track(y)
    rows = []
    for s, e in av.detect_notes(y):
        hz = av.median_pitch_in_window(times, pitch, per, s, e, 0.5)
        if hz is None:
            rows.append((s, e, None, None, None, None, "unvoiced")); continue
        n, o, c = av.hz_to_note(hz)
        rows.append((s, e, hz, n, o, c, "OK" if abs(c) <= 15 else "OFF"))
    rows = av.merge_same_note(av.fix_octave_errors(rows, 15), 15)
    return [(r[0], r[1], r[2]) for r in rows if r[2] is not None]


# ---------- knob 1: graded score (partial credit) ----------
def graded_score(cents, full=10.0, zero=50.0):
    """0-100 for one note. Full credit inside ±full¢, linear decay to 0 at ±zero¢.
    Replaces the cliff at ±15¢ with a ramp, so 16¢ and 45¢ no longer score the same."""
    a = abs(cents)
    if a <= full:
        return 100.0
    if a >= zero:
        return 0.0
    return 100.0 * (zero - a) / (zero - full)


def score_summary(cents_list, threshold=15.0, full=10.0, zero=50.0):
    hard = 100.0 * sum(abs(c) <= threshold for c in cents_list) / len(cents_list)
    graded = float(np.mean([graded_score(c, full, zero) for c in cents_list]))
    return hard, graded


# ---------- knob 2: strictness / threshold sweep ----------
def threshold_sweep(cents_list, thresholds=(5, 10, 15, 20, 25, 30)):
    out = []
    for t in thresholds:
        passed = sum(abs(c) <= t for c in cents_list)
        out.append((t, passed, len(cents_list), 100.0 * passed / len(cents_list)))
    return out


# ---------- knob 3: reference pitch + uniform-offset reporter ----------
def cents_under_ref(hzs, a4=440.0):
    return [hz_to_cents(h, a4)[2] for h in hzs]


def detect_offset(hzs):
    """Report (don't hide) a uniform tuning offset. Returns median cents vs A=440 and the
    A4 that offset implies. If the whole scale sits, say, +12¢, that's ~443, not bad playing."""
    cents_440 = cents_under_ref(hzs, 440.0)
    med = float(np.median(cents_440))
    suggested_a4 = 440.0 * 2 ** (med / 1200)
    return med, suggested_a4


# ---------- knob 4: intonation reference (equal temperament vs just) ----------
# Just-intonation major-scale degree offsets from equal temperament, in cents, keyed by
# semitones above the tonic (0..11). These are the expressive intervals players lean into.
JUST_MAJOR_OFFSETS = {0: 0.0, 2: 3.9, 4: -13.7, 5: -2.0, 7: 2.0, 9: -15.6, 11: -11.7}


def cents_vs_just(hzs, tonic="D4", a4=440.0):
    """Re-judge each note against the nearest JUST-intonation target in the given key,
    instead of the equal-tempered grid. Returns [(et_cents, just_cents_or_None)]."""
    tonic_hz = librosa.note_to_hz(tonic) * (a4 / 440.0)
    out = []
    for h in hzs:
        _, _, et_c = hz_to_cents(h, a4)
        deg = int(round(12 * np.log2(h / tonic_hz))) % 12
        off = JUST_MAJOR_OFFSETS.get(deg)
        out.append((et_c, None if off is None else et_c - off))
    return out
