"""Synthetic-tone helpers for Phase 0 calibration. We control true pitch exactly."""
import numpy as np
import librosa

SYN_SR = 44100
PARTIALS = [1.0, 0.5, 0.33, 0.22, 0.15, 0.10]  # violin-ish harmonic stack


def synth_tone(f0, dur=1.5, sr=SYN_SR):
    t = np.arange(int(dur * sr)) / sr
    sig = sum(a * np.sin(2 * np.pi * f0 * (k + 1) * t) for k, a in enumerate(PARTIALS))
    sig /= np.max(np.abs(sig))
    env = np.ones_like(sig)
    a, r = int(0.05 * sr), int(0.10 * sr)
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return sig * env * 0.9


def target_hz(note, cents=0.0):
    return librosa.note_to_hz(note) * 2 ** (cents / 1200)


def build_signal(specs, gap=0.4, dur=1.5, sr=SYN_SR):
    """specs = [(note, cents), ...] -> concatenated signal with leading/trailing silence.
    NOTE: use DISTINCT note names — merge_same_note() collapses consecutive identical
    pitches, so repeated same-note tones will be merged (Entry 002 lesson)."""
    silence = np.zeros(int(gap * sr))
    parts = [silence]
    for note, cents in specs:
        parts.append(synth_tone(target_hz(note, cents), dur, sr))
        parts.append(silence)
    return np.concatenate(parts)
