"""
maestro audio v0 — pitch-accuracy report for a violin scale recording.

Usage:
    .venv/bin/python audio_v0.py path/to/file [--threshold 15] [--scale "G major asc-desc"]

Scale spec forms (any of):
    --scale "G major"                # 1 octave ascending
    --scale "G major asc-desc"       # asc then desc
    --scale "C major asc-desc 2oct"  # 2 octaves up and down
    --scale "G3 A3 B3 ... G5"        # explicit space-separated notes

When --scale is given, each detected note is DTW-aligned to the expected scale,
so wrong notes (D played instead of D#) are distinguished from intonation
drift (D played 30¢ flat).
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import librosa
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
A4_HZ = 440.0
A4_MIDI = 69
AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aiff", ".aif"}
SR = 22050  # CREPE resamples to 16k internally; we keep the rest at 22050

SCALE_INTERVALS = {
    "major":          [0, 2, 4, 5, 7, 9, 11],
    "minor":          [0, 2, 3, 5, 7, 8, 10],     # natural minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor":  [0, 2, 3, 5, 7, 9, 11],     # ascending form
    "dorian":         [0, 2, 3, 5, 7, 9, 10],
    "mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "chromatic":      list(range(12)),
}


def hz_to_note(hz: float) -> tuple[str, int, float]:
    midi_float = 12 * np.log2(hz / A4_HZ) + A4_MIDI
    midi_nearest = int(round(midi_float))
    cents = (midi_float - midi_nearest) * 100
    return NOTE_NAMES[midi_nearest % 12], midi_nearest // 12 - 1, float(cents)


def _midi(hz: float) -> float:
    return 12 * np.log2(hz / A4_HZ) + A4_MIDI


def load_audio(input_path: Path) -> np.ndarray:
    if input_path.suffix.lower() in AUDIO_EXTS:
        y, _ = librosa.load(input_path, sr=SR, mono=True)
        return y
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg required for video input — `brew install ffmpeg`")
    out = Path(tempfile.gettempdir()) / f"{input_path.stem}_maestro.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-ac", "1", "-ar", str(SR), str(out)],
        check=True, capture_output=True,
    )
    y, _ = librosa.load(out, sr=SR, mono=True)
    return y


def detect_notes(y: np.ndarray) -> list[tuple[float, float]]:
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=SR, units="frames", backtrack=True, hop_length=512,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=SR, hop_length=512)
    duration = len(y) / SR
    if len(onset_times) == 0:
        return [(0.0, duration)]
    bounds = list(onset_times) + [duration]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
            if bounds[i + 1] - bounds[i] >= 0.10]


def crepe_pitch_track(y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run CREPE on the whole audio. Returns (times_sec, hz, periodicity)."""
    import torch
    import torchcrepe
    audio = torch.from_numpy(y.astype(np.float32)).unsqueeze(0)
    hop = 160  # 10ms at the internal 16kHz CREPE rate
    pitch, periodicity = torchcrepe.predict(
        audio, sample_rate=SR, hop_length=hop,
        fmin=librosa.note_to_hz("G3"),
        fmax=librosa.note_to_hz("E7"),
        model="full",
        return_periodicity=True,
        device="cpu",
        batch_size=512,
    )
    pitch = pitch.squeeze(0).cpu().numpy()
    periodicity = periodicity.squeeze(0).cpu().numpy()
    times = np.arange(len(pitch)) * hop / SR
    return times, pitch, periodicity


def median_pitch_in_window(
    times: np.ndarray, pitch: np.ndarray, periodicity: np.ndarray,
    start: float, end: float, conf_thresh: float = 0.5,
) -> float | None:
    s, e = start + 0.06, end - 0.03
    if e - s < 0.05:
        return None
    mask = (times >= s) & (times <= e) & (periodicity > conf_thresh) & (pitch > 0)
    voiced = pitch[mask]
    if len(voiced) < 5:
        return None
    return float(np.median(voiced))


def fix_octave_errors(rows: list[tuple], threshold: float) -> list[tuple]:
    """If a voiced note sits >7 semitones from BOTH neighbors, try ±12.
    Rare with CREPE but cheap insurance."""
    fixed = list(rows)
    voiced_hz = [r[2] for r in fixed]
    for i, row in enumerate(fixed):
        s, e, hz, *_ = row
        if hz is None:
            continue
        prev = next((h for h in reversed(voiced_hz[:i]) if h is not None), None)
        nxt = next((h for h in voiced_hz[i + 1:] if h is not None), None)
        if prev is None or nxt is None:
            continue
        m, mp, mn = _midi(hz), _midi(prev), _midi(nxt)
        if abs(m - mp) <= 7 or abs(m - mn) <= 7:
            continue
        best_hz, best_score = hz, abs(m - mp) + abs(m - mn)
        for shift in (12, -12):
            cand = hz * (2 ** (shift / 12))
            mc = _midi(cand)
            score = abs(mc - mp) + abs(mc - mn)
            if score < best_score:
                best_hz, best_score = cand, score
        if best_hz != hz:
            name, octv, cents = hz_to_note(best_hz)
            verdict = "OK" if abs(cents) <= threshold else "OFF"
            fixed[i] = (s, e, best_hz, name, octv, cents, verdict)
            voiced_hz[i] = best_hz
    return fixed


def merge_same_note(rows: list[tuple], threshold: float) -> list[tuple]:
    merged: list[tuple] = []
    i = 0
    while i < len(rows):
        s, e, hz, name, octv, cents, verdict = rows[i]
        if hz is None:
            merged.append(rows[i])
            i += 1
            continue
        hzs = [hz]
        j = i + 1
        while j < len(rows):
            _, e2, hz2, name2, octv2, *_ = rows[j]
            if hz2 is None or name2 != name or octv2 != octv:
                break
            hzs.append(hz2)
            e = e2
            j += 1
        if len(hzs) > 1:
            new_hz = float(np.median(hzs))
            n, o, c = hz_to_note(new_hz)
            v = "OK" if abs(c) <= threshold else "OFF"
            merged.append((s, e, new_hz, n, o, c, v))
        else:
            merged.append(rows[i])
        i = j
    return merged


def parse_scale_spec(spec: str) -> list[str]:
    """Returns expected note list, e.g. ['G4','A4','B4','C5','D5','E5','F#5','G5']."""
    tokens = spec.split()
    note_pat = re.compile(r"^[A-G][#b]?\d$")
    if tokens and all(note_pat.match(t) for t in tokens):
        return tokens
    if not tokens:
        raise ValueError("empty scale spec")
    tonic = tokens[0]
    mode = tokens[1] if len(tokens) > 1 else "major"
    pattern = "asc"
    octaves = 1
    for t in tokens[2:]:
        if t in {"asc", "desc", "asc-desc"}:
            pattern = t
        elif t.endswith("oct"):
            octaves = int(t.removesuffix("oct"))
        else:
            raise ValueError(f"unknown scale token: {t!r}")
    tm = re.match(r"^([A-G][#b]?)(\d)?$", tonic)
    if not tm:
        raise ValueError(f"bad tonic: {tonic!r}")
    tonic_midi = librosa.note_to_midi(f"{tm.group(1)}{tm.group(2) or 4}")
    intervals = SCALE_INTERVALS[mode.lower().replace("-", "_")]
    asc: list[int] = []
    for o in range(octaves):
        for i in intervals:
            asc.append(int(tonic_midi + 12 * o + i))
    asc.append(int(tonic_midi + 12 * octaves))
    if pattern == "asc":
        midis = asc
    elif pattern == "desc":
        midis = list(reversed(asc))
    else:
        midis = asc + list(reversed(asc))[1:]
    return [librosa.midi_to_note(m, unicode=False) for m in midis]


def align_to_scale(rows: list[tuple], expected: list[str]) -> dict[int, str]:
    """DTW-align voiced rows to expected notes. Returns {row_index: expected_note}."""
    voiced_idx = [i for i, r in enumerate(rows) if r[2] is not None]
    if not voiced_idx or not expected:
        return {}
    detected_midi = np.array([_midi(rows[i][2]) for i in voiced_idx])
    expected_midi = np.array(
        [librosa.note_to_midi(n) for n in expected], dtype=float
    )
    cost = np.abs(detected_midi[:, None] - expected_midi[None, :])
    _, wp = librosa.sequence.dtw(C=cost, subseq=False)
    mapping: dict[int, str] = {}
    for det_i, exp_i in wp[::-1]:
        mapping[voiced_idx[int(det_i)]] = expected[int(exp_i)]
    return mapping


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("input", type=Path)
    ap.add_argument("--threshold", type=float, default=15.0,
                    help="cents deviation considered 'imperfect' (default 15)")
    ap.add_argument("--scale", type=str, default=None,
                    help='expected scale, e.g. "G major asc-desc 2oct"')
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"file not found: {args.input}")

    print(f"Loading {args.input.name}…")
    y = load_audio(args.input)
    print(f"Duration: {len(y) / SR:.2f}s @ {SR}Hz")

    print("Running CREPE pitch tracker…")
    times, pitch, periodicity = crepe_pitch_track(y)

    windows = detect_notes(y)
    print(f"Detected {len(windows)} note window(s)")

    rows: list[tuple] = []
    for start, end in windows:
        hz = median_pitch_in_window(times, pitch, periodicity, start, end)
        if hz is None:
            rows.append((start, end, None, None, None, None, "unvoiced"))
            continue
        name, octave, cents = hz_to_note(hz)
        verdict = "OK" if abs(cents) <= args.threshold else "OFF"
        rows.append((start, end, hz, name, octave, cents, verdict))

    raw_count = len(rows)
    rows = fix_octave_errors(rows, args.threshold)
    rows = merge_same_note(rows, args.threshold)
    print(f"After cleanup: {len(rows)} note(s) (from {raw_count} raw windows)\n")

    has_scale = bool(args.scale)
    expected_map: dict[int, str] = {}
    if has_scale:
        expected_notes = parse_scale_spec(args.scale)
        print(f"Expected scale ({len(expected_notes)} notes): "
              f"{' '.join(expected_notes)}\n")
        expected_map = align_to_scale(rows, expected_notes)

    header = f"{'#':>3}  {'start':>6}  {'end':>6}  {'Hz':>7}  {'detected':>8}  {'cents':>7}"
    if has_scale:
        header += f"  {'expected':>8}  verdict"
    else:
        header += "  verdict"
    print(header)
    print("-" * len(header))

    wrong_count = 0
    for i, (s, e, hz, name, octv, cents, verdict) in enumerate(rows):
        prefix = f"{i + 1:>3}  {s:>6.2f}  {e:>6.2f}"
        if hz is None:
            line = f"{prefix}  {'—':>7}  {'—':>8}  {'—':>7}"
            line += f"  {'—':>8}  unvoiced" if has_scale else "  unvoiced"
            print(line)
            continue
        det = f"{name}{octv}"
        line = f"{prefix}  {hz:>7.1f}  {det:>8}  {cents:>+7.1f}"
        if has_scale:
            exp = expected_map.get(i, "?")
            if exp != "?" and exp != det:
                wrong_count += 1
                final = "WRONG"
            else:
                final = verdict
            line += f"  {exp:>8}  {final}"
        else:
            line += f"  {verdict}"
        print(line)

    voiced = [r for r in rows if r[2] is not None]
    imperfect = [r for r in voiced if r[6] == "OFF"]
    print()
    summary = (f"Summary: {len(voiced)} voiced notes, "
               f"{len(imperfect)} flat/sharp (|cents| > {args.threshold:g})")
    if has_scale:
        summary += f", {wrong_count} wrong-note"
    print(summary)
    if voiced:
        problems = len(imperfect) + wrong_count
        print(f"Accuracy: {100 * (1 - problems / len(voiced)):.1f}%")


if __name__ == "__main__":
    main()
