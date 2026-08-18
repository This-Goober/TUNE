# audio/

The recordings the experiments run on. Most experiments generate their own synthetic tones, so
only a couple of these are actually loaded by a script — the rest are reference takes kept for
later comparison.

All recordings are me, on violin, playing D major three octaves ascending then descending,
unless noted.

## reference-2026-06/

Recorded June 2026. The `.wav` and `.m4a` of each take are the **same performance**, not two
separate ones — that pairing is the whole point of the format experiment.

| File | What it is | Used by |
|---|---|---|
| `scale_notvib.wav` | Slow, sustained, **no vibrato**, lossless 48 kHz mono. The cleanest reference take. | [`001-format-m4a-vs-wav`](../experiments/001-format-m4a-vs-wav/) |
| `scale_notvib.m4a` | Same take as above, compressed to AAC 68 kbps. The controlled format pair. | [`001-format-m4a-vs-wav`](../experiments/001-format-m4a-vs-wav/) |
| `scale_vib.wav` | Same scale **with vibrato**, lossless. Held for future vibrato comparison against the synthetic curve. | not yet used by a script |
| `scale_vib.m4a` | Same vibrato take, compressed. | not yet used by a script |

## phase2-session/

Empty, waiting on a recording session. The plan is a batch recorded in one sitting: a plain
scale, narrow and wide vibrato, a take tuned by ear against a drone (expressive "just"
intonation), a take with mistakes put in on purpose so there's a known right answer, short
staccato notes, and a piece of real repertoire.

The deliberate-mistakes take is the important one — it's the first time the tool gets graded
against ground truth on real playing rather than on tones generated to be exactly wrong.

## A note on why so much is synthetic

Nobody knows the true pitch of a human performance, which makes real recordings useless for
checking whether the *tool* is accurate. Generated tones have an exactly known pitch, so any
disagreement is the tool's error. Real audio answers a different question — whether findings
from the lab survive contact with actual playing — and that's the next phase.
