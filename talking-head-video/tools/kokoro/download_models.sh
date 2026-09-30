#!/usr/bin/env bash
# Download and verify the pinned Kokoro v1.0 model files. Resume partial files.
set -euo pipefail
MODELS_DIR="${1:-$(cd "$(dirname "$0")" && pwd)/models}"
BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
mkdir -p "$MODELS_DIR"

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d ' ' -f 1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d ' ' -f 1
  else
    echo "error: sha256sum or shasum is required to verify model downloads" >&2
    exit 1
  fi
}

verified() {
  [ -f "$1" ] && [ "$(wc -c < "$1" | tr -d ' ')" = "$2" ] && [ "$(sha256_file "$1")" = "$3" ]
}

fetch_model() {
  local name="$1" size="$2" digest="$3" target="$MODELS_DIR/$1" partial="$MODELS_DIR/$1.part"
  if verified "$target" "$size" "$digest"; then
    echo "$name verified; using existing file."
    return
  fi
  if [ -f "$target" ]; then
    echo "$name failed verification; downloading a clean copy." >&2
    rm -f "$target"
  fi
  if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl is required to download Kokoro models" >&2
    exit 1
  fi
  echo "downloading $name..."
  curl --fail --location --silent --show-error --retry 3 --continue-at - \
    "$BASE/$name" --output "$partial"
  if ! verified "$partial" "$size" "$digest"; then
    echo "error: $name download failed size or SHA-256 verification; partial file kept for retry" >&2
    exit 1
  fi
  mv "$partial" "$target"
  echo "$name verified."
}

# SHA-256 values pinned from the v1.0 release files (sizes from GitHub's release API).
fetch_model kokoro-v1.0.onnx 325532387 7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5
fetch_model voices-v1.0.bin 28214398 bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d
