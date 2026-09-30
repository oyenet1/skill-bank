#!/bin/sh
# First-use bootstrap launcher for Linux and macOS.
# Detects a Python 3 interpreter, then runs the cross-platform bootstrap.
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

for PY in python3 python; do
    if command -v "$PY" >/dev/null 2>&1; then
        exec "$PY" "$DIR/bootstrap.py" "$@"
    fi
done

echo "Python 3.10+ is required. Install it from https://www.python.org/downloads/ and rerun this script." >&2
exit 1
