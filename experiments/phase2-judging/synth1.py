"""Phase 1 synthesis extensions — vibrato, noise, and non-equal tunings.
Built on the same 6-partial violin-ish stack + attack/release as Phase 0's synth.py,
so timbre is held constant across phases. We control true pitch/width/SNR exactly:
the synthetic tone is the CONTROL — any error maestro reports is the evaluator's."""
import numpy as np
import librosa

SYN_SR = 44100
PARTIALS = [1.0, 0.5, 0.33, 0.22, 0.15, 0.10]


def _envelope(n, sr):
    env = np.ones(n)
    a, r = int(0.05 * sr), int(0.10 * sr)
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return env


def synth_tone(f0, dur=1.5, sr=SYN_SR):
    """Steady tone (matches Phase 0 synth.py exactly)."""
    t = np.arange(int(dur * sr)) / sr
    sig = sum(a * np.sin(2 * np.pi * f0 * (k + 1) * t) for k, a in enumerate(PARTIALS))
    sig /= np.max(np.abs(sig))
    return sig * _envelope(len(sig), sr) * 0.9


def synth_vibrato(f0, width_cents, rate_hz=6.0, dur=2.0, sr=SYN_SR):
    """Sinusoidal vibrato: instantaneous pitch = f0 * 2^((width/1200)*sin(2*pi*rate*t)).
    Vibrato is SYMMETRIC about f0, so the true CENTER pitch is exactly f0 (0 error).
    width_cents is the PEAK deviation (so peak-to-peak = 2*width)."""
    t = np.arange(int(dur * sr)) / sr
    # phase integral of a frequency-modulated carrier
    dev = (width_cents / 1200.0) * np.sin(2 * np.pi * rate_hz * t)  # in octaves
    inst_f = f0 * (2.0 ** dev)
    phase = 2 * np.pi * np.cumsum(inst_f) / sr
    sig = sum(a * np.sin((k + 1) * phase) for k, a in enumerate(PARTIALS))
    sig /= np.max(np.abs(sig))
    return sig * _envelope(len(sig), sr) * 0.9


def target_hz(note, cents=0.0):
    return librosa.note_to_hz(note) * 2 ** (cents / 1200)


def build_signal(specs, gap=0.4, dur=1.5, sr=SYN_SR, tones=None):
    """specs=[(note,cents),...] -> concatenated with leading/trailing silence.
    Use DISTINCT notes (merge_same_note collapses repeats). If `tones` (list of
    raw signals) is given, concatenate those instead."""
    silence = np.zeros(int(gap * sr))
    parts = [silence]
    if tones is not None:
        for tsig in tones:
            parts.append(tsig); parts.append(silence)
    else:
        for note, cents in specs:
            parts.append(synth_tone(target_hz(note, cents), dur, sr)); parts.append(silence)
    return np.concatenate(parts)


def add_noise_snr(sig, snr_db, seed=0):
    """Add white Gaussian noise at a target SNR (dB) relative to signal RMS.
    Noise added only where there is signal? No — added everywhere (realistic hiss)."""
    rng = np.random.default_rng(seed)
    p_sig = np.mean(sig ** 2)
    if p_sig == 0:
        return sig
    p_noise = p_sig / (10 ** (snr_db / 10))
    noise = rng.normal(0, np.sqrt(p_noise), size=sig.shape)
    return sig + noise


def pink_noise(n, seed=0):
    """Approximate pink (1/f) noise via FFT filtering."""
    rng = np.random.default_rng(seed)
    white = rng.normal(0, 1, n)
    X = np.fft.rfft(white)
    f = np.arange(1, len(X) + 1)
    X = X / np.sqrt(f)
    p = np.fft.irfft(X, n=n)
    return p / np.std(p)


def add_pink_snr(sig, snr_db, seed=0):
    p_sig = np.mean(sig ** 2)
    if p_sig == 0:
        return sig
    noise = pink_noise(len(sig), seed)
    noise = noise / np.sqrt(np.mean(noise ** 2))  # unit RMS
    p_noise = p_sig / (10 ** (snr_db / 10))
    return sig + noise * np.sqrt(p_noise)


# ---- Tuning systems: cents of each major-scale degree vs equal temperament ----
# Ratios relative to tonic; tonic placed exactly on the ET grid so it reads 0.
JUST_MAJOR = [1/1, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8, 2/1]
PYTHAG_MAJOR = [1/1, 9/8, 81/64, 4/3, 3/2, 27/16, 243/128, 2/1]
ET_STEPS = [0, 2, 4, 5, 7, 9, 11, 12]  # semitones
DEGREE_NAMES = ["1 (root)", "2", "3", "4", "5", "6", "7", "8 (oct)"]


def ratio_cents_vs_et(ratio, semitones):
    """Cents deviation of a just/Pythagorean interval from its nearest ET semitone."""
    cents_interval = 1200 * np.log2(ratio)
    return cents_interval - semitones * 100


def build_tuned_scale(tonic="D4", ratios=JUST_MAJOR, dur=1.5, sr=SYN_SR):
    """Synthesize an ascending major scale in a given tuning. Tonic sits exactly on
    the ET grid (reads 0); each degree carries its true tuning-system deviation."""
    f_tonic = librosa.note_to_hz(tonic)
    tones = [synth_tone(f_tonic * r, dur, sr) for r in ratios]
    return build_signal(None, dur=dur, sr=sr, tones=tones)
