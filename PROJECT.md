# PROJECT.md — TUNE

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
auto-scale-detection). If yes → separate skill (e.g. a polyphony/chord transcriber, a timbre
describer). Vibrato-sensitivity and noise-robustness are **experiments**, not skills.
(The vision/bow-technique lane is out of scope entirely — see DESIGN.md §Scope.)

---

## Where things live

- **This folder (`~/Desktop/TUNE`)** — code, skills, experiments, audio. Computer stuff.
- **Google Drive "TUNE" folder** — content: the lab journal (SOURCE OF TRUTH),
  Substack drafts + framing kits, project summary, recording-session plan, reel script.
- **GitHub** (github.com/This-Goober/TUNE) — **this folder is the repo.** `git init` lives
  at the TUNE root, so skills, experiments, and reference audio all publish together; the repo
  reads as a public lab notebook. Anything private lives in `_private/` — gitignored, and kept
  as one obvious top-level folder so it's never dragged into an upload by accident.
  **Branch is `main`, both locally and on the remote** (it was `master` locally until
  2026-08-19, which is why pushes used to misbehave). Publish with `git push`, never by
  uploading files through the GitHub web UI — hand-uploads create a parallel history that
  duplicates local commits and makes the two impossible to reconcile cleanly.

## Folder map (this folder)

```
TUNE/                              ← this folder IS the public repo
├── README.md                      ← the repo's front page (written for visitors)
├── PROJECT.md                     ← this file (on-ramp)
├── .gitignore
├── skills/
│   ├── README.md                  ← what a skill is, how to install it
│   └── Maestro/                   ← the analyzer skill (public)
│       ├── SKILL.md
│       ├── scripts/audio_v0.py
│       └── references/DESIGN.md   ← capability map, known gaps, roadmap (audio only)
├── experiments/
│   ├── README.md                  ← what the experiments ask and answer
│   ├── lib/                       ← shared helpers (run_pyin.py, synth.py)
│   ├── 001-format-m4a-vs-wav/     ← Entry 001
│   ├── phase0-calibration/        ← Entry 002 (scripts + RESULTS.md)
│   ├── phase1-failure-modes/      ← Entry 003 (scripts + RESULTS-phase1.md)
│   └── phase2-judging/            ← the verdict knobs (scripts + RESULTS-phase2.md)
├── tools/
│   └── status.py                  ← prints the repo's ACTUAL state; run before trusting §Current state
├── audio/
│   ├── README.md                  ← what each recording is, and which experiment uses it
│   ├── reference-2026-06/         ← June reference takes (scale_notvib/_vib, wav+m4a)
│   └── phase2-session/            ← drop the recording-session takes here
└── _private/                      ← NEVER publish. maestro-entry lives here.
```

To run an experiment script: `python experiments/<name>/<script>.py` from the project
root. Audio paths point at `audio/`, not the old `samples/`.

**Publishing rule:** everything in this folder is public *except* `_private/`. When uploading
by hand, drag the contents (`skills`, `experiments`, `audio`, `README.md`, `PROJECT.md`) —
never the TUNE folder itself, or it nests a level deep — and never `_private/`.

---

## Standing methods (durable setup)

- **maestro = the instrument.** Pipeline: decode (ffmpeg for non-wav) → resample to
  **22050 Hz mono** → pitch-track → librosa onset segmentation → **median pitch per note**
  (attack trimmed) → octave-fix → merge same-note slivers → optional DTW scale alignment →
  per-note table + accuracy summary. Script judges; the model narrates.
- **Pitch tracker = pYIN, not CREPE.** CREPE needs `torch`; the CUDA wheel overflows disk
  and the CPU wheel's index is blocked in-sandbox. All results so far use librosa pYIN
  (the design doc's documented fallback). **What CREPE is still wanted for is robustness on
  real, noisy, vibrato-laden audio — NOT resolution.** Resolution was solved without it
  (see the two-pass fact below).
- **The metric.** Per note, `cents` = signed distance from the nearest equal-tempered
  semitone on the A=440 grid. Verdict: `OK` if |cents| ≤ 15, else `OFF`; `WRONG` (wrong
  pitch class) only when a scale is given; `unvoiced` = silence. Accuracy = within-tolerance
  ÷ voiced. It scores **intonation precision, not correctness** without a scale, and it's
  hard pass/fail. A uniform tuning offset is penalized (fixed A=440 grid).
- **KEY CALIBRATION FACT (Entry 002).** pYIN's default `resolution=0.1` semitone means the
  ruler reads in **10-cent bins**. Every suspiciously round cents value in older results is
  this quantization.
- **THAT FACT WAS HALF WRONG (Phase 2, 2026-08-17).** Entry 002 measured 1¢ resolution at
  ~360× slower and concluded "cent-level work needs CREPE." The 360× was an artifact of
  searching the whole G3–E7 range at 1¢. **Two-pass refinement** — locate the note at default
  resolution, then re-run at 1¢ over a ±3-semitone band around it — gets mean error from
  2.82¢ to **0.36¢ for 2.8× the cost.** Cent-level work never needed CREPE. ⚠️ Not yet wired
  into `audio_v0.py`; it lives in `experiments/phase2-judging/p2_tworuler.py`.
- **merge_same_note** collapses consecutive identical pitches by design (repeated same notes
  read as one).

---

## Current state

> **⚠️ VOLATILE SECTION — Last verified: 2026-08-19.**
> Everything from here to "Working conventions" goes stale. Do not trust it on sight.
> Run `python tools/status.py` to see what is actually on disk and in git, and reconcile
> before acting on anything below. If the date above is more than a couple of weeks old,
> assume it is wrong.

**Built:** maestro skill packaged + installable; maestro-entry skill (journaling); journal
with storyline + Entries 000–003; Phase 0, Phase 1 and the judging experiments (scripts +
results); launch article published on Substack; recording-session plan + reel script drafted
(Drive).

**Findings so far:**
- *Entry 001* — m4a vs WAV: identical readings on a real same-take pair; format is
  transparent for sustained-note intonation.
- *Entry 002* — Phase 0 calibration: the ruler quantizes to **10¢**; **no inherent top-octave
  imprecision** on clean tones (corrects an earlier hypothesis — that mess was vibrato);
  format-transparent for cents but lossy codecs over-segment onsets (merge absorbs most).
  *Its "fine resolution is impractical" conclusion was later overturned — see Entry 004.*
- *Entry 003* — Phase 1 failure modes (all synthetic): median-per-note is **robust to
  vibrato up to ±50¢** (breaks only at ±75–100¢ via frame loss); the **equal-temperament
  penalty is real** (Just 6th = −15.6¢, past the line) but the 10¢ ruler masks it; noise
  never biases cents, it breaks **note segmentation** (collapse below ~10 dB SNR); short
  notes (<0.3 s) are erratic to count but correct in pitch. Cross-cutting: measurement is
  robust, segmentation is the weak layer, and "too harsh" is a scoring-design choice.
- *Judging experiments (`experiments/phase2-judging/`, run 2026-08-17)* — **the strictness
  dial is quantized into uselessness**: every threshold from ±10¢ to ±20¢ returns an
  identical verdict, so "is ±15¢ too harsh?" is unanswerable on the standing setup.
  **Two-pass refinement fixes the ruler for 2.8×, not 360×** (2.82¢ → 0.36¢ mean error),
  which overturns Entry 002's CREPE-gating conclusion. **And the real unfairness survives
  the fix**: a flawless Just 6th lands ~0.6¢ from the ±15¢ line, so any hard threshold
  decides it by measurement noise rather than musicianship. Graded scoring (87/100) vs hard
  pass/fail (62%) on the same performance; uniform +10¢ offset recovered exactly (→ A4 ≈
  442.5 Hz). ⚠️ **Journal Entry 004 for this is NOT yet written.**

**Open items, in priority order:**
1. **Real audio — the biggest hole.** Everything except Entry 001 is synthetic.
   `audio/phase2-session/` is empty; the T01–T07 session has not happened. The two-pass
   ruler's coarse locating pass has never met vibrato, bow noise, or a room.
2. **The unexplained +1¢ two-pass bias near zero offset** — same magnitude as the effects
   being chased near a threshold. Blocks any sub-cent claim.
3. **Wire two-pass into `audio_v0.py`** so the actual skill benefits, not just the experiment.
4. **Re-run the dial with 24–36 notes.** At N=8 each note is worth 12.5 points.
5. **Multi-target scoring is half-built** — `cents_vs_just` handles just-major only; no
   Pythagorean, no expressive leading tones (~80–90¢), no disagreement report.
6. **Segmentation** — named the weak layer in Entry 003, untouched since. Needs no CREPE.
7. **Vibrato description** (FFT of detrended f0 per note) — turns "vibrato survived" into
   "vibrato measured".
8. **CREPE installation** — now wanted only for robustness on real audio, *not* for
   resolution. Downgraded from blocker to nice-to-have.

**Write-up status:** enough findings exist for Substack #2 (the roadmap's bar is 5 solid
findings or 1–2 deep ones; the dead dial and the coin-flip Just 6th both qualify). Items 1
and 2 above are what would make that post honest rather than entirely synthetic.

---

## Experiment schedule

⚠️ **The phase numbers below drifted from the folder names.** `experiments/phase2-judging/`
contains what this schedule calls **Phase 3**. What the schedule calls Phase 2 (real audio)
has not started. Folder names are kept as-is so existing journal entries and the published
article stay accurate; trust the folder, not the number.

- **Phase 0 — Calibrate the ruler.** ✅ DONE (Entry 002): offset accuracy, register sweep,
  note count, repeatability, format matrix. *(One conclusion since overturned.)*
- **Phase 1 — Failure modes.** ✅ DONE (Entry 003, synthetic control): vibrato-width curve,
  ET/Just/Pythagorean penalty, noise/SNR robustness, short notes + directionality.
- **Phase 3 — The judging.** ✅ MOSTLY DONE, in `experiments/phase2-judging/`: threshold
  sweep, graded vs hard pass/fail, tuning-offset attribution, two-pass ruler. Remaining:
  multi-target scoring, and deriving the graded curve from something real.
- **Phase 2 — Real audio (ACTUALLY NEXT).** Record the sample batch per
  **RECORDING-SESSION-PLAN** (in Drive): T01 no-vib baseline, T02/T03 vibrato widths, T04
  just intonation vs drone, T05 deliberate errors (ground truth), T06 staccato, T07
  repertoire. Doubles as the Instagram reel shoot (see REEL-SCRIPT in Drive). Drop takes in
  `audio/phase2-session/`, analyze into `experiments/phase2-real-audio/`, compare against
  the synthetic baselines. Every headline finding so far is synthetic-only until this runs.
- **Phase 4 — Capability ladder (forward-looking arc).** sharp/flat → auto key/scale detection
  (maestro mode) → chords/harmony wall (needs polyphonic transcription, e.g. Basic Pitch — a
  separate skill) → monophonic melody → sheet music. Answers "what's the value?"
- **Phase 5 — Breadth.** Other monophonic instruments; melody vs scale; graceful failure on
  double-stops.

## Working conventions

- **Logging.** After an experiment or at end of day, use the **maestro-entry** skill: it
  outputs (A) a new numbered Entry in the fixed template and (B) a full-replacement plain-English
  storyline. Paste both into the Drive journal. Entries so far run 000–003 → **next is 004**.
  Pull real numbers from the actual run; never invent.
- **Journal is source of truth**, kept in Drive (`maestro-lab-journal.md`). This PROJECT.md
  is the orientation layer.
- **Keeping this file honest.** The §Current state block is hand-maintained and WILL rot.
  Two rules: (a) anyone — human or model — picking this project up runs
  `python tools/status.py` and reconciles its output against §Current state *before* acting
  on the doc; (b) whoever finishes an experiment updates §Current state and bumps its
  "Last verified" date in the same commit as the results. A finding that isn't reflected
  here within one commit is a finding someone will redo by accident.
- **Content goes to Drive; code/audio stays here.** Substack drafts, framing kits, plans,
  and scripts-for-video are Drive docs. Experiment scripts, skills, and recordings live in
  this folder.
- **New skills** get their own `skills/<name>/` folder (self-contained: SKILL.md + scripts/ +
  references/, relative paths). Private helpers live in `_private/`, never in `skills/`.

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
