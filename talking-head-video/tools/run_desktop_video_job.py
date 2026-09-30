#!/usr/bin/env python3
"""Convert Video Studio form media into a durable video job and run it.

The input wraps the desktop ProjectRequest as {schemaVersion: 1, request: ...}.
Media arrives as base64; filenames are metadata, never filesystem paths.
Progress is JSON on stderr and the verified desktop outcome is JSON on stdout.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
from pathlib import Path
import shutil
import signal
import subprocess
import sys

from assemble_video import probe
from author_desktop_video import author, ENGINES
from ensure_video_runtime import MANIFEST, default_runtime_dir
from run_video_job import fingerprint, interrupted, media_paths, progress, run_job


IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
AUDIO_TYPES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
VIDEO_TYPES = {".mp4", ".webm", ".mov", ".mkv"}


def text(value: object, label: str, maximum: int = 1500) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{label} must be text under {maximum} characters")
    return value


def decode(value: object, label: str, maximum: int) -> bytes:
    if not isinstance(value, str) or len(value) > (maximum + 2) // 3 * 4:
        raise ValueError(f"{label} is missing or exceeds its media size limit")
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError(f"Invalid base64 for {label}") from None
    if not data or len(data) > maximum:
        raise ValueError(f"{label} is empty or exceeds its media size limit")
    return data


def save_asset(asset: object, target: Path, allowed: set[str], maximum: int) -> tuple[Path, dict]:
    if not isinstance(asset, dict):
        raise ValueError("Uploaded media must be an object")
    name = text(asset.get("name"), "Uploaded filename", 300)
    extension = Path(name.replace("\\", "/")).suffix.lower()
    if extension not in allowed:
        raise ValueError(f"Unsupported uploaded media: {name}")
    target = target.with_suffix(extension)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(decode(asset.get("dataBase64"), name, maximum))
    return target, {"name": name, "mime": str(asset.get("mime", "")), "file": str(target.name)}


def prepare_request(payload_file: Path, workspace: Path) -> Path:
    if payload_file.stat().st_size > 750_000_000:
        raise ValueError("Desktop request exceeds the 750 MB limit")
    payload = json.loads(payload_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1 or not isinstance(payload.get("request"), dict):
        raise ValueError("Desktop request needs schemaVersion 1 and a request object")
    request = payload["request"]
    renderer = request.get("renderer", "scenes")
    route = request.get("jobRoute", "product-launch-video" if request.get("category") == "product" else "explainer-video")
    if route not in MANIFEST["routes"] or renderer not in ENGINES | {"scenes"}:
        raise ValueError("Choose a supported video route and renderer")
    if renderer != "scenes" and renderer not in MANIFEST["routes"][route]:
        raise ValueError(f"Renderer {renderer} is not available for {route}")
    title = text(request.get("title"), "Title", 160).strip()
    if not title:
        raise ValueError("Enter a title")
    scenes = request.get("scenes")
    assets = request.get("sourceAssets", [])
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 80:
        raise ValueError("A desktop project needs 1 to 80 scenes")
    if not isinstance(assets, list) or len(assets) > 80:
        raise ValueError("A desktop project accepts at most 80 source images")
    if request.get("aspect") not in ("16:9", "9:16", "1:1", "4:5") or request.get("fps") not in (24, 25, 30, 60):
        raise ValueError("Choose a supported aspect and frame rate")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("Workspace is not empty; resume its original request or choose a new workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    inputs = workspace / "inputs"
    inputs.mkdir()
    progress("import", "Importing desktop media", artifact=str(workspace))
    runtime = Path(payload["runtimeDir"]).expanduser().resolve() if payload.get("runtimeDir") else default_runtime_dir()
    _, ffprobe = media_paths(runtime)
    original_assets = []
    for index, asset in enumerate(assets, 1):
        if not isinstance(asset, dict) or asset.get("mime") not in IMAGE_TYPES:
            raise ValueError(f"Source image {index} must be PNG, JPEG, or WebP")
        # Assign extensions from the actual image type, ignoring untrusted paths.
        asset = {**asset, "name": f"source{IMAGE_TYPES[asset['mime']]}", "originalName": asset.get("name", "")}
        path, metadata = save_asset(asset, inputs / "originals" / f"image-{index:04}", set(IMAGE_TYPES.values()), 22_000_000)
        metadata.update(name=text(asset["originalName"], "Image filename", 300), file=str(path.relative_to(inputs)))
        if asset.get("provenance"):
            record = asset["provenance"]
            if not isinstance(record, dict) or record.get("provider") != "openai" or record.get("sourceType") != "generated":
                raise ValueError("Generated image provenance needs a known provider and source type")
            if record.get("sha256") != fingerprint(path):
                raise ValueError("Generated image provenance does not match its uploaded bytes")
            public = {key: text(record.get(key), f"Image {key}", 12000 if key == "prompt" else 300)
                      for key in ("provider", "model", "prompt", "size", "quality", "createdAt", "sha256", "termsUrl", "sourceType")}
            public["rightsReviewRequired"] = True
            metadata["provenance"] = public
        original_assets.append(metadata)
    avatar = request.get("avatar")
    avatar_job = None
    if avatar:
        if not isinstance(avatar, dict) or avatar.get("rightsConfirmed") is not True or avatar.get("provider") != "local" or avatar.get("mode") != "photo" or route != "avatar-video":
            raise ValueError("A local presenter requires the avatar route, photo mode, local provider and confirmed image rights")
        portrait, _ = save_asset(avatar.get("image"), inputs / "portrait", set(IMAGE_TYPES.values()), 22_000_000)
        avatar_job = {"provider": "local", "mode": "photo", "backend": text(avatar.get("backend"), "Presenter backend", 100), "rightsConfirmed": True, "image": str(portrait.relative_to(workspace))}
    prepared = []
    desktop_scenes = []
    seen = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be an object")
        scene_id = text(scene.get("id"), f"Scene {index} ID", 160).strip()
        if not scene_id or scene_id in seen:
            raise ValueError(f"Scene {index} has an empty or duplicate ID")
        seen.add(scene_id)
        duration = scene.get("durationSec")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 0.5 <= duration <= 120:
            raise ValueError(f"Scene {index} duration must be 0.5 to 120 seconds")
        caption = text(scene.get("caption", ""), f"Scene {index} caption")
        visual_description = text(scene.get("visual", ""), f"Scene {index} visual")
        screen_text = text(scene["screenText"], f"Scene {index} on-screen text", 300) if "screenText" in scene else None
        source_index = scene.get("sourceAssetIndex")
        if source_index is not None and (isinstance(source_index, bool) or not isinstance(source_index, int) or not 0 <= source_index < len(assets)):
            raise ValueError(f"Scene {index} references a missing source image")
        if scene.get("audioSource") and scene.get("audioWavBase64"):
            raise ValueError(f"Scene {index} has two narration sources")
        card = inputs / f"scene-{index:04}.png"
        card_bytes = decode(scene.get("imagePngBase64"), f"Scene {index} card", 15_000_000)
        if not card_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Scene {index} card must be PNG")
        card.write_bytes(card_bytes)
        visual = card
        uploads = {}
        if avatar_job and scene.get("videoSource"):
            raise ValueError("A presenter scene cannot also have uploaded footage")
        if scene.get("videoSource"):
            visual, uploads["video"] = save_asset(scene["videoSource"], inputs / f"clip-{index:04}", VIDEO_TYPES, 100_000_000)
        narration = None
        if scene.get("audioSource"):
            narration, uploads["narration"] = save_asset(scene["audioSource"], inputs / f"narration-{index:04}", AUDIO_TYPES, 60_000_000)
        elif scene.get("audioWavBase64"):
            narration = inputs / f"narration-{index:04}.wav"
            wav = decode(scene["audioWavBase64"], f"Scene {index} narration", 45_000_000)
            if not wav.startswith(b"RIFF") or wav[8:12] != b"WAVE":
                raise ValueError(f"Scene {index} generated narration must be WAV")
            narration.write_bytes(wav)
        item = {"id": scene_id, "visual": visual.name, "duration_sec": duration, "caption": caption}
        if narration:
            if not caption.strip():
                raise ValueError(f"Scene {index} needs its narration transcript")
            item["narration"] = narration.name
        elif visual != card and "audio" in probe(ffprobe, visual)["streams"]:
            if not caption.strip():
                raise ValueError(f"Scene {index} needs its footage transcript")
            item["audio_from_visual"] = True
        prepared.append(item)
        desktop_scenes.append({**item, "visualDescription": visual_description, "screenText": screen_text, "sourceAssetIndex": source_index,
                               "card": card.name, "uploads": uploads})
        progress("import", f"Imported scene {index} of {len(scenes)}", scene=index, sceneCount=len(scenes))
    if sum(scene["duration_sec"] for scene in prepared) > 1800:
        raise ValueError("The desktop project exceeds 30 minutes")
    timing = {"title": title, "aspect": request["aspect"], "fps": request["fps"], "scenes": prepared}
    (inputs / "timing.json").write_text(json.dumps(timing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = {key: value for key, value in request.items() if key not in ("scenes", "sourceAssets", "avatar")}
    if avatar_job:
        metadata["avatar"] = avatar_job
    metadata.update(scenes=desktop_scenes, sourceAssets=original_assets, payloadSha256=fingerprint(payload_file))
    (inputs / "desktop.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    job = {"schemaVersion": 1, "route": route,
           "renderer": "scenes" if renderer == "scenes" else "storyboard", "timing": "inputs/timing.json", "output": "output", "captions": payload.get("captions", "auto"),
           "language": request.get("language", "en"), "runtimeDir": str(runtime)}
    if avatar_job:
        job["avatar"] = avatar_job
    if renderer != "scenes":
        progress("source", f"Authoring editable {renderer} scene projects")
        contract = author(inputs, renderer, ffprobe)
        job.update(source=str(contract.relative_to(workspace)), authoringRenderer=renderer)
    job_path = workspace / "job-request.json"
    job_path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return job_path


def run_desktop_job(payload_file: Path, workspace: Path, resume: bool = False) -> dict:
    workspace = workspace.resolve()
    if resume:
        metadata = json.loads((workspace / "inputs/desktop.json").read_text(encoding="utf-8"))
        if metadata.get("payloadSha256") != fingerprint(payload_file):
            raise ValueError("Resume requires the original desktop request")
        job_path = workspace / "job-request.json"
    else:
        job_path = prepare_request(payload_file, workspace)
    result = run_job(job_path, resume=resume)
    output = Path(result["directory"])
    metadata = json.loads((workspace / "inputs/desktop.json").read_text(encoding="utf-8"))
    source = output / "source" / "desktop"
    if not source.exists():
        shutil.copytree(workspace / "inputs", source, ignore=shutil.ignore_patterns(".work-*"))
    style = output / "style.md"
    if not style.exists():
        style.write_text("# Desktop style\n\n" + "\n".join(f"- {key}: {metadata.get(key, '')}" for key in
                         ("brandPrimary", "brandSurface", "brandText", "headlineFont", "bodyFont", "aspect", "fps")) + "\n", encoding="utf-8")
    manifest_file = output / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    asset_review = any(asset.get("provenance", {}).get("rightsReviewRequired") for asset in metadata["sourceAssets"])
    manifest.update(desktopSource="source/desktop/desktop.json", style="style.md",
                    assetSources=[{**asset, "file": "source/desktop/" + asset["file"]} for asset in metadata["sourceAssets"]],
                    assetReviewRequired=asset_review)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {**result, "assetReviewRequired": asset_review, "script": str(output / "script.md"), "storyboard": str(output / "storyboard.md"),
            "narration": [str(path) for path in sorted((output / "audio").glob("*")) if path.is_file()],
            "captionsSrt": str(output / "captions.srt"), "captionsVtt": str(output / "captions.vtt"),
            "sizeBytes": (output / "video.mp4").stat().st_size,
            "mixedAudio": str(output / "audio.mp3") if (output / "audio.mp3").is_file() else None,
            "transcript": str(output / "transcript.json") if (output / "transcript.json").is_file() else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        result = run_desktop_job(args.request.resolve(), args.workspace, args.resume)
    except KeyboardInterrupt:
        result = {"ready": False, "status": "cancelled"}
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        result = {"ready": False, "status": "failed", "error": str(error)}
    print(json.dumps(result))
    return 0 if result.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
