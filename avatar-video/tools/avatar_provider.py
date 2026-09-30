#!/usr/bin/env python3
"""Resolve installed local, authenticated hosted, or editable fallback presenters."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import signal

from avatar_probe import compatible, manifest, probe, progress
from avatar_runtime import runtime_dir, status


def hosted_ready() -> tuple[bool, str]:
    if binary := shutil.which("heygen"):
        command = [binary, "auth", "status"]
    elif platform.system() == "Windows" and (binary := shutil.which("wsl.exe")):
        command = [binary, "--exec", "heygen", "auth", "status"]
    else:
        return False, "HeyGen CLI is missing"
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, "HeyGen CLI is authenticated" if result.returncode == 0 else "HeyGen CLI is unavailable or unauthenticated"
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"HeyGen status failed: {type(error).__name__}"


def resolve(root: Path, provider: str | None = None, backend_id: str | None = None, mode: str = "photo") -> dict:
    choice = provider or os.environ.get("SKILL_BANK_AVATAR_PROVIDER", "auto")
    if choice not in ("local", "heygen", "auto"):
        raise ValueError("Avatar provider must be local, heygen or auto")
    if choice == "heygen":
        ready, reason = hosted_ready()
        return {"ready": ready, "provider": "heygen", "mode": mode, "reason": reason,
                **({} if ready else {"blocked": "presenter-generation", "retryCommand": "heygen auth login --oauth"})}
    config = manifest()
    capability = probe(config, allow_restricted=backend_id is not None)
    rows = compatible(config, capability["accelerator"]["kind"], capability["accelerator"]["memoryBytes"], allow_restricted=backend_id is not None) if capability["eligible"] else []
    rows = [row for row in rows if mode in row["modes"] and (backend_id is None or row["id"] == backend_id)]
    installed = [row for row in rows if status(root, row)["ready"]]
    if choice in ("auto", "local") and installed:
        result = {"ready": True, "provider": "local", "backend": installed[0]["id"], "mode": mode,
                  "reason": "Compatible local presenter backend is installed", "capability": capability}
    elif choice == "local":
        result = {"ready": False, "provider": "local", "backend": backend_id, "mode": mode,
                  "reason": f"local-{mode}-mode-unsupported" if mode != "photo" else "No compatible installed local presenter backend",
                  "blocked": "presenter-generation", "capability": capability,
                  "retryCommand": "python3 tools/avatar_ensure.py avatar-video" + (f" --backend {backend_id}" if backend_id else "")}
    else:
        ready, reason = hosted_ready()
        if ready:
            result = {"ready": True, "provider": "heygen", "mode": mode, "reason": reason, "capability": capability}
        elif choice == "heygen":
            result = {"ready": False, "provider": "heygen", "mode": mode, "reason": reason, "blocked": "presenter-generation", "retryCommand": "heygen auth login --oauth"}
        else:
            result = {"ready": True, "provider": "fallback", "mode": mode,
                      "reason": f"Local: {capability['reason']}; hosted: {reason}", "blocked": "presenter-generation", "capability": capability,
                      "retryCommand": "python3 tools/avatar_ensure.py avatar-video", "fallbackCapabilities": ["script", "verified local narration", "storyboard"]}
    progress("provider", "Presenter provider resolved", provider=result["provider"], reason=result["reason"])
    return result


def deliver_fallback(script: Path, audio: Path, output: Path) -> dict:
    """Package an actual local Kokoro/exported narration track, never fake one."""
    from run_video_job import media_paths
    from avatar_runtime import run, environment
    from assemble_video import probe as inspect_media
    if not script.is_file() or not audio.is_file():
        raise ValueError("Fallback delivery needs a script and an existing verified local narration track")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Fallback output must be empty")
    from ensure_video_runtime import default_runtime_dir
    ffmpeg, ffprobe = media_paths(default_runtime_dir())
    original = inspect_media(ffprobe, audio)
    if "audio" not in original["streams"] or original["duration"] <= 0:
        raise ValueError("Fallback narration is missing or empty")
    output.mkdir(parents=True, exist_ok=True)
    text = script.read_text(encoding="utf-8")
    (output / "script.md").write_text(text, encoding="utf-8")
    (output / "storyboard.md").write_text("# Presenter storyboard\n\nPortrait animation is blocked until a compatible local backend or authenticated hosted provider is available.\n\n" + text, encoding="utf-8")
    for name in ("narration.wav", "audio.mp3"):
        run([str(ffmpeg), "-v", "error", "-y", "-protocol_whitelist", "file,pipe", "-i", str(audio.resolve()), str(output / name)], output / (name + ".log"), environment(runtime_dir()), phase="fallback")
        info = inspect_media(ffprobe, output / name)
        if "audio" not in info["streams"] or info["duration"] <= 0:
            raise RuntimeError("Fallback audio failed verification")
    result = {"ready": True, "provider": "fallback", "blocked": "presenter-generation", "video": None,
              "artifacts": [str(output / name) for name in ("script.md", "narration.wav", "audio.mp3", "storyboard.md")],
              "retryCommand": "python3 tools/avatar_ensure.py avatar-video"}
    (output / "manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["auto", "local", "heygen"])
    parser.add_argument("--backend")
    parser.add_argument("--mode", choices=["photo", "avatar", "dub"], default="photo")
    parser.add_argument("--runtime-dir", type=Path, default=runtime_dir())
    parser.add_argument("--deliver-fallback", type=Path, metavar="OUT")
    parser.add_argument("--script", type=Path)
    parser.add_argument("--audio", type=Path)
    args = parser.parse_args()
    from avatar_runtime import interrupted
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        if args.deliver_fallback:
            if not args.script or not args.audio:
                raise ValueError("Fallback delivery requires --script and --audio from the local narration step")
            if (args.provider or os.environ.get("SKILL_BANK_AVATAR_PROVIDER")) in ("local", "heygen"):
                raise ValueError("Explicit provider requests cannot silently become fallback delivery")
            result = deliver_fallback(args.script, args.audio, args.deliver_fallback.resolve())
        else:
            result = resolve(args.runtime_dir.expanduser().resolve(), args.provider, args.backend, args.mode)
    except (Exception, KeyboardInterrupt) as error:
        result = {"ready": False, "error": str(error)}
    print(json.dumps(result))
    return 0 if result.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
