"""Phase 1 pipeline helper — identical pYIN path to Phase 0's run_pyin.py,
but resolves audio_v0 from the same directory (self-contained harness).

pYIN: librosa default resolution=0.1 => 10-cent bins (Entry 002). We keep the
SAME frame_length/hop_length/resolution as Phase 0 so numbers are comparable.
"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import librosa
import audio_v0 as av

SR = av.SR          # 22050
SYN_SR = 44100      # synthesis rate (matches synth.py)


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


def analyze(signal, resolution=0.1, syn_sr=SYN_SR):
    """Full maestro pYIN pipeline on a raw numpy signal at syn_sr.
    Returns voiced rows: (s,e,hz,name,octave,cents,verdict)."""
    y = librosa.resample(signal, orig_sr=syn_sr, target_sr=SR)
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


# ---- single-tone reader: bypass onset segmentation, just measure center pitch ----
def measure_single(signal, resolution=0.1, syn_sr=SYN_SR, trim=0.10):
    """For one sustained tone: median pitch over the stable middle (skip attack/release).
    Returns (hz, name, octave, cents) or None."""
    y = librosa.resample(signal, orig_sr=syn_sr, target_sr=SR)
    times, pitch, per = pyin_track(y, resolution=resolution)
    dur = len(y) / SR
    s, e = trim, dur - trim
    mask = (times >= s) & (times <= e) & (per > 0.5) & (pitch > 0)
    voiced = pitch[mask]
    if len(voiced) < 5:
        return None
    hz = float(np.median(voiced))
    n, o, c = av.hz_to_note(hz)
    return hz, n, o, c
