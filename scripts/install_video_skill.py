#!/usr/bin/env python3
"""Copy a generated media skill and prepare its runtime immediately.

Usage: python3 scripts/install_video_skill.py explainer-video --target ~/.agents/skills
After a setup failure, repeat the same command with --resume.
The target is the directory that contains installed skill directories.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
ROUTES = {
    "slide-decks": ["slide-decks"],
    "explainer-video": ["explainer-video"],
    "motion-graphics-video": ["explainer-video"],
    "product-launch-video": ["product-launch-video"],
    "talking-head-video": ["talking-head-video"],
    "avatar-video": ["avatar-video"],
    "voice-narration": [],
    "course-creator": ["explainer-video"],
}
VOICE_SKILLS = {"explainer-video", "motion-graphics-video", "product-launch-video", "talking-head-video", "avatar-video", "voice-narration", "course-creator"}


def check_avatar_provider() -> None:
    """Report the hosted prerequisite without starting a billable video job."""
    binary = shutil.which("heygen")
    if binary:
        command = [binary, "auth", "status"]
    elif platform.system() == "Windows" and (wsl := shutil.which("wsl.exe")):
        command = [wsl, "--exec", "heygen", "auth", "status"]
    else:
        raise RuntimeError("HeyGen CLI is missing; install it from https://github.com/heygen-com/heygen-cli, then rerun with --resume")
    status = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if status.returncode:
        login = "wsl --exec heygen auth login" if command[1:3] == ["--exec", "heygen"] else "heygen auth login"
        raise RuntimeError(f"HeyGen CLI is unavailable or not authenticated; run '{login}' or set HEYGEN_API_KEY, then rerun with --resume")


def install(skill: str, target: Path, runtime_dir: Path | None = None, resume: bool = False) -> Path:
    if skill not in ROUTES:
        raise ValueError(f"Unknown skill: {skill}")
    source = REPO / skill
    if not (source / "SKILL.md").is_file():
        raise RuntimeError(f"Generated skill is missing: {source}")
    destination = target.expanduser().resolve() / skill
    if resume:
        if destination.is_symlink() or not (destination / "SKILL.md").is_file():
            raise RuntimeError(f"No installed skill to resume at: {destination}")
    elif destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not (destination / "SKILL.md").is_file():
            raise RuntimeError(f"Destination already exists without a reusable skill: {destination}; no files were overwritten")
        print(f"Reusing installed skill at {destination}", flush=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".venv", "models", "node_modules", "__pycache__", "*.pyc"))
    command = [sys.executable, str(destination / "tools/bootstrap.py"),
               "--yes", "--target", str(destination.parent)]
    if runtime_dir:
        command.extend(["--runtime-dir", str(runtime_dir)])
    print(f"Preparing {skill} dependencies in parallel...", flush=True)
    subprocess.run(command, check=True)
    if skill == "avatar-video":
        # Presenter backends are optional. Capability detection never installs
        # models; local narration above makes the editable fallback usable.
        subprocess.run([sys.executable, str(destination / "tools/avatar_ensure.py"), "avatar-video", "--check"], check=True)
        # The dispatcher chooses a verified local installation before checking
        # hosted authentication. Installation never implies model consent.
        subprocess.run([sys.executable, str(destination / "tools/avatar_provider.py")], check=True)
    print(f"Installed {skill} at {destination}", flush=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=ROUTES)
    parser.add_argument("--target", type=Path, required=True, help="Directory containing installed skill folders")
    parser.add_argument("--runtime-dir", type=Path, help="Private video runtime directory")
    parser.add_argument("--resume", action="store_true", help="Retry prerequisite setup in an existing skill directory")
    args = parser.parse_args()
    try:
        install(args.skill, args.target, args.runtime_dir, args.resume)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        if not args.resume:
            print("If the skill files were copied, rerun with --resume after resolving the error.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
