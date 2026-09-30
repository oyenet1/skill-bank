#!/usr/bin/env bash
# Locate uv or install it beside this tool without changing the user's PATH.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MANAGED="$HERE/.tooling/uv"

if [ -x "$MANAGED" ]; then
  printf '%s\n' "$MANAGED"
  exit 0
fi
if command -v uv >/dev/null 2>&1; then
  command -v uv
  exit 0
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "error: curl is required to install uv automatically" >&2
  exit 1
fi

mkdir -p "$HERE/.tooling"
INSTALLER="$(mktemp)"
trap 'rm -f "$INSTALLER"' EXIT
echo "uv missing; downloading the official installer..." >&2
curl --fail --location --silent --show-error --retry 3 \
  https://astral.sh/uv/install.sh --output "$INSTALLER"
UV_INSTALL_DIR="$HERE/.tooling" UV_NO_MODIFY_PATH=1 sh "$INSTALLER" >&2
if [ ! -x "$MANAGED" ]; then
  echo "error: uv installer finished without creating $MANAGED" >&2
  exit 1
fi
"$MANAGED" --version >&2
printf '%s\n' "$MANAGED"
