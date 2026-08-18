---
name: maestro
description: Analyze a violin (or other monophonic instrument) recording and turn it into a readable pitch/intonation report — for a teacher giving a student feedback, a judge assessing a youth-symphony audition, or a player self-reviewing before a lesson. Use whenever someone has an audio or video clip of a scale or short passage and wants to know if it is in tune, which notes are wrong, or how the intonation drifts. Triggers on phrases like "analyze this violin recording", "check my intonation", "is this scale in tune", "audition feedback", "score my scale", "pitch report", or when a .wav/.mp3/.m4a/.flac/.mp4/.mov of someone playing is provided. Powered by CREPE pitch tracking plus DTW alignment to an expected scale.
license: Apache-2.0
metadata:
  version: 0.2.0
---

# maestro

Audio-first violin recording analyzer. It runs a bundled Python script (`scripts/audio_v0.py`) that detects each note, measures how far it sits from the expected pitch, and distinguishes *wrong notes* (wrong pitch class) from *intonation drift* (right note, off by some cents). Your job is to drive that script and turn its raw table into a report pitched at the right audience.

The script is the judge; you are the narrator. It computes the numbers; you explain them in a teacher's, judge's, or self-reviewer's voice. Don't invent pitch facts the script didn't produce.

## Locate the skill and set up dependencies

Everything ships inside this skill folder. Let `SKILL_DIR` be the directory containing this `SKILL.md`. The analyzer is at `SKILL_DIR/scripts/audio_v0.py` and its dependencies are in `SKILL_DIR/requirements.txt`.

The dependencies are heavy — `torch` + `torchcrepe` pull roughly **1 GB** plus CREPE model weights, and `ffmpeg` is needed for video input. Before installing, confirm the deps aren't already present and tell the user about the download size; ask before a fresh ~1 GB install.

Pick the install path that matches the environment:

- **Persistent machine (e.g. Claude Code on the user's laptop):** create a venv next to the script once and reuse it.
  ```bash
  python3 -m venv "$SKILL_DIR/.venv"
  "$SKILL_DIR/.venv/bin/pip" install -r "$SKILL_DIR/requirements.txt"
  ```
  Then run with `"$SKILL_DIR/.venv/bin/python"`.

- **Sandbox / ephemeral container (e.g. Claude.ai code execution):** install into the system interpreter and run with plain `python3`.
  ```bash
  pip install --break-system-packages -r "$SKILL_DIR/requirements.txt"
  ```
  `ffmpeg` is only required for video (`.mp4`/`.mov`); for plain audio you can skip it.

A quick `python3 -c "import torch, torchcrepe, librosa"` tells you whether setup is already done.

## Workflow

### 1. Gather context (ask before running)

- **Input file** — audio (`.wav`/`.mp3`/`.m4a`/`.flac`/`.aiff`) or video (`.mp4`/`.mov`; the audio is extracted via ffmpeg).
- **Scale played** — tonic (with octave), mode, pattern (asc / desc / asc-desc), number of octaves. If the user can't say, run without `--scale`: you still get intonation-drift analysis, just no wrong-note detection.
- **Audience** — sets the report tone:
  - **Teacher → student** (default): warm, specific, action-oriented.
  - **Audition assessment**: objective, structured, scoring-friendly.
  - **Self-review**: same as teacher but blunter.

### 2. Run the analyzer

```bash
<python> "$SKILL_DIR/scripts/audio_v0.py" <file> [--scale "<spec>"] [--threshold <cents>]
```

where `<python>` is the venv or system interpreter from setup above.

Scale-spec forms:
- Mode form: `"G3 major asc-desc 2oct"` — `tonic[octave] mode [asc|desc|asc-desc] [Noct]`
- Modes: `major`, `minor` (natural), `harmonic_minor`, `melodic_minor` (ascending form), `dorian`, `mixolydian`, `chromatic`
- Explicit notes: `"G3 A3 B3 C4 D4 E4 F#4 G4"`

Default threshold is ±15¢. It's a reporting knob, not a score-fixer — don't widen it just to make the accuracy number look better.

### 3. Read the raw output

The script prints a per-note table: `# | start | end | Hz | detected | cents | expected | verdict`, then a summary line (voiced notes, # flat/sharp, # wrong-note, accuracy %).

Verdicts:
- `OK` — within threshold.
- `OFF` — right pitch class, off by more than threshold cents.
- `WRONG` — wrong pitch class entirely (only appears when `--scale` is given).
- `unvoiced` — silence/breath; ignore.

### 4. Build the report

Convert the table into Markdown. Skip any section that has nothing real to say — don't pad.

**Header**
```
# Violin Pitch Report — <filename>
- Recording: <duration>s
- Notes detected: <N> (vs. <M> expected)
- Scale: <human description, e.g. "G major, 2 octaves up and down">
```

**Headline** (one or two sentences)
- Crisp count: "X within tolerance, Y intonation drift, Z wrong notes."
- If the median cents-deviation across stable notes is ≥3¢ in one consistent direction, attribute it to **tuning, not playing**, and say so. The instrument is probably tuned slightly off A=440 — don't blame the player for a uniform offset.

**What went well**
- 2–3 bullets pointing at the cleanest stretch (e.g. "ascending B4 → G5 was steady within ±10¢"). Omit if there's genuinely nothing to praise.

**Wrong notes** (only when `--scale` was given)
- One bullet per WRONG row: timestamp, played-vs-expected, and a *cautious* one-line technical hypothesis a teacher might offer (string crossing, half-step finger placement, missed accidental). Don't speculate past the data; if the cause is unclear, just describe what happened.
  ```
  - 0:01.6 — D#4 instead of E4 (about a semitone flat). First-finger placement on the D string.
  ```

**Intonation drift** (the OFF rows)
- Group by pattern when one exists ("D5 was sharp both times it appeared — possibly third-finger placement on the A string"). Otherwise list with timestamp and cents.

**Patterns to address** (synthesis across the whole table)
- Same note repeated, same direction off → finger habit.
- Errors cluster at register changes → position-shift issue.
- Errors cluster at a scale degree (e.g. always the leading tone) → tuning concept.
- These are *hypotheses* — frame them as "consider checking…", not verdicts.

**Overall**
- Accuracy %: notes within tolerance ÷ total.
- For audition reports, also give: max deviation, # wrong notes, scale completeness (detected vs. expected).

### 5. Tone and length

- **Teacher report:** 250–500 words, warm and specific, ending with 1–2 concrete practice suggestions.
- **Audition report:** 150–300 words, neutral and objective, leading with the numeric summary.
- **Self-review:** teacher length, blunter.

After showing the report inline, **offer to save** it (e.g. to a `reports/<filename>-<YYYY-MM-DD>.md` next to the recording). Don't save without asking.

## Common pitfalls

- **Wrong scale tonic** — DTW mis-aligns and flags many false WRONG notes. Symptom: the "expected" column gets stuck on one note for many rows. Verify the scale with the user before reporting.
- **Systematic ±5¢ bias** — almost always tuning, not playing. Note it once at the top; don't flag it on every row.
- **First/last unvoiced rows** — usually breath or a bow lift; don't list them as problems.
- **Onset over-segmentation** — the script already merges duplicate-onset slivers (see the `raw → cleanup` count it prints). Trust the cleaned count.
- **CREPE startup** — the first run takes an extra 5–10s for model load + JIT. Normal; mention it only if the user asks why it's slow.

## Limitations (be upfront)

- **Monophonic only** — double-stops confuse the pitch tracker.
- **Equal-temperament reference** — for just-intonation playing the cents numbers look off in predictable ways (sharp leading tones, flat major thirds).
- **No vibrato / dynamics analysis yet.**
- **No vision side** — it can't see bow angle, posture, or finger position; every technique hypothesis is inferred from pitch alone.

The full multi-modal roadmap (audio + vision + VLM coaching, capability map, current gaps) is in `references/DESIGN.md`. Read it only if the user asks where the project is headed or wants to extend the analyzer beyond pitch.
