---
name: maestro-entry
description: Generate a consistent research-journal entry plus a refreshed plain-English "storyline" summary for the violin-intonation / "vibe-coding an ear" lab journal (the Substack source doc). Use this whenever the user finishes an experiment, logs off for the day, or says things like "make a loggable entry", "log this experiment", "maestro entry", "add a journal entry", "update the storyline", or invokes /maestro-entry. It outputs two paste-ready Markdown blocks — a new numbered Entry following a fixed template, and a complete replacement for the running plain-English summary — using the real numbers from the experiment actually run in the conversation, never invented.
license: Apache-2.0
metadata:
  version: 0.1.0
---

# maestro-entry

A journaling command for the violin-intonation research project. Its whole point is **consistency**: every entry and every storyline refresh comes out in the same shape, so the journal stays uniform across many sessions and the eventual Substack article can lift sections wholesale. When the user finishes an experiment or wraps a day, produce both deliverables below — clean, in order, ready to paste.

The user keeps the journal themselves (Drive or GitHub) and pastes what you return. So your output is the product: two clearly separated Markdown blocks, nothing they have to reformat.

## What you produce (always both)

1. **A new Entry** — appended to the bottom of the journal's entry log.
2. **A full replacement Storyline** — the plain-English running summary near the top of the journal. The user deletes the old one and pastes this in whole, so it must be complete, not a diff.

Deliver them as two separate fenced Markdown blocks, each labeled, so copy-paste is unambiguous.

## Before writing: gather the real material

The integrity of this journal depends on accuracy — it's becoming a public article. So:

- **Pull numbers from what actually ran in the conversation** (tool outputs, script results, tables). Do not reconstruct figures from memory or round to something cleaner than the run produced. If a number the template wants isn't available, say so plainly in the entry rather than inventing one.
- **Determine the next entry number** from context (the last entry produced or referenced). If you can't tell, ask the user for the last number before writing — a mis-numbered entry is worse than a one-line question.
- **Date** the entry with today's actual date.
- If the session had no single crisp experiment (an end-of-day log), still write an entry — summarize what was explored and learned, and let the less-relevant template fields collapse to a line or be omitted. Don't pad empty fields.

## Output A — the Entry

Use this exact template. Keep it terse but reproducible; a reader should be able to redo the experiment from "What I did." Be honest in "Caveats" — naming a limitation is a feature of this journal, not a weakness.

```
## Entry NNN — YYYY-MM-DD — <short title>

**Question.** What were we actually asking?
**Prior / hypothesis.** What did we expect going in?
**Setup.** Files, skill version, tracker, params (or "standing setup, no change").
**What I did.** The procedure, terse but reproducible.
**Findings.** The numbers. Tables welcome.
**Interpretation.** What the numbers mean.
**Caveats / threats to validity.** What could make this wrong or non-general.
**Takeaway (article angle).** One or two sentences a reader should leave with.
**Next.** What this opens up.
```

Notes on filling it:
- **Findings**: lead with the headline number, then support. Small Markdown tables are good when comparing conditions. Keep units explicit (¢ for cents, kbps, Hz).
- **Interpretation vs Findings**: Findings are what the run said; Interpretation is what it means. Don't blur them.
- **Takeaway**: this is the sentence that may end up in the article. Make it land — the surprising or counterintuitive part, not a restatement of the number.
- If you corrected an earlier claim during the experiment, say so in Interpretation. Visible self-correction is exactly the credibility this journal trades on.

## Output B — the Storyline (full replacement, plain English)

This is the part a tired reader skims to remember where things stand. Keep it genuinely plain — a musician with no signal-processing background should follow every line. Avoid jargon, or defang it in passing (e.g. "15 cents — about 15% of the gap between two neighboring notes").

Reproduce all six parts every time, in this order. The first three are largely **stable** (the project's premise and how the tool works) — carry them forward, lightly editing only if the toolchain genuinely changed. The last three **update** to reflect the newest experiment.

```
## The story so far (plain English)

**What I'm building.** The project's premise in one breath: a *skill*, not an app, that listens to a violin scale and grades each note for tuning — and the bet that customizable skills beat frozen apps.

**Why I care.** The motivation: existing "is this in tune?" tools are too harsh and nobody in the user's circle uses them; the goal is to understand why and whether a home-built version maps or moves that line.

**How the grader works, roughly.** Plain-language mechanics: it finds each note, measures distance from the nearest correct pitch, passes anything within ~15 cents, scores the fraction that pass. Note the two honest catches (no scale given → checks cleanliness not correctness; hard pass/fail line).

**The catch under the hood.** The current tooling limitation in plain terms (e.g. the lighter pitch detector standing in for the heavy one, and where it gets shaky). Update if the toolchain changed.

**Biggest thing I've learned so far.** UPDATE THIS: the single most surprising or important finding to date, told as a small story with the intuition for *why*.

**Where this is pointing.** UPDATE THIS: what the accumulated findings suggest the real story is, and what it implies for the next move.
```

When a new finding supersedes the old "biggest thing," you can fold the previous headline into a single carried sentence if it still matters, but keep the section from growing without bound — it's a summary, not a second log.

## Delivery

End your turn with the two blocks and almost nothing else — the user is going to paste, not read commentary. A single line noting the entry number and that the storyline is a full replace is enough.

If a Google Drive or GitHub connector is available and the user has said they want it written directly rather than pasted, offer to do that instead of returning blocks. Default to returning paste-ready blocks, since the user chose manual control.

## Why this skill exists (for the model using it)

The user is running a long series of small experiments that become a public article. The failure mode this skill prevents is *format drift* — entries that each look slightly different, a storyline that mutates structure session to session, numbers that get prettier than the data. Hold the shape steady and keep the figures honest, and the journal stays publishable by accretion.
