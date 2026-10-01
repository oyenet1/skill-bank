#!/bin/sh
# Compatibility entry point; use the same private runtime as Windows/Python.
set -eu
KOKORO_TOOL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for KOKORO_PYTHON in python3 python; do
    if command -v "$KOKORO_PYTHON" >/dev/null 2>&1 && "$KOKORO_PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3,10))' >/dev/null 2>&1; then
        exec "$KOKORO_PYTHON" "$KOKORO_TOOL_DIR/start.py" "$@"
    fi
done
if [ "${1:-}" = '--check' ]; then
    echo '{"ready":false,"missing":["Python 3.10+"]}'
    exit 1
fi
case $(uname -s) in
    Darwin) KOKORO_RUNTIME_BASE="$HOME/Library/Application Support";;
    Linux) KOKORO_RUNTIME_BASE="${XDG_DATA_HOME:-$HOME/.local/share}";;
    *) echo 'Use the PowerShell setup launcher on Windows.' >&2; exit 1;;
esac
KOKORO_PYTHON_RUNTIME="${SKILL_BANK_PYTHON_HOME:-$KOKORO_RUNTIME_BASE/skill-bank/video-runtime}"
KOKORO_UV="$KOKORO_PYTHON_RUNTIME/python-tools/uv"
if command -v uv >/dev/null 2>&1; then
    KOKORO_UV=$(command -v uv)
elif [ ! -x "$KOKORO_UV" ]; then
    sh "$KOKORO_TOOL_DIR/../setup.sh" --yes --no-skills
fi
export UV_PYTHON_INSTALL_DIR="$KOKORO_PYTHON_RUNTIME/python" UV_CACHE_DIR="$KOKORO_PYTHON_RUNTIME/uv-cache"
export PATH="$(dirname -- "$KOKORO_UV"):$PATH"
exec "$KOKORO_UV" run --no-project --no-build --python 3.12 python "$KOKORO_TOOL_DIR/start.py" "$@"
