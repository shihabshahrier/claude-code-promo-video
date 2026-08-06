# LetX 95s explainer — scene sheet, VO script, cue list

1920×1080 · 30 fps · 95.000 s · 16:9 for the site hero, YouTube and LinkedIn.

Source visual master: `LetX Explainer.mp4` (silent, 2850 frames).
Deliverable: `renders/explainer-95s/LetX_Explainer_95s_marin.mp4`.

Unlike the promo, this is **not** hard-cut. It is mostly continuous UI motion
with typewriter title cards, so the audio is keyed to the script's section
boundaries plus the cuts actually measured in the render:

```
13.77  14.63  21.30  25.53  52.03  60.30  61.23  63.00
68.33  74.43  85.43  89.63  91.83
```

The big one is **68.33** — the light-to-dark wipe into the testimonials. That is
the only truly cinematic transition in the piece and it gets the biggest whoosh.

---

## Why this sounds different from the 30s promo

The promo is a dark vertical trailer: sub drops, hard impacts, aggressive filter
sweeps. This is a light 16:9 product explainer over a lavender/white UI. Same
pipeline, opposite palette:

| | promo | explainer |
|---|---|---|
| Bed | dark synth, heavy sub | soft plucked synth + warm pad |
| Impacts | full sub drop + crack | soft thud, no sub drop anywhere |
| SFX role | the hook | punctuation, mixed 12 dB back |
| Speech density | 22.5 s / 30 s (75%) | 51.4 s / 95 s (54%) |
| Final LRA | 1.3 LU | 6.2 LU |

The much higher loudness range is the point: this piece has a written dynamic
arc (lift, dip, swell) and crushing it flat would erase the direction.

---

## Voiceover

Voice: **`marin`** via OpenRouter `openai/gpt-audio`. Cost **$0.094** per full
render, so re-rendering to tune timing is effectively free.

Rendered per line with an identical persona prompt each time — that is what
holds the voice consistent, since gpt-audio drifts if the framing changes.
There is no `speed` parameter, so a line that overruns its slot is re-rendered
with an escalating pacing instruction rather than time-stretched.

| Start | Line | Len |
|------:|------|----:|
| 0.60 | Tired of clunky LaTeX setups? | 2.31 |
| 5.35 | Meet LetX — collaborative LaTeX, right in your browser. | 4.03 |
| 10.30 | No installs. Just start writing, for free. | 3.05 |
| 14.45 | Sign in in seconds. Zero config. | 2.76 |
| 19.45 | Keep every project organized — or import straight from GitHub, or a zip. | 4.70 |
| 26.40 | Choose from over a thousand templates, ready to go. | 3.52 |
| 32.45 | Write together in real time. No conflicts, no version clashes. | 5.20 |
| 40.45 | Compile in seconds. No paywalls, no waiting. | 3.85 |
| 48.45 | Meet your AI assistant — like Cursor, for papers. Ask it to write a section, and watch it generate right in your editor. | 8.01 |
| 61.45 | Editor, templates, AI, and PDF — all in one platform. | 4.97 |
| 68.70 | Loved by students and faculty who've made the switch. | 2.89 |
| 78.45 | Built by researchers, for researchers. | 3.12 |
| 85.70 | Start writing, free — at letx.app. | 2.97 |

Total speech **51.4 s of 95 s (54%)**.

**Spelled for the speech model, not for humans:** `LaTeX` → `Lay-tek` (it
otherwise says "latex", the material), `LetX` → `Let X`, `letx.app` →
`Let X dot app`, `AI` → `A I`, `PDF` → `P D F`.

**One deliberate change from the supplied script.** The praise line was
"Loved by researchers and students"; the card on screen at that moment reads
"Loved by students and faculty". The VO now matches the screen.

---

## Music

120 BPM (beat 0.5 s, bar 2.0 s), progression **C–G–Am–F**, one chord per bar, so
the phrase is 8.0 s. Every section boundary in the script lands on a whole
second and therefore on a beat; the three that carry musical direction (32 / 68 /
85) land on even seconds and are bar-aligned.

"The music lifts" is implemented as **density and brightness, not a tempo
change** — a real BPM jump mid-render would audibly seam. Measured, score only:

| Section | Level | Direction |
|---|---:|---|
| 0–5 hook | −27.8 dBFS | low pulse only |
| 14–26 build | −29.8 dBFS | pad + pluck |
| **32–48 collaborate** | **−24.2 dBFS** | **lift: +5.6 dB, kick and hats enter** |
| 61–68 platform | −23.7 dBFS | fullest |
| **68–78 praise** | **−29.5 dBFS** | **dip: −5.8 dB, drums out** |
| **85–95 outro** | **−22.2 dBFS** | **swell: loudest point of the piece** |

---

## Cue sheet

| Time | Visual | Audio |
|------:|--------|-------|
| 0.15 | cold open | reverse swell in |
| 0.55–2.15 | "Tired of clunky LaTeX setups?" types on | 24 soft key clicks |
| 4.75 | → hero page | whoosh |
| 12.55 | "Start Writing Free" pressed | thud + ping |
| 13.55 | measured cut | whoosh |
| 14.66 | auth | UI tick, then a signed-in ping at 15.60 |
| 19.55–21.05 | "Your projects. Organized." types on | 21 key clicks |
| 21.45–22.30 | project rows populate | 6 ascending ticks, panned L→R |
| 25.35 | → templates | whoosh |
| 26.55–28.05 | 6 category cards reveal | 6 ticks in a 3-column pan pattern |
| **31.30 / 32.00** | **collaboration — the lift** | **riser → soft thud + C6 ping** |
| 33.1–35.9 | three collaborator cursors appear | 3 pings at different pitches/pans |
| 33.6–39.3 | remote typing | 26 interleaved key clicks across 3 pan positions |
| 40.55 | Recompile pressed | tick + thud |
| 41.0–42.7 | compiling | 7 accelerating ticks |
| 43.60 | PDF pane refreshes | shimmer whoosh |
| 44.05 | compile succeeds | 3-note rising chime (C6/E6/G6) |
| 48.55 | AI command bar opens | ping |
| 49.0–51.4 | prompt typed into the bar | 26 key clicks |
| 52.03 | measured cut | whoosh |
| 53.0–59.0 | generation streams into the document | 30 soft ticks, randomly panned |
| 59.40 | insertion lands | ping |
| 60.05 / 61.10 / 62.85 | platform montage cuts | 3 whooshes |
| 63.4–65.1 | editor / templates / AI / PDF | 4 ascending pings |
| **67.45 → 68.33** | **light-to-dark wipe** | **biggest riser of the piece → thud** |
| 68.90–74.75 | quote cards | sparse pings, deliberately bare under the softened bed |
| 78.70 / 79.35 | two founder cards settle | 2 soft thuds |
| 84.60 → 85.43 | → outro | riser + thud |
| 86.10–88.60 | "Start writing free" types on | 19 key clicks |
| 91.20 → 91.83 | logo card | riser → thud + 3-note resolving chime, 3 s tail |
| 92–95 | hold | pad and final chord decay to the end |

A filtered noise air bed runs from 0.30 s to the end at −45 dB, so nothing is
ever truly silent. Verified: no gap longer than 0.6 s falls below −50 dBFS.

---

## Master

**−14.3 LUFS integrated · −1.6 dBTP · LRA 6.2 LU.**

Note the TP target: `build.sh` was run with `TP=-1.7`, not the usual `-1.5`.
AAC encoding after `loudnorm` overshoots by roughly 0.2 dB, and at the default
target this file measured **−1.3 dBTP** — inside safe headroom but outside our
own documented spec. Asking loudnorm for −1.7 lands the finished file at −1.6.

Video is stream-copied throughout: the muxed output's video MD5 matches the
silent master exactly (`a11a0904672342dd698f0bdd963aa275`).

---

## Rebuilding

```bash
cd audio
set -a && . ../.env && set +a          # OPENROUTER_API_KEY, for the VO only
./venv/bin/python explainer/vo_gpt.py marin build/ex_vo_marin.wav
cd build && ../venv/bin/python ../explainer/synth_ex.py
../venv/bin/python ../explainer/mix_ex.py ex_vo_marin.wav ex_mix_marin.wav
cd .. && SRC="../LetX Explainer.mp4" LRA=9 TP=-1.7 \
  ./build.sh build/ex_mix_marin.wav ../renders/explainer-95s/LetX_Explainer_95s_marin.mp4
```

Swapping the voice is one argument and about two minutes:
`alloy ash ballad coral echo sage shimmer verse marin cedar`.
`renders/voice-audition.m4a` has all ten reading the same lines, in that order.
