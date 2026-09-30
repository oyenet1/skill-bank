#!/usr/bin/env python3
"""Generate and verify a local photo presenter with an installed backend."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import signal
import time
import uuid

from assemble_video import probe as inspect_media
from avatar_probe import compatible, manifest, probe, progress
from avatar_runtime import environment, interrupted, paths, run, runtime_dir, status


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def infer(root: Path, backend: dict, state: dict, image: Path, audio: Path, work: Path) -> tuple[Path, float]:
    location = paths(root, backend)
    source = location["source"] / backend["codeSubdir"]
    project = work / "project"
    shutil.copytree(source, project)
    model_prefix = "models" if backend["workerKind"] == "musetalk" else "checkpoints"
    for file in backend["files"]:
        name = file["name"]
        if name.startswith(("hub/", "gfpgan/")):
            destination = project / name
        elif backend["workerKind"] == "sadtalker" and name.startswith("BFM_Fitting/"):
            destination = project / "src/config" / Path(name).name
        else:
            destination = project / model_prefix / name
        if destination.exists():
            destination.unlink()
        link_or_copy(location["models"] / name, destination)
    media = project / "media"
    media.mkdir(exist_ok=True)
    ffmpeg, ffprobe = (Path(state["mediaPaths"][name]) for name in ("ffmpeg", "ffprobe"))
    env = environment(root)
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1", PYTORCH_ENABLE_MPS_FALLBACK="1",
               TORCH_HOME=str(project), HF_HOME=str(work / "hf"), GLOG_minloglevel="2")
    env["PATH"] = os.pathsep.join([str(ffmpeg.parent), str(ffprobe.parent), env.get("PATH", "")])
    if state["accelerator"]["kind"] == "cuda":
        env["CUDA_VISIBLE_DEVICES"] = str(state["accelerator"].get("deviceIndex", 0))
    run([str(ffmpeg), "-v", "error", "-y", "-protocol_whitelist", "file,pipe", "-i", str(image),
         "-vf", "scale=1024:1024:force_original_aspect_ratio=decrease", "-frames:v", "1", str(media / "portrait.png")], work / "portrait.log", env)
    run([str(ffmpeg), "-v", "error", "-y", "-protocol_whitelist", "file,pipe", "-i", str(audio),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(media / "narration.wav")], work / "audio.log", env)
    audio_info = inspect_media(ffprobe, media / "narration.wav")
    duration = audio_info["duration"]
    if not math.isfinite(duration) or duration <= 0 or "audio" not in audio_info["streams"]:
        raise ValueError("Presenter narration is not a verified non-empty audio track")
    if duration > backend["recommendedMaxSeconds"]:
        progress("warning", "Narration exceeds the recommended local presenter clip length; split scenes for shorter generation runs",
                 durationSec=duration, recommendedMaxSeconds=backend["recommendedMaxSeconds"])
    progress("generate", "Starting offline photo presenter inference", backend=backend["id"], durationSec=duration,
             estimatedElapsedSec=[round(duration * value) for value in backend["estimatedSecondsPerSecond"]],
             messageDetail="Resolution and accelerator tier dominate memory and runtime; this is an estimate")
    if backend["workerKind"] == "latentsync":
        # Upstream processes complete 16-frame blocks. Pad inference inputs so
        # its final block cannot drop the end of the original narration.
        padded_duration = math.ceil(duration * 25 / 16) * 16 / 25 + 0.04
        run([str(ffmpeg), "-v", "error", "-y", "-i", str(media / "narration.wav"), "-af", f"apad=whole_dur={padded_duration}",
             "-t", str(padded_duration), str(media / "inference.wav")], work / "pad-audio.log", env)
        run([str(ffmpeg), "-v", "error", "-y", "-loop", "1", "-i", str(media / "portrait.png"), "-t", str(padded_duration),
             "-r", "25", "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2", "-pix_fmt", "yuv420p", str(media / "portrait.mp4")], work / "portrait-video.log", env)
    config = {"root": str(project), "workerKind": backend["workerKind"], "accelerator": state["accelerator"]["kind"]}
    config_path = work / "inference.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    worker = Path(__file__).with_name("avatar_infer_worker.py")
    run([str(location["python"]), str(worker), str(config_path)], work / "inference.log", env, phase="generate")
    candidates = [path for path in (project / "results").rglob("*.mp4") if not path.name.startswith("temp_") and not path.name.endswith("_concat.mp4")]
    if len(candidates) != 1:
        raise RuntimeError(f"Inference did not produce one final presenter clip; see {work / 'inference.log'}")
    info = inspect_media(ffprobe, candidates[0])
    if "video" not in info["streams"] or not math.isfinite(info["duration"]) or info["duration"] < duration - 0.15:
        raise RuntimeError("Generated presenter clip is missing video or is shorter than its narration")
    result = work / "video.mp4"
    run([str(ffmpeg), "-v", "error", "-y", "-i", str(candidates[0]), "-i", str(media / "narration.wav"),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(result)], work / "mux.log", env)
    info = inspect_media(ffprobe, result)
    if not {"video", "audio"}.issubset(info["streams"]) or not math.isfinite(info["duration"]) or info["duration"] < duration - 0.15:
        raise RuntimeError("Final local presenter MP4 failed media verification")
    return result, info["duration"]


def generate(root: Path, backend_id: str, mode: str, image: Path | None, audio: Path | None, output: Path, *, rights_confirmed: bool = False) -> dict:
    start = time.monotonic()
    base = {"ready": False, "backend": backend_id, "mode": mode, "video": None, "durationSec": None, "elapsedSec": 0}
    if mode != "photo":
        return {**base, "reason": f"local-{mode}-mode-unsupported", "unsupportedReason": f"local-{mode}-mode-unsupported"}
    if not rights_confirmed:
        return {**base, "reason": "image-rights-confirmation-required", "error": "Confirm rights to the person's image before photo generation"}
    if image is None or audio is None or not image.is_file() or not audio.is_file():
        raise ValueError("Photo presenter generation needs a local portrait and narration file")
    config = manifest()
    capability = probe(config, allow_restricted=True)
    rows = compatible(config, capability["accelerator"]["kind"], capability["accelerator"]["memoryBytes"], allow_restricted=True) if capability["eligible"] else []
    backend = next((row for row in rows if row["id"] == backend_id), None)
    if backend is None:
        return {**base, "reason": "incompatible-backend", "capability": capability, "error": "This host cannot run the requested local presenter backend"}
    installed = status(root, backend)
    if not installed["ready"]:
        return {**base, "reason": "backend-not-installed", "missing": installed["missing"], "retryCommand": f"python3 tools/avatar_ensure.py avatar-video --backend {backend_id}"}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "video.mp4").exists():
        raise ValueError("Presenter output already contains a video; choose a new output directory")
    work = output / (".work-" + uuid.uuid4().hex)
    work.mkdir()
    try:
        video, duration = infer(root, backend, installed["state"], image.resolve(), audio.resolve(), work)
        record = {"provider": "local", "backend": backend_id, "mode": mode, "accelerator": capability["accelerator"],
                  "revision": backend["revision"], "manifestHash": installed["state"]["manifestHash"], "consent": installed["state"]["consent"],
                  "imageRightsConfirmed": True, "durationSec": duration, "elapsedSec": round(time.monotonic() - start, 3), "video": "video.mp4", "work": work.name}
        (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        video.replace(output / "video.mp4")
        progress("complete", "Local presenter MP4 verified", backend=backend_id, durationSec=duration)
        return {**base, "ready": True, "provider": "local", "video": str(output / "video.mp4"), "durationSec": duration,
                "elapsedSec": record["elapsedSec"], "manifest": str(output / "manifest.json"), "work": str(work)}
    except (Exception, KeyboardInterrupt) as error:
        return {**base, "reason": "cancelled" if isinstance(error, KeyboardInterrupt) else "generation-failed", "error": str(error),
                "elapsedSec": round(time.monotonic() - start, 3), "work": str(work), "log": str(work / "inference.log"),
                "retryCommand": "Repeat the same generation command with a fresh output directory; installed models are reused"}


def smoke(root: Path, backend: dict, state: dict) -> None:
    import wave
    import struct
    location = paths(root, backend)
    work = location["base"] / ("smoke-" + uuid.uuid4().hex)
    work.mkdir()
    audio = work / "fixture.wav"
    with wave.open(str(audio), "wb") as stream:
        stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        stream.writeframes(b"".join(struct.pack("<h", int(2000 * math.sin(index * 2 * math.pi * 220 / 16000))) for index in range(3 * 16000)))
    portrait = location["source"] / backend["codeSubdir"] / backend["smokeFixture"]
    progress("verify", "Running on-device three-second presenter inference check", backend=backend["id"])
    infer(root, backend, state, portrait, audio, work / "inference")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["photo", "avatar", "dub"], default="photo")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rights-confirmed", action="store_true")
    parser.add_argument("--runtime-dir", type=Path, default=runtime_dir())
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        result = generate(args.runtime_dir.expanduser().resolve(), args.backend, args.mode, args.image, args.audio, args.out.resolve(), rights_confirmed=args.rights_confirmed)
    except (Exception, KeyboardInterrupt) as error:
        result = {"ready": False, "backend": args.backend, "mode": args.mode, "error": str(error)}
    print(json.dumps(result))
    return 0 if result.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
