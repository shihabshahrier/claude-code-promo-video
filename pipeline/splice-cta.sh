#!/usr/bin/env bash
# Build the v2 visual master: "LetX Promo 2" body + "LetX Promo" CTA.
#
# Promo 2 has better visuals throughout but its Scene 5 wordmark is a circled-X
# glyph instead of the clean LetX lockup. Both renders share identical timing,
# codec params, and — crucially — a keyframe at exactly 25.000s, which is also
# the Scene 4→5 cut. So the swap is a pure stream copy: no re-encode, no
# generation loss, no audio resync needed.
#
#   frames    0-749  (0.000-25.000s)  <- LetX Promo 2.mp4   (better visuals)
#   frames  750-899  (25.000-30.000s) <- LetX Promo.mp4     (good wordmark)
set -euo pipefail

cd "$(dirname "$0")/.."

BODY="${BODY:-LetX Promo 2.mp4}"
TAIL="${TAIL:-LetX Promo.mp4}"
CUT="${CUT:-25}"
OUT="${OUT:-assets/LetX_Promo_v2_silent.mp4}"

mkdir -p assets video/.tmp
cd video/.tmp

# Both cuts land on a keyframe, so -c copy is exact.
ffmpeg -v error -y -i "../../$BODY" -t "$CUT"  -c copy -an body.mp4
ffmpeg -v error -y -ss "$CUT" -i "../../$TAIL" -c copy -an tail.mp4

printf "file 'body.mp4'\nfile 'tail.mp4'\n" > concat.txt
ffmpeg -v error -y -f concat -safe 0 -i concat.txt -c copy \
  -movflags +faststart "../../$OUT"

cd ../..
rm -rf video/.tmp

echo "wrote $OUT"
ffprobe -v error -select_streams v -count_frames \
  -show_entries stream=nb_read_frames,duration,width,height,r_frame_rate \
  -of default=nw=1 "$OUT"
