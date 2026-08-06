#!/usr/bin/env bash
# One-time setup for the LetX promo audio pipeline.
#
# Everything runs locally — no API keys, no per-render cost, no licensing
# questions about the music or SFX (all of it is synthesized).
set -euo pipefail

cd "$(dirname "$0")"

# --- system deps ------------------------------------------------------------
command -v ffmpeg >/dev/null || brew install ffmpeg
command -v espeak-ng >/dev/null || brew install espeak-ng

# Kokoro pulls in spaCy, which has no wheels for Python 3.14 (blis fails to
# build). 3.12 is the newest version that installs cleanly.
PY=$(command -v python3.12 || true)
[ -n "$PY" ] || { echo "need python3.12: brew install python@3.12"; exit 1; }

# --- venv -------------------------------------------------------------------
[ -d venv ] || "$PY" -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q numpy scipy soundfile kokoro

# --- espeak-ng data ---------------------------------------------------------
# The espeakng_loader wheel ships an incomplete data dir: no phontab/phondata,
# so misaki's phonemizer dies with
#   Error processing file '.../espeakng_loader/phontab': No such file
# espeak-ng also looks for those files in the loader dir itself, not in its
# espeak-ng-data/ subdir, so they get copied to both places.
LOADER=$(./venv/bin/python -c "import espeakng_loader,os;print(os.path.dirname(espeakng_loader.__file__))")
BREW_DATA=$(brew --prefix espeak-ng)/share/espeak-ng-data
cp -R "$BREW_DATA"/* "$LOADER/"
cp -Rn "$BREW_DATA"/* "$LOADER/espeak-ng-data/" 2>/dev/null || true

./venv/bin/python -c "import kokoro; print('kokoro ok')"
echo "setup complete — now run ./render.sh"
