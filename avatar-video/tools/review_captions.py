#!/usr/bin/env python3
"""Load or save reviewed captions bound to a verified final video.

Saving exports JSON/SRT/VTT together, retains the original ASR transcript,
records the review in the manifest and job state, and keeps a revision backup.
Concurrent or stale edits are rejected. An interrupted write is recovered
before the next load/save, using a durable journal of the caption bundle.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import uuid

from run_video_job import fingerprint, state_path
from write_subtitles import render, validate


def digest(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(prefix="caption-", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def review_lock(project: Path):
    with (project / ".caption-review.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            if lock.tell() == 0:
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise RuntimeError("Another caption review is being saved") from None
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise RuntimeError("Another caption review is being saved") from None
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def bundle_paths(project: Path) -> dict[str, Path]:
    return {name: project / name for name in ("captions.json", "captions.srt", "captions.vtt", "manifest.json", "reviewed-transcript.txt")} | {"job-state.json": state_path(project)}


def recover(project: Path) -> None:
    journal_file = project / ".caption-review.pending.json"
    if not journal_file.is_file():
        return
    journal = json.loads(journal_file.read_text(encoding="utf-8"))
    paths = bundle_paths(project)
    if not isinstance(journal, dict) or set(journal) != set(paths):
        raise ValueError("Caption review recovery journal is invalid")
    previous = {}
    finished = True
    for name, path in paths.items():
        entry = journal[name]
        previous[name] = base64.b64decode(entry["before"], validate=True) if entry["before"] is not None else None
        current = path.read_bytes() if path.exists() else None
        current_sha = digest(current)
        if current_sha not in (digest(previous[name]), entry["afterSha256"]):
            raise ValueError("Caption recovery found an external edit; preserve the pending journal for recovery")
        finished = finished and current_sha == entry["afterSha256"]
    if not finished:
        for name, path in paths.items():
            if previous[name] is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous[name])
    journal_file.unlink()


def verified_project(project: Path) -> tuple[dict, dict]:
    state = json.loads(state_path(project).read_text(encoding="utf-8"))
    manifest = json.loads((project / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(state, dict) or not isinstance(manifest, dict) or manifest.get("status") != "complete":
        raise ValueError("Caption review needs a verified video project")
    expected = state.get("videoSha256")
    if not expected or fingerprint(project / "video.mp4") != expected:
        raise ValueError("The final video changed; regenerate caption timing before reviewing it")
    duration = state.get("durationSec")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("The verified project has no measured duration")
    return state, manifest


def load_review(project: Path) -> dict:
    project = project.resolve()
    with review_lock(project):
        recover(project)
        state, _ = verified_project(project)
        captions = json.loads((project / "captions.json").read_text(encoding="utf-8"))
        if not isinstance(captions, dict) or not isinstance(captions.get("cues"), list):
            raise ValueError("Project captions are invalid")
        if captions["cues"]:
            validate({"duration_sec": state["durationSec"], "cues": captions["cues"]})
        return {**captions, "duration_sec": state["durationSec"], "videoSha256": state["videoSha256"],
                "captionSha256": fingerprint(project / "captions.json"),
                "review_required": bool(state.get("reviewRequired"))}


def save_review(project: Path, edits: dict, expected_caption_sha: str) -> dict:
    project = project.resolve()
    with review_lock(project):
        recover(project)
        state, manifest = verified_project(project)
        if fingerprint(project / "captions.json") != expected_caption_sha:
            raise ValueError("Captions changed since they were opened; reload before saving")
        if not isinstance(edits, dict) or edits.get("videoSha256") != state["videoSha256"]:
            raise ValueError("Caption edits belong to a different final video")
        duration = edits.get("duration_sec")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or abs(duration - state["durationSec"]) > 0.001:
            raise ValueError("Caption edits must keep the final video's measured duration")
        cues = edits.get("cues")
        if not isinstance(cues, list) or len(cues) > 20_000:
            raise ValueError("Caption edits need at most 20000 cues")
        normalized = []
        for index, cue in enumerate(cues, 1):
            if not isinstance(cue, dict) or not isinstance(cue.get("text"), str) or len(cue["text"]) > 1500:
                raise ValueError(f"Cue {index} needs text under 1500 characters")
            # Blank lines delimit subtitle blocks; retain actual line breaks only.
            words = "\n".join(line.strip() for line in cue["text"].replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip())
            normalized.append({"start": cue.get("start"), "end": cue.get("end"), "text": words})
        if normalized:
            validate({"duration_sec": duration, "cues": normalized})
        original = json.loads((project / "captions.json").read_text(encoding="utf-8"))
        reviewed_at = datetime.now(timezone.utc).isoformat()
        captions = {**original, "duration_sec": duration, "cues": normalized, "review_required": False,
                    "reviewed_at": reviewed_at, "video_sha256": state["videoSha256"]}
        caption_bytes = json_bytes(captions)
        manifest.update(reviewRequired=False, captionReview={"status": "reviewed", "reviewedAt": reviewed_at,
                        "videoSha256": state["videoSha256"], "captionSha256": digest(caption_bytes)},
                        reviewedTranscript="reviewed-transcript.txt")
        state.update(status="complete", phase="complete", reviewRequired=False, captionsReviewedAt=reviewed_at,
                     captionsSha256=digest(caption_bytes))
        changes = {"captions.json": caption_bytes,
                   "captions.srt": (render(normalized) if normalized else "").encode("utf-8"),
                   "captions.vtt": (render(normalized, webvtt=True) if normalized else "WEBVTT\n").encode("utf-8"),
                   "reviewed-transcript.txt": ("\n".join(cue["text"] for cue in normalized) + "\n").encode("utf-8"),
                   "manifest.json": json_bytes(manifest), "job-state.json": json_bytes(state)}
        paths = bundle_paths(project)
        revision = project / "reviews" / uuid.uuid4().hex
        revision.mkdir(parents=True)
        journal = {}
        for name, path in paths.items():
            before = path.read_bytes() if path.exists() else None
            if before is not None:
                (revision / name).write_bytes(before)
            journal[name] = {"before": base64.b64encode(before).decode("ascii") if before is not None else None,
                             "afterSha256": digest(changes[name])}
        journal_path = project / ".caption-review.pending.json"
        atomic_write(journal_path, json_bytes(journal))
        try:
            for name, path in paths.items():
                atomic_write(path, changes[name])
        except BaseException:
            recover(project)
            raise
        journal_path.unlink()
        return {"ready": True, "duration_sec": duration, "cues": normalized, "review_required": False,
                "videoSha256": state["videoSha256"], "captionSha256": digest(caption_bytes),
                "reviewedAt": reviewed_at, "reviewedTranscript": str(project / "reviewed-transcript.txt"),
                "backup": str(revision)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--edits", type=Path)
    parser.add_argument("--expected-caption-sha")
    args = parser.parse_args()
    try:
        if args.edits:
            if args.edits.stat().st_size > 10_000_000 or not args.expected_caption_sha:
                raise ValueError("Saving needs a draft under 10 MB and its expected caption hash")
            result = save_review(args.project, json.loads(args.edits.read_text(encoding="utf-8")), args.expected_caption_sha)
        else:
            result = {"ready": True, **load_review(args.project)}
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
