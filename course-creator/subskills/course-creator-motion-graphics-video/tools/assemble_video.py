#!/usr/bin/env python3
"""Assemble rendered scenes and optional narration into a portable video project.

Input JSON example:
{
  "title": "A short explainer", "aspect": "16:9", "fps": 30,
  "scenes": [
    {"id": "hook", "visual": "frames/hook.png", "duration_sec": 2.5,
     "narration": "audio/hook.wav", "caption": "A better opening"},
    {"id": "demo", "visual": "clips/demo.mp4", "duration_sec": 4,
     "caption": "The real product screen"}
  ]
}

Visuals are produced by Slidev, Remotion, HyperFrames, or supplied footage.
This tool assembles them; it does not generate or verify factual claims.
Progress is JSON on stderr. The finished project path is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from write_subtitles import render as render_subtitles, validate as validate_cues


ASPECTS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv"}
MAX_SCENES = 80
MAX_SECONDS = 30 * 60


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def run(command: list[str], log: Path) -> None:
    with log.open("w", encoding="utf-8") as output:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
        try:
            code = child.wait()
        except KeyboardInterrupt:
            child.kill()
            child.wait()
            raise
    if code:
        detail = log.read_text(encoding="utf-8", errors="replace")[-2500:]
        raise RuntimeError(f"Command failed ({code}); see {log}: {detail}")


def probe(ffprobe: Path, source: Path) -> dict:
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(source)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode:
        raise ValueError(f"Could not inspect {source}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    try:
        duration = float(data.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0.0
    return {"duration": duration, "streams": {item.get("codec_type") for item in data.get("streams", [])}}


def source_path(base: Path, value: object, kind: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{kind} needs a file path")
    source = (base / value).resolve()
    if not source.is_file():
        raise ValueError(f"{kind} is missing: {source}")
    return source


def validate_plan(plan: object, base: Path, ffprobe: Path) -> tuple[list[dict], tuple[int, int], int]:
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list):
        raise ValueError("Plan needs a scenes array")
    scenes = plan["scenes"]
    if not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError(f"Plan needs 1 to {MAX_SCENES} scenes")
    aspect = plan.get("aspect", "16:9")
    if aspect not in ASPECTS:
        raise ValueError(f"Unsupported aspect: {aspect}")
    fps = plan.get("fps", 30)
    if isinstance(fps, bool) or fps not in (24, 25, 30, 60):
        raise ValueError("fps must be 24, 25, 30 or 60")
    music = plan.get("music")
    if music is not None:
        if not isinstance(music, dict):
            raise ValueError("music must be an object with file and volume")
        music_file = source_path(base, music.get("file"), "Music")
        if "audio" not in probe(ffprobe, music_file)["streams"]:
            raise ValueError("Music file has no audio stream")
        volume = music.get("volume", 0.15)
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not math.isfinite(volume) or not 0 < volume <= 1:
            raise ValueError("music volume must be above 0 and at most 1")
    prepared = []
    total = 0.0
    seen = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be an object")
        scene_id = scene.get("id", f"s{index}")
        if not isinstance(scene_id, str) or not scene_id.strip() or scene_id in seen:
            raise ValueError(f"Scene {index} has an invalid or duplicate ID")
        seen.add(scene_id)
        visual = source_path(base, scene.get("visual"), f"Scene {index} visual")
        if visual.suffix.lower() not in IMAGE_SUFFIXES | VIDEO_SUFFIXES:
            raise ValueError(f"Scene {index} visual must be an image or video")
        visual_probe = probe(ffprobe, visual)
        if "video" not in visual_probe["streams"]:
            raise ValueError(f"Scene {index} visual has no video stream")
        narration = source_path(base, scene["narration"], f"Scene {index} narration") if scene.get("narration") else None
        audio_from_visual = scene.get("audio_from_visual", False)
        if not isinstance(audio_from_visual, bool) or (audio_from_visual and narration):
            raise ValueError(f"Scene {index} must choose one audio source")
        if audio_from_visual and (visual.suffix.lower() in IMAGE_SUFFIXES or "audio" not in visual_probe["streams"]):
            raise ValueError(f"Scene {index} visual has no audio to use")
        audio_duration = 0.0
        if narration:
            audio_probe = probe(ffprobe, narration)
            if "audio" not in audio_probe["streams"] or audio_probe["duration"] <= 0:
                raise ValueError(f"Scene {index} narration has no measured audio")
            audio_duration = audio_probe["duration"]
        elif audio_from_visual:
            audio_duration = visual_probe["duration"]
        requested = scene.get("duration_sec")
        if requested is None:
            requested = audio_duration or visual_probe["duration"]
        if isinstance(requested, bool) or not isinstance(requested, (int, float)) or not math.isfinite(requested):
            raise ValueError(f"Scene {index} needs a finite duration_sec")
        duration = float(requested) if audio_from_visual else max(float(requested), audio_duration)
        if not 0.3 <= duration <= MAX_SECONDS:
            raise ValueError(f"Scene {index} duration must be 0.3 to {MAX_SECONDS} seconds")
        if audio_from_visual and duration > visual_probe["duration"] + 0.001:
            raise ValueError(f"Scene {index} cannot extend footage audio by looping it")
        if audio_from_visual:
            audio_duration = duration
        caption = scene.get("caption", "")
        if not isinstance(caption, str):
            raise ValueError(f"Scene {index} caption must be text")
        if (narration or audio_from_visual) and not caption.strip() and not scene.get("cues"):
            raise ValueError(f"Scene {index} audio needs its transcript in caption or cues")
        local_cues = scene.get("cues")
        if local_cues is not None:
            validate_cues({"duration_sec": duration, "cues": local_cues})
        total += duration
        prepared.append({"id": scene_id, "visual": visual, "narration": narration,
                         "audio_from_visual": audio_from_visual,
                         "requested_duration": duration, "audio_duration": audio_duration,
                         "caption": caption.strip(), "cues": local_cues})
    if total > MAX_SECONDS:
        raise ValueError("Project duration exceeds 30 minutes")
    return prepared, ASPECTS[aspect], fps


def render_scene(ffmpeg: Path, scene: dict, index: int, size: tuple[int, int], fps: int, has_audio: bool, output: Path, log: Path) -> None:
    width, height = size
    visual = scene["visual"]
    args = [str(ffmpeg), "-hide_banner", "-y"]
    if visual.suffix.lower() in IMAGE_SUFFIXES:
        args.extend(["-loop", "1", "-framerate", str(fps)])
    else:
        args.extend(["-stream_loop", "-1"])
    args.extend(["-i", str(visual)])
    if scene["narration"]:
        args.extend(["-i", str(scene["narration"])])
    elif has_audio and not scene["audio_from_visual"]:
        args.extend(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"])
    duration = scene["requested_duration"]
    args.extend(["-map", "0:v:0"])
    if has_audio:
        args.extend(["-map", "0:a:0" if scene["audio_from_visual"] else "1:a:0"])
    args.extend([
        "-t", f"{duration:.3f}",
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps},format=yuv420p",
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
    ])
    if has_audio:
        args.extend(["-af", "aresample=48000,apad", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"])
    args.extend(["-movflags", "+faststart", str(output)])
    progress("render", f"Rendering scene {index}", scene=index)
    run(args, log)


def assemble(plan_file: Path, out_dir: Path, ffmpeg: Path, ffprobe: Path) -> dict:
    plan_file = plan_file.resolve()
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {out_dir}")
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    scenes, size, fps = validate_plan(plan, plan_file.parent, ffprobe)
    has_scene_audio = any(scene["narration"] or scene["audio_from_visual"] for scene in scenes)
    music_spec = plan.get("music")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "assets").mkdir()
    (out_dir / "audio").mkdir()
    (out_dir / "segments").mkdir()
    (out_dir / "logs").mkdir()
    script = [f"# {plan.get('title', 'Video')}\n"]
    storyboard = ["# Storyboard\n"]
    imported = []
    portable_scenes = []
    segments = []
    cues = []
    cursor = 0.0
    for index, scene in enumerate(scenes, 1):
        visual = scene["visual"]
        visual_copy = out_dir / "assets" / f"scene-{index:03d}{visual.suffix.lower()}"
        shutil.copy2(visual, visual_copy)
        audio_copy = None
        if scene["narration"]:
            audio_copy = out_dir / "audio" / f"scene-{index:03d}{scene['narration'].suffix.lower()}"
            shutil.copy2(scene["narration"], audio_copy)
        scene_copy = {**scene, "visual": visual_copy, "narration": audio_copy}
        segment = out_dir / "segments" / f"scene-{index:03d}.mp4"
        render_scene(ffmpeg, scene_copy, index, size, fps, has_scene_audio, segment, out_dir / "logs" / f"scene-{index:03d}.log")
        segment_duration = probe(ffprobe, segment)["duration"]
        if segment_duration <= 0:
            raise RuntimeError(f"Rendered scene {index} has no duration")
        if scene["cues"]:
            for cue in scene["cues"]:
                cues.append({"start": cursor + cue["start"], "end": cursor + cue["end"], "text": cue["text"]})
        elif scene["caption"]:
            caption_end = min(segment_duration, scene["audio_duration"] or segment_duration)
            cues.append({"start": cursor, "end": cursor + max(caption_end, 0.1), "text": scene["caption"]})
        transcript = scene["caption"] or "\n".join(cue["text"] for cue in scene["cues"] or [])
        script.append(f"## {scene['id']}\n\n{transcript}\n")
        storyboard.append(f"- {scene['id']} · {segment_duration:.3f}s · {visual_copy.relative_to(out_dir)}\n")
        imported.append({"sceneId": scene["id"], "visual": str(visual_copy.relative_to(out_dir)),
                         "originalVisual": str(visual), "narration": str(audio_copy.relative_to(out_dir)) if audio_copy else None,
                         "audioFromVisual": scene["audio_from_visual"]})
        portable_scene = dict(plan["scenes"][index - 1])
        portable_scene["visual"] = str(visual_copy.relative_to(out_dir))
        if audio_copy:
            portable_scene["narration"] = str(audio_copy.relative_to(out_dir))
        portable_scenes.append(portable_scene)
        segments.append(segment)
        cursor += segment_duration
        progress("render", f"Rendered scene {index} of {len(scenes)}", scene=index, durationSec=segment_duration)
    concat = out_dir / "segments.txt"
    concat.write_text("".join(f"file '{path.as_posix().replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n" for path in segments), encoding="utf-8")
    final = out_dir / "video.mp4"
    assembled = out_dir / "segments" / "assembled.mp4" if music_spec else final
    progress("assemble", "Joining scenes")
    run([str(ffmpeg), "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(assembled)], out_dir / "logs" / "final.log")
    if music_spec:
        music_source = source_path(plan_file.parent, music_spec["file"], "Music")
        music_copy = out_dir / "audio" / f"background{music_source.suffix.lower()}"
        shutil.copy2(music_source, music_copy)
        assembled_duration = probe(ffprobe, assembled)["duration"]
        volume = float(music_spec.get("volume", 0.15))
        if has_scene_audio:
            audio_filter = f"[0:a]aresample=48000[scene];[1:a]aresample=48000,volume={volume},atrim=duration={assembled_duration:.3f}[bed];[scene][bed]amix=inputs=2:duration=first:dropout_transition=0[mix]"
        else:
            audio_filter = f"[1:a]aresample=48000,volume={volume},atrim=duration={assembled_duration:.3f}[mix]"
        progress("audio", "Mixing background music")
        run([str(ffmpeg), "-hide_banner", "-y", "-i", str(assembled), "-stream_loop", "-1", "-i", str(music_copy),
             "-filter_complex", audio_filter, "-map", "0:v:0", "-map", "[mix]", "-t", f"{assembled_duration:.3f}",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(final)],
            out_dir / "logs" / "mix.log")
    final_probe = probe(ffprobe, final)
    duration = final_probe["duration"]
    has_audio = has_scene_audio or bool(music_spec)
    if duration <= 0 or "video" not in final_probe["streams"] or (has_audio and "audio" not in final_probe["streams"]):
        raise RuntimeError("Final MP4 is missing a required media stream")
    audio = None
    if has_audio:
        audio = out_dir / "audio.mp3"
        progress("audio", "Exporting audio")
        run([str(ffmpeg), "-hide_banner", "-y", "-i", str(final), "-vn", "-c:a", "libmp3lame", "-q:a", "2", str(audio)], out_dir / "logs" / "audio.log")
        if "audio" not in probe(ffprobe, audio)["streams"]:
            raise RuntimeError("Audio export did not verify")
    caption_data = {"duration_sec": duration, "cues": cues}
    if cues:
        validate_cues(caption_data)
    (out_dir / "captions.json").write_text(json.dumps(caption_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "captions.srt").write_text(render_subtitles(cues) if cues else "", encoding="utf-8")
    (out_dir / "captions.vtt").write_text(render_subtitles(cues, webvtt=True) if cues else "WEBVTT\n", encoding="utf-8")
    (out_dir / "script.md").write_text("\n".join(script), encoding="utf-8")
    (out_dir / "storyboard.md").write_text("\n".join(storyboard), encoding="utf-8")
    portable_plan = {**plan, "scenes": portable_scenes}
    if music_spec:
        portable_plan["music"] = {**music_spec, "file": str(music_copy.relative_to(out_dir))}
    (out_dir / "project.json").write_text(json.dumps(portable_plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {"status": "complete", "title": plan.get("title", "Video"), "durationSec": duration,
                "video": "video.mp4", "audio": "audio.mp3" if audio else None, "script": "script.md", "storyboard": "storyboard.md",
                "captions": ["captions.json", "captions.srt", "captions.vtt"], "scenes": imported,
                "music": str(music_copy.relative_to(out_dir)) if music_spec else None}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    progress("complete", "Video project ready", durationSec=duration)
    return {"ready": True, "directory": str(out_dir), "video": str(final), "audio": str(audio) if audio else None, "durationSec": duration,
            "captions": manifest["captions"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, default=shutil.which("ffmpeg"))
    parser.add_argument("--ffprobe", type=Path, default=shutil.which("ffprobe"))
    args = parser.parse_args()
    try:
        if not args.ffmpeg or not args.ffprobe:
            raise ValueError("FFmpeg and FFprobe are required; run ensure_video_runtime.py first")
        result = assemble(args.plan, args.out, Path(args.ffmpeg), Path(args.ffprobe))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
