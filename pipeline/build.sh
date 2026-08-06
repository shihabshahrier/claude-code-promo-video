#!/usr/bin/env bash
# LetX promo — mux the finished mix onto the silent render.
#
# Video is stream-copied (no re-encode, no quality loss).
# Audio uses TWO-PASS loudnorm in linear mode: pass 1 measures, pass 2 applies
# a single static gain. Single-pass loudnorm is dynamic — it pumps, and it
# overshot to +0.4 dBTP here, which clips once a platform re-encodes.
set -euo pipefail

SRC="${SRC:-/Users/shahriar/github/letx-marketing/LetX Promo.mp4}"
MIX="$1"
OUT="$2"
I="${I:--14}"        # integrated target (LUFS)
TP="${TP:--1.5}"     # true-peak ceiling (dBTP)
LRA="${LRA:-7}"

# ---- pass 1: measure -------------------------------------------------------
MEAS=$(ffmpeg -hide_banner -nostats -i "$MIX" \
  -af "loudnorm=I=$I:TP=$TP:LRA=$LRA:print_format=json" \
  -f null - 2>&1 | awk '/^\{/,/^\}/')

get() { echo "$MEAS" | grep "\"$1\"" | sed 's/.*: *"\(.*\)".*/\1/'; }
MI=$(get input_i); MTP=$(get input_tp); MLRA=$(get input_lra)
MTH=$(get input_thresh); MOFF=$(get target_offset)
echo "measured: I=$MI TP=$MTP LRA=$MLRA thresh=$MTH offset=$MOFF"

# ---- pass 2: apply + mux ---------------------------------------------------
ffmpeg -y -v error \
  -i "$SRC" -i "$MIX" \
  -filter_complex "[1:a]loudnorm=I=$I:TP=$TP:LRA=$LRA:\
measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:\
measured_thresh=$MTH:offset=$MOFF:linear=true:print_format=summary,\
aresample=48000:resampler=soxr:precision=28[a]" \
  -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 \
  -movflags +faststart -shortest \
  "$OUT"

echo "wrote $OUT"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 \
  | grep -E "^ *(I|LRA|Peak): *-?[0-9]" | sed 's/^/  final /'
