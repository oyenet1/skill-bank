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

command -v uv >/dev/null || { echo "error: 'uv' not found. Install from https://docs.astral.sh/uv/"; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  echo "creating venv (Python 3.12)..."
  uv venv "$VENV" --python 3.12
fi
echo "installing requirements..."
VIRTUAL_ENV="$VENV" uv pip install -r "$HERE/requirements.txt"

if [ ! -s "$HERE/models/kokoro-v1.0.onnx" ] || [ ! -s "$HERE/models/voices-v1.0.bin" ]; then
  echo "downloading models..."
  bash "$HERE/download_models.sh" "$HERE/models"
else
  echo "models present, skipping download."
fi

run_gen() { "$VENV/bin/python" "$HERE/generate.py" --models-dir "$HERE/models" "$@"; }

if [ "${1:-}" = "--sample" ]; then
  mkdir -p "$AUDIO_DIR"
  run_gen --text "Hello! This is Kokoro running locally for your course creator. Audio narration is ready." --out "$AUDIO_DIR/kokoro_sample.wav"
  exit 0
fi

if [ $# -eq 0 ]; then
  echo "Kokoro ready. Generate audio with:"
  echo "  $VENV/bin/python $HERE/generate.py --text \"Hello class\" --out $AUDIO_DIR/lesson.wav"
  echo "  ./start.sh --text \"Hello class\" --out ../../assets/audio/lesson.wav --voice af_sky"
  echo "  ./start.sh --sample   # regenerate the demo wav"
  "$VENV/bin/python" "$HERE/generate.py" --help
  exit 0
fi

run_gen "$@"
