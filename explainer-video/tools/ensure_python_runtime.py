#!/usr/bin/env python3
"""Provision isolated Python packages in writable video runtime data."""
from __future__ import annotations

import argparse
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
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        progress("setup", "Standalone installer unavailable; using verified PyPI wheel", reason=type(error).__name__)
        install_pinned_uv(target)
    if not target.is_file() or not usable(target):
        raise RuntimeError("Private Python manager installation did not verify")
    return target


def isolated_command(runtime: Path, packages: dict[str, str], script: Path, arguments: list[str]) -> tuple[list[str], dict[str, str]]:
    uv = ensure_uv(runtime)
    command = [str(uv), "run", "--no-project", "--no-build", "--python", "3.12"]
    packages = dict(packages)
    if platform.system() == "Darwin" and "av" in packages:
        release = platform.mac_ver()[0]
        major = int(release.split(".")[0]) if release else 0
        if major < 14:
            packages["av"] = MANIFEST["transcription"]["legacyMacAv"]
    for name, version in packages.items():
        command.extend(["--with", f"{name}=={version}"])
    command.extend(["python", str(script), *arguments])
    env = os.environ.copy()
    env.update(UV_PYTHON_INSTALL_DIR=str(runtime / "python"), UV_CACHE_DIR=str(runtime / "uv-cache"),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return command, env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    parser.add_argument("--prepare-transcription", action="store_true")
    parser.add_argument("--model", default=MANIFEST["transcription"]["englishModel"])
    args = parser.parse_args()
    runtime = args.runtime_dir.expanduser().resolve()
    try:
        if args.prepare_transcription:
            progress("setup", "Preparing speech packages and model")
            worker = Path(__file__).with_name("transcribe_with_faster_whisper.py")
            command, env = isolated_command(runtime, MANIFEST["transcription"]["packages"], worker,
                ["--out", str(runtime / "asr/prepare.json"), "--models", str(runtime / "asr/models"), "--model", args.model])
            subprocess.run(command, env=env, check=True)
        else:
            print(json.dumps({"ready": True, "uv": str(ensure_uv(runtime))}))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
