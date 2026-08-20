"""Shared pYIN pitch-tracking helper — the CREPE fallback used across experiments.

Resolves the maestro analyzer relative to the project root, so it runs anywhere
the project folder is checked out (Drive, repo, sandbox) without absolute paths.

pYIN note: librosa.pyin's default `resolution=0.1` means 0.1 semitone = 10-cent
pitch bins. Phase 0 (Entry 002) found this quantizes every cents reading to 10¢.
Pass a finer `resolution` (e.g. 0.01) for 1¢ accuracy. NOTE: an earlier version of this
note said that was ~360x slower and that cent-level work therefore needs CREPE. Phase 2
overturned that — the 360x came from searching the whole G3-E7 range at once. Locate the
note coarsely first, then refine at 0.01 over a +/-3 semitone band, and the cost is 2.8x
for 0.36¢ mean error. See experiments/phase2-judging/p2_tworuler.py.
"""
import sys
from pathlib import Path

# project root = two levels up from experiments/lib/
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "Maestro" / "scripts"))

import numpy as np
import librosa
import audio_v0 as av

SR = av.SR


def pyin_track(y, resolution=0.1, frame_length=2048, hop_length=256):
    fmin = librosa.note_to_hz("G3")
    fmax = librosa.note_to_hz("E7")
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, sr=SR, fmin=fmin, fmax=fmax,
        frame_length=frame_length, hop_length=hop_length, resolution=resolution,
    )
    times = librosa.frames_to_time(np.arange(len(f0)), sr=SR, hop_length=hop_length)
    hz = np.nan_to_num(f0, nan=0.0)
    periodicity = np.nan_to_num(voiced_prob, nan=0.0)
    return times, hz, periodicity


def analyze(path_or_signal, resolution=0.1, syn_sr=None):
    """Run the full maestro pipeline with pYIN. Accepts a file path or a raw
    numpy signal (with syn_sr set). Returns voiced rows: (s,e,hz,name,octave,cents,verdict)."""
    if syn_sr is not None:
        y = librosa.resample(path_or_signal, orig_sr=syn_sr, target_sr=SR)
    else:
        y = av.load_audio(Path(path_or_signal))
    times, pitch, per = pyin_track(y, resolution=resolution)
    rows = []
    for s, e in av.detect_notes(y):
        hz = av.median_pitch_in_window(times, pitch, per, s, e, 0.5)
        if hz is None:
            rows.append((s, e, None, None, None, None, "unvoiced")); continue
        n, o, c = av.hz_to_note(hz)
        rows.append((s, e, hz, n, o, c, "OK" if abs(c) <= 15 else "OFF"))
    rows = av.merge_same_note(av.fix_octave_errors(rows, 15), 15)
    return [r for r in rows if r[2] is not None]
