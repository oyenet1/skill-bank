#!/usr/bin/env python3
"""First-use bootstrap for a video skill on Windows, macOS or Linux.

Detects the operating system and CPU architecture, prepares the private video
runtime (Node, FFmpeg/FFprobe, Slidev/Remotion/HyperFrames, Chromium, Kokoro
and speech models) and offers to install the associated sibling skills that are
not present yet.

Usage:
    python3 tools/bootstrap.py                 # plan, confirm, then install
    python3 tools/bootstrap.py --check         # report only, install nothing
    python3 tools/bootstrap.py --yes           # non-interactive; install all
    python3 tools/bootstrap.py --no-skills     # runtimes only
    python3 tools/bootstrap.py --target ~/.agents/skills
The final stdout line is JSON. Progress and install logs go to stderr.
This tool never modifies PATH, shell profiles, or global packages.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEPENDENCIES = HERE / "dependencies.json"

# Node ships installed runtimes only for these systems and architectures.
ARCHITECTURES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}
SUPPORTED_SYSTEMS = ("Linux", "Darwin", "Windows")


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def host() -> dict[str, str]:
    system = platform.system()
    machine = platform.machine().lower()
    arch = ARCHITECTURES.get(machine)
    return {
        "system": system,
        "machine": machine,
        "arch": arch or "unsupported",
        "supported": bool(arch) and system in SUPPORTED_SYSTEMS,
    }


def load_dependencies() -> dict[str, object]:
    if not DEPENDENCIES.is_file():
        raise RuntimeError(f"Missing dependency manifest: {DEPENDENCIES}")
    return json.loads(DEPENDENCIES.read_text(encoding="utf-8"))


def default_skills_dir() -> Path:
    """The directory that holds installed skill folders, inferred from this skill."""
    return SKILL_ROOT.parent


def sibling_installed(skills_dir: Path, name: str) -> bool:
    return (skills_dir / name / "SKILL.md").is_file()


def windows_argv(command: list[str]) -> list[str]:
    """Run a .cmd/.bat launcher, which CreateProcess cannot start directly."""
    first = Path(command[0])
    if platform.system() == "Windows" and first.suffix.lower() in (".cmd", ".bat"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", *command]
    return command


def runtime_steps(spec: dict[str, object], runtime_dir: Path | None) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    routes = list(spec.get("routes") or [])
    for route in routes:
        command = [sys.executable, str(HERE / "ensure_video_runtime.py"), str(route)]
        if runtime_dir:
            command += ["--runtime-dir", str(runtime_dir)]
        steps.append({"kind": "runtime", "name": str(route), "command": command})
    if routes and spec.get("transcription"):
        command = [sys.executable, str(HERE / "ensure_python_runtime.py"), "--prepare-transcription"]
        if runtime_dir:
            command += ["--runtime-dir", str(runtime_dir)]
        steps.append({"kind": "transcription", "name": "speech-recognition", "command": command})
    if spec.get("voice"):
        steps.append({"kind": "voice", "name": "kokoro", "command": [sys.executable, str(HERE / "kokoro/start.py")]})
    return steps


def skill_steps(spec: dict[str, object], skills_dir: Path, install: bool) -> list[dict[str, object]]:
    associated = [name for name in (spec.get("associated") or []) if not sibling_installed(skills_dir, name)]
    if not associated:
        return []
    repo = str(spec.get("repo") or "")
    npx = shutil.which("npx")
    steps: list[dict[str, object]] = []
    for name in associated:
        command = [npx or "npx", "skills", "add", f"{repo}@{name}", "-g"]
        steps.append({"kind": "skill", "name": name, "command": command, "available": bool(npx) and bool(repo), "install": install})
    return steps


def build_plan(spec: dict[str, object], skills_dir: Path, runtime_dir: Path | None, with_skills: bool) -> dict[str, object]:
    steps = runtime_steps(spec, runtime_dir)
    if with_skills:
        steps += skill_steps(spec, skills_dir, install=True)
    return {"steps": steps}


def summarize(steps: list[dict[str, object]]) -> str:
    lines = []
    for step in steps:
        kind, name = step["kind"], step["name"]
        if kind == "skill" and not step.get("available"):
            lines.append(f"  sibling skill {name}: install with `npx skills add` (npx not found)")
        else:
            lines.append(f"  {kind}: {name}")
    return "\n".join(lines)


def confirm(steps: list[dict[str, object]]) -> bool:
    print("This will prepare the following, inside a private user data directory:", file=sys.stderr)
    print(summarize(steps), file=sys.stderr)
    if not sys.stdin.isatty():
        return True
    answer = input("Proceed? [Y/n] ").strip().lower()
    return answer in ("", "y", "yes")


def run_step(step: dict[str, object]) -> dict[str, object]:
    kind, name = step["kind"], step["name"]
    command = list(step["command"])  # type: ignore[arg-type]
    if kind == "skill" and not step.get("available"):
        # No npx or registry: report the exact command the requester can run.
        return {"kind": kind, "name": name, "ok": False, "prompt": " ".join(command),
                "reason": "npx is not available; run the command manually"}
    progress(kind, f"Preparing {name}")
    try:
        result = subprocess.run(windows_argv(command), capture_output=True, text=True)
    except OSError as error:
        return {"kind": kind, "name": name, "ok": False, "error": str(error)}
    if result.returncode:
        return {"kind": kind, "name": name, "ok": False, "error": (result.stderr or result.stdout)[-2000:]}
    payload: object = None
    for line in reversed((result.stdout or "").strip().splitlines()):
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    return {"kind": kind, "name": name, "ok": True, "result": payload}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report the plan and install nothing")
    parser.add_argument("--yes", action="store_true", help="Non-interactive; install everything")
    parser.add_argument("--no-skills", action="store_true", help="Prepare runtimes only")
    parser.add_argument("--target", type=Path, help="Directory holding installed skill folders")
    parser.add_argument("--runtime-dir", type=Path, help="Private video runtime directory")
    args = parser.parse_args()

    machine = host()
    skills_dir = (args.target.expanduser().resolve() if args.target else default_skills_dir())
    try:
        spec = load_dependencies()
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ready": False, "os": machine, "error": str(error)}, indent=2))
        return 1

    runtime_dir = args.runtime_dir.expanduser().resolve() if args.runtime_dir else None
    plan = build_plan(spec, skills_dir, runtime_dir, with_skills=not args.no_skills)
    steps = plan["steps"]

    base = {"skill": spec.get("skill"), "os": machine, "skillsDir": str(skills_dir),
            "steps": [{"kind": s["kind"], "name": s["name"]} for s in steps]}
    if args.check:
        base["ready"] = machine["supported"]
        print(json.dumps(base, indent=2))
        return 0 if machine["supported"] else 1
    if not machine["supported"]:
        print(json.dumps({**base, "ready": False,
                          "error": f"No managed runtime for {machine['system']}/{machine['machine']}"}, indent=2))
        return 1
    if not args.yes and not confirm(steps):
        print(json.dumps({**base, "ready": False, "cancelled": True}, indent=2))
        return 1

    results = [run_step(step) for step in steps]
    failed = [r for r in results if not r["ok"]]
    prompts = [r["prompt"] for r in failed if r.get("prompt")]
    ready = not any(r["kind"] in ("runtime", "transcription", "voice") for r in failed)
    print(json.dumps({**base, "ready": ready, "results": results, "prompts": prompts}, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
