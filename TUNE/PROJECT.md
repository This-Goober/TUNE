# PROJECT.md — TUNE / maestro / "Vibe-Coding an Ear"

**Read this first, then the Drive journal (`maestro-lab-journal.md`), before doing anything.**
This file is the on-ramp: it exists so a fresh session with no memory of prior chats can
become fully oriented from the files alone. If something here conflicts with the journal,
the **journal is newer and wins** — update this file when the project moves on.

---

## What this project is

An open-ended probe into **what AI can do with audio analysis using only "vibe coding"
and Claude skills** — no fixed app, no model trained from scratch, just composable
instructions wired to off-the-shelf parts.

The bet: **apps are frozen; skills are not.** A shipped app encodes one team's fixed idea
of what you want; a skill is an abstract, shareable recipe the user bends to their own
question mid-stream. The project stress-tests that idea on one domain: **violin intonation
scoring** — tech that exists but sits in an awkward "borderline-useful, nobody-adopts-it"
spot because it's too harsh and too sensitive to vibrato and noise. The recurring question
under every experiment: **where is the line between a real mistake and the tool being
oversensitive, and can the skill approach map or move it?**

The output is a **Substack series** ("Vibe-Coding an Ear"); the journal is the draft
material. **Post #1 is published** (launch article, 2026-07).

---

## The three layers (do not conflate)

1. **Project** — the whole effort, named TUNE (maestro is the flagship skill inside it).
2. **Skill** — a reusable capability a session auto-invokes. `maestro` (the analyzer) is
   the flagship skill.
3. **Experiment** — a one-off study run *with* a skill (does format matter? does vibrato
   break it?). Experiments are **not** skills; they're scripts + a journal entry, and the
   write-ups become the articles.

**Test for "is this a new skill?"** Would you ever run it *without* first analyzing pitch?
If no → it's a mode/flag inside maestro (e.g. graded scoring, vibrato-aware scoring,
auto-scale-detection). If yes → separate skill (e.g. the vision/bow-technique lane, a
polyphony/chord transcriber, a timbre describer). Vibrato-sensitivity and noise-robustness
are **experiments**, not skills.

---

## Where things live

- **This folder (`~/Desktop/TUNE`)** — code, skills, experiments, audio. Computer stuff.
- **Google Drive "TUNE" folder** — content: the lab journal (SOURCE OF TRUTH),
  Substack drafts + framing kits, project summary, recording-session plan, reel script.
- **GitHub** (github.com/This-Goober/Maestro) — **this folder is the repo.** `git init` lives
  at the TUNE root, so skills, experiments, and reference audio all publish together; the repo
  reads as a public lab notebook. `skills/maestro-entry/` is gitignored and stays private.

## Folder map (this folder)

```
TUNE/
├── PROJECT.md                     ← this file (on-ramp)
├── skills/
│   ├── Maestro/                   ← the analyzer skill / GitHub repo mirror
│   │   ├── SKILL.md
│   │   ├── scripts/audio_v0.py
│   │   └── references/DESIGN.md   ← full multi-modal roadmap (audio+vision+VLM)
│   └── maestro-entry/             ← PRIVATE journaling helper (keeps entries consistent;
│                                     do NOT push to the public GitHub repo)
├── experiments/
│   ├── lib/                       ← shared helpers (run_pyin.py, synth.py)
│   ├── 001-format-m4a-vs-wav/     ← Entry 001
│   ├── phase0-calibration/        ← Entry 002 (scripts + RESULTS.md)
│   ├── phase1-failure-modes/      ← Entry 003 (scripts + RESULTS-phase1.md)
│   └── phase2-real-audio/         ← next: real-recording analysis goes here
├── audio/
│   ├── reference-2026-06/         ← June reference takes (scale_notvib/_vib, wav+m4a)
│   └── phase2-session/            ← drop the recording-session takes here (see README)
└── _archive/                      ← old handoff bundle; safe to delete after review
```

To run an experiment script: `python experiments/<name>/<script>.py` from the project
root. Audio paths now point at `audio/`, not the old `samples/`.

---

## Standing methods (durable setup)

- **maestro = the instrument.** Pipeline: decode (ffmpeg for non-wav) → resample to
  **22050 Hz mono** → pitch-track → librosa onset segmentation → **median pitch per note**
  (attack trimmed) → octave-fix → merge same-note slivers → optional DTW scale alignment →
  per-note table + accuracy summary. Script judges; the model narrates.
- **Pitch tracker = pYIN, not CREPE.** CREPE needs `torch`; the CUDA wheel overflows disk
  and the CPU wheel's index is blocked in-sandbox. All results so far use librosa pYIN
  (the design doc's documented fallback). **This is a real constraint, not a footnote —
  see the 10¢ finding.**
- **The metric.** Per note, `cents` = signed distance from the nearest equal-tempered
  semitone on the A=440 grid. Verdict: `OK` if |cents| ≤ 15, else `OFF`; `WRONG` (wrong
  pitch class) only when a scale is given; `unvoiced` = silence. Accuracy = within-tolerance
  ÷ voiced. It scores **intonation precision, not correctness** without a scale, and it's
  hard pass/fail. A uniform tuning offset is penalized (fixed A=440 grid).
- **KEY CALIBRATION FACT (Entry 002).** pYIN's default `resolution=0.1` semitone means the
  ruler reads in **10-cent bins**. Fine resolution (0.01 = 1¢) is accurate but ~360× slower
  and impractical on real recordings → **cent-level work needs CREPE.** Every suspiciously
  round cents value in older results is this quantization.
- **merge_same_note** collapses consecutive identical pitches by design (repeated same notes
  read as one).

---

## Current state (as of Entry 003, 2026-07-02; folder reorganized 2026-07-15)

**Built:** maestro skill packaged + installable; maestro-entry skill (journaling); journal
with storyline + Entries 000–003; Phase 0 + Phase 1 experiment scripts + results;
launch article published on Substack; recording-session plan + reel script drafted (Drive).

**Findings so far:**
- *Entry 001* — m4a vs WAV: identical readings on a real same-take pair; format is
  transparent for sustained-note intonation.
- *Entry 002* — Phase 0 calibration: the ruler quantizes to **10¢**; the accurate setting
  is ~360× slower (needs CREPE); **no inherent top-octave imprecision** on clean tones
  (corrects an earlier hypothesis — that mess was vibrato); format-transparent for cents but
  lossy codecs over-segment onsets (merge absorbs most).
- *Entry 003* — Phase 1 failure modes (all synthetic): median-per-note is **robust to
  vibrato up to ±50¢** (breaks only at ±75–100¢ via frame loss); the **equal-temperament
  penalty is real** (Just 6th = −15.6¢, past the line) but the 10¢ ruler masks it; noise
  never biases cents, it breaks **note segmentation** (collapse below ~10 dB SNR); short
  notes (<0.3 s) are erratic to count but correct in pitch. Cross-cutting: measurement is
  robust, segmentation is the weak layer, and "too harsh" is a scoring-design choice.
  (The Entry 002 C4 outlier did not reproduce — fragile onset edge effect, closed.)

**Open items:** CREPE installation (the gating step for cent-level work: fair ET-penalty
measurement, CREPE-vs-pYIN comparison, redoing the vibrato curve with a continuous tracker).

---

## Experiment schedule

- **Phase 0 — Calibrate the ruler.** ✅ DONE (Entry 002): offset accuracy, register sweep,
  note count, repeatability, format matrix.
- **Phase 1 — Failure modes.** ✅ DONE (Entry 003, synthetic control): vibrato-width curve,
  ET/Just/Pythagorean penalty, noise/SNR robustness, short notes + directionality.
- **Phase 2 — Real audio (NEXT).** Record the sample batch per **RECORDING-SESSION-PLAN**
  (in Drive): T01 no-vib baseline, T02/T03 vibrato widths, T04 just intonation vs drone,
  T05 deliberate errors (ground truth), T06 staccato, T07 repertoire. Doubles as the
  Instagram reel shoot (see REEL-SCRIPT in Drive). Drop takes in `audio/phase2-session/`,
  analyze into `experiments/phase2-real-audio/`, compare against the synthetic baselines.
  Optionally add a public professional recording (a live demo of the ET penalty).
- **Phase 3 — The judging.** Threshold sweep (is ±15¢ arbitrary?); hard pass/fail vs graded
  score; tuning-offset attribution. Blocked in part by CREPE.
- **Phase 4 — Capability ladder (forward-looking arc).** sharp/flat → auto key/scale detection
  (maestro mode) → chords/harmony wall (needs polyphonic transcription, e.g. Basic Pitch — a
  separate skill) → monophonic melody → sheet music. Answers "what's the value?"
- **Phase 5 — Breadth.** Other monophonic instruments; melody vs scale; graceful failure on
  double-stops.

---

## Working conventions

- **Logging.** After an experiment or at end of day, use the **maestro-entry** skill: it
  outputs (A) a new numbered Entry in the fixed template and (B) a full-replacement plain-English
  storyline. Paste both into the Drive journal. Entries so far run 000–003 → **next is 004**.
  Pull real numbers from the actual run; never invent.
- **Journal is source of truth**, kept in Drive (`maestro-lab-journal.md`). This PROJECT.md
  is the orientation layer.
- **Content goes to Drive; code/audio stays here.** Substack drafts, framing kits, plans,
  and scripts-for-video are Drive docs. Experiment scripts, skills, and recordings live in
  this folder.
- **New skills** get their own `skills/<name>/` folder (self-contained: SKILL.md + scripts/ +
  references/, relative paths). `maestro-entry` stays out of the public GitHub repo.

---

## The article's forming thesis

We set out to replicate an intonation scorer and found the judging is the least useful thing
the pitch tech can do — too harsh, vibrato-fragile, and (Phase 0) measured with a coarse ruler.
Point the *same* capability at creating and informing — what key am I in, transcribe my
improvisation, feedback instead of a grade — and the value appears. And the form that takes is
the original bet: not one frozen app, but a small **family of composable skills** the player steers.

---

## Honest limits of this handoff

A fresh session knows **what these files say**, not the reasoning, dead ends, or corrections
from the chats that produced them (e.g. *how* the top-octave hypothesis got overturned). The
richer the journal, the more continuous it feels; unwritten nuance does not carry over. When in
doubt, re-run the experiment — the scripts and RESULTS.md make the findings reproducible.
