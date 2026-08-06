# Step 2 — Generate the animation

**Where:** Claude  
**Time:** ~20 min

Now turn the scene sheet into a real animated video. The trick that makes it exportable: every frame must be a pure function of time. No randomness, no CSS transitions, no wall-clock — otherwise the render and the preview disagree and your audio lands on the wrong frame.

**You end up with:** A 1080×1920 MP4, silent, exactly 30.000 seconds.

---

```
Build the 30-second animated promo from the scene sheet above.

=== HARD TECHNICAL REQUIREMENTS (needed for MP4 export) ===
- Wrap everything in a single <Stage width={1080} height={1920} duration={30}>.
- Drive ALL motion from useTime(). Never use CSS @keyframes, CSS
  transitions, Math.random(), or Date.now() — every frame must be a pure
  function of time, or the export will not match the preview.
- Any on-canvas control gets data-export-hide.

=== CANVAS & SAFE ZONES ===
1080 x 1920 (9:16). Reels, Shorts and TikTok overlay their own UI.
Keep ALL text and key visuals inside:
  vertical:   y = 260 to y = 1560
  horizontal: x = 70 to x = 950   (right edge holds the like/share rail)
Background art may bleed to the edges; text may not.

=== BRAND ===
Background <#hex>  Surface <#hex>  Hairline <#hex>
Primary <#hex>     Accent <#hex>   Secondary text <#hex>
Display type: <font> (heavy weights, tight tracking)
Mono type: <font> (for filenames, code, numbers)
Feel: <e.g. premium dark developer tool. Confident, not playful.
Think Linear or Vercel. Generous negative space. No drop shadows, no
gradients on text, no emoji, no stock illustration.>

=== MOTION PRINCIPLES ===
- Ease everything with a smooth cubic ease-out. Nothing linear,
  nothing bouncy.
- Cuts are hard. Use at most one wipe in the whole video.
- Something must move in every single frame — no dead holds over 1.4s.
- The final frame must be legible as a still. It becomes the thumbnail.

Then walk scene by scene through the sheet, describing exactly what
appears, when, and how it eases in.
```

---

Replace anything in `<angle brackets>`.

Full write-up: <https://shihub.online/blog/make-promo-video-with-claude-code>
