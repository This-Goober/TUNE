# skills/

## What a "skill" is

A skill is a folder of plain-English instructions — plus any scripts it needs — that you hand
to an AI model. The model reads the instructions and follows them. That's the whole idea. It
isn't an app, there's no interface, and nothing is compiled; you can open every file here and
read exactly what the thing does.

That matters for this project. A shipped app encodes one team's fixed idea of what "in tune"
means, and you get what you get. A skill is a recipe you can bend: change the tolerance,
change what it reports, point it at a question the original author never considered. If you
disagree with how this tool judges a note, you can edit the file and make it judge differently.

The format is [Anthropic's open Agent Skills standard](https://docs.claude.com), so these
folders aren't locked to Claude — a number of other tools read the same structure.

## What's in here

### [`Maestro/`](Maestro/) — the violin intonation analyzer

Give it a recording of a scale. It finds each note, measures how far that note sits from the
pitch it should be (in **cents** — hundredths of the distance between two neighboring notes),
tells a *wrong note* apart from a *slightly-off note*, and writes back a table plus a readable
report aimed at a teacher, a judge, or yourself.

The design principle: **the script judges, the model narrates.** A strict Python analyzer
produces the numbers, and the model turns them into prose. Keeping those two jobs separate is
what keeps it honest — the model can't invent a pitch fact the analyzer didn't measure.

See [`Maestro/README.md`](Maestro/README.md) for the full detail. The short version follows.

## Installing it

**In Claude Code** — copy the folder into your skills directory:

```bash
cp -r skills/Maestro ~/.claude/skills/maestro
```

Then just ask it to analyze a violin recording in any session.

**In the Claude app** — upload the prebuilt bundle `Maestro/maestro-skill.zip` in your skills
settings (rename it to `maestro.skill` if the uploader is picky about the extension).

## What you'll need

- **Python 3** with `librosa`, `numpy`, and `soundfile` — see `Maestro/requirements.txt`.
- **ffmpeg** on your PATH, but only if you're feeding it `.m4a`, `.mp4`, or `.mov`. Plain
  `.wav` needs nothing extra.
- Optionally **CREPE** (`torch` + `torchcrepe`), the more accurate pitch tracker. It's about a
  1 GB download and it does not install everywhere — see the note below.

A one-time virtual environment is the cleanest setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r skills/Maestro/requirements.txt
```

**An honest caveat:** the skill is designed around CREPE, but CREPE wouldn't install in the
environment this project runs in, so everything here actually runs on a lighter fallback
tracker (librosa's pYIN). The skill degrades to it gracefully. That fallback is *why* several
findings in [`experiments/`](../experiments/) read the way they do — pYIN rounds its readings
to 10-cent steps, which turns out to matter a lot. It's documented rather than hidden, which
is the point of building this as a skill instead of an app.

## Things worth trying yourself

- **Run it on your own playing.** A slow scale, notes held about two seconds each. Tune to
  A=440 first — the tool measures against that grid, so an instrument tuned sharp gets every
  note marked off.
- **Feed it a professional recording.** Interesting because a great performance often uses
  expressive tuning that this tool, judging against the piano grid, will mark as errors. That
  disagreement is the most interesting thing in the project.
- **Move the tolerance.** The ±15¢ pass/fail line is a choice, not a law. Widen it, narrow it,
  and see whether the verdicts start matching your ear.
- **Change what the report says.** Open `SKILL.md` and rewrite the reporting instructions —
  more encouraging for a beginner, more clinical for an audition. Nothing needs recompiling.
- **Break it and tell me.** Short notes, heavy vibrato, a noisy room, double-stops. The failure
  modes are the research.

## What's deliberately not here

A second skill (`maestro-entry`) handles my private research journaling. It's kept out of this
repo because it's a personal notebook helper, not something anyone else would use.
