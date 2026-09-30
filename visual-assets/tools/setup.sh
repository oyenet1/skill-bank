#!/bin/sh
# First-use launcher for Linux/macOS. All provisioned tools stay in user data.
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for PY in python3 python; do
    if command -v "$PY" >/dev/null 2>&1 && "$PY" -c 'import sys; raise SystemExit(sys.version_info < (3,10))' >/dev/null 2>&1; then
        exec "$PY" "$DIR/bootstrap.py" "$@"
    fi
done
# Read-only inspection never downloads a runtime to perform its inspection.
for ARG in "$@"; do
    if [ "$ARG" = '--check' ]; then
        echo '{"ready":false,"missing":["Python 3.10+"],"retry":"Run setup.sh without --check to prepare private Python"}'
        exit 1
    fi
done
SYSTEM=$(uname -s)
ARCH=$(uname -m)
case "$ARCH" in arm64) ARCH=aarch64;; amd64) ARCH=x86_64;; esac
case "$SYSTEM" in
    Darwin) KEY="darwin-$ARCH"; BASE="$HOME/Library/Application Support";;
    Linux) KEY="linux-$ARCH"; BASE="${XDG_DATA_HOME:-$HOME/.local/share}"
        if [ "$ARCH" = x86_64 ]; then
            for LOADER in /lib/ld-musl-*.so.1; do
                if [ -f "$LOADER" ]; then KEY=linux-musl-x86_64; break; fi
            done
        fi;;
    *) echo "No private Python runtime for $SYSTEM/$ARCH" >&2; exit 1;;
esac
RUNTIME="${SKILL_BANK_PYTHON_HOME:-$BASE/skill-bank/video-runtime}"
mkdir -p "$RUNTIME/python-tools"
UV="$RUNTIME/python-tools/uv"
if ! "$UV" --version >/dev/null 2>&1; then
    if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
        UV=$(command -v uv)
    else
        SCRATCH=$(mktemp -d "$RUNTIME/python-tools/uv-launcher-XXXXXX")
        trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM
        fetch() {
            if command -v curl >/dev/null 2>&1; then
                curl --fail --location --silent --show-error --connect-timeout 20 --max-time 180 "$1" -o "$2"
            elif command -v wget >/dev/null 2>&1; then
                wget --quiet --timeout=60 -O "$2" "$1"
            else
                echo 'Private setup needs curl or wget to download its runtime.' >&2; return 1
            fi
        }
        if command -v unzip >/dev/null 2>&1; then
            SPEC=$(awk -v key="$KEY" '$0 ~ "\"" key "\"" {found=1; next} found && /}/ {exit} found {print}' "$DIR/uv_wheels.json")
            URL=$(printf '%s\n' "$SPEC" | awk -F '"' '$2=="url" {print $4}')
            HASH=$(printf '%s\n' "$SPEC" | awk -F '"' '$2=="sha256" {print $4}')
            SIZE=$(printf '%s\n' "$SPEC" | awk '/"size"/ {gsub(/[^0-9]/, ""); print}')
            VERSION=$(awk -F '"' '$2=="version" {print $4; exit}' "$DIR/uv_wheels.json")
            if [ -z "$URL" ] || [ -z "$HASH" ] || [ -z "$SIZE" ]; then
                echo "No prebuilt Python manager for $KEY" >&2; exit 1
            fi
            echo 'Preparing verified private Python manager from PyPI' >&2
            fetch "$URL" "$SCRATCH/uv.whl"
            ACTUAL_SIZE=$(wc -c < "$SCRATCH/uv.whl" | tr -d ' ')
            if command -v sha256sum >/dev/null 2>&1; then
                ACTUAL_HASH=$(sha256sum "$SCRATCH/uv.whl" | awk '{print $1}')
            elif command -v shasum >/dev/null 2>&1; then
                ACTUAL_HASH=$(shasum -a 256 "$SCRATCH/uv.whl" | awk '{print $1}')
            elif command -v openssl >/dev/null 2>&1; then
                ACTUAL_HASH=$(openssl dgst -sha256 "$SCRATCH/uv.whl" | awk '{print $NF}')
            else
                echo 'A SHA-256 verifier is required for private runtime setup.' >&2; exit 1
            fi
            if [ "$ACTUAL_SIZE" != "$SIZE" ] || [ "$ACTUAL_HASH" != "$HASH" ]; then
                echo 'Private Python manager failed pinned size/SHA-256 verification.' >&2; exit 1
            fi
            unzip -p "$SCRATCH/uv.whl" "uv-$VERSION.data/scripts/uv" > "$SCRATCH/uv"
            chmod 755 "$SCRATCH/uv"
            "$SCRATCH/uv" --version >&2
            for LICENSE in LICENSE-APACHE LICENSE-MIT; do
                unzip -p "$SCRATCH/uv.whl" "uv-$VERSION.dist-info/licenses/$LICENSE" > "$RUNTIME/python-tools/uv-$LICENSE"
            done
            mv "$SCRATCH/uv" "$UV"
        else
            # The official installer uses tar when an unzip executable is absent.
            fetch 'https://astral.sh/uv/install.sh' "$SCRATCH/install.sh"
            UV_INSTALL_DIR="$RUNTIME/python-tools" UV_NO_MODIFY_PATH=1 sh "$SCRATCH/install.sh" >&2
        fi
        "$UV" --version >/dev/null
        rm -rf "$SCRATCH"
        trap - EXIT HUP INT TERM
    fi
fi
export UV_PYTHON_INSTALL_DIR="$RUNTIME/python" UV_CACHE_DIR="$RUNTIME/uv-cache"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
exec "$UV" run --no-project --no-build --python 3.12 python "$DIR/bootstrap.py" "$@"
