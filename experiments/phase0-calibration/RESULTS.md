# Phase 0 — Results (2026-07-02)

Calibration of the **pYIN-backed** maestro ruler (CREPE unavailable in-environment).
These numbers back Journal Entry 002. Scripts in this folder reproduce them.

## A. Offset accuracy (distinct notes)
`phase0_calibration.py`, Test A. Readings snap to 10¢ bins (pYIN `resolution=0.1`).

| intended | read | error |
|---|---|---|
| C4 −30¢ | 0.0¢ | +30 (low/first-note outlier — OPEN) |
| E4 +20¢ | +20.0¢ | 0 |
| A4 −10¢ | −10.0¢ | 0 |
| C5 +0¢ | 0.0¢ | 0 |
| E5 +25¢ | +30.0¢ | +5 (snapped up) |

mean |err| ≈ 7¢, dominated by 10¢ snapping + the C4 outlier.

## B. Resolution tradeoff (single E5 +25¢ tone)
`phase0_resolution.py`.

| resolution | reading | error | time |
|---|---|---|---|
| 0.1 (10¢ bins, default) | +30.0¢ | +5.0¢ | 0.2 s |
| 0.01 (1¢ bins) | +26.0¢ | +1.0¢ | 72.5 s |

~360× slower for accuracy → fine-resolution pYIN is impractical on full recordings.
**Cent-level work needs CREPE.**

## C. Register sweep (fixed +15¢)
`phase0_calibration.py`, Test B. All read +20¢ (= +15 snapped to nearest 10¢), no
dependence on pitch height A3→A6. **Corrects the earlier "top octave is intrinsically
imprecise" hypothesis** — the earlier high-note mess was vibrato/playing, not height.

## D. Note count + repeatability
- 8/8 on a distinct-note D-major scale.
- Deterministic across 3 runs.
- Caveat: `merge_same_note` collapses consecutive identical pitches by design.

## E. Format matrix
`phase0_format_matrix.py`. One scale encoded to 7 formats.

| format | lossy | cents vs wav | raw onset count |
|---|---|---|---|
| wav / flac / aiff | no | identical (0.00¢) | 9 (1 spurious) |
| ogg | yes | identical | 8 (exact) |
| mp3 / m4a / mp4 | yes | identical | 17 (~doubled) |

**Cents: format-transparent.** **Onsets: format-sensitive** — lossy AAC/MP3 add
pre-echo/priming transients that spawn spurious onsets; the merge step absorbs most.
Caveat: cents tested on in-tune tones (weak probe), leaning on the Entry 001
real-recording m4a=wav result.

## Open items
- C4 / first-note −30¢ misread (30¢ error) — low-register or first-note edge effect.
- Re-run A/B under CREPE once installable, to compare continuous vs binned.
