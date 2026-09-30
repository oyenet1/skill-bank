#!/usr/bin/env python3
"""Validate avatar model pins; optionally verify digests against pinned sources."""
import argparse
import hashlib
import json
import re
import urllib.request
from network_tls import tls_context

from avatar_probe import manifest, progress


def validate(config: dict, online: bool = False) -> dict:
    verified = set()
    for backend in config["backends"] + config.get("disabledBackends", []):
        code = backend.get("code", {})
        if not re.fullmatch(r"[a-f0-9]{64}", code.get("sha256") or "") or code.get("bytes", 0) <= 0:
            raise ValueError(f"Invalid code archive pin: {backend['id']}")
        if backend in config["backends"] and backend["licenseClass"] == "research-only":
            raise ValueError("Research-only backends cannot be included in the active registry")
        for file in backend["files"]:
            if not re.fullmatch(r"[a-f0-9]{64}", file.get("sha256") or "") or file.get("bytes", 0) <= 0:
                raise ValueError(f"Invalid model pin: {backend['id']}/{file['name']}")
            key = (file["sourceRepo"], file["revision"], file["sourcePath"])
            if key in verified:
                continue
            if online:
                repo, revision, source = key
                url = f"https://huggingface.co/api/models/{repo}/paths-info/{revision}"
                request = urllib.request.Request(url, data=json.dumps({"paths": [source]}).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=60, context=tls_context()) as response:
                    rows = json.load(response)
                if len(rows) != 1 or rows[0]["size"] != file["bytes"]:
                    raise ValueError(f"Source size differs: {source}")
                digest = rows[0].get("lfs", {}).get("oid")
                if digest is None:
                    if file["bytes"] > 1_000_000:
                        raise ValueError(f"Large file has no published LFS digest: {source}")
                    with urllib.request.urlopen(file["url"], timeout=60, context=tls_context()) as response:
                        digest = hashlib.sha256(response.read()).hexdigest()
                if digest != file["sha256"]:
                    raise ValueError(f"Source digest differs: {source}")
            verified.add(key)
    return {"ready": True, "filesVerified": len(verified), "online": online}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()
    try:
        progress("verify", "Verifying avatar model manifest pins")
        result = validate(manifest(), args.online)
    except Exception as error:
        result = {"ready": False, "error": str(error)}
    print(json.dumps(result))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
