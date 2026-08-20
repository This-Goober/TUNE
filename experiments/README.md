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
| [`phase2-judging/`](phase2-judging/) | Is the pass/fail verdict itself fair, and can it be adjusted? | The strictness dial mostly **doesn't work** — and the ruler can be fixed cheaply. |
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

**The strictness dial barely functions.** Sweeping the pass/fail threshold, every setting from
±10¢ to ±20¢ gives an identical verdict — 22 of 25 steps change nothing. The tool literally
cannot tell a strict setting from a lenient one, because the reading is quantized more coarsely
than the dial. "Is ±15¢ too harsh?" is unanswerable on the standing setup.

**But the ruler was fixable for free.** Locating a note coarsely and then re-measuring at 1¢
resolution over a narrow band around it cuts the error from 2.8¢ to 0.36¢ for 2.8× the time —
not the 360× that got fine resolution shelved as impractical. That cost was an artifact of
searching the whole pitch range at once, not a fact about the tracker.

**And the real problem survived the fix.** Once the ruler is fine enough to see the
equal-temperament penalty, what it reveals is a legitimate musical choice sitting about half a
cent from the fail line — close enough that any hard threshold decides it by measurement noise.
Precision doesn't settle which standard applies. That question isn't a measurement problem.

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

Everything above tests *measurement*. The open questions are all about *judgment* — whether
the verdict is fair, not whether the number is right:

- **Sweep the threshold.** Treat ±15¢ as a variable and find where the verdicts start agreeing
  with musical judgment.
- **Score against several targets at once.** Equal temperament, Just, Pythagorean, and the
  narrow expressive leading tones violinists actually prefer (~80–90¢ semitones) — and report
  the disagreement instead of picking a winner.
- **Harmonic context.** Let the target move with the music rather than staying pinned to a grid.
- **Ask musicians.** Compare the scorer's verdicts against what trained ears prefer. If they
  disagree, the scorer is wrong by definition.
- **CREPE vs pYIN on real recordings**, and real audio generally — a session with deliberate,
  known errors is the first honest test of whether any of this survives actual playing.
