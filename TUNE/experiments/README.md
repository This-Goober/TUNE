# experiments/

Everything here exists to answer one question: **when the tool says a note is out of tune,
is it right?**

That sounds simple and isn't. A scorer can be wrong in two directions — missing a real
mistake, or flagging something a musician would call correct. Before any of its verdicts mean
anything, you have to know how accurately it measures, where it falls apart, and which of its
"errors" are actually the ruler's fault. That's what these folders work through, roughly in
order.

Most experiments run on **synthetic tones** — notes generated at an exactly known pitch. That's
deliberate: if the tool reads a tone we built to be 15¢ flat as 20¢ flat, the 5¢ is the tool's
error, not a player's. Real recordings can't tell you that, because nobody knows the true pitch
of a human performance. Synthetic first, real playing after.

## The folders

| Folder | Question it asks | Short answer |
|---|---|---|
| [`001-format-m4a-vs-wav/`](001-format-m4a-vs-wav/) | Does a compressed file (m4a) change the reading vs lossless (WAV)? | No — identical to the decimal on the same take. |
| [`phase0-calibration/`](phase0-calibration/) | Does the tool measure correctly at all? | Mostly, but it reads in **10¢ steps** — a blunt ruler. |
| [`phase1-failure-modes/`](phase1-failure-modes/) | Where does it break — vibrato, noise, short notes, expressive tuning? | Pitch measurement is tough; **note-splitting** is the weak part. |
| [`phase2-judging/`](phase2-judging/) | Is the pass/fail verdict itself fair, and can it be adjusted? | Turns the hidden constants into visible, adjustable knobs. |
| [`lib/`](lib/) | — | Shared helpers: tone synthesis and the pitch-tracker wrapper. |

Each folder has a `RESULTS` file with the actual numbers, tables, and caveats. The narrative
version of all this — why it matters, what surprised me — is on the Substack; these files are
the receipts.

## What we know so far

**The ruler is coarse.** The pitch tracker in use (pYIN) rounds every reading to the nearest
10 cents by default. The pass/fail line is at 15 cents. So the measuring stick is nearly as
coarse as the thing it's measuring. A precise setting exists but runs ~360× slower, which is
unusable on a real recording — the accurate tracker (CREPE) won't install in this environment,
and that's currently the biggest blocker in the project.

**Vibrato doesn't break it — which was the surprise.** Vibrato is the top reason players
abandon these tools. But because the tool takes one median reading per note, a note centered
in tune reads in tune even with very wide vibrato (±50¢). It only fails at extremes. The
harshness players complain about comes from tools that grade *every instant* of a note, not
from measuring pitch.

**Noise and file format don't bias it either** — same reason, the median washes them out.

**What actually breaks is counting the notes.** Under noise or on fast notes, the tool
mis-splits where one note ends and the next begins. Every pitch it does catch is accurate; it
just catches the wrong number of them.

**The one real unfairness: expressive tuning.** Play a scale in "just" intonation — the sweeter,
older tuning musicians naturally lean into — and its sixth sits about 15.6¢ below the piano
grid, just past the fail line. A flawless performance gets marked wrong. And the coarse 10¢
ruler currently rounds that error away, hiding the tool's most interesting flaw behind its
other one.

## Which audio each experiment uses

| Experiment | Audio |
|---|---|
| 001-format-m4a-vs-wav | `audio/reference-2026-06/scale_notvib.wav` + `.m4a` (same take, both formats) |
| phase0-calibration | Synthetic tones only (generated at runtime) |
| phase1-failure-modes | Synthetic tones only |
| phase2-judging | Synthetic tones; built to accept a real recording as a drop-in |

See [`audio/`](../audio/) for what each recording is.

## Running them

From the repo root:

```bash
python experiments/<folder>/<script>.py
```

You'll need the analyzer's dependencies — `librosa`, `numpy`, `soundfile`, and `ffmpeg` on
your PATH for anything touching m4a/mp4. Experiments that generate their own tones need no
audio files at all, so they're the easiest to reproduce.

## What's next

- **Real audio.** Everything above characterizes the *evaluator*. A recording session with
  known, deliberate errors is the next batch — that's the first test of whether these findings
  survive contact with actual playing.
- **CREPE.** Getting the accurate tracker running unlocks the cent-level questions: how much
  of the leftover noise is just the tracker, and whether the expressive-tuning penalty is as
  bad as it looks once the ruler is fine enough to see it.
