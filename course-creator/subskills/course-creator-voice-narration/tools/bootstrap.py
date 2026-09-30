#!/usr/bin/env python3
"""First-use bootstrap for a video skill on Windows, macOS or Linux.

Detects the operating system and CPU architecture, prepares the private video
runtime (Node, FFmpeg/FFprobe, Slidev/Remotion/HyperFrames, Chromium, Kokoro
and speech models) and installs missing associated sibling skills from its
bundled source snapshot. No npx or Git is needed to install these siblings.

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
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import queue
import signal
import threading
import time
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from install_sibling_skill import dependency_order
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


def runtime_steps(spec: dict[str, object], runtime_dir: Path | None, *, check: bool = False) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    routes = list(spec.get("routes") or [])
    for route in routes:
        command = [sys.executable, str(HERE / "ensure_video_runtime.py"), str(route)]
        if runtime_dir:
            command += ["--runtime-dir", str(runtime_dir)]
        if check:
            command.append("--check")
        steps.append({"kind": "runtime", "name": str(route), "command": command})
    if routes and spec.get("transcription"):
        command = [sys.executable, str(HERE / "ensure_python_runtime.py"), "--prepare-transcription"]
        if runtime_dir:
            command += ["--runtime-dir", str(runtime_dir)]
        if check:
            command.append("--check")
        steps.append({"kind": "transcription", "name": "speech-recognition", "command": command})
    if spec.get("voice"):
        command = [sys.executable, str(HERE / "kokoro/start.py")]
        if check:
            command.append("--check")
        steps.append({"kind": "voice", "name": "kokoro", "command": command})
    return steps


def skill_steps(spec: dict[str, object], skills_dir: Path, install: bool) -> list[dict[str, object]]:
    associated = list(spec.get("associated") or [])
    if not associated:
        return []
    installer = HERE / "install_sibling_skill.py"
    available = installer.is_file() and (HERE / "sibling_skills.json").is_file()
    if available:
        associated = dependency_order(associated, HERE / "sibling_skills.json")
    associated = [name for name in associated if not sibling_installed(skills_dir, name)]
    steps: list[dict[str, object]] = []
    for name in associated:
        command = [sys.executable, str(installer), name, "--target", str(skills_dir)]
        steps.append({"kind": "skill", "name": name, "command": command,
                      "available": available, "install": install})
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
            lines.append(f"  sibling skill {name}: bundled snapshot is missing")
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


def run_step(step: dict[str, object], cancel: threading.Event | None = None) -> dict[str, object]:
    kind, name = step["kind"], step["name"]
    command = list(step["command"])  # type: ignore[arg-type]
    if kind == "skill" and not step.get("available"):
        # An incomplete skill copy must not silently claim dependency readiness.
        return {"kind": kind, "name": name, "ok": False, "prompt": " ".join(command),
                "reason": "The installed skill is missing its bundled sibling snapshot; reinstall the complete skill"}
    progress(kind, f"Preparing {name}")
    if cancel is not None and cancel.is_set():
        return {"kind": kind, "name": name, "ok": False, "cancelled": True}
    try:
        process = subprocess.Popen(windows_argv(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf-8", errors="replace",
                                   env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"), start_new_session=os.name != "nt",
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    except OSError as error:
        return {"kind": kind, "name": name, "ok": False, "error": str(error)}
    events = queue.Queue(maxsize=1000)
    def read(stream, source):
        try:
            for line in stream:
                events.put((source, line))
        finally:
            events.put((source, None))
    readers = [threading.Thread(target=read, args=(stream, source), daemon=True)
               for stream, source in ((process.stdout, "stdout"), (process.stderr, "stderr"))]
    for reader in readers:
        reader.start()
    stdout = ""; stderr = ""; remaining = 2; reported = time.monotonic()
    try:
        while remaining or process.poll() is None:
            if cancel is not None and cancel.is_set():
                raise InterruptedError("Setup cancelled")
            try:
                source, line = events.get(timeout=0.5)
                if line is None:
                    remaining -= 1
                elif source == "stderr":
                    stderr = (stderr + line)[-6000:]
                    sys.stderr.write(line); sys.stderr.flush()
                else:
                    stdout = (stdout + line)[-200000:]
            except queue.Empty:
                pass
            if time.monotonic() - reported >= 15:
                progress(kind, f"Still preparing {name}")
                reported = time.monotonic()
        process.wait()
    except BaseException:
        if os.name == "nt":
            subprocess.run(["taskkill.exe", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.kill(); process.wait()
        raise
    finally:
        for reader in readers:
            reader.join(timeout=1)
        process.stdout.close(); process.stderr.close()
    payload = None
    for value in [stdout.strip(), *reversed(stdout.strip().splitlines())]:
        try:
            candidate = json.loads(value)
            if isinstance(candidate, dict):
                payload = candidate
                break
        except ValueError:
            pass
    ok = process.returncode == 0 and isinstance(payload, dict) and payload.get("ready") is True
    if not ok:
        return {"kind": kind, "name": name, "ok": False, "result": payload,
                "error": (stderr or stdout)[-2000:]}
    return {"kind": kind, "name": name, "ok": True, "result": payload}


def run_steps(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    """Overlap independent runtimes, keeping shared renderer routes and sibling copies serial.

    Narration and transcription own separate environments/model directories.
    Renderer routes share Node/media/profile directories, and sibling installers
    traverse overlapping cyclic graphs, so each of those branches stays serial.
    """
    indexed = list(enumerate(steps))
    branches = [
        [(index, step) for index, step in indexed if step["kind"] == kind]
        for kind in ("runtime", "transcription", "voice", "skill")
    ]
    cancel = threading.Event()
    results: dict[int, dict[str, object]] = {}

    def branch(items):
        completed = []
        for index, step in items:
            if cancel.is_set():
                break
            completed.append((index, run_step(step, cancel)))
        return completed

    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(branch, items) for items in branches if items]
        try:
            for future in pending:
                results.update(future.result())
        except BaseException:
            # Worker threads cannot receive SIGTERM/KeyboardInterrupt directly.
            # Wake them so run_step terminates every active child process tree.
            cancel.set()
            raise
    return [results[index] for index, _ in indexed]


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
    try:
        plan = build_plan(spec, skills_dir, runtime_dir, with_skills=not args.no_skills)
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    steps = plan["steps"]

    base = {"skill": spec.get("skill"), "os": machine, "skillsDir": str(skills_dir),
            "pythonExecutable": sys.executable,
            "steps": [{"kind": s["kind"], "name": s["name"]} for s in steps]}
    if args.check:
        # Run only read-only checks; never report OS support as tool readiness.
        checked = runtime_steps(spec, runtime_dir, check=True)
        results = [run_step(step) for step in checked] if machine["supported"] else []
        missing_siblings = [step["name"] for step in steps if step["kind"] == "skill"]
        ready = machine["supported"] and not missing_siblings and all(result["ok"] for result in results)
        print(json.dumps({**base, "ready": ready, "supported": machine["supported"],
                          "results": results, "missingSkills": missing_siblings}, indent=2))
        return 0 if ready else 1
    if not machine["supported"]:
        print(json.dumps({**base, "ready": False,
                          "error": f"No managed runtime for {machine['system']}/{machine['machine']}"}, indent=2))
        return 1
    if not args.yes and not confirm(steps):
        print(json.dumps({**base, "ready": False, "cancelled": True}, indent=2))
        return 1

    results = run_steps(steps)
    failed = [r for r in results if not r["ok"]]
    prompts = [r["prompt"] for r in failed if r.get("prompt")]
    ready = not failed
    print(json.dumps({**base, "ready": ready, "results": results, "prompts": prompts}, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(json.dumps({"ready": False, "cancelled": True}))
        raise SystemExit(130)
