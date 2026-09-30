#!/bin/sh
# Docker entrypoint: ensure models exist in /models, then run the generator.
set -eu
MODELS_DIR="${KOKORO_MODELS:-/models}"
mkdir -p "$MODELS_DIR"
BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
[ -s "$MODELS_DIR/kokoro-v1.0.onnx" ] || curl -sSL -C - -o "$MODELS_DIR/kokoro-v1.0.onnx" "$BASE/kokoro-v1.0.onnx"
[ -s "$MODELS_DIR/voices-v1.0.bin" ] || curl -sSL -C - -o "$MODELS_DIR/voices-v1.0.bin" "$BASE/voices-v1.0.bin"
exec python /app/generate.py --models-dir "$MODELS_DIR" "$@"
