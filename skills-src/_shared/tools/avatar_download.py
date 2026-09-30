#!/usr/bin/env python3
"""Resumable, size- and SHA-256-verified local avatar model downloads."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re
import urllib.request
from network_tls import tls_context

from avatar_probe import progress


def verified(path: Path, file: dict) -> bool:
    if not path.is_file() or path.stat().st_size != file["bytes"]:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == file["sha256"]


def destination(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or not relative.parts:
        raise ValueError("Avatar model filename is invalid")
    target = root.joinpath(*relative.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Avatar model filename escapes its runtime")
    return target


def download(root: Path, file: dict) -> Path:
    if not isinstance(file.get("bytes"), int) or file["bytes"] <= 0 or not re.fullmatch(r"[a-f0-9]{64}", file.get("sha256") or ""):
        raise ValueError("Avatar model lacks a valid size and SHA-256 pin")
    target = destination(root, file["name"])
    if verified(target, file):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    if not partial.resolve().is_relative_to(root.resolve()):
        raise ValueError("Avatar partial download escapes its runtime")
    offset = partial.stat().st_size if partial.is_file() else 0
    if offset == file["bytes"] and verified(partial, file):
        partial.replace(target)
        return target
    if offset >= file["bytes"]:
        offset = 0
    request = urllib.request.Request(file["url"], headers={"Range": f"bytes={offset}-"} if offset else {})
    progress("download", f"Downloading {file['name']}", downloadedBytes=offset, totalBytes=file["bytes"])
    with urllib.request.urlopen(request, timeout=60, context=tls_context()) as response:
        status = response.status
        if status == 206:
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
            if not match or int(match[1]) != offset or int(match[3]) != file["bytes"]:
                raise ValueError("Avatar download returned an invalid resume range")
        elif status == 200:
            offset = 0
        else:
            raise ValueError(f"Avatar download returned HTTP {status}")
        mode = "ab" if offset else "wb"
        count = offset
        with partial.open(mode) as output:
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > file["bytes"]:
                    raise ValueError("Avatar model download exceeds its pinned size")
                output.write(chunk)
                progress("download", f"Downloading {file['name']}", downloadedBytes=count, totalBytes=file["bytes"])
    progress("verify", f"Verifying {file['name']}")
    if not verified(partial, file):
        raise ValueError(f"Avatar model size/SHA-256 mismatch: {file['name']}; partial kept for retry")
    partial.replace(target)
    return target
