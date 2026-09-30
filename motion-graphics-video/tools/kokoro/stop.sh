#!/usr/bin/env bash
# Stop everything Kokoro-related. Native runs are one-shot (nothing to stop);
# this cleans up any leftover docker containers/network from `docker compose run`.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  cd "$HERE"
  docker compose down --remove-orphans 2>/dev/null || true
  # safety net: remove any exited kokoro containers if 'run --rm' didn't
  LEFT=$(docker ps -aq --filter "ancestor=course-kokoro:latest" 2>/dev/null || true)
  if [ -n "$LEFT" ]; then
    # shellcheck disable=SC2086
    docker rm -f $LEFT >/dev/null 2>&1 || true
    echo "removed leftover container(s): $LEFT"
  fi
else
  echo "docker compose not available, nothing to tear down."
fi

echo "Kokoro stopped. (Native runs exit on their own — nothing runs in background.)"
echo "Optional full cleanup:"
echo "  docker rmi course-kokoro:latest   # delete the built image (~1.5GB)"
echo "  rm -rf \"$HERE/.venv\" \"$HERE/models\"  # delete venv+models (~500MB, re-downloaded by ./start.sh)"
