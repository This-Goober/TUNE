<div align="center">

# TUNE

**Exploration of AI pitch detection program capabilities**

[![Substack](https://img.shields.io/badge/Substack-Read%20the%20TUNE%20series-FF6719?logo=substack&logoColor=white)](https://eideetan.substack.com/s/tune-exploration-of-ai-pitch-detection)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

</div>

**Can an AI tell a violinist something true and useful about their intonation?**

Tools that answer "is this in tune?" have existed for years, and almost nobody I know uses
them. They're too harsh — they panic at vibrato, choke on room noise, and flag expressive
choices that are musically correct. So this project takes one apart and tests it: how
accurately does it actually measure, where does it fall apart, and how many of the "errors" it
reports are the tool's fault rather than the player's?

It's built as a **skill** rather than an app — a set of readable instructions plus a script,
which you can open, change, and point at your own question. That's the second thing being
tested here: whether that's a better way to build small tools than shipping a frozen binary.

This repo is the working half — the tool, the experiments, the numbers. The story half (why
any of this matters, what surprised me) is on the Substack. Findings here have been overturned
twice so far, and both reversals are left in the record on purpose.

## Where to go

| | |
|---|---|
| [**`skills/`**](skills/) | The analyzer itself, and how to install and run it on your own playing. Start here if you want to use the thing. |
| [**`experiments/`**](experiments/) | Every test run against it, with the numbers and the caveats. Start here if you want to know whether to believe it. |
| [**`audio/`**](audio/) | The recordings, labeled — what each take is and which experiment uses it. |
| [**`PROJECT.md`**](PROJECT.md) | The full technical on-ramp: methods, metric definitions, current state, roadmap. |

## Where things stand

Four experiment batches are done. In short:

- **The ruler is blunter than the thing it measures.** The pitch tracker rounds every reading
  to the nearest 10 cents; the pass/fail line sits at 15. The precise setting runs ~360× slower
  and is unusable on real recordings.
- **Vibrato doesn't break it**, which was the surprise — that's the #1 reason players reject
  these tools. Taking one median reading per note washes symmetric vibrato out entirely. The
  harshness comes from *how tools score*, not from measuring pitch.
- **Note-splitting is the fragile part.** Under noise or on fast notes, the tool miscounts
  where notes begin and end — while reading every pitch it does catch correctly.
- **Expressive tuning gets punished.** A flawlessly played "just"-intonation scale lands its
  sixth just past the fail line. The machine would correct a musician for playing beautifully —
  and right now the coarse ruler is accidentally hiding that.

The through-line: measuring pitch is largely a solved problem. Deciding whether a pitch is
*correct* is not — and that's where the interesting failures live.

**Next up:** moving past synthetic calibration to test the scorer against actual musical
judgment — sweeping the threshold itself, scoring the same performance against several
defensible tuning targets, giving it harmonic context, asking musicians which versions they
prefer, and comparing pYIN against CREPE on real violin recordings.

## If you want to poke at it

Clone it, run the skill on a recording of yourself, and tell me where it's wrong. The
experiments that use synthetic tones need no audio files and reproduce in one command. Every
failure mode found so far came from someone playing something the tool didn't expect.
