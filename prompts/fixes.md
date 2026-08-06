# When it goes wrong

Every one of these actually happened while making the LetX promo.

## The voice sounds robotic

**Why it happens.** Almost always one of two things: the text was stretched to fit a time slot, or it was spelled for humans instead of for the speech engine. Stretching audio is what produces that flat, synthetic quality — and an engine reading “.tex” says “dot tex” like a filename, not “dot tek” like a person.

**The fix.** Re-render the line at a slightly different speed instead of stretching it, and respell anything the engine will mispronounce. Generate one line at a time so each gets natural sentence-final intonation, rather than one long flat take.

Paste into Claude Code:

```
The voiceover sounds robotic. Fix it without changing my script:

1. Never time-stretch a take to fit its slot. If a line overruns, nudge
   the TTS speed parameter and re-render it clean.
2. Render each line as its own take so sentence-final prosody is
   natural, then place them at their timestamps.
3. Respell anything the phonemizer will get wrong — read my script back
   to me and flag every word where the spelling and the pronunciation
   disagree (file extensions, product names, URLs, acronyms).
4. Trim the dead air the engine leaves at the start and end of each
   take, then add an 8ms fade so nothing clicks at the seams.
```

## It sounds fine locally, but distorted after uploading

**Why it happens.** The platform re-encodes your audio. If your master is already at or above the ceiling, that re-encode pushes it over and it clips. This is the single most common way a good mix arrives broken.

**The fix.** Master to −14 LUFS with a true peak of −1.5 dBTP, and get there with a two-pass normalisation rather than a single dynamic pass. Do not crush the mix before normalising — leave it headroom and let the normaliser do the lift.

Paste into Claude Code:

```
My audio distorts after uploading to Reels/Shorts/TikTok.

Re-master it to -14 LUFS and -1.5 dBTP using two-pass loudnorm with
linear=true. Single-pass loudnorm is dynamic and will pump and overshoot
the ceiling.

Also check whether I am over-compressing before the normaliser. If the
loudness range has collapsed below about 2 LU, back the bus compression
and limiting off and leave roughly 3 dB of headroom, then let loudnorm
do the lift.

Print the measured integrated loudness and true peak so I can confirm.
```

## The audio drifts out of sync with the picture

**Why it happens.** Usually the video got re-encoded somewhere in the chain, or a new version of the render is not actually frame-identical to the one the audio was written against — even when it looks the same.

**The fix.** Stream-copy the video whenever you attach audio, so the picture is never re-encoded. And before reusing a soundtrack on a new render, verify the timing actually matches instead of assuming it does.

Paste into Claude Code:

```
Attach the audio without re-encoding the video — use -c:v copy. Never
re-encode the picture just to add a soundtrack.

I have a new version of the video render and want to reuse the existing
audio. Do NOT assume the timing matches. Verify it: sample the average
brightness of every frame in both renders, cross-correlate the two
series, and tell me the best-fit offset in frames. Also list the frames
where each render has a hard cut, and show me which cuts they share.

If the offset is not 0, tell me before muxing anything.
```

## One section is wrong but the rest is perfect

**Why it happens.** You regenerated the video, got better visuals overall, and something in one scene came out worse. Re-rendering the whole thing to fix five seconds risks losing everything that improved.

**The fix.** Swap just that section between the two renders. If the cut point falls on a keyframe in both files, this is a lossless copy — no quality loss at all, and the audio does not need to move.

Paste into Claude Code:

```
I have two renders of the same video. The newer one is better
everywhere except <scene>, where the older one is better.

Splice them: take the new render up to <time>s and the old render from
<time>s onward.

First check whether <time> is a keyframe in both files, and whether the
two files share the same codec profile, level, pixel format, colour
settings and frame rate. If they do, do the whole splice with -c copy
through the concat demuxer so there is zero quality loss — do not
re-encode.

Then confirm the result: total frame count, duration, and that the
seam is invisible.
```

## It looks fine but feels flat

**Why it happens.** Nothing is landing on the cuts. If the music runs at an arbitrary tempo, its beats drift against your edits, and the whole thing feels loose even when every individual element is good.

**The fix.** Pick a tempo whose bar length divides your scene cuts evenly, then put an impact on every hard cut and a riser leading into it. The riser is what makes a cut feel intentional rather than abrupt.

Paste into Claude Code:

```
The video feels flat. My scene cuts are at <list your cuts>s.

Choose a BPM whose bar length divides those cuts evenly so the music
lands on the edits rather than drifting against them, and tell me which
BPM you picked and why.

Then:
- Put an impact on every hard cut.
- Put a riser leading into each one, ending exactly on the cut.
- Duck the music under the voiceover with about 50ms of lookahead so
  the duck opens before the word rather than on top of it.
- Leave the impacts mostly un-ducked so they still hit through the voice.
- Never let it go fully silent — keep a quiet air bed under everything.
```

## You are about to publish a number you cannot prove

**Why it happens.** The model will happily invent a plausible statistic, and a promo video is exactly where an unverifiable claim does the most damage. This one is worth a dedicated pass.

**The fix.** Verify every number against something you can actually query, and round down rather than up. An “N+” claim never expires as you grow, so there is no reason to reach.

Paste into Claude Code:

```
Before I publish: list every factual claim and every number that
appears on screen or in the voiceover in this video.

For each one, tell me what evidence would be needed to defend it. Mark
anything you generated rather than took from me.

Rules I want applied:
- Round every public number DOWN to the round figure below the verified
  count, never up.
- If a number cannot be verified, cut it or rewrite the line to route
  around it rather than softening it.
- Never state a competitor's statistic as mine.
```

---

Full write-up: <https://shihub.online/blog/make-promo-video-with-claude-code>
