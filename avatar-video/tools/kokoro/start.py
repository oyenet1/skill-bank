#!/usr/bin/env python3
"""Prepare Kokoro and run narration on Windows, macOS, or Linux.

The private uv binary, Python environment, and verified models live in user
data. No package manager, global pip install, or shell profile edit is
needed. Use ``python start.py --sample`` or pass generate.py arguments.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from network_tls import tls_context


def runtime_dir() -> Path:
    override = os.environ.get("SKILL_BANK_KOKORO_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    elif platform.system() == "Darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return base / "skill-bank" / "kokoro"


RUNTIME = runtime_dir()
UV = RUNTIME / ".tooling" / ("uv.exe" if os.name == "nt" else "uv")
VENV = RUNTIME / ".venv"
MODELS = RUNTIME / "models"
MODEL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
MODEL_FILES = {
    "kokoro-v1.0.onnx": (325532387, "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5"),
    "voices-v1.0.bin": (28214398, "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"),
}


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(arguments: list[str | Path], **kwargs: object) -> None:
    subprocess.run([str(argument) for argument in arguments], check=True, **kwargs)


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def ensure_uv() -> Path:
    if UV.is_file():
        return UV
    existing = shutil.which("uv")
    if existing:
        return Path(existing)
    if platform.system() not in ("Windows", "Darwin", "Linux"):
        raise RuntimeError(f"Kokoro setup does not support {platform.system()}")
    UV.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".ps1" if os.name == "nt" else ".sh"
    url = f"https://astral.sh/uv/install{suffix}"
    progress("uv", "Installing private uv runtime")
    with tempfile.TemporaryDirectory(prefix="kokoro-uv-") as scratch:
        installer = Path(scratch) / ("install" + suffix)
        with urllib.request.urlopen(url, timeout=30, context=tls_context()) as response, installer.open("wb") as output:
            shutil.copyfileobj(response, output)
        env = os.environ.copy()
        env.update(UV_INSTALL_DIR=str(UV.parent), UV_NO_MODIFY_PATH="1")
        if os.name == "nt":
            powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
            if not powershell:
                raise RuntimeError("PowerShell is required for the Windows uv installer")
            run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", installer], env=env)
        else:
            run(["sh", installer], env=env)
    if not UV.is_file():
        raise RuntimeError(f"uv installer did not create {UV}")
    run([UV, "--version"])
    return UV


def verified(path: Path, expected_size: int, expected_sha: str) -> bool:
    if not path.is_file() or path.stat().st_size != expected_size:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_sha


def download_model(name: str, expected_size: int, expected_sha: str) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    target = MODELS / name
    if verified(target, expected_size, expected_sha):
        progress("model", f"Verified {name}", downloadedBytes=expected_size, totalBytes=expected_size)
        return
    target.unlink(missing_ok=True)
    partial = MODELS / (name + ".part")
    offset = partial.stat().st_size if partial.is_file() else 0
    if offset >= expected_size:
        partial.unlink()
        offset = 0
    request = urllib.request.Request(f"{MODEL_BASE}/{name}")
    progress("model", f"Downloading {name}", downloadedBytes=offset, totalBytes=expected_size)
    if offset:
        request.add_header("Range", f"bytes={offset}-")
    with urllib.request.urlopen(request, timeout=60, context=tls_context()) as response:
        if offset and response.status != 206:
            offset = 0  # Server ignored Range; start a clean download.
        with partial.open("ab" if offset else "wb") as output:
            received = offset
            reported = offset
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                received += len(chunk)
                if received - reported >= 8 * 1024 * 1024 or received >= expected_size:
                    progress("model", f"Downloading {name}", downloadedBytes=received, totalBytes=expected_size)
                    reported = received
    if not verified(partial, expected_size, expected_sha):
        raise RuntimeError(f"{name} failed size or SHA-256 verification; retry to resume")
    partial.replace(target)
    progress("model", f"Verified {name}", downloadedBytes=expected_size, totalBytes=expected_size)


def setup() -> Path:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    uv = ensure_uv()
    python = venv_python()
    if not python.is_file():
        progress("python", "Preparing private Python 3.12 environment")
        run([uv, "venv", VENV, "--python", "3.12"])
    requirements = (ROOT / "requirements.txt").read_bytes()
    marker = VENV / ".requirements-sha256"
    wanted = hashlib.sha256(requirements).hexdigest()
    if not marker.is_file() or marker.read_text().strip() != wanted:
        progress("packages", "Installing Kokoro packages")
        run([uv, "pip", "install", "--python", python, "-r", ROOT / "requirements.txt"])
        marker.write_text(wanted + "\n")
    for name, (size, sha) in MODEL_FILES.items():
        download_model(name, size, sha)
    progress("complete", "Kokoro narration tools are ready")
    return python


def main() -> int:
    try:
        python = setup()
        args = sys.argv[1:]
        if args == ["--sample"]:
            sample = RUNTIME / "kokoro_sample.mp3"
            sample.parent.mkdir(parents=True, exist_ok=True)
            args = ["--text", "Hello! This is Kokoro running locally. Audio narration is ready.", "--out", str(sample)]
        if not args:
            print(f"Kokoro ready. Generate audio with: {sys.executable} {ROOT / 'start.py'} --text 'Hello' --out narration.mp3")
            return 0
        run([python, ROOT / "generate.py", "--models-dir", MODELS, *args])
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Kokoro setup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
