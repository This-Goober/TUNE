# maestro — Claude skill

Audio-first violin intonation analyzer, packaged as an installable [Claude skill](https://docs.claude.com). It turns a scale recording into a teacher-, audition-, or self-review-style pitch report: it detects each note, measures how far it sits from the expected pitch in cents, and (when given the scale) separates *wrong notes* from *intonation drift*.

The script is the judge; the model is the narrator — the analyzer computes the numbers, the skill turns them into prose.

## Layout

```
maestro/
├── SKILL.md            # the skill: workflow, report format, pitfalls
├── requirements.txt    # Python deps (librosa, numpy, torchcrepe, soundfile)
├── LICENSE             # Apache-2.0
├── scripts/
│   └── audio_v0.py     # the analyzer (CREPE pitch tracking + DTW scale alignment)
└── references/
    └── DESIGN.md       # full multi-modal roadmap (audio + vision + VLM), loaded on demand
```

Everything the skill needs travels inside this folder, so paths are relative and it runs the same in Claude Code, Claude.ai, and via the API.

## Install

**Claude Code** — copy the folder into your skills directory:

```bash
cp -r maestro ~/.claude/skills/maestro
```

Then it's available in any session; trigger it by asking to analyze a violin recording (or `/maestro`).

**Claude.ai / API** — build the `.skill` bundle (below) and upload it in the skills settings.

## Build the `.skill` bundle

A `.skill` file is just a zip of this folder. To produce one for upload:

```bash
cd ..                       # parent of the maestro/ folder
zip -r maestro.skill maestro \
  -x '*/__pycache__/*' '*.pyc' '*/.venv/*' '.DS_Store'
```

(Anthropic's `skill-creator` also ships a `package_skill.py` that validates frontmatter before zipping, if you have it.)

## Dependencies

`requirements.txt` pulls `torch` + `torchcrepe` for CREPE pitch tracking — roughly **1 GB** plus model weights — and the skill expects `ffmpeg` on `PATH` for video/`.m4a` input. On a persistent machine, a one-time venv is cleanest:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

If CREPE/torch can't be installed in a given environment, `DESIGN.md` documents librosa's pYIN as a lighter fallback pitch tracker (no torch), at some cost to accuracy on high notes and vibrato.

## What it produces

A per-note table (detected pitch, expected pitch when a scale is given, cents deviation, verdict) plus an accuracy summary, which the skill then narrates into a report tuned to the audience:

```
  #   start     end       Hz  detected    cents  expected  verdict
------------------------------------------------------------------
  1    0.14    0.81    262.5        C4     +5.9        C4  OK
  4    1.65    2.28    319.4       D#4    +45.6        E4  WRONG
 13    6.29    6.85    593.5        D5    +18.1        D5  OFF
```

Verdicts: `OK` (within ±15¢, configurable), `OFF` (right note, off by more than threshold), `WRONG` (wrong pitch class — only with a scale), `unvoiced` (silence/breath).

## Roadmap & limitations

See [`references/DESIGN.md`](references/DESIGN.md) for the full design (audio + vision + VLM coaching) and current gaps. In short: monophonic only, equal-temperament reference, no vibrato/dynamics analysis yet, and no vision side (bow geometry, posture) — every technique hypothesis is inferred from pitch alone.
