#!/usr/bin/env python3
"""Measure skill discovery, first-use setup and cached verification in isolated data.

System Node/npm, Python, UV and FFmpeg may be reused; downloaded environments,
packages, browsers, speech models and installed skills stay in the sandbox.
No video generation or hosted provider request is performed by this script.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="oyenet1/skill-bank")
    parser.add_argument("--skill", default="motion-graphics-video")
    parser.add_argument("--sandbox-dir", type=Path)
    parser.add_argument("--files-only", action="store_true")
    args = parser.parse_args()
    root = args.sandbox_dir or Path(tempfile.mkdtemp(prefix="skill-bank-smoke-"))
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        parser.error("Use an empty sandbox directory to measure a fresh installation")
    paths = {name: root / name for name in ("home", "config", "data", "cache", "npm", "workspace")}
    for path in paths.values():
        path.mkdir()
    env = dict(os.environ)
    env.update(HOME=str(paths["home"]), XDG_CONFIG_HOME=str(paths["config"]),
               XDG_DATA_HOME=str(paths["data"]), XDG_CACHE_HOME=str(paths["cache"]),
               npm_config_cache=str(paths["npm"]), UV_CACHE_DIR=str(root / "uv-cache"),
               UV_PYTHON_INSTALL_DIR=str(root / "python"), HF_HOME=str(root / "huggingface"),
               HF_HUB_CACHE=str(root / "huggingface/hub"),
               PLAYWRIGHT_BROWSERS_PATH=str(root / "browsers"),
               SKILL_BANK_KOKORO_HOME=str(root / "kokoro"), DISABLE_TELEMETRY="1", CI="1")
    # Do not inherit agent-specific destinations outside the isolated HOME.
    env.pop("CODEX_HOME", None)
    (root / "environment.json").write_text(json.dumps(
        {key: value for key, value in env.items() if key not in os.environ or value != os.environ[key]}, indent=2))
    report = {"sandbox": str(root), "source": args.source, "skill": args.skill,
              "systemToolsMayBeReused": True, "stages": []}

    def stage(name: str, command: list[str]) -> bool:
        print(f"{name}: started ({root})", flush=True)
        started = time.monotonic()
        with (root / f"{name}.log").open("w") as log:
            result = subprocess.run(command, cwd=paths["workspace"], env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
        entry = {"name": name, "seconds": round(time.monotonic() - started, 3),
                 "exitCode": result.returncode}
        report["stages"].append(entry)
        report["ready"] = result.returncode == 0
        (root / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(entry), flush=True)
        return result.returncode == 0

    if not stage("skill-files", ["npx", "--yes", "skills", "add", args.source,
                                 "--skill", args.skill, "-g", "-a", "codex", "--yes"]):
        return 1
    skill = paths["home"] / ".agents/skills" / args.skill
    if not (skill / "tools/bootstrap.py").is_file():
        raise RuntimeError("Skill CLI exited successfully without installing the required bootstrap")
    if args.files_only:
        return 0
    command = [os.sys.executable, str(skill / "tools/bootstrap.py"), "--yes",
               "--runtime-dir", str(root / "video-runtime"), "--target", str(skill.parent)]
    if not stage("first-use-setup", command):
        return 1
    if not stage("cached-setup", command):
        return 1
    if not stage("read-only-check", [arg for arg in command if arg != "--yes"] + ["--check"]):
        return 1
    report["installedSkills"] = sorted(path.parent.name for path in skill.parent.glob("*/SKILL.md"))
    report["installationSeconds"] = round(sum(entry["seconds"] for entry in report["stages"][:2]), 3)
    (root / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
