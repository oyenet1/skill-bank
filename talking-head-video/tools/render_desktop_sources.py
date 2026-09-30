#!/usr/bin/env python3
"""Render generated desktop scene projects and assemble their original audio."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

from assemble_video import assemble, probe, progress, run
from ensure_video_runtime import default_runtime_dir, environment, setup, tool_command
from run_video_job import interrupted
from desktop_fonts import package_fonts


def render(contract: Path, timing: Path, output: Path, runtime: Path) -> dict:
    contract, timing, output, runtime = (path.resolve() for path in (contract, timing, output, runtime))
    spec = json.loads(contract.read_text(encoding="utf-8"))
    plan = json.loads(timing.read_text(encoding="utf-8"))
    engine = spec["renderer"]
    if engine not in ("hyperframes", "remotion", "slidev") or len(spec["scenes"]) != len(plan["scenes"]):
        raise ValueError("Authoring source does not match the storyboard")
    tools = setup("explainer-video", runtime, ensure=True, only=engine)
    if not tools["ready"]:
        raise RuntimeError(f"Renderer setup is incomplete: {tools['missing']}")
    paths = tools["paths"]
    node, ffmpeg, ffprobe = (Path(paths[key]) for key in ("node", "ffmpeg", "ffprobe"))
    os.environ.update(environment(node))
    profile = runtime / engine
    for scene in spec["scenes"]:
        progress("fonts", "Preparing local project fonts")
        package_fonts(contract.parent / scene["folder"], runtime, engine)
    if engine == "hyperframes":
        gsap = profile / "node_modules/gsap/dist/gsap.min.js"
        if not gsap.is_file():
            raise RuntimeError("The managed HyperFrames profile is missing GSAP")
        for scene in spec["scenes"]:
            vendor = contract.parent / scene["folder"] / "vendor"
            vendor.mkdir(exist_ok=True)
            shutil.copy2(gsap, vendor / "gsap.min.js")
    prepared = {**plan, "scenes": []}
    # Nest temporary source under the runtime profile for normal Node module
    # resolution without Windows junctions, symlink privileges, or per-scene npm installs.
    with tempfile.TemporaryDirectory(prefix="desktop-source-", dir=profile) as scratch:
        stage = Path(scratch)
        logs = output.with_name(output.name + ".source-logs")
        logs.mkdir(parents=True, exist_ok=True)
        for index, (scene, authored) in enumerate(zip(plan["scenes"], spec["scenes"]), 1):
            if scene["id"] != authored["id"]:
                raise ValueError("Authoring scene identity does not match the storyboard")
            original = contract.parent / authored["folder"]
            root = stage / authored["folder"]
            shutil.copytree(original, root)
            entry = root / authored["entry"]
            visual = stage / f"scene-{index:04}.mp4"
            log = logs / f"scene-{index:04}-{engine}.log"
            progress("source", f"Rendering editable {engine} source {index} of {len(plan['scenes'])}", scene=index, sceneCount=len(plan["scenes"]))
            if engine == "hyperframes":
                args = [paths[engine], "render", "-c", entry.name, "--output", str(visual), "--quality", "looks", "--fps", str(plan["fps"])]
            elif engine == "remotion":
                args = [paths[engine], "render", str(entry), "DesktopScene", str(visual),
                        "--public-dir", str(root / "public")]
            else:
                frames = stage / f"frames-{index:04}"
                args = [paths[engine], "export", str(entry), "--format", "png", "--output", str(frames), "--timeout", "60000"]
            previous = Path.cwd()
            try:
                os.chdir(root)
                run(tool_command(args, node), log)
            finally:
                os.chdir(previous)
            if engine == "slidev":
                images = sorted(frames.glob("*.png"))
                if len(images) != 1:
                    raise RuntimeError(f"Expected one exported Slidev scene, got {len(images)}; see {log}")
                visual = images[0]
            elif not visual.is_file() or "video" not in probe(ffprobe, visual)["streams"]:
                raise RuntimeError(f"Renderer did not produce a playable scene; see {log}")
            if engine != "slidev" and probe(ffprobe, visual)["duration"] + 1 / plan["fps"] < authored["duration_sec"]:
                raise RuntimeError(f"Rendered scene {index} is shorter than its narration timeline")
            item = {**scene, "visual": str(visual), "duration_sec": authored["duration_sec"]}
            if scene.get("narration"):
                item["narration"] = str((timing.parent / scene["narration"]).resolve())
            elif scene.get("audio_from_visual"):
                # The rendered visual is muted; retain the original footage's
                # speech once, with the original requested trim duration.
                narration = stage / f"source-audio-{index:04}.wav"
                run([str(ffmpeg), "-v", "error", "-y", "-i", str((timing.parent / scene["visual"]).resolve()),
                     "-t", str(scene["duration_sec"]), "-vn", "-ar", "48000", str(narration)], log)
                item.pop("audio_from_visual", None)
                item["narration"] = str(narration)
            prepared["scenes"].append(item)
            progress("source", f"Rendered editable source {index} of {len(plan['scenes'])}",
                     completedScenes=index, sceneCount=len(plan["scenes"]))
        if isinstance(plan.get("music"), dict):
            prepared["music"] = {**plan["music"], "file": str((timing.parent / plan["music"]["file"]).resolve())}
        prepared_file = stage / "prepared-timing.json"
        prepared_file.write_text(json.dumps(prepared, ensure_ascii=False), encoding="utf-8")
        result = assemble(prepared_file, output, ffmpeg, ffprobe)
        shutil.copytree(contract.parent, output / "source" / "authoring")
        for log in logs.iterdir():
            shutil.copy2(log, output / "logs" / log.name)
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(renderer=engine, authoringSource="source/authoring/authoring.json")
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("timing", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        result = render(args.contract, args.timing, args.out, args.runtime_dir)
    except KeyboardInterrupt:
        result = {"ready": False, "status": "cancelled"}
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as error:
        result = {"ready": False, "error": str(error)}
    print(json.dumps(result))
    return 0 if result.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
