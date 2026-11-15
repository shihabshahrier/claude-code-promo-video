# Step 4 — Build the soundtrack

**Where:** Claude Code  
**Time:** ~30 min setup, then ~2 min per render

Hand Claude Code the video and the timestamped script and ask for the whole audio pipeline. You are not writing DSP — you are describing what you want to hear and letting it build the thing that makes that sound.

**You end up with:** Voiceover, an original score, and sound effects — mixed, and muxed onto the video.

---

```
In this folder is <video.mp4>: a silent 30.000s 1080x1920 promo at
30fps. Scene cuts land at <3.0 / 8.0 / 19.0 / 25.0>s.

Build me a complete soundtrack for it, locally and for free. No paid
APIs, no licensed audio, no stock music.

1. VOICEOVER — use Kokoro-82M running locally (pip install kokoro).
   Here is the script with timestamps: <paste your table>
   Render each line as its own take so the sentence-final prosody is
   natural. If a take overruns its slot, nudge the speed parameter and
   re-render it — never time-stretch the audio to fit, that is exactly
   what makes TTS sound robotic.

2. SCORE — synthesize it from scratch in numpy. Pick a BPM whose bar
   length divides my scene cuts evenly so the music lands on the cuts.
   Use a fixed random seed so renders are reproducible.

3. SOUND EFFECTS — synthesize these too, and arrange them against the
   scene boundaries: risers into each cut, an impact on every hard
   slam, UI ticks for anything that appears on screen.

4. MIX — duck the music under the voice with a little lookahead so the
   duck opens before the word, not on top of it. Carve a small dip in
   the music around 2.5 kHz so the speech has a pocket. Keep sound
   effects mostly un-ducked so impacts still hit.

5. MASTER — normalise to -14 LUFS and -1.5 dBTP, the Reels/Shorts/
   TikTok target. Use two-pass loudnorm with linear=true. Do not
   compress the bus hard before that — leave headroom and let the
   normaliser do the lift.

6. MUX — stream-copy the video (-c:v copy). Never re-encode the
   picture just to attach audio.

Make it one script I can re-run, and print the measured LUFS and true
peak at the end so I can check it.
```

---

Replace anything in `<angle brackets>`.

Full write-up: <https://shihub.site/blog/make-promo-video-with-claude-code>
