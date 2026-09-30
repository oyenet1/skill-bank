#!/usr/bin/env python3
"""Provision isolated Python packages in writable video runtime data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import sys
import urllib.request
from network_tls import tls_context
from bootstrap_uv import install_pinned_uv

from ensure_video_runtime import MANIFEST, default_runtime_dir, progress


def ensure_uv(runtime: Path, *, minimum_version: tuple[int, ...] | None = None, runner=None) -> Path:
    def usable(candidate: Path) -> bool:
        result = subprocess.run([str(candidate), "--version"], capture_output=True, text=True, timeout=20)
        if result.returncode:
            return False
        if minimum_version is None:
            return True
        match = re.search(r"uv (\d+)\.(\d+)\.(\d+)", result.stdout or "")
        return bool(match and tuple(map(int, match.groups())) >= minimum_version)

    name = "uv.exe" if platform.system() == "Windows" else "uv"
    target = runtime / "python-tools" / name
    candidates = [target]
    if found := shutil.which(name):
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file():
            try:
                if usable(candidate):
                    return candidate
            except (OSError, subprocess.TimeoutExpired):
                pass
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".ps1" if platform.system() == "Windows" else ".sh"
    progress("setup", "Installing private Python manager")
    try:
        with tempfile.TemporaryDirectory(prefix="python-manager-", dir=target.parent) as scratch:
            installer = Path(scratch) / ("install" + suffix)
            with urllib.request.urlopen("https://astral.sh/uv/install" + suffix, timeout=60, context=tls_context()) as response, installer.open("wb") as output:
                shutil.copyfileobj(response, output)
            env = os.environ.copy()
            env.update(UV_INSTALL_DIR=str(target.parent), UV_NO_MODIFY_PATH="1")
            if suffix == ".ps1":
                shell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
                if not shell:
                    raise RuntimeError("PowerShell is required to install the private Python manager")
                command = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(installer)]
            else:
                command = ["sh", str(installer)]
            if runner:
                runner(command, env)
            else:
                subprocess.run(command, env=env, check=True, stdout=subprocess.DEVNULL)
            if not target.is_file() or not usable(target):
                raise RuntimeError("Standalone Python manager installation did not verify")
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        progress("setup", "Standalone installer unavailable; using verified PyPI wheel", reason=type(error).__name__)
        install_pinned_uv(target)
    if not target.is_file() or not usable(target):
        raise RuntimeError("Private Python manager installation did not verify")
    return target


def transcription_packages() -> dict[str, str]:
    packages = dict(MANIFEST["transcription"]["packages"])
    if platform.system() == "Darwin":
        release = platform.mac_ver()[0]
        major = int(release.split(".")[0]) if release else 0
        if major < 14:
            packages["av"] = MANIFEST["transcription"]["legacyMacAv"]
    return packages


def transcription_receipt(runtime: Path, model: str) -> Path:
    name = hashlib.sha256(model.encode()).hexdigest()[:20]
    return runtime / "asr" / f"ready-{name}.json"


def check_transcription(runtime: Path, model: str) -> dict:
    missing = {"ready": False, "missing": ["transcription"], "model": model}
    try:
        receipt = json.loads(transcription_receipt(runtime, model).read_text(encoding="utf-8"))
        if (not isinstance(receipt, dict) or receipt.get("packages") != transcription_packages()
                or receipt.get("model") != model):
            return missing
        python = Path(receipt["pythonExecutable"])
        if not python.is_file():
            return missing
        env = dict(os.environ, HF_HUB_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        command = [str(python), str(Path(__file__).with_name("transcribe_with_faster_whisper.py")),
                   "--out", str(runtime / "asr/unused.json"), "--models", str(runtime / "asr/models"),
                   "--model", model, "--check"]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120)
        status = json.loads(result.stdout)
        if not isinstance(status, dict):
            return {**missing, "error": "Invalid transcription readiness response"}
        if result.returncode or not status.get("ready") or status.get("packages") != transcription_packages():
            return {**missing, "error": status.get("error", "Cached transcription runtime did not verify")}
        return {**status, "missing": []}
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        return {**missing, "error": str(error)}


def isolated_command(runtime: Path, packages: dict[str, str], script: Path, arguments: list[str]) -> tuple[list[str], dict[str, str]]:
    uv = ensure_uv(runtime)
    packages = dict(packages)
    if platform.system() == "Darwin" and "av" in packages:
        packages["av"] = transcription_packages()["av"]
    env = os.environ.copy()
    # Large ASR wheels need more than UV's default 30-second read timeout on
    # slow links. Bound its internal downloads while other setup branches run.
    env.setdefault("UV_HTTP_TIMEOUT", "120")
    env.setdefault("UV_CONCURRENT_DOWNLOADS", "4")
    env.update(UV_PYTHON_INSTALL_DIR=str(runtime / "python"), UV_CACHE_DIR=str(runtime / "uv-cache"),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    identity = hashlib.sha256(json.dumps({"python": "3.12", "packages": packages}, sort_keys=True).encode()).hexdigest()[:20]
    venv = runtime / "python-environments" / identity
    python = venv / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    if venv.is_symlink():
        raise RuntimeError("Private Python environment is an unexpected symbolic link")
    if not python.is_file():
        if venv.exists():
            shutil.rmtree(venv)  # Retry an incomplete managed environment only.
        venv.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(uv), "venv", str(venv), "--python", "3.12"], env=env, check=True)
    marker = venv / ".packages.json"
    expected = json.dumps(packages, sort_keys=True)
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != expected:
        subprocess.run([str(uv), "pip", "install", "--python", str(python), "--only-binary", ":all:",
                        *[f"{name}=={version}" for name, version in packages.items()]], env=env, check=True)
        marker.write_text(expected + "\n", encoding="utf-8")
    return [str(python), str(script), *arguments], env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    parser.add_argument("--prepare-transcription", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--model", default=MANIFEST["transcription"]["englishModel"])
    args = parser.parse_args()
    runtime = args.runtime_dir.expanduser().resolve()
    try:
        if args.check:
            result = check_transcription(runtime, args.model)
            print(json.dumps(result))
            return 0 if result["ready"] else 1
        if args.prepare_transcription:
            progress("setup", "Preparing speech packages and model")
            worker = Path(__file__).with_name("transcribe_with_faster_whisper.py")
            command, env = isolated_command(runtime, transcription_packages(), worker,
                ["--out", str(runtime / "asr/prepare.json"), "--models", str(runtime / "asr/models"), "--model", args.model])
            prepared = subprocess.run(command, env=env, check=True, stdout=subprocess.PIPE, text=True)
            result = json.loads(prepared.stdout)
            if not isinstance(result, dict) or not result.get("ready") or result.get("packages") != transcription_packages():
                raise RuntimeError("Transcription packages and model did not verify")
            receipt = transcription_receipt(runtime, args.model)
            receipt.parent.mkdir(parents=True, exist_ok=True)
            staged = receipt.with_suffix(".part")
            staged.write_text(json.dumps(result) + "\n", encoding="utf-8")
            staged.replace(receipt)
            print(json.dumps(result))
        else:
            print(json.dumps({"ready": True, "uv": str(ensure_uv(runtime))}))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
