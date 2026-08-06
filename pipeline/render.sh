#!/usr/bin/env bash
# Render the whole promo soundtrack and mux it onto the silent video.
#
#   ./render.sh                 # default voice (af_heart)
#   ./render.sh af_bella        # a different Kokoro voice
#   VOICE=am_fenrir ./render.sh
#
# Roughly 2 min end to end on an M-series Mac. Fully deterministic —
# same inputs always produce the same master.
set -euo pipefail

cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:$PATH"

VOICE="${1:-${VOICE:-af_heart}}"
# The v2 visual master — Promo 2's body spliced onto Promo 1's CTA.
# Build it with ../video/splice-cta.sh if it's missing.
SRC="${SRC:-../assets/LetX_Promo_v2_silent.mp4}"
OUTDIR="${OUTDIR:-../renders/promo-30s-v2}"
mkdir -p "$OUTDIR" build

PY=./venv/bin/python
[ -x "$PY" ] || { echo "run ./setup.sh first"; exit 1; }

echo "==> score + sfx"
(cd build && "../$PY" ../synth.py)

echo "==> voiceover ($VOICE)"
(cd build && "../$PY" ../vo.py "$VOICE" "vo_$VOICE.wav")

echo "==> mix"
(cd build && "../$PY" ../mix.py "vo_$VOICE.wav" "mix_$VOICE.wav")

echo "==> mux"
SRC="$SRC" ./build.sh "build/mix_$VOICE.wav" "$OUTDIR/LetX_Promo_30s_$VOICE.mp4"
cp "build/mix_$VOICE.wav" "$OUTDIR/audio_master_$VOICE.wav"
