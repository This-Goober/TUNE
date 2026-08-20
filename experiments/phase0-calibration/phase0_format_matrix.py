"""Phase 0 — format-coverage matrix. Encode one synthetic scale to every input
format the skill claims, then compare per-note cents AND onset counts to WAV.
Finding (Entry 002): cents identical across all formats; lossy codecs (mp3/m4a/mp4)
over-segment onsets (~2x) via pre-echo/priming — the pipeline's merge step absorbs most.
Run:  python experiments/phase0-calibration/phase0_format_matrix.py"""
import sys, subprocess, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
LIB = HERE.parent / "lib"
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(HERE.parents[1] / "skills" / "Maestro" / "scripts"))
import numpy as np, librosa, soundfile as sf
import audio_v0 as av
from synth import synth_tone

OUT = HERE / "_fmt_tmp"; OUT.mkdir(exist_ok=True)
SR = 44100
scale = ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"]
sil = np.zeros(int(0.4 * SR))
sig = np.concatenate([sil] + [x for n in scale
                              for x in (synth_tone(librosa.note_to_hz(n), sr=SR), sil)])
sf.write(OUT / "base.wav", sig, SR)

enc = {"mp3": ["-c:a", "libmp3lame", "-q:a", "2"], "flac": ["-c:a", "flac"],
       "ogg": ["-c:a", "libvorbis", "-q:a", "5"], "m4a": ["-c:a", "aac", "-b:a", "192k"],
       "aiff": ["-c:a", "pcm_s16be"]}
for ext, args in enc.items():
    subprocess.run(["ffmpeg", "-y", "-i", str(OUT / "base.wav")] + args + [str(OUT / f"base.{ext}")],
                   check=True, capture_output=True)
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=64x64:r=10",
                "-i", str(OUT / "base.wav"), "-c:v", "libx264", "-c:a", "aac",
                "-b:a", "192k", "-shortest", str(OUT / "base.mp4")], check=True, capture_output=True)


def cents(path):
    y = av.load_audio(Path(path))
    f0, vf, vp = librosa.pyin(y, sr=av.SR, fmin=librosa.note_to_hz("G3"),
                             fmax=librosa.note_to_hz("E7"), frame_length=2048, hop_length=256)
    t = librosa.frames_to_time(np.arange(len(f0)), sr=av.SR, hop_length=256)
    p = np.nan_to_num(f0, nan=0.0); per = np.nan_to_num(vp, nan=0.0)
    out = []
    for s, e in av.detect_notes(y):
        hz = av.median_pitch_in_window(t, p, per, s, e, 0.5)
        if hz is not None:
            out.append(av.hz_to_note(hz)[2])
    return out


base = cents(OUT / "base.wav")
print(f"{'format':>6}  {'lossy':>5}  {'notes':>5}  {'max|Δ¢ vs wav|':>14}")
for ext in ["wav", "flac", "aiff", "mp3", "ogg", "m4a", "mp4"]:
    c = cents(OUT / f"base.{ext}")
    n = min(len(c), len(base))
    md = max((abs(c[i] - base[i]) for i in range(n)), default=float("nan"))
    lossy = "no" if ext in ("wav", "flac", "aiff") else "yes"
    print(f"{ext:>6}  {lossy:>5}  {len(c):>5}  {md:>14.2f}")
