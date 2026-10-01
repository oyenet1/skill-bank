#!/usr/bin/env python3
"""Managed local speech recognition with downloaded binary Python packages."""
from __future__ import annotations

import argparse
import json
from importlib.metadata import version
import os
from pathlib import Path
import sys
import threading


def progress(message: str, **details: object) -> None:
    print(json.dumps({"phase": "transcribe", "message": message, **details}), file=sys.stderr, flush=True)


def transcribe(media: Path | None, output: Path, models: Path, model_name: str, language: str | None, *, check: bool = False) -> dict:
    import ctranslate2
    from faster_whisper import WhisperModel
    supported = ctranslate2.get_supported_compute_types("cpu")
    compute = "int8" if "int8" in supported else "float32"
    threads = max(1, min(8, os.cpu_count() or 1))
    progress(f"Preparing local {model_name} speech model", computeType=compute, cpuThreads=threads)
    if not check:
        models.mkdir(parents=True, exist_ok=True)
    finished = threading.Event()

    def report_cache() -> None:
        while not finished.wait(10):
            cached = 0
            for path in models.rglob("*"):
                try:
                    if path.is_file() and not path.is_symlink():
                        cached += path.stat().st_size
                except OSError:
                    pass
            progress(f"Preparing speech model · {cached / 1048576:.1f} MB cached", cachedBytes=cached)

    watcher = threading.Thread(target=report_cache, daemon=True)
    watcher.start()
    try:
        model = WhisperModel(model_name, device="cpu", compute_type=compute, cpu_threads=threads,
                             download_root=str(models), local_files_only=check)
    finally:
        finished.set()
        watcher.join(timeout=1)
    if media is None:
        return {"ok": True, "ready": True, "engine": "faster-whisper", "model": model_name,
                "pythonExecutable": sys.executable,
                "packages": {name: version(name) for name in ("faster-whisper", "ctranslate2", "av")}}
    progress("Recognizing speech with measured word timing")
    segments, info = model.transcribe(str(media), language=language, task="transcribe", word_timestamps=True,
                                     vad_filter=True, beam_size=5)
    words = []
    for segment in segments:
        for word in segment.words or []:
            value = word.word.strip()
            if value and word.end > word.start:
                words.append({"text": value, "start": word.start, "end": word.end})
        progress("Recognized speech segment", endSec=segment.end, detectedLanguage=info.language)
    if not words:
        raise ValueError("No spoken words were recognized; check the media and language")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(words, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "engine": "faster-whisper", "model": model_name, "language": info.language,
            "transcriptPath": str(output.resolve()), "wordCount": len(words)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, nargs="?")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--language")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = transcribe(args.media, args.out, args.models, args.model, args.language, check=args.check)
    except Exception as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
