# Step 3 — Write the voiceover with timestamps

**Where:** Claude  
**Time:** ~10 min

This is the step people skip, and it is the one that makes the result feel produced rather than assembled. You are not writing a script — you are writing a script that already knows where the silences are.

**You end up with:** A table of lines, each with a start time and a maximum length in seconds.

---

```
Write the voiceover for this 30-second video.

Rules:
- Give me a table: start time (seconds), the line, and a max length in
  seconds it must fit inside.
- Lines must sit in the GAPS around the on-screen moments, never on top
  of an impact. If the screen slams at 2.20s, the line lands at 2.28s.
- Total speech should be roughly 20-23 seconds of the 30. Silence is
  what makes the rest land.
- Short sentences. Fragments are fine. Read it out loud — if you run out
  of breath, it is too long.
- Do NOT narrate what is already on screen. Add the thing the picture
  cannot say.
- Never speak a number I have not verified. Route around it.

Then give me a second column: each line respelled for a text-to-speech
phonemizer rather than for humans. For example ".tex" becomes "dot tek",
"LetX" becomes "Let X", "letx.app" becomes "Let X dot app". TTS reads
the spelling, not your intent.
```

---

Replace anything in `<angle brackets>`.

Full write-up: <https://shihub.site/blog/make-promo-video-with-claude-code>
