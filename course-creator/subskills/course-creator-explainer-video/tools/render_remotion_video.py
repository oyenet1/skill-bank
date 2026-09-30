#!/usr/bin/env python3
"""Render one Remotion composition and package its video, audio, and captions.

The timing JSON follows assemble_video.py's plan format with exactly one scene.
The rendered composition supplies that scene's visual. Use audio_from_visual:
true with a transcript to retain the composition's audio, or narration to
replace it. Progress is JSON on stderr; the project result is JSON on stdout.
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


IGNORED_DIRS = {".git", "node_modules", "dist", "build", ".cache", ".next", ".remotion"}


def project_root(entry: Path) -> Path:
    return next((folder for folder in (entry.parent, *entry.parent.parents) if (folder / "package.json").is_file()), entry.parent)


def copy_project(root: Path, target: Path, output: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        parent = Path(directory)
        skipped = {name for name in names if name in IGNORED_DIRS and (parent / name).is_dir()}
        skipped.update(name for name in names if (parent / name).resolve() == output)
        return skipped

    shutil.copytree(root, target, ignore=ignore, symlinks=True)


def render(entry: Path, composition: str, timing: Path, out_dir: Path, runtime_dir: Path,
           source_root: Path | None = None, props: Path | None = None) -> dict:
    entry = entry.resolve()
    timing = timing.resolve()
    out_dir = out_dir.resolve()
    if not entry.is_file():
        raise ValueError(f"Remotion entry file is missing: {entry}")
    if not composition.strip():
        raise ValueError("Remotion composition ID is required")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {out_dir}")
    root = (source_root or project_root(entry)).resolve()
    if not root.is_dir() or not entry.is_relative_to(root):
        raise ValueError("Entry file must be inside the source project directory")
    plan = json.loads(timing.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list) or len(plan["scenes"]) != 1:
        raise ValueError("Remotion timing plan needs exactly one scene")
    scene = plan["scenes"][0]
    if not isinstance(scene, dict):
        raise ValueError("Remotion scene must be an object")
    if scene.get("narration") and scene.get("audio_from_visual"):
        raise ValueError("Choose narration or audio_from_visual for the Remotion render")
    props = props.resolve() if props else None
    if props and not props.is_file():
        raise ValueError(f"Remotion props file is missing: {props}")
    progress("setup", "Preparing Remotion and FFmpeg")
    runtime = setup("product-launch-video", runtime_dir, ensure=True, only="remotion")
    if not runtime["ready"]:
        raise RuntimeError(f"Video runtime is incomplete: {runtime['missing']}")
    paths = runtime["paths"]
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    render_log = out_dir.with_name(out_dir.name + ".remotion-render.log")
    with tempfile.TemporaryDirectory(prefix="remotion-video-", dir=out_dir.parent) as scratch:
        scratch_dir = Path(scratch)
        clip = scratch_dir / "composition.mp4"
        env = os.environ.copy()
        env["PATH"] = str(Path(paths["node"]).parent) + os.pathsep + env.get("PATH", "")
        command = [paths["remotion"], "render", str(entry), composition, str(clip)]
        if props:
            command.append(f"--props={props}")
        progress("visuals", f"Rendering Remotion composition {composition}")
        with render_log.open("w", encoding="utf-8") as log:
            child = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        if child.returncode or not clip.is_file():
            detail = render_log.read_text(encoding="utf-8", errors="replace")[-2500:]
            raise RuntimeError(f"Remotion render failed ({child.returncode}); see {render_log}: {detail}")
        clip_info = probe(Path(paths["ffprobe"]), clip)
        if "video" not in clip_info["streams"] or clip_info["duration"] <= 0:
            raise RuntimeError("Remotion output has no playable video stream")
        if "audio" in clip_info["streams"] and not (scene.get("audio_from_visual") or scene.get("narration")):
            raise ValueError("Remotion output contains audio; choose audio_from_visual with transcript, or provide narration")
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
        copy_project(root, source, out_dir)
        if props and not props.is_relative_to(root):
            shutil.copy2(props, source / "render-props.json")
        shutil.copy2(render_log, out_dir / "logs" / "remotion-render.log")
        manifest = out_dir / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data.update(renderer="remotion", composition=composition,
                    sourceEntry=str((source / entry.relative_to(root)).relative_to(out_dir)))
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("composition", help="Registered Remotion composition ID")
    parser.add_argument("timing", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--props", type=Path)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    args = parser.parse_args()
    try:
        result = render(args.entry, args.composition, args.timing, args.out, args.runtime_dir,
                        args.project_root, args.props)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
