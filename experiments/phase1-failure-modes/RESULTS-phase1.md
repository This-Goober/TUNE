# Phase 1 — Results (2026-07-02)

Failure-mode characterization of the **pYIN-backed** maestro evaluator, using
**synthetic tones as the control**: the true pitch/vibrato-width/SNR/tuning is known
exactly, so every error reported here is the *evaluator's*, not a player's. Same 6-partial
violin-ish timbre and same pipeline (pYIN, 22050 Hz, median-per-note, ±15¢) as Phase 0, so
numbers are comparable across phases. CREPE still unavailable in-environment.

Scripts in this folder reproduce every number. Harness validated against Phase 0 before use
(10¢ binning and E5 +25¢→+30¢ snap reproduced exactly; a perfect A4 control reads +0.0¢).

---

## A. Vibrato-width degradation curve  (`p1_vibrato.py`)

Sustained tone, **symmetric** sinusoidal vibrato at 6 Hz. Because vibrato oscillates around
the center, the true center pitch is exactly the note (0¢ by construction). "reported" = what
maestro's median-per-note actually outputs; "frame 5–95%" = the spread a *frame-by-frame*
scorer would see.

| vibrato (±¢ peak) | maestro reports | verdict | frame spread (5–95%) | voiced frames |
|---|---|---|---|---|
| 0   | +0.0¢ | OK  | 0¢        | 100% |
| 10  | +0.0¢ | OK  | −10..+10  | 100% |
| 20  | +0.0¢ | OK  | −10..+10  | 100% |
| 30  | +0.0¢ | OK  | −20..+20  | 100% |
| 40  | +0.0¢ | OK  | −20..+20  | 100% |
| 50  | +0.0¢ | OK  | −30..+30  | 100% |
| 75  | +10.0¢ | OK | −40..+40  | 100% |
| 100 | +40/+45¢ | **OFF** | −60..+60 | 59–66% |

Identical shape at **A4 and A5** — no register dependence. **The median-per-note design is
robust to realistic vibrato:** a center-in-tune note reads in tune all the way to ±50¢ (a very
wide vibrato). It only breaks at ±75–100¢, and the mechanism is **asymmetric frame loss** —
pYIN stops voicing the extremes, so the surviving median gets biased — not a measurement bias
per se. Meanwhile a naive frame scorer would already see ±30¢ swings at ±50¢ width and panic.

**Takeaway:** the vibrato "harshness" that makes players reject these tools is a
*frame-scoring* design choice, not inherent to pitch measurement. Taking one median per note
launders symmetric vibrato away.

## B. The equal-temperament penalty  (`p1_tuning.py`, `p1_verify4.py`)

A **perfectly played** major scale in Just and Pythagorean intonation (tonic pinned to the ET
grid), scored against the nearest A=440 equal-tempered semitone.

| degree | Just (true vs ET) | Pythagorean (true vs ET) |
|---|---|---|
| 3rd | **−13.7¢** | +7.8¢ |
| 6th | **−15.6¢** | +5.9¢ |
| 7th | −11.7¢ | +9.8¢ |
| (root/4th/5th/oct) | ≤2¢ | ≤4¢ |

The Just 3rd/6th/7th are the expressive intervals players actually lean into — and the Just
6th (−15.6¢) sits **just past the ±15¢ line**, so a flawless Just performance should be
flagged OFF on that note. Pythagorean stays inside ±15¢ everywhere (max +9.8¢).

**But the coarse ruler masks it.** Under default pYIN (10¢ bins), the −15.6¢ Just 6th snaps to
−10¢ → **OK**; at fine 1¢ resolution the same tone reads −15¢ → **OFF**. Verified directly:

| resolution | Just 6th reads | verdict |
|---|---|---|
| 0.1 (10¢, default) | −10.0¢ | OK (forgiven) |
| 0.01 (1¢, ~360× slower) | −15.0¢ | **OFF** |

**Takeaway:** the equal-temperament penalty is real — expressive Just intonation crosses the
±15¢ line on the 6th — but Entry 002's 10¢ quantization accidentally *forgives* it. Two of the
project's threads collide: you can't fairly measure the ET penalty until the ruler is both
fine and fast, which (again) means CREPE.

## C. Noise / SNR robustness  (`p1_noise.py`)

Clean, in-tune 8-note D-major scale + white / pink noise at known SNR.

| SNR (dB) | white: detected / accuracy | pink: detected / accuracy |
|---|---|---|
| clean | 8/8 · 100% | 8/8 · 100% |
| 40 | 8/8 · 100% | 8/8 · 100% |
| 30 | 8/8 · 100% | 9/8 · 100% |
| 20 | 10/8 · 100% | 11/8 · 100% |
| 10 | 11/8 · 100% | 11/8 · 100% |
| 5 | **0/8** | 1/8 · 100% |
| 0 | **0/8** | **0/8** |

**Whenever a note is detected, its cents reading is perfect (mean 0.0¢).** Noise does not bias
intonation — the median launders it, exactly as it laundered codec noise in Entry 001. The
fragile layer is **onset segmentation**: spurious onsets appear by ~20 dB (10–11 "notes" from
8), then detection collapses below ~10 dB (white) / ~5 dB (pink). Pink (1/f, room-tone-like)
is gentler than white.

**Takeaway:** same split as everywhere — pitch *measurement* is robust; note *counting* is the
weak link.

## D. Short notes + sharp/flat directionality  (`p1_shortnotes.py`, `p1_verify.py`)

**Directionality (sign check):** perfect. Every detuned note reports the correct sign
(sharp → +, flat → −) at −30/−20/−10/+10/+20/+30¢.

**Duration sweep** (5-note scale, in tune, deterministic across runs):

| note dur (s) | detected |
|---|---|
| 0.40 | 5/5 |
| 0.30 | 5/5 |
| 0.25 | 2/5 |
| 0.20 | 5/5 |
| 0.15 | 1/5 |
| 0.12 | 5/5 |
| 0.10 | 5/5 |

Deterministic but **erratic below ~0.3 s**: the count jumps with exact note length. This is
onset-segmentation behavior (backtracking to energy minima interacts with note/gap lengths),
not a clean cliff — and again, pitch reads fine (0¢) *whenever* a note is caught. Short-note
handling is the segmentation layer's problem, not the tracker's.

---

## Cross-cutting finding

Across all four experiments the same structure appears: **the median-per-note pitch
measurement is remarkably robust** (vibrato to ±50¢, noise to ~10 dB, any format, any
register — all laundered), **while the discrete note-segmentation layer is the consistent weak
point** (spurious/missing onsets under noise and at short durations). And the 10¢ ruler cuts
both ways — it forgives vibrato-scale jitter but *masks* the real equal-temperament penalty.
The "too harsh" reputation of intonation tools is therefore mostly **not** about pitch
measurement; it's frame-by-frame scoring and hard-threshold verdicts.

## Notes / open items

- **C4 first-note outlier did not reproduce.** Entry 002's open item (C4 −30¢ misread as ~0¢)
  read correctly as −30.0¢ in this session's harness — likely a fragile onset/first-note edge
  effect sensitive to environment, not a stable bug.
- All Phase 1 evidence is **synthetic control** — it characterizes the *evaluator*. Real-audio
  confirmation is the next step: a self-recorded scale, and optionally a public professional
  recording (which, tellingly, would itself read OFF on the ET grid — a live demo of finding B).
- Fine-resolution (1¢) confirmation is limited to single short tones (~360× slower); full-scale
  cent-level work still needs CREPE.
