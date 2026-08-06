# The pipeline

These are the real scripts that rendered the
[LetX promo](https://youtube.com/shorts/CPx11OL0yMc), not a sanitized demo.

They are tuned to **one specific 30-second video**, with cue timings hard-coded
against its scene cuts at 3.0 / 8.0 / 19.0 / 25.0s. Read them as a worked
example rather than a general-purpose tool.

The fastest way to use them: point Claude Code at this directory, give it
`../prompts/04-soundtrack.md` filled in for your video, and let it adapt these
files. That produces a better result than trying to parameterize someone else's
timeline.

## Setup

```bash
./setup.sh     # system deps + venv + Kokoro + the espeak-ng data fix
./render.sh    # score + VO + mix + master + mux   (~2 min, deterministic)
```

`setup.sh` assumes macOS with Homebrew. On Linux, install `espeak-ng` and
`ffmpeg` from your package manager — the espeak data-copy step is usually
unnecessary there.

**Python 3.12 is required.** Kokoro's dependency chain (misaki → spaCy → blis)
has no wheels for 3.14 and the install dies compiling `blis/py.pyx`.

## Files

| File | Role |
|---|---|
| `synth.py` | Procedural score (120 BPM, Am–F–C–G) + ~90 SFX cues, arranged against the scene boundaries. Fixed RNG seed — keep it, it's what makes renders reproducible. |
| `vo.py` | Kokoro-82M voiceover. One take per line, auto-fitted by nudging `speed` and re-rendering — never by time-stretching. |
| `mix.py` | VO chain (de-ess, EQ, two-stage compression, room), sidechain ducking, bus glue, limiter. |
| `build.sh` | Two-pass linear `loudnorm` to -14 LUFS / -1.5 dBTP, then mux with the video stream-copied. |
| `render.sh` | Runs all of the above. Takes a voice name: `./render.sh af_bella`. |
| `splice-cta.sh` | Losslessly swaps one section between two renders of the same video. |

## Paths

`render.sh` defaults to a source video and output directory from the original
project. Override them:

```bash
SRC=../my-video.mp4 OUTDIR=../out ./render.sh
```
