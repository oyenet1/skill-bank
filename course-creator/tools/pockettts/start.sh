#!/usr/bin/env bash
# PocketTTS start: ensures .venv + deps, then generates or serves.
# Usage:
#   ./start.sh --sample                    # demo mp3 -> ../../assets/audio/
#   ./start.sh --text "Hi" --voice marius --out ../../assets/audio/hi.mp3 [--language english]
#   ./start.sh serve                        # FastAPI server (web UI + API)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"
AUDIO_DIR="$HERE/../../assets/audio"

command -v uv >/dev/null || { echo "error: 'uv' not found."; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  echo "creating venv (Python 3.12)..."
  uv venv "$VENV" --python 3.12
fi
echo "installing requirements..."
VIRTUAL_ENV="$VENV" uv pip install -r "$HERE/requirements.txt"

if [ "${1:-}" = "serve" ]; then
  exec "$VENV/bin/pocket-tts" serve
fi

ARGS=("$@")
OUT=""
NEXT_IS_OUT=0
for a in "$@"; do
  if [ "$NEXT_IS_OUT" = 1 ]; then OUT="$a"; NEXT_IS_OUT=0; fi
  if [ "$a" = "--out" ]; then NEXT_IS_OUT=1; fi
done

if [ "${1:-}" = "--sample" ]; then
  mkdir -p "$AUDIO_DIR"
  "$VENV/bin/pocket-tts" generate \
    --text "Hello! This is Pocket TTS running locally for your course creator. Audio narration is ready." \
    --voice alba --language english \
    --output-path "$AUDIO_DIR/pocket_sample_tmp.wav"
  ffmpeg -y -v error -i "$AUDIO_DIR/pocket_sample_tmp.wav" -codec:a libmp3lame -q:a 3 "$AUDIO_DIR/pocket_sample_alba.mp3"
  rm "$AUDIO_DIR/pocket_sample_tmp.wav"
  echo "wrote $AUDIO_DIR/pocket_sample_alba.mp3"
  exit 0
fi

if [ $# -eq 0 ]; then
  echo "PocketTTS ready. Examples:"
  echo "  ./start.sh --text \"Hi class\" --voice marius --out ../../assets/audio/hi.mp3"
  echo "  ./start.sh serve   # web UI + API server"
  echo "Voices include: alba anna marius javert jean vera fantine paul michael estelle giovanni lola juergen rafael ..."
  echo "Cloning YOUR voice needs: accept terms at https://huggingface.co/kyutai/pocket-tts then 'uvx hf auth login',"
  echo "  then pass --voice /path/to/your_10s.wav"
  exit 0
fi

# passthrough to pocket-tts generate; --out becomes --output-path (+mp3 encode)
GEN_ARGS=()
i=0
argv=("$@")
while [ $i -lt $# ]; do
  a="${argv[$i]}"
  if [ "$a" = "--out" ]; then
    i=$((i+1)); OUT="${argv[$i]}"
    GEN_ARGS+=(--output-path "$OUT.wav.tmp.wav")
  else
    GEN_ARGS+=("$a")
  fi
  i=$((i+1))
done
"$VENV/bin/pocket-tts" generate "${GEN_ARGS[@]}"
if [ -n "$OUT" ]; then
  if [[ "$OUT" == *.mp3 ]]; then
    ffmpeg -y -v error -i "$OUT.wav.tmp.wav" -codec:a libmp3lame -q:a 3 "$OUT"
    rm "$OUT.wav.tmp.wav"
    echo "wrote $OUT"
  else
    mv "$OUT.wav.tmp.wav" "$OUT"
    echo "wrote $OUT"
  fi
fi
