#!/usr/bin/env python3
"""Run a video request through rendering, final-media captions, and review.

Input JSON paths are relative to the request file. Progress is newline-delimited
JSON on stderr; one result document is printed on stdout. Failed render attempts
stay beside the requested output. Re-run with --resume to reuse a verified MP4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from assemble_video import probe
from ensure_video_runtime import MANIFEST, default_runtime_dir, media_version, resolve_media, resolve_node


TOOLS = Path(__file__).resolve().parent
RENDER_SCRIPTS = {
    "slidev": "render_slidev_video.py",
    "remotion": "render_remotion_video.py",
    "hyperframes": "render_hyperframes_video.py",
    "scenes": "assemble_video.py",
    "storyboard": "render_desktop_sources.py",
}
ACTIVE_CHILD: subprocess.Popen | None = None


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def source_path(base: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} needs a path")
    return (base / value).resolve()


def request_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schemaVersion") != 1:
        raise ValueError("Video job needs schemaVersion 1")
    renderer = config.get("renderer")
    route = config.get("route")
    if renderer not in RENDER_SCRIPTS or route not in MANIFEST["routes"]:
        raise ValueError("Video job has an unknown renderer or route")
    selected = config.get("authoringRenderer") if renderer == "storyboard" else renderer
    if renderer != "scenes" and selected not in MANIFEST["routes"][route]:
        raise ValueError(f"Renderer {selected} is unavailable for route {route}")
    if config.get("captions", "auto") not in ("auto", "plan", "transcribe"):
        raise ValueError("captions must be auto, plan or transcribe")
    base = path.parent
    config["timing"] = source_path(base, config.get("timing"), "timing")
    config["output"] = source_path(base, config.get("output"), "output")
    if not config["timing"].is_file():
        raise ValueError(f"Timing plan is missing: {config['timing']}")
    if renderer != "scenes":
        config["source"] = source_path(base, config.get("source"), "source")
        if not config["source"].is_file():
            raise ValueError(f"Renderer source is missing: {config['source']}")
    if renderer == "storyboard":
        authored = json.loads(config["source"].read_text(encoding="utf-8"))
        if not isinstance(authored, dict) or authored.get("renderer") != selected:
            raise ValueError("Authoring source renderer does not match the requested workflow")
    for key in ("projectRoot", "props", "variables", "runtimeDir"):
        if config.get(key):
            config[key] = source_path(base, config[key], key)
    if renderer == "remotion" and not isinstance(config.get("compositionId"), str):
        raise ValueError("Remotion job needs compositionId")
    return config


def state_path(output: Path) -> Path:
    return output.with_name(output.name + ".job-state.json")


def write_state(project_path: Path, **state: object) -> None:
    target = state_path(project_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and "avatar" not in state:
        try:
            original = json.loads(target.read_text(encoding="utf-8"))
            if original.get("avatar"):
                state["avatar"] = original["avatar"]
        except (OSError, ValueError):
            pass
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        while chunk := input_file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stop_child() -> None:
    child = ACTIVE_CHILD
    if not child or child.poll() is not None:
        return
    if platform.system() == "Windows":
        try:
            stopped = subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                                     capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            stopped = False
        if not stopped and child.poll() is None:
            child.terminate()
    else:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError:
            child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if platform.system() == "Windows":
            child.kill()
        else:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                child.kill()
        child.wait(timeout=5)


def interrupted(_number: int, _frame: object) -> None:
    stop_child()
    raise KeyboardInterrupt


def command_result(command: list[str], log: Path) -> dict:
    global ACTIVE_CHILD
    output_lines: list[str] = []
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
    ACTIVE_CHILD = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    bufsize=1, start_new_session=platform.system() != "Windows",
                                    creationflags=creationflags, stdin=subprocess.DEVNULL)
    child = ACTIVE_CHILD

    def read_stdout() -> None:
        assert child.stdout is not None
        output_lines.extend(child.stdout)

    def read_stderr() -> None:
        assert child.stderr is not None
        with log.open("w", encoding="utf-8") as destination:
            for line in child.stderr:
                destination.write(line)
                destination.flush()
                print(line, end="", file=sys.stderr, flush=True)

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    try:
        code = child.wait()
        stdout_thread.join()
        stderr_thread.join()
    finally:
        if child.stdout:
            child.stdout.close()
        if child.stderr:
            child.stderr.close()
        ACTIVE_CHILD = None
    output = "".join(output_lines)
    try:
        result = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"Tool returned invalid JSON; see {log}: {output[-500:]}") from None
    if code or not isinstance(result, dict) or not result.get("ready"):
        detail = result.get("error", output[-500:]) if isinstance(result, dict) else output[-500:]
        raise RuntimeError(f"Tool failed ({code}); see {log}: {detail}")
    return result


def media_paths(runtime_dir: Path) -> tuple[Path, Path]:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ffmpeg and ffprobe and media_version(ffmpeg) and media_version(ffprobe):
        return Path(ffmpeg), Path(ffprobe)
    selected = resolve_node(runtime_dir, ensure=True)
    if not selected:
        raise RuntimeError("Node is required to install managed FFmpeg")
    paths = resolve_media(runtime_dir, *selected, ensure=True)
    if not paths:
        raise RuntimeError("FFmpeg and FFprobe could not be prepared")
    return paths


def render_command(config: dict, work: Path, runtime_dir: Path) -> list[str]:
    renderer = config["renderer"]
    command = [sys.executable, str(TOOLS / RENDER_SCRIPTS[renderer])]
    if renderer == "scenes":
        ffmpeg, ffprobe = media_paths(runtime_dir)
        command.extend([str(config["timing"]), "--ffmpeg", str(ffmpeg), "--ffprobe", str(ffprobe)])
    elif renderer in ("slidev", "storyboard"):
        command.extend([str(config["source"]), str(config["timing"]), "--runtime-dir", str(runtime_dir)])
    elif renderer == "remotion":
        command.extend([str(config["source"]), config["compositionId"], str(config["timing"]),
                        "--runtime-dir", str(runtime_dir)])
        if config.get("projectRoot"):
            command.extend(["--project-root", str(config["projectRoot"])])
        if config.get("props"):
            command.extend(["--props", str(config["props"])])
    else:
        command.extend([str(config["source"]), str(config["timing"]), "--runtime-dir", str(runtime_dir)])
        if config.get("projectRoot"):
            command.extend(["--project-root", str(config["projectRoot"])])
        if config.get("variables"):
            command.extend(["--variables", str(config["variables"])])
    command.extend(["--out", str(work)])
    return command


def should_transcribe(config: dict) -> bool:
    if config.get("captions") == "transcribe":
        return True
    if config.get("captions") == "plan":
        return False
    plan = json.loads(config["timing"].read_text(encoding="utf-8"))
    return any(isinstance(scene, dict) and (scene.get("narration") or scene.get("audio_from_visual"))
               for scene in plan.get("scenes", []))


def verify_render(output: Path, ffprobe: Path) -> float:
    video = output / "video.mp4"
    manifest = output / "manifest.json"
    if not video.is_file() or not manifest.is_file():
        raise ValueError("Existing project is missing its video or manifest")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    measured = probe(ffprobe, video)
    if data.get("status") != "complete" or "video" not in measured["streams"] or measured["duration"] <= 0:
        raise ValueError("Existing project render did not verify")
    return measured["duration"]


def run_job(request: Path, resume: bool = False) -> dict:
    request = request.resolve()
    config = request_config(request)
    output = config["output"]
    runtime_dir = config.get("runtimeDir") or default_runtime_dir()
    request_hash = fingerprint(request)
    previous = json.loads(state_path(output).read_text(encoding="utf-8")) if state_path(output).is_file() else None
    if output.exists() and not resume:
        raise ValueError(f"Output already exists: {output}; use --resume for the same request")
    if output.exists() and (not isinstance(previous, dict) or previous.get("requestSha256") != request_hash):
        raise ValueError("Existing output belongs to a different or untracked request")
    if output.exists() and previous.get("status") in ("complete", "review_required") and previous.get("videoSha256"):
        _, ffprobe = media_paths(runtime_dir)
        duration = verify_render(output, ffprobe)
        if fingerprint(output / "video.mp4") != previous["videoSha256"]:
            raise ValueError("Completed video changed after caption timing; use a new output directory")
        if all((output / name).is_file() for name in ("captions.json", "captions.srt", "captions.vtt")):
            progress("complete", "Reusing verified complete project", durationSec=duration)
            return {"ready": True, "status": previous["status"], "directory": str(output),
                    "video": str(output / "video.mp4"), "durationSec": duration,
                    "reviewRequired": bool(previous.get("reviewRequired")),
                    "captions": [str(output / name) for name in ("captions.json", "captions.srt", "captions.vtt")]}
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    attempt: Path | None = None
    write_state(output, status="running", phase="validate", request=str(request), requestSha256=request_hash,
                output=str(output), startedAt=started)
    try:
        avatar_records = []
        if config.get("avatar") and not output.exists():
            from prepare_avatar_job import prepare
            avatar_records = prepare(request, config)
            write_state(output, status="running", phase="avatar", request=str(request), requestSha256=request_hash,
                        output=str(output), startedAt=started, avatar=avatar_records)
        progress("validate", "Video request validated", renderer=config["renderer"])
        if output.exists():
            _, ffprobe = media_paths(runtime_dir)
            duration = verify_render(output, ffprobe)
            progress("render", "Reusing verified video", durationSec=duration)
        else:
            work = output.with_name(output.name + f".work-{uuid.uuid4().hex[:8]}")
            attempt = work
            progress("render", "Starting renderer", renderer=config["renderer"])
            write_state(output, status="running", phase="render", request=str(request), requestSha256=request_hash,
                        output=str(output), attempt=str(work), startedAt=started)
            result = command_result(render_command(config, work, runtime_dir),
                                    output.with_name(output.name + ".render.log"))
            _, ffprobe = media_paths(runtime_dir)
            duration = verify_render(work, ffprobe)
            work.rename(output)
            progress("render", "Video rendered and verified", durationSec=duration)
        write_state(output, status="running", phase="subtitles", request=str(request), requestSha256=request_hash,
                    output=str(output), startedAt=started)
        review_required = False
        if should_transcribe(config):
            progress("subtitles", "Timing captions to final speech")
            command = [sys.executable, str(TOOLS / "transcribe_captions.py"), str(output / "video.mp4"),
                       "--out", str(output), "--runtime-dir", str(runtime_dir)]
            if config.get("language"):
                command.extend(["--language", str(config["language"])])
            if config.get("transcriptionModel"):
                command.extend(["--model", str(config["transcriptionModel"])])
            captions = command_result(command, output / "transcription-job.log")
            review_required = bool(captions.get("reviewRequired"))
        manifest = output / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        shutil.copy2(request, output / "request.json")
        if avatar_records:
            data["avatar"] = avatar_records
        data.update(jobRoute=config["route"], captionSource="local-asr" if review_required else "plan",
                    reviewRequired=review_required, request="request.json")
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        status = "review_required" if review_required else "complete"
        write_state(output, status=status, phase="complete", request=str(request), requestSha256=request_hash,
                    output=str(output), durationSec=duration, reviewRequired=review_required,
                    videoSha256=fingerprint(output / "video.mp4"), startedAt=started, completedAt=time.time())
        progress("complete", "Video project ready for review" if review_required else "Video project complete",
                 durationSec=duration, reviewRequired=review_required)
        return {"ready": True, "status": status, "directory": str(output), "video": str(output / "video.mp4"),
                "durationSec": duration, "reviewRequired": review_required,
                "captions": [str(output / name) for name in ("captions.json", "captions.srt", "captions.vtt")]}
    except BaseException as error:
        status = "cancelled" if isinstance(error, KeyboardInterrupt) else "failed"
        write_state(output, status=status, phase="error", request=str(request), requestSha256=request_hash,
                    output=str(output), attempt=str(attempt) if attempt else None,
                    error=str(error), startedAt=started, updatedAt=time.time())
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        result = run_job(args.request, args.resume)
    except KeyboardInterrupt:
        print(json.dumps({"ready": False, "status": "cancelled"}))
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "status": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
