#!/usr/bin/env python3
"""Export SRT and WebVTT from measured, absolute-time caption cues.

Input JSON: {"duration_sec": 12.4, "cues": [
  {"start": 0.2, "end": 2.1, "text": "Hello world"}
]}
Times are seconds on the final video timeline. Make cues from final audio or
reviewed scene timing; this tool never guesses speech alignment.
"""

import argparse
import json
import math
from pathlib import Path


def stamp(seconds, separator):
    milliseconds = round(seconds * 1000)
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{millis:03}"


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("cues"), list):
        raise ValueError("input must contain a cues array")
    duration = data.get("duration_sec")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration_sec must be a positive finite number")
    previous_end = 0.0
    for index, cue in enumerate(data["cues"], 1):
        if not isinstance(cue, dict):
            raise ValueError(f"cue {index} must be an object")
        start, end, words = cue.get("start"), cue.get("end"), cue.get("text")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (start, end)):
            raise ValueError(f"cue {index} needs finite numeric start and end")
        if start < 0 or start < previous_end - 0.0005 or end <= start:
            raise ValueError(f"cue {index} overlaps the previous cue or has invalid timing")
        if round(end * 1000) <= round(start * 1000):
            raise ValueError(f"cue {index} is shorter than subtitle timestamp precision")
        if end > duration + 0.0005:
            raise ValueError(f"cue {index} ends after duration_sec")
        if not isinstance(words, str) or not words.strip():
            raise ValueError(f"cue {index} needs nonempty text")
        if "-->" in words or "\x00" in words:
            raise ValueError(f"cue {index} has invalid subtitle text")
        previous_end = end
    if not data["cues"]:
        raise ValueError("cues must not be empty")
    return data["cues"]


def render(cues, webvtt=False):
    sep = "." if webvtt else ","
    blocks = []
    for index, cue in enumerate(cues, 1):
        timing = f"{stamp(cue['start'], sep)} --> {stamp(cue['end'], sep)}"
        body = cue["text"].strip().replace("\r\n", "\n").replace("\r", "\n")
        blocks.append(f"{timing}\n{body}" if webvtt else f"{index}\n{timing}\n{body}")
    return ("WEBVTT\n\n" if webvtt else "") + "\n\n".join(blocks) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cues_json", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Output stem or .srt/.vtt path")
    args = parser.parse_args()
    try:
        cues = validate(json.loads(args.cues_json.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    stem = args.out.with_suffix("") if args.out.suffix.lower() in (".srt", ".vtt") else args.out
    stem.parent.mkdir(parents=True, exist_ok=True)
    for suffix, webvtt in ((".srt", False), (".vtt", True)):
        target = stem.with_suffix(suffix)
        target.write_text(render(cues, webvtt), encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
