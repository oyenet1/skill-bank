#!/usr/bin/env python3
"""Render a HyperFrames HTML composition into a portable video project.

The timing JSON follows assemble_video.py's plan format with exactly one scene.
The rendered composition supplies the visual. Declare audio_from_visual with
transcript text to retain embedded audio, or narration to replace it.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from assemble_video import assemble, probe, progress
from ensure_video_runtime import default_runtime_dir, setup


IGNORED_DIRS = {".git", "node_modules", "dist", "build", ".cache", "renders"}


def copy_source(root: Path, target: Path, output: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        parent = Path(directory)
        skipped = {name for name in names if name in IGNORED_DIRS and (parent / name).is_dir()}
        skipped.update(name for name in names if (parent / name).resolve() == output)
        return skipped

    shutil.copytree(root, target, ignore=ignore, symlinks=True)


def render(composition: Path, timing: Path, out_dir: Path, runtime_dir: Path,
           source_root: Path | None = None, variables: Path | None = None) -> dict:
    composition = composition.resolve()
    timing = timing.resolve()
    out_dir = out_dir.resolve()
    if not composition.is_file() or composition.suffix.lower() != ".html":
        raise ValueError(f"HyperFrames composition is missing: {composition}")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {out_dir}")
    root = (source_root or composition.parent).resolve()
    if not root.is_dir() or not composition.is_relative_to(root):
        raise ValueError("Composition must be inside the source project directory")
    plan = json.loads(timing.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list) or len(plan["scenes"]) != 1:
        raise ValueError("HyperFrames timing plan needs exactly one scene")
    scene = plan["scenes"][0]
    if not isinstance(scene, dict):
        raise ValueError("HyperFrames scene must be an object")
    if scene.get("narration") and scene.get("audio_from_visual"):
        raise ValueError("Choose narration or audio_from_visual for the HyperFrames render")
    variables = variables.resolve() if variables else None
    if variables and not variables.is_file():
        raise ValueError(f"HyperFrames variables file is missing: {variables}")
    progress("setup", "Preparing HyperFrames and FFmpeg")
    runtime = setup("product-launch-video", runtime_dir, ensure=True, only="hyperframes")
    if not runtime["ready"]:
        raise RuntimeError(f"Video runtime is incomplete: {runtime['missing']}")
    paths = runtime["paths"]
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    render_log = out_dir.with_name(out_dir.name + ".hyperframes-render.log")
    with tempfile.TemporaryDirectory(prefix="hyperframes-video-", dir=out_dir.parent) as scratch:
        scratch_dir = Path(scratch)
        clip = scratch_dir / "composition.mp4"
        env = os.environ.copy()
        env["PATH"] = str(Path(paths["node"]).parent) + os.pathsep + env.get("PATH", "")
        command = [paths["hyperframes"], "render", "-c", str(composition.relative_to(root)), "--output", str(clip),
                   "--quality", "looks"]
        if variables:
            command.extend(["--variables-file", str(variables)])
        progress("visuals", f"Rendering HyperFrames composition {composition.name}")
        with render_log.open("w", encoding="utf-8") as log:
            child = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        if child.returncode or not clip.is_file():
            detail = render_log.read_text(encoding="utf-8", errors="replace")[-2500:]
            raise RuntimeError(f"HyperFrames render failed ({child.returncode}); see {render_log}: {detail}")
        clip_info = probe(Path(paths["ffprobe"]), clip)
        if "video" not in clip_info["streams"] or clip_info["duration"] <= 0:
            raise RuntimeError("HyperFrames output has no playable video stream")
        if "audio" in clip_info["streams"] and not (scene.get("audio_from_visual") or scene.get("narration")):
            raise ValueError("HyperFrames output contains audio; choose audio_from_visual with transcript, or provide narration")
        prepared_scene = {**scene, "visual": str(clip)}
        if prepared_scene.get("narration"):
            prepared_scene["narration"] = str((timing.parent / prepared_scene["narration"]).resolve())
        prepared = {**plan, "scenes": [prepared_scene]}
        if isinstance(plan.get("music"), dict) and plan["music"].get("file"):
            prepared["music"] = {**plan["music"], "file": str((timing.parent / plan["music"]["file"]).resolve())}
        prepared_file = scratch_dir / "prepared-plan.json"
        prepared_file.write_text(json.dumps(prepared, ensure_ascii=False), encoding="utf-8")
        result = assemble(prepared_file, out_dir, Path(paths["ffmpeg"]), Path(paths["ffprobe"]))
        source = out_dir / "source"
        copy_source(root, source, out_dir)
        if variables and not variables.is_relative_to(root):
            shutil.copy2(variables, source / "render-variables.json")
        shutil.copy2(render_log, out_dir / "logs" / "hyperframes-render.log")
        manifest = out_dir / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data.update(renderer="hyperframes", sourceComposition=str((source / composition.relative_to(root)).relative_to(out_dir)))
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("composition", type=Path)
    parser.add_argument("timing", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--variables", type=Path)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    args = parser.parse_args()
    try:
        result = render(args.composition, args.timing, args.out, args.runtime_dir,
                        args.project_root, args.variables)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
