#!/usr/bin/env python3
"""Package selected, verified Fontsource fonts with editable scene source."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import urllib.request
from network_tls import tls_context

from ensure_video_runtime import MANIFEST, progress


def family(value: object) -> str:
    if value is None or value == "system-ui":
        return "system-ui"
    if not isinstance(value, str) or value not in MANIFEST["fonts"]:
        raise ValueError("Choose a supported desktop font")
    return value


def archive(spec: dict, runtime: Path) -> Path:
    cache = runtime / "fonts"
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{spec['slug']}-{spec['version']}.tgz"
    expected = spec["integrity"].removeprefix("sha512-")

    def verified(path: Path) -> bool:
        return path.is_file() and base64.b64encode(hashlib.sha512(path.read_bytes()).digest()).decode() == expected

    if verified(target):
        return target
    progress("fonts", f"Downloading local {spec['slug']} font files")
    with tempfile.NamedTemporaryFile(prefix="font-", dir=cache, delete=False) as output:
        temporary = Path(output.name)
        try:
            with urllib.request.urlopen(spec["url"], timeout=60, context=tls_context()) as source:
                total = 0
                while chunk := source.read(1024 * 1024):
                    total += len(chunk)
                    if total > 25_000_000:
                        raise ValueError("Font download exceeds its size limit")
                    output.write(chunk)
            output.flush()
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        if not verified(temporary):
            raise ValueError("Font download integrity check failed")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def package_fonts(folder: Path, runtime: Path, renderer: str) -> None:
    scene = json.loads((folder / "scene.json").read_text(encoding="utf-8"))
    families = sorted({family(scene.get(key)) for key in ("headlineFont", "bodyFont")} - {"system-ui"})
    css = []
    records = []
    for name in families:
        spec = MANIFEST["fonts"][name]
        destination = folder / "public/fonts" / spec["slug"]
        destination.mkdir(parents=True, exist_ok=True)
        # Only extract regular CSS, font, metadata and licence files. Never
        # trust archive paths or symlinks, including with older Python versions.
        with tarfile.open(archive(spec, runtime), "r:gz") as bundle:
            for member in bundle:
                path = PurePosixPath(member.name)
                if not member.isfile() or path.parts[:1] != ("package",) or ".." in path.parts:
                    continue
                relative = PurePosixPath(*path.parts[1:])
                if not (relative.suffix in (".woff", ".woff2") or str(relative) in ("400.css", "600.css", "700.css", "metadata.json", "LICENSE")):
                    continue
                if member.size > 10_000_000:
                    raise ValueError("Font archive member exceeds its size limit")
                target = destination.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        if not (destination / "LICENSE").is_file() or not (destination / "400.css").is_file():
            raise ValueError(f"Font package is incomplete: {name}")
        for weight in (400, 600, 700):
            source = destination / f"{weight}.css"
            if not source.is_file():
                continue  # Single-weight faces such as Bebas Neue use browser synthesis.
            content = source.read_text(encoding="utf-8")
            urls = re.findall(r"url\((?:['\"])?(\./files/[^)'\"]+)", content)
            if not urls or any(not (destination / url).is_file() for url in urls):
                raise ValueError(f"Font package has missing font files: {name}")
            prefix = f"./public/fonts/{spec['slug']}/files/" if renderer == "remotion" else f"./fonts/{spec['slug']}/files/"
            css.append(content.replace("./files/", prefix).replace("font-display: swap", "font-display: block"))
        records.append({"family": name, **spec, "license": f"public/fonts/{spec['slug']}/LICENSE"})
    stylesheet = folder / "fonts.css" if renderer == "remotion" else folder / "public/fonts.css"
    stylesheet.write_text("\n".join(css), encoding="utf-8")
    (folder / "fonts.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
