#!/usr/bin/env bash
# Download Kokoro ONNX model + voices (~350MB total). Safe to re-run (resumes).
set -euo pipefail
MODELS_DIR="${1:-$(cd "$(dirname "$0")" && pwd)/models}"
mkdir -p "$MODELS_DIR"
BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
echo "models -> $MODELS_DIR"
curl -sSL -C - -o "$MODELS_DIR/kokoro-v1.0.onnx" "$BASE/kokoro-v1.0.onnx"
curl -sSL -C - -o "$MODELS_DIR/voices-v1.0.bin" "$BASE/voices-v1.0.bin"
ls -l "$MODELS_DIR"
