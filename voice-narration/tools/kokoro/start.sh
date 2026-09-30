#!/usr/bin/env bash
# Native start: creates .venv (Python 3.12), installs deps, fetches models.
# Usage:
#   ./start.sh                     # setup only, prints usage
#   ./start.sh --sample            # setup + generate sample wav into assets/audio/
#   ./start.sh --text "Hi class" --out ../../assets/audio/intro.wav [--voice af_sky]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"
AUDIO_DIR="$HERE/../../assets/audio"

UV_BIN="$(bash "$HERE/ensure_uv.sh")"

if [ ! -x "$VENV/bin/python" ]; then
  echo "creating venv (Python 3.12)..."
  "$UV_BIN" venv "$VENV" --python 3.12
fi
if [ ! -f "$VENV/.requirements-installed" ] || ! cmp -s "$HERE/requirements.txt" "$VENV/.requirements-installed"; then
  echo "installing requirements..."
  VIRTUAL_ENV="$VENV" "$UV_BIN" pip install -r "$HERE/requirements.txt"
  cp "$HERE/requirements.txt" "$VENV/.requirements-installed"
fi

bash "$HERE/download_models.sh" "$HERE/models"

run_gen() { "$VENV/bin/python" "$HERE/generate.py" --models-dir "$HERE/models" "$@"; }

if [ "${1:-}" = "--sample" ]; then
  mkdir -p "$AUDIO_DIR"
  run_gen --text "Hello! This is Kokoro running locally for your course creator. Audio narration is ready." --out "$AUDIO_DIR/kokoro_sample.mp3"
  exit 0
fi

if [ $# -eq 0 ]; then
  echo "Kokoro ready. Generate audio with:"
  echo "  $VENV/bin/python $HERE/generate.py --text \"Hello class\" --out $AUDIO_DIR/lesson.mp3"
  echo "  ./start.sh --text \"Hello class\" --out ../../assets/audio/lesson.mp3 --voice af_sky"
  echo "  ./start.sh --sample   # regenerate the demo mp3"
  "$VENV/bin/python" "$HERE/generate.py" --help
  exit 0
fi

run_gen "$@"
