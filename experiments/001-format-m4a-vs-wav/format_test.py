"""Isolate the AAC-codec effect on pitch cents using one clean source.
Encode scale_notvib.wav to several AAC bitrates, decode, run the same
pYIN pipeline, and compare per-note cents — overall and by octave."""
import sys, subprocess, tempfile, warnings
from pathlib import Path
from collections import defaultdict
warnings.filterwarnings("ignore")
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "skills" / "Maestro" / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import numpy as np
import audio_v0 as av
from run_pyin import pyin_track

SRC = Path(__file__).resolve().parents[2] / "audio" / "reference-2026-06" / "scale_notvib.wav"
THR = 15.0


def analyze(path):
    y = av.load_audio(Path(path))
    times, pitch, per = pyin_track(y)
    rows = []
    for s, e in av.detect_notes(y):
        hz = av.median_pitch_in_window(times, pitch, per, s, e, 0.5)
        if hz is None:
            rows.append((s, e, None, None, None, None, "unvoiced")); continue
        n, o, c = av.hz_to_note(hz)
        rows.append((s, e, hz, n, o, c, "OK" if abs(c) <= THR else "OFF"))
    rows = av.merge_same_note(av.fix_octave_errors(rows, THR), THR)
    return [r for r in rows if r[2] is not None]


def encode(bitrate):
    out = Path(tempfile.gettempdir()) / f"rt_{bitrate}.m4a"
    subprocess.run(["ffmpeg", "-y", "-i", str(SRC), "-c:a", "aac",
                    "-b:a", bitrate, str(out)], check=True, capture_output=True)
    return out


def stats(rows, label):
    cents = [r[5] for r in rows]
    off = sum(1 for r in rows if r[6] == "OFF")
    by_oct = defaultdict(list)
    for r in rows:
        by_oct[r[4]].append(abs(r[5]))
    print(f"\n{label}")
    print(f"  voiced={len(rows)}  OFF={off}  acc={100*(1-off/len(rows)):.1f}%  "
          f"median={np.median(cents):+.1f}  mean={np.mean(cents):+.1f}  "
          f"max|dev|={max(abs(c) for c in cents):.1f}")
    print("  mean|cents| by octave: " +
          "  ".join(f"oct{o}={np.mean(v):.1f}(n{len(v)})"
                    for o, v in sorted(by_oct.items())))
    return rows


def paired_diff(base, other, label):
    """Align by matching note name+octave in sequence; report cent deltas."""
    n = min(len(base), len(other))
    diffs, hi_diffs = [], []
    for a, b in zip(base[:n], other[:n]):
        if a[3] == b[3] and a[4] == b[4]:
            d = b[5] - a[5]
            diffs.append(d)
            if a[4] >= 6:  # top octave (oct6/7)
                hi_diffs.append(d)
    if diffs:
        print(f"  {label}: matched {len(diffs)} notes  "
              f"mean|Δcents|={np.mean(np.abs(diffs)):.2f}  "
              f"max|Δ|={np.max(np.abs(diffs)):.1f}", end="")
        if hi_diffs:
            print(f"   | top-octave(n{len(hi_diffs)}) "
                  f"mean|Δ|={np.mean(np.abs(hi_diffs)):.2f} "
                  f"max|Δ|={np.max(np.abs(hi_diffs)):.1f}")
        else:
            print()


print("Baseline = lossless WAV; others = WAV→AAC→decode roundtrips")
base = stats(analyze(SRC), "WAV (lossless)")
for br in ["96k", "72k", "48k"]:
    rows = stats(analyze(encode(br)), f"AAC {br} roundtrip")
    paired_diff(base, rows, f"vs WAV")
