# MAESTRO — Design

The analyzer behind TUNE: what it measures, how, and — more importantly — what it refuses to
decide for you.

**Scope: audio only.** An earlier draft of this document sketched a second "vision lane"
(bow angle, contact point, posture, hand geometry from video). That's cut. It was a different
project wearing this project's name. The question here is what "in tune" means and whether a
computer can judge it, and a camera doesn't help answer that.

## 1. The two jobs

Every intonation tool does two things that get conflated:

| | Job | Status |
|---|---|---|
| **Measurement** | Turn audio into a fundamental frequency, note by note | Largely solved |
| **Judgment** | Decide whether that frequency is *correct* | Not solved — and the actual subject of this project |

Measurement is a signal-processing problem with decades of good answers. Judgment is a musical
question with no fixed answer: a leading tone that violinists prefer at 80–90 cents reads as
10–20 cents "wrong" against a 100-cent equal-tempered grid, and eight artist-level violinists
recorded playing the same Bach don't consistently follow *any* single tuning system.

So the design rule that follows: **the analyzer measures and reports; it never silently decides
what standard to measure against.** Every judgment constant is an explicit, visible setting.

## 2. Capability map

| Capability | Approach | Status |
|---|---|---|
| Monophonic pitch (f0) | **CREPE** (neural, robust to vibrato and noise) | Not installed — dependency stack fails here. Wanted for *robustness*, not resolution |
| Monophonic pitch, fallback | **librosa pYIN** (probabilistic YIN + HMM) | **In use.** Quantizes to 10¢ at default resolution |
| Cent-level resolution | **Two-pass pYIN**: locate coarsely, refine at 1¢ over a ±3-semitone band | Proven in Phase 2 (0.36¢ mean error, 2.8× cost). **Not yet wired into the pipeline** |
| Note onset / segmentation | librosa `onset_detect` + merge pass | Built; the weakest layer |
| Scale alignment | DTW against a named scale template | Built; optional (`--scale`) |
| Cents deviation | Signed distance to a stated reference grid | Built |
| Reference pitch | A=440 default, settable (442, 443) | Built |
| Alternative tuning targets | Just / Pythagorean interval tables | Built (Phase 2) |
| Graded score | Partial credit instead of pass/fail | Built (Phase 2), not yet default |
| Vibrato rate & depth | FFT of detrended f0 within a note | Not built — see §5 |
| Dynamics / timbre | librosa RMS, spectral centroid | Not built |
| Polyphony (double stops, chords) | Would need a separate tool (e.g. Basic Pitch) | Out of scope — see §6 |
| Narration | Model reads the numbers, writes the report | Built |

## 3. Pipeline

```
input (.wav/.m4a/.mp4)
   │  ffmpeg decode → 22050 Hz mono
   │
   ├── pitch track (pYIN; CREPE when available) → f0(t)
   │      └── optional second pass at 1¢ over a narrow band → cent-level f0  [built, not default]
   ├── onset detect → note boundaries
   │      └── merge over-segmented slivers, drop unvoiced
   ├── per note: median f0 over the window, attack transient trimmed
   │      └── octave-error correction
   ├── optional: DTW align to a named scale → note labels
   │
   ├── JUDGE: cents = distance to the chosen reference
   │      knobs: reference pitch · tuning system · tolerance · graded vs binary
   │
   └── per-note table + summary  →  model narrates the report
```

**Why the median per note.** Taking one median reading per note rather than scoring every frame
is the single most consequential choice in the pipeline. It launders symmetric vibrato (a
centered note reads in tune out to ±50¢ of vibrato width), and it washes out codec artifacts
and room noise the same way. Most of the "harshness" players complain about in commercial
intonation scorers is frame-by-frame grading, not pitch measurement.

## 4. Principles

1. **The script judges, the model narrates.** The analyzer computes every number; the model only
   turns numbers into prose. It may not assert a pitch fact the analyzer didn't produce. This is
   what keeps the reports honest.
2. **Degrade gracefully, and say so.** CREPE → pYIN when the dependency stack fails, with the
   downgrade stated in the output rather than hidden. A skill's portability is capped by its
   heaviest dependency.
3. **Thresholds are reporting knobs, not score-fixers.** Never widen the tolerance to make an
   accuracy number look better. If the threshold is doing the work, that's the finding.
4. **Name the reference.** "15 cents flat" is meaningless without saying flat *of what*. Every
   report states the reference pitch and tuning system it judged against.
5. **A uniform offset is a tuning observation, not a performance error.** If every note is
   +10¢, the instrument is tuned near 442 — report that, don't penalize the player twelve times.

## 5. Known gaps

1. **The ruler reads in 10¢ steps — but this is now fixable, and unfixed.** pYIN's default
   resolution is 0.1 semitone, nearly as coarse as the ±15¢ line it's judged against. This
   document previously said fine resolution was ~360× slower and that CREPE was the fill.
   **Both claims were wrong.** The 360× came from searching the entire G3–E7 range at 1¢;
   a two-pass search (locate coarse, refine over ±3 semitones) reaches 0.36¢ mean error for
   2.8× the cost. *Fill: port `read_twopass` from `experiments/phase2-judging/p2_tworuler.py`
   into this pipeline.* Until that port happens, the shipped analyzer still reads in 10¢ bins
   and every judging knob downstream is capped by it.
   **Caveat blocking the port:** the two-pass reading runs ~+1¢ high near zero offset, cause
   unknown, and it has never been tested on real (vibrato, noisy, reverberant) audio where
   the coarse locating pass may not be reliable.
2. **Segmentation is the fragile layer.** Under noise, or on notes shorter than ~0.3 s, the tool
   miscounts where notes begin and end — while reading every pitch it does catch correctly.
   *Fill: better onset handling, or score against an aligned score rather than detected onsets.*
3. **Hard pass/fail.** 15.0¢ passes and 15.1¢ fails, with no partial credit. A graded scorer
   exists in Phase 2 but isn't the default yet, and **its curve (full credit ±10¢, zero at
   ±50¢) is invented** — not derived from anything a musician reported. *Fill: decide what a
   fair curve looks like — which is a musical question, not a coding one.*
   Sharper form of the problem, from Phase 2: a flawless just-intonation 6th lands ~0.6¢ from
   the ±15¢ line, so **any** hard threshold decides that note by measurement noise. Precision
   does not rescue the verdict; it relocates the coin flip.
4. **No harmonic context.** The tool judges each note against a fixed grid with no idea what
   chord it sits in, whether it's a leading tone, or whether it's a melodic passage (where
   Pythagorean tendencies show up) versus a double stop (where players lean Just). This is the
   largest gap between what it measures and what a musician hears.
5. **Vibrato is survived, not described.** The median makes vibrato harmless to the score, but
   the tool can't tell you the rate or width — which is the feedback a teacher would actually
   want. *Fill: FFT of the detrended f0 inside each note window.*
6. **Monophonic only.** Double stops and chords produce garbage. Detecting that condition and
   saying "I can't score this" is more useful than a confident wrong answer.
7. **No correctness without a scale.** Given no `--scale`, the tool measures how cleanly each
   note is played, not whether it was the right note. A wrong note played perfectly in tune to
   itself reads OK.

## 6. Roadmap

In rough order of what would teach the most, and matching the open questions in the write-ups:

- ~~**Sweep the threshold.**~~ ✅ Done (Phase 2). Result: on the standing 10¢ ruler the dial
  has no effect between ±10¢ and ±20¢ — 22 of 25 steps are dead. With the two-pass ruler it
  tracks ground truth closely. The dial was never the problem; the ruler under it was.
- **Alternative pitch targets.** Score the same performance against equal temperament, Just,
  Pythagorean, and expressive leading tones (~80–90¢ semitones) and report the disagreement
  rather than picking a winner.
- **Harmonic context.** Give the scorer the chord or function a note sits in, so the target can
  move with the music instead of staying pinned to one grid.
- **Human preference.** Ask musicians which of several manipulated versions they prefer, and
  compare that to what the scorer says. If the tool disagrees with trained ears, the tool is
  wrong by definition.
- **CREPE vs pYIN on real recordings.** How much of the residual noise is the tracker, and does
  a finer ruler change any verdict?
- **Real audio generally.** Everything so far is synthetic control. A recording with deliberate,
  known errors is the first honest test.

## 7. Non-goals

- **Video and technique.** No bow tracking, posture, or fingering analysis. Different problem.
- **Replacing a teacher.** The output is a readable report to hand to a human, not a grade.
- **Declaring one true intonation.** If artist-level violinists don't agree on a single system,
  a script shouldn't pretend to. The useful output is *where* a performance sits relative to
  several defensible standards — and how far apart those standards are.
