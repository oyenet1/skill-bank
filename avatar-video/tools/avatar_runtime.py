#!/usr/bin/env python3
"""Private avatar runtime paths, verification, and cancellable child processes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import threading
import time

from avatar_download import verified
from avatar_probe import progress

ACTIVE_CHILD = None


def runtime_dir() -> Path:
    if override := os.environ.get("SKILL_BANK_AVATAR_HOME"):
        return Path(override).expanduser().resolve()
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    elif platform.system() == "Darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return base / "skill-bank/avatar"


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def paths(root: Path, backend: dict) -> dict:
    base = root / "backends" / backend["id"]
    venv = base / ".venv"
    return {"base": base, "venv": venv, "python": venv / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python"),
            "models": root / "models" / backend["id"], "source": base / "source", "state": base / "installed.json"}


def environment(root: Path) -> dict:
    env = os.environ.copy()
    env.update(UV_PYTHON_INSTALL_DIR=str(root / "python"), UV_CACHE_DIR=str(root / "uv-cache"),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", UV_NO_CONFIG="1",
               HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1")
    return env


def _status(root: Path, backend: dict, *, verify_models: bool = True) -> dict:
    location = paths(root, backend)
    missing = []
    state = {}
    try:
        state = json.loads(location["state"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        missing.append("installed-state")
    if state.get("manifestHash") != fingerprint(backend):
        missing.append("manifest-version")
    requirements = location["base"] / "requirements.sha256"
    expected_requirements = fingerprint({"python": backend["pythonVersion"], "environment": backend["environment"], "accelerator": state.get("accelerator", {}).get("kind")})
    if not requirements.is_file() or requirements.read_text().strip() != expected_requirements:
        missing.append("environment-version")
    for key in ("python", "source"):
        if not location[key].exists():
            missing.append(key)
    code_hashes = state.get("sourceHashes", {})
    if not code_hashes:
        missing.append("source-verification")
    else:
        for name, expected in code_hashes.items():
            path = location["source"] / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                missing.append("source:" + name)
    if verify_models:
        for file in backend["files"]:
            if not verified(location["models"] / file["name"], file):
                missing.append("model:" + file["name"])
    if backend.get("requiresSmokeTest") and not state.get("smokeVerified"):
        missing.append("inference-smoke-check")
    for key in ("ffmpeg", "ffprobe"):
        value = state.get("mediaPaths", {}).get(key)
        if not value or not Path(value).is_file():
            missing.append(key)
    return {"ready": not missing, "backend": backend["id"], "paths": {key: str(value) for key, value in location.items()},
            "missing": missing, "state": state}


def status(root: Path, backend: dict, *, verify_models: bool = True) -> dict:
    try:
        return _status(root, backend, verify_models=verify_models)
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return {"ready": False, "backend": backend["id"], "paths": {key: str(value) for key, value in paths(root, backend).items()},
                "missing": ["invalid-installed-metadata"], "state": {}}


def stop_child() -> None:
    child = ACTIVE_CHILD
    if child is None or child.poll() is not None:
        return
    if platform.system() == "Windows":
        try:
            subprocess.run(["taskkill.exe", "/T", "/F", "/PID", str(child.pid)], capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            child.kill()
    else:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if platform.system() != "Windows":
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                child.kill()
        else:
            child.kill()
        child.wait(timeout=5)


def interrupted(_number, _frame) -> None:
    stop_child()
    raise KeyboardInterrupt


def run(command: list[str], log: Path, env: dict, *, cwd: Path | None = None, phase: str = "env") -> None:
    global ACTIVE_CHILD
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as output:
        ACTIVE_CHILD = subprocess.Popen(command, env=env, cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            start_new_session=platform.system() != "Windows",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0)
        child = ACTIVE_CHILD

        def consume():
            for line in child.stdout:
                output.write(line)
                output.flush()
                try:
                    event = json.loads(line)
                    if isinstance(event, dict) and isinstance(event.get("phase"), str) and isinstance(event.get("message"), str):
                        progress(event.pop("phase"), event.pop("message"), **event)
                except (ValueError, TypeError):
                    pass

        reader = threading.Thread(target=consume, daemon=True)
        reader.start()
        try:
            while child.poll() is None:
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    progress(phase, "Local avatar operation is still running", log=str(log))
            reader.join()
        except BaseException:
            stop_child()
            reader.join(timeout=5)
            raise
        finally:
            child.stdout.close()
            ACTIVE_CHILD = None
    if child.returncode:
        detail = log.read_text(encoding="utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"Avatar command failed ({child.returncode}); see {log}: {detail}")
