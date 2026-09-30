#!/usr/bin/env python3
"""Export a Slidev deck's click states and assemble them into a timed MP4.

The timing JSON uses the assemble_video.py plan schema, except each scene's
visual is supplied by the exported Slidev frame in order. The number of scenes
must equal the number of exported click states. Progress is JSON on stderr and
the final project result is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from assemble_video import assemble, progress
from ensure_video_runtime import default_runtime_dir, setup


FRAME = re.compile(r"^(\d+)-(\d+)\.png$")


def frame_order(path: Path) -> tuple[int, int]:
    match = FRAME.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unexpected Slidev frame name: {path.name}")
    return int(match.group(1)), int(match.group(2))


def render(deck: Path, timing: Path, out_dir: Path, runtime_dir: Path) -> dict:
    deck = deck.resolve()
    timing = timing.resolve()
    out_dir = out_dir.resolve()
    if not deck.is_file() or deck.suffix.lower() != ".md":
        raise ValueError(f"Slidev deck is missing: {deck}")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {out_dir}")
    plan = json.loads(timing.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list):
        raise ValueError("Timing file needs a scenes array")
    progress("setup", "Preparing Slidev and FFmpeg")
    runtime = setup("explainer-video", runtime_dir, ensure=True, only="slidev")
    if not runtime["ready"]:
        raise RuntimeError(f"Video runtime is incomplete: {runtime['missing']}")
    paths = runtime["paths"]
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    export_log = out_dir.with_name(out_dir.name + ".slidev-export.log")
    with tempfile.TemporaryDirectory(prefix="slidev-video-", dir=out_dir.parent) as scratch:
        scratch_dir = Path(scratch)
        frames_dir = scratch_dir / "frames"
        env = os.environ.copy()
        env["PATH"] = str(Path(paths["node"]).parent) + os.pathsep + env.get("PATH", "")
        command = [paths["slidev"], "export", str(deck), "--format", "png", "--with-clicks",
                   "--output", str(frames_dir), "--timeout", "60000"]
        progress("visuals", "Exporting Slidev click states")
        with export_log.open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=deck.parent, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            detail = export_log.read_text(encoding="utf-8", errors="replace")[-2500:]
            raise RuntimeError(f"Slidev export failed ({result.returncode}); see {export_log}: {detail}")
        frames = sorted(frames_dir.glob("*.png"), key=frame_order)
        if len(frames) != len(plan["scenes"]):
            raise ValueError(f"Slidev exported {len(frames)} click states but timing has {len(plan['scenes'])} scenes")
        portable_plan = {**plan, "scenes": []}
        for scene, frame in zip(plan["scenes"], frames):
            if not isinstance(scene, dict):
                raise ValueError("Every timed scene must be an object")
            item = {**scene, "visual": str(frame)}
            if item.get("narration"):
                item["narration"] = str((timing.parent / item["narration"]).resolve())
            portable_plan["scenes"].append(item)
        if isinstance(plan.get("music"), dict) and plan["music"].get("file"):
            portable_plan["music"] = {**plan["music"], "file": str((timing.parent / plan["music"]["file"]).resolve())}
        prepared = scratch_dir / "prepared-plan.json"
        prepared.write_text(json.dumps(portable_plan, ensure_ascii=False), encoding="utf-8")
        result = assemble(prepared, out_dir, Path(paths["ffmpeg"]), Path(paths["ffprobe"]))
        source = out_dir / "source"
        source.mkdir()
        shutil.copy2(deck, source / deck.name)
        if (deck.parent / "public").is_dir():
            shutil.copytree(deck.parent / "public", source / "public")
        shutil.copy2(export_log, out_dir / "logs" / "slidev-export.log")
        manifest = out_dir / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["renderer"] = "slidev"
        data["sourceDeck"] = str((source / deck.name).relative_to(out_dir))
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("timing", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    args = parser.parse_args()
    try:
        result = render(args.deck, args.timing, args.out, args.runtime_dir)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
