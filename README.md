# Make a promo video with Claude Code

**Everything needed to produce a 30-second vertical promo video — animation,
voiceover, original music and sound effects — by prompting. No paid APIs, no
licensed music, no video editor, and zero marginal cost per render.**

This is the exact process and the exact scripts behind the promo for
[LetX](https://letx.app/), a collaborative LaTeX editor:

▶ **[Watch the result (30s)](https://youtube.com/shorts/CPx11OL0yMc)**
📖 **[Read the full write-up, with interactive prompt builder](https://shihub.site/blog/make-promo-video-with-claude-code)**

---

## What this is

Most "AI video" guides wire together three paid services. This one doesn't. The
animation comes out of Claude, and the entire soundtrack is generated locally:

| Piece | How | Cost |
|---|---|---|
| Animation | Prompted, exported as MP4 | — |
| Voiceover | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), running on your machine | free, unlimited re-renders |
| Music | Synthesized from scratch in numpy | free, nothing licensed |
| Sound effects | Synthesized from scratch in numpy | free, nothing licensed |
| Mix, master, mux | ffmpeg | free |

Because nothing is licensed, there is no attribution to track and nothing to
trip a content-ID match. Because the score is generated against your timeline
rather than trimmed to fit it, every cue lands on the exact frame you asked for.
And because the generator uses a fixed seed, renders are reproducible.

## You do not need to be a video editor

I am not one. The skill this actually requires is **writing a precise brief**.
The prompts in [`prompts/`](prompts/) are the deliverable of this repo — the
code in [`pipeline/`](pipeline/) is what Claude Code wrote when given them.

## The five steps

| # | Step | Where | Prompt |
|---|---|---|---|
| 1 | Write a timestamped scene sheet | Claude | [`prompts/01-scene-sheet.md`](prompts/01-scene-sheet.md) |
| 2 | Generate the animation | Claude | [`prompts/02-animation.md`](prompts/02-animation.md) |
| 3 | Write the voiceover as a timetable | Claude | [`prompts/03-voiceover.md`](prompts/03-voiceover.md) |
| 4 | Build the soundtrack | Claude Code | [`prompts/04-soundtrack.md`](prompts/04-soundtrack.md) |
| 5 | Check it, then ship | You | [`prompts/05-ship-checklist.md`](prompts/05-ship-checklist.md) |

Something breaks? [`prompts/fixes.md`](prompts/fixes.md) has a prompt for each
of the six failures that actually happened while making this video.

### The single most important idea

**Do not ask for a video first. Ask for the scene sheet.**

A video is thirty seconds of decisions — what appears, when, for how long, and
what sound lands on it. Ask for all of it at once and the model picks defaults
for every decision. Defaults are what "AI slop" is made of.

So step 1 produces a document: five scenes with exact start and end seconds.
Everything downstream keys off it. The voiceover is written into its gaps, the
music picks a tempo that lands on its cuts, and every sound effect is placed
against its boundaries.

In the LetX promo the cuts are at **3.0 / 8.0 / 19.0 / 25.0 seconds**, and every
audio cue in the video is defined relative to those four numbers. See
[`example/scene-and-cue-sheet.md`](example/scene-and-cue-sheet.md) for the
finished article — the full scene sheet, the voiceover script with timings, and
all ~90 cues.

## Running the pipeline

The scripts in [`pipeline/`](pipeline/) are the real ones that rendered the
video above, not a sanitized demo. They are tuned to one specific 30-second
video, so read them as a **worked example**: point Claude Code at them, describe
your video, and let it adapt them. That is faster and produces a better result
than trying to parameterize someone else's timeline.

```bash
cd pipeline
./setup.sh            # once: system deps + venv + Kokoro + espeak data fix
./render.sh           # score + VO + mix + master + mux  (~2 min, deterministic)
./render.sh af_bella  # same, different voice
```

| File | Role |
|---|---|
| `synth.py` | Procedural score (120 BPM, Am–F–C–G) + ~90 SFX cues, arranged against the scene boundaries |
| `vo.py` | Kokoro-82M voiceover; one take per line, auto-fitted to its slot |
| `mix.py` | VO chain, sidechain ducking, bus glue, limiter |
| `build.sh` | Two-pass linear `loudnorm` + mux (video stream-copied) |
| `render.sh` | Runs all of the above |
| `splice-cta.sh` | Losslessly swaps one section between two renders — see below |

## Gotchas that cost me real time

- **Python 3.12.** Kokoro's dependency chain (misaki → spaCy → blis) has no
  wheels for 3.14; the install dies compiling `blis/py.pyx`.
- **espeak-ng data ships broken.** The `espeakng_loader` wheel has an incomplete
  data dir, so you get `Error processing file '.../phontab': No such file or
  directory`. Fix: copy Homebrew's `espeak-ng-data/*` into **both** the loader
  package dir and its `espeak-ng-data/` subdir — espeak looks in the package dir
  itself. `setup.sh` does this.
- **Two voice options, pick deliberately.** Local (Kokoro-82M) is free, private
  and unlimited. OpenRouter's `openai/gpt-audio` sounds better and costs about
  **$0.09 per 95s narration** — see `pipeline/vo_gpt.py`. If you use the API:
  audio output **requires** `stream: true` (a normal request 400s), the audio
  arrives as base64 chunks you concatenate, and there is no `speed` parameter,
  so an overlong line gets re-rendered with a pacing instruction rather than
  stretched. Send an identical persona prompt with every line or the voice
  drifts between takes.
- **macOS `say` is too robotic** — and the good system voices can't be scripted.
- **Never time-stretch a take to fit its slot.** Re-render it at a nudged speed
  instead. Stretching is exactly what makes synthetic voice sound synthetic.
- **Spell for the phonemizer, not for humans.** `.tex` → `dot tek`,
  `LetX` → `Let X`, `letx.app` → `Let X dot app`.
- **Two-pass `loudnorm` with `linear=true`.** Single-pass is dynamic: it pumped
  and overshot to **+0.4 dBTP**, which clips the moment a platform re-encodes.
- **Don't crush the bus before `loudnorm`.** An aggressive glue comp + limiter
  collapsed the loudness range to 1.2 LU and caused that overshoot. Leave ~3 dB
  of headroom and let the normaliser do the lift.
- **The venv is ~1.1 GB** (torch). Budget the disk once.

## Swapping one bad section, losslessly

A late re-render came back better everywhere except the last five seconds. Rather
than re-render everything, `splice-cta.sh` takes the body from one file and the
tail from the other.

This is a **stream copy** — zero re-encode, zero generation loss — which works
because both renders share a keyframe at exactly the cut point and identical
codec parameters. Check that before trusting it; the script prints what it did.

Before reusing a soundtrack on a *new* render, prove the timing matches instead
of assuming: cross-correlate per-frame brightness between the two files and
confirm a best-fit offset of 0 frames. `prompts/fixes.md` has the prompt.

## Publish numbers you can defend

The failure mode worth guarding against: a model will write a confident,
specific, entirely invented statistic, and a promo video is the worst place for
one — it gets embedded, reposted and screenshotted, and outlives any correction.

Two rules that came out of this:

1. **Derive claims from something queryable**, not an optional profile field. A
   self-reported country field was blank for most users and would have supported
   a far larger, completely unusable number than verified institutional email
   domains did.
2. **Round down.** Publish the round figure *below* the verified count. An "N+"
   claim never expires as you grow, so there is no reason to reach.

`prompts/05-ship-checklist.md` includes a prompt that audits every claim in your
video before you post it.

## Licence

MIT — see [LICENSE](LICENSE). Use the prompts and the scripts freely.

The promo video itself, the LetX name and the LetX brand assets are not covered
by that licence.

---

Built by [Shihab Shahriar Antor](https://shihub.site) while making the launch
video for [LetX](https://letx.app/) — a free collaborative LaTeX editor that runs
in the browser and lets you drag an existing project straight in.

If you make something with this, I'd like to see it.
