#!/usr/bin/env python3
"""Transcribe final audio/video locally and write timed JSON, SRT and VTT.

HyperFrames supplies measured word timestamps. This tool groups those words
into readable cues; it does not assert that recognition is error-free.
Progress is JSON on stderr and the result is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from ensure_video_runtime import default_runtime_dir, setup
from write_subtitles import render as render_subtitles, validate as validate_cues


END_SENTENCE = re.compile(r"[.!?。！？][\"'”’)]*$")
NO_SPACE_BEFORE = re.compile(r"^[,.;:!?%。，！？；：、)\]}”’]")
MAX_WORDS = 8
MAX_CUE_SECONDS = 3.5
PAUSE_SECONDS = 0.55
MAX_TRANSCRIBE_SECONDS = 2 * 60 * 60


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def media_duration(ffprobe: Path, media: Path) -> float:
    result = subprocess.run([str(ffprobe), "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                             "-of", "json", str(media)], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(f"Could not inspect media: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    duration = float(payload.get("format", {}).get("duration", 0))
    streams = {stream.get("codec_type") for stream in payload.get("streams", [])}
    if not math.isfinite(duration) or duration <= 0 or "audio" not in streams:
        raise ValueError("Input needs a measurable audio stream")
    return duration


def read_words(path: Path, duration: float) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("words") if isinstance(payload, dict) else payload
    if not isinstance(raw, list):
        raise ValueError("Transcript needs a word array")
    words = []
    previous_start = -1.0
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Transcript entry {index} must be an object")
        if item.get("type") == "spacing":
            continue
        start, end, text = item.get("start"), item.get("end"), item.get("text")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in (start, end)):
            raise ValueError(f"Transcript word {index} needs finite timing")
        if not isinstance(text, str) or not text.strip() or start < 0 or end <= start or start < previous_start:
            raise ValueError(f"Transcript word {index} has invalid text or timing")
        if end > duration + 0.1:
            raise ValueError(f"Transcript word {index} ends after the media")
        words.append({"start": float(start), "end": min(float(end), duration), "text": text.strip()})
        previous_start = float(start)
    if not words:
        raise ValueError("Transcription returned no spoken words")
    return words


def cue_text(words: list[dict]) -> str:
    result = ""
    for word in words:
        token = word["text"]
        if not result or NO_SPACE_BEFORE.match(token) or result.endswith(("(", "[", "{", "“", "‘")):
            result += token
        elif "\u3400" <= token[0] <= "\u9fff":
            result += token
        else:
            result += " " + token
    return result


def group_words(words: list[dict], duration: float) -> list[dict]:
    cues = []
    group: list[dict] = []
    for word in words:
        if group and (len(group) >= MAX_WORDS or word["end"] - group[0]["start"] > MAX_CUE_SECONDS
                      or word["start"] - group[-1]["end"] >= PAUSE_SECONDS
                      or END_SENTENCE.search(group[-1]["text"])):
            cues.append({"start": group[0]["start"], "end": group[-1]["end"], "text": cue_text(group)})
            group = []
        group.append(word)
    if group:
        cues.append({"start": group[0]["start"], "end": group[-1]["end"], "text": cue_text(group)})
    for index in range(len(cues) - 1):
        cues[index]["end"] = min(cues[index]["end"], cues[index + 1]["start"])
    for cue in cues:
        cue["end"] = min(cue["end"], duration)
    validate_cues({"duration_sec": duration, "cues": cues})
    return cues


def run_transcriber(binary: Path, media: Path, scratch: Path, log: Path,
                    model: str, language: str | None) -> Path:
    command = [str(binary), "transcribe", str(media), "--dir", str(scratch), "--json", "--model", model]
    if language:
        command.extend(["--language", language])
    start = time.monotonic()
    progress("transcribe", "Transcribing final media")
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                if time.monotonic() - start > MAX_TRANSCRIBE_SECONDS:
                    process.kill()
                    process.wait()
                    raise RuntimeError(f"Transcription exceeded two hours; see {log}")
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    progress("transcribe", "Still transcribing", elapsedSeconds=round(time.monotonic() - start))
        except KeyboardInterrupt:
            process.kill()
            process.wait()
            raise
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    if process.returncode:
        raise RuntimeError(f"Transcription failed ({process.returncode}); see {log}: {' '.join(lines[-8:])}")
    result = None
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                result = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if not isinstance(result, dict) or not result.get("ok"):
        raise RuntimeError(f"Transcription returned no success result; see {log}")
    reported_path = result.get("transcriptPath")
    transcript = Path(reported_path).resolve() if isinstance(reported_path, str) else scratch / "transcript.json"
    if not transcript.is_file() or not transcript.is_relative_to(scratch.resolve()):
        raise RuntimeError("Transcription result points outside its workspace")
    return transcript


def transcribe(media: Path, out_dir: Path, runtime_dir: Path, model: str | None, language: str | None) -> dict:
    media = media.resolve()
    out_dir = out_dir.resolve()
    if not media.is_file():
        raise ValueError(f"Media is missing: {media}")
    model = model or ("large-v3" if language and not language.lower().startswith("en") else "small.en")
    if language and not language.lower().startswith("en") and model.endswith(".en"):
        raise ValueError("Non-English speech needs the multilingual large-v3 model")
    progress("setup", "Preparing local transcription tools")
    runtime = setup("talking-head-video", runtime_dir, ensure=True, only="hyperframes")
    if not runtime["ready"]:
        raise RuntimeError(f"Transcription runtime is incomplete: {runtime['missing']}")
    paths = runtime["paths"]
    duration = media_duration(Path(paths["ffprobe"]), media)
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "transcribe.log"
    with tempfile.TemporaryDirectory(prefix="transcribe-", dir=out_dir) as scratch:
        transcript = run_transcriber(Path(paths["hyperframes"]), media, Path(scratch), log, model, language)
        words = read_words(transcript, duration)
        cues = group_words(words, duration)
        payload = {"duration_sec": duration, "cues": cues, "review_required": True,
                   "source": "local-asr", "model": model, "language": language}
        outputs = {
            "transcript.json": json.dumps(words, indent=2, ensure_ascii=False) + "\n",
            "captions.json": json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            "captions.srt": render_subtitles(cues),
            "captions.vtt": render_subtitles(cues, webvtt=True),
        }
        for name, content in outputs.items():
            (out_dir / name).write_text(content, encoding="utf-8")
    progress("complete", "Timed captions ready for review", cueCount=len(cues))
    return {"ready": True, "directory": str(out_dir), "durationSec": duration, "cueCount": len(cues),
            "captions": ["captions.json", "captions.srt", "captions.vtt"], "transcript": "transcript.json",
            "reviewRequired": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="Final MP4 or audio file")
    parser.add_argument("--out", type=Path, required=True, help="Project directory for transcript and captions")
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    parser.add_argument("--model", choices=["tiny.en", "base.en", "small.en", "medium.en", "large-v3"],
                        help="Defaults to small.en for English or large-v3 for other languages")
    parser.add_argument("--language", help="Speech language code such as en, es, or ja")
    args = parser.parse_args()
    try:
        result = transcribe(args.media, args.out, args.runtime_dir, args.model, args.language)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
