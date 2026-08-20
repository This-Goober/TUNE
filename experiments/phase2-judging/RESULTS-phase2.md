# Phase 2 — Results (2026-08-18)

**The judging, not the measuring.** Phases 0 and 1 asked whether the tool reads pitch
correctly. This phase asks whether its *verdict* is fair, and whether the knobs that control
that verdict actually control anything.

Same pipeline as Phases 0–1 (pYIN, 22050 Hz, median-per-note), same synthetic-control method:
every tone is generated at an exactly known pitch, so any error reported here is the tool's.
Scripts in this folder reproduce every number below.

Test performance for the dial experiments: a D-major scale with hand-set per-note errors
(−8, +3, +18, −22, +5, −12, +2, +9 ¢) **plus a uniform +10¢**, standing in for an instrument
tuned near A=442.5. True cents are therefore +2, +13, +28, −12, +15, −2, +12, +19.

---

## A. Graded scoring vs hard pass/fail  (`p2_demo.py`)

| note | reads | hard @±15¢ | graded |
|---|---|---|---|
| D4 | +0.0¢ | OK | 100 |
| E4 | +10.0¢ | OK | 100 |
| F#4 | +30.0¢ | **OFF** | 50 |
| G4 | −10.0¢ | OK | 100 |
| A4 | +20.0¢ | **OFF** | 75 |
| B4 | +0.0¢ | OK | 100 |
| C#5 | +10.0¢ | OK | 100 |
| D5 | +20.0¢ | **OFF** | 75 |

**Hard pass/fail: 62%. Graded: 87/100.** Same performance, two numbers that tell different
stories — and the gap is the point. Pass/fail throws away *how* off a note was, so the 30¢ note
and the 20¢ notes are equally "wrong". The graded score (full credit inside ±10¢, linear decay
to zero at ±50¢) preserves the distinction a teacher would actually care about.

Neither number is more correct. But a player told "62%" hears a failing grade; a player told
"87, and your F# is the one to work on" hears something usable.

## B. The strictness dial has dead zones  (`p2_tworuler.py`)

Sweeping the pass/fail threshold from 5¢ to 30¢ in 1¢ steps, on the standing setup:

| threshold | pass rate |
|---|---|
| 5–9¢ | 25% |
| **10–20¢** | **62%** |
| 21–29¢ | 88% |
| 30¢ | 100% |

**Every setting from ±10¢ to ±20¢ produces an identical verdict.** Choosing ±15¢ over ±10¢ or
±20¢ is not a strict-or-lenient decision; it changes nothing at all. Across 5–30¢, only 3 of
26 settings move the result — **22 of 25 steps are dead.**

The cause is Entry 002's finding, now biting: pYIN's default resolution snaps every reading
into a 10¢ bin, so a threshold only flips a verdict when it crosses a bin edge. A dial finer
than the ruler underneath it is not a dial.

This matters beyond tidiness. "Is ±15¢ too harsh?" was one of this project's opening
questions — and with the standing setup **the question is unanswerable**, because the tool
cannot tell ±15¢ from ±10¢ or ±20¢.

## C. The ruler can be made fine *and* fast — without CREPE  (`p2_tworuler.py`)

Entry 002 measured 1¢ resolution at ~360× slower than default and shelved it as impractical,
which is where "cent-level work needs CREPE" came from. That number came from searching the
**entire G3–E7 range** at 1¢ resolution — roughly 45 semitones × 100 bins.

Constraining the search fixes it. **Two-pass refinement:** locate the note at default
resolution over the full range, then re-run at 1¢ resolution over a ±3-semitone band around
what you found. No prior knowledge of the played note required.

Known detunings on A4 (0.7 s tones):

| true | coarse (standing) | error | two-pass | error |
|---|---|---|---|---|
| +0¢ | +0.0¢ | +0.0 | +1.0¢ | +1.0 |
| −5¢ | +0.0¢ | +5.0 | −4.0¢ | +1.0 |
| −8¢ | −10.0¢ | −2.0 | −7.0¢ | +1.0 |
| −12¢ | −10.0¢ | +2.0 | −12.0¢ | 0.0 |
| −15¢ | −10.0¢ | +5.0 | −15.0¢ | 0.0 |
| −16¢ | −20.0¢ | −4.0 | −16.0¢ | 0.0 |
| −20¢ | −20.0¢ | 0.0 | −20.0¢ | 0.0 |
| −25¢ | −20.0¢ | +5.0 | −25.0¢ | 0.0 |
| +7¢ | +10.0¢ | +3.0 | +8.0¢ | +1.0 |
| +13¢ | +10.0¢ | −3.0 | +13.0¢ | 0.0 |
| +18¢ | +20.0¢ | +2.0 | +18.0¢ | 0.0 |

**Mean |error|: 2.82¢ → 0.36¢, an 8× improvement, at 2.8× the cost — not 360×.**
In wall-clock terms, 0.13 s → 0.36 s per note.

This partially overturns a standing project assumption. CREPE is still worth having (it's
more robust on real, noisy, vibrato-laden audio, which synthetic tones don't test), but
**cent-level resolution was never the thing that required it.** The 360× figure was an
artifact of how the search was configured, not a property of pYIN.

Residual bias worth noting: the two-pass reading runs about **+1¢ high near zero offset** and
is exact further out. Small, but the same size as the effects being chased near a threshold.

## D. With a fine ruler, the dial starts working

Same performance, same sweep, all three columns:

| ±¢ | coarse | two-pass | ground truth |
|---|---|---|---|
| 5–9 | 25% | 25% | 25% |
| 10–11 | 62% | 25% | 25% |
| 12 | 62% | 38% | 50% |
| 13–14 | 62% | 50% | 62% |
| 15–18 | 62% | **75%** | **75%** |
| 19–20 | 62% | 75% | 88% |
| 21–27 | 88% | 88% | 88% |
| 28 | 88% | 88% | 100% |
| 29 | 88% | 100% | 100% |
| 30 | 100% | 100% | 100% |

The two-pass column tracks the truth closely — exactly right through 13–18¢ and 21–27¢, and
never more than one step away. The coarse column is badly wrong through the entire 10–20¢
region, which is precisely where a musician would want to set the threshold.

Dead steps drop from 22/25 to 20/25 — still high, but that's now a property of having only 8
notes (each note flipping moves the rate by 12.5 points), not of the ruler.

## E. Reference pitch: report the offset, don't punish it  (`p2_demo.py`)

The scale was synthesized +10¢ sharp overall. The offset detector recovered it exactly:

> uniform offset **+10.0¢** → suggests **A4 ≈ 442.5 Hz**

Against a fixed A=440 grid, that offset is charged to *every note*, twelve times over. Once
reported, it becomes one sentence about the instrument's tuning rather than eight intonation
errors — and the player's actual per-note errors become visible underneath it.

Caution found while running this: re-judging the same notes at a *rounded* A=443 made things
worse (D4 went from +0.0¢ to −11.8¢), because 443 overshoots the true 442.5 by ~2¢. The right
move is to judge against the **detected** reference, not the nearest standard pitch.

## F. Equal temperament vs just intonation — the comparison the ruler hides

Scoring a perfectly played just-intonation D-major scale both ways, on the standing setup:

**0 notes flagged OFF under ET. 0 under Just.** The demo intends to show expressive intonation
being unfairly punished, and at default resolution **it cannot show it** — because the 10¢
binning rounds the Just 6th's −15.6¢ up to −10¢, comfortably inside the line.

Isolating the two intervals that should cross it:

| interval | true | coarse | fine (1¢, wide band) | fine (1¢, ±3 semitone band) |
|---|---|---|---|---|
| Just 3rd | −13.7¢ | −10.0¢ → OK | — | −12.7¢ → OK |
| Just 6th | −15.6¢ | −10.0¢ → **OK** | −15.0¢ → **OFF** | −14.6¢ → **OK** |

The Just 6th flips verdict depending on how it's measured. It sits ~0.6¢ from the ±15¢ line,
so the decision is made by measurement noise, not by musicianship.

**That is the finding, and it's a bigger one than "the tool is too harsh":** the case this
project cares most about — a flawless expressive performance being marked wrong — lands close
enough to the threshold that *any* hard line will decide it arbitrarily. Sharpening the ruler
doesn't rescue the verdict; it just relocates the coin flip.

---

## Cross-cutting finding

Phase 1 concluded the measurement was more robust than the scoring. Phase 2 sharpens that:
**every judging knob is capped by the ruler beneath it.** The threshold dial has a dead range
covering the settings anyone would actually pick. The ET-vs-Just comparison can't render its
own point. The offset detector reports in 10¢ steps.

And the fix for the ruler turned out to be cheap — a two-pass search, not a 1 GB dependency.

The deeper problem survives the fix. Once the ruler is fine enough to see the equal-temperament
penalty, what it shows is a legitimate musical choice sitting half a cent from the fail line.
No amount of measurement precision decides whether that note is "in tune." That's a question
about which standard applies, and it can't be answered by measuring harder.

## Caveats / threats to validity

- **All synthetic.** These are clean, steady, single-pitch tones. They test the evaluator, not
  playing. Real audio has vibrato, bow noise, and room — the two-pass speedup in particular
  should be re-timed on real recordings, where the coarse locating pass is less reliable.
- **8 notes** in the dial experiments. Each note is worth 12.5 percentage points, so the pass
  rates are coarse in their own way. Directionally sound, not precise.
- **The ±3-semitone band is a floor, not a choice.** librosa errors below roughly 5 semitones
  of range at 0.01 resolution, so the band couldn't be narrowed further to test whether the
  speedup improves.
- **The +1¢ two-pass bias near zero** is unexplained; likely an interaction between band edges
  and the median. Worth chasing before trusting sub-cent claims.
- **The graded curve (full credit ±10¢, zero at ±50¢) is invented**, not derived from anything
  musicians reported. It's a shape to argue about, not a result.

## What this opens

The measurement questions are now largely closed. What's left is the judgment question, and it
isn't a coding problem:

- Score the same performance against ET, Just, Pythagorean, and expressive leading tones
  (~80–90¢ semitones) at once, and **report the disagreement** instead of picking a winner.
- Give the scorer harmonic context, so the target moves with the music.
- Ask actual musicians which version they prefer, and check the tool against their ears rather
  than against a grid.
- Re-run all of this on real audio, where the two-pass ruler has to survive vibrato.
