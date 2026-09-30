#!/usr/bin/env python3
"""Prepare a compatible local presenter only after explicit model consent."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import tarfile
import tempfile

from avatar_download import download
from avatar_probe import compatible, manifest, probe, progress
from avatar_runtime import environment, fingerprint, interrupted, paths, run, runtime_dir, status
from ensure_python_runtime import ensure_uv


def consent_payload(capability: dict, candidates: list[dict]) -> dict:
    return {"phase": "consent-required", "message": "Choose and accept a local presenter model before installation",
            "accelerator": capability["accelerator"], "candidates": [
                {**{key: row[key] for key in ("id", "displayName", "qualityTier", "license", "licenseClass", "componentLicenses", "downloadBytes", "diskBytes", "recommendedMaxSeconds", "estimatedSecondsPerSecond")},
                 "consentToken": fingerprint(row), "dependencyDownloads": "Private Python and inference packages are additional downloads within the disk allowance",
                 "installCommand": f"python3 tools/avatar_ensure.py avatar-video --backend {row['id']} --accept" + (" --allow-restricted" if row["licenseClass"] == "restricted" else "")}
                for row in candidates]}


def extract_source(archive: Path, destination: Path) -> dict:
    hashes = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle:
            relative = PurePosixPath(member.name)
            if not member.isfile():
                continue
            if relative.is_absolute() or ".." in relative.parts or len(relative.parts) < 2:
                raise ValueError("Avatar source archive contains an unsafe filename")
            name = PurePosixPath(*relative.parts[1:])
            if "\\" in str(name) or ":" in str(name) or member.size > 150_000_000:
                raise ValueError("Avatar source archive contains an unsupported file")
            target = destination.joinpath(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            hashes[str(name)] = hashlib.sha256(target.read_bytes()).hexdigest()
    if not hashes:
        raise ValueError("Avatar source archive is empty")
    return hashes


def prepare_environment(root: Path, backend: dict, kind: str, location: dict) -> None:
    env = environment(root)
    progress("uv", "Preparing private Python manager")
    minimum = tuple(map(int, backend["environment"]["uvMinimumVersion"].split(".")))
    uv = ensure_uv(root, minimum_version=minimum,
                   runner=lambda command, install_env: run(command, location["base"] / "uv.log", install_env, phase="uv"))
    marker = location["base"] / "requirements.sha256"
    wanted = fingerprint({"python": backend["pythonVersion"], "environment": backend["environment"], "accelerator": kind})
    if location["python"].is_file() and marker.is_file() and marker.read_text().strip() == wanted:
        return
    progress("python", f"Preparing private Python {backend['pythonVersion']}")
    run([str(uv), "venv", "--python", backend["pythonVersion"], str(location["venv"])], location["base"] / "python.log", env)
    spec = backend["environment"]
    torch = spec["torch"][kind]
    command = [str(uv), "pip", "install", "--python", str(location["python"]), "--only-binary", ":all:", *torch["packages"]]
    if torch.get("index"):
        command.extend(["--index-url", torch["index"]])
    progress("packages", "Installing accelerator-compatible inference packages")
    run(command, location["base"] / "torch.log", env)
    requirements = location["base"] / "requirements.txt"
    requirements.write_text("\n".join([*torch["packages"], *[f"{name}=={version}" for name, version in spec["packages"].items()]]) + "\n", encoding="utf-8")
    command = [str(uv), "pip", "install", "--python", str(location["python"]), "--only-binary", ":all:", "--constraints", str(requirements),
               *[f"{name}=={version}" for name, version in spec["packages"].items()]]
    if spec.get("allowSourcePackages"):
        command.extend(["--no-binary", ",".join(spec["allowSourcePackages"])])
    for url in spec.get("findLinks", []):
        command.extend(["--find-links", url])
    if spec.get("extraBuildDependencies"):
        settings = location["base"] / "uv.toml"
        settings.write_text("[extra-build-dependencies]\n" + "\n".join(f"{json.dumps(name)} = {json.dumps(values)}" for name, values in spec["extraBuildDependencies"].items()) + "\n", encoding="utf-8")
        command.extend(["--config-file", str(settings)])
        env.pop("UV_NO_CONFIG", None)
    run(command, location["base"] / "packages.log", env)
    imports = "; ".join("import " + name for name in spec["imports"])
    run([str(location["python"]), "-c", imports], location["base"] / "imports.log", env, phase="verify")
    run([str(uv), "pip", "freeze", "--python", str(location["python"])], location["base"] / "installed-requirements.txt", env)
    device = "cuda:0" if kind == "cuda" else "mps"
    check_device = f"import torch; x=torch.ones(1, device={device!r}); assert x.cpu().item() == 1"
    run([str(location["python"]), "-c", check_device], location["base"] / "device.log", env, phase="verify")
    marker.write_text(wanted + "\n", encoding="utf-8")


def ensure(root: Path, backend_id: str | None = None, *, check: bool = False, accept: bool = False,
           allow_restricted: bool = False, consent_token: str | None = None) -> dict:
    config = manifest()
    capability = probe(config, allow_restricted=allow_restricted)
    candidates = compatible(config, capability["accelerator"]["kind"], capability["accelerator"]["memoryBytes"], allow_restricted=allow_restricted) if capability["eligible"] else []
    results = [status(root, row) for row in candidates]
    selected = next((row for row in candidates if row["id"] == backend_id), None) if backend_id else next((row for row, report in zip(candidates, results) if report["ready"]), candidates[0] if candidates else None)
    base = {"ready": False, "route": "avatar-video", "backend": selected["id"] if selected else backend_id,
            "capability": capability, "installedBackends": [report["backend"] for report in results if report["ready"]],
            "paths": {}, "missing": [], "consent": consent_payload(capability, candidates)}
    if selected is None:
        return {**base, "reason": "incompatible-backend" if backend_id else capability["reason"],
                "error": "No compatible local presenter backend is available", "retryCommand": "python3 tools/avatar_probe.py"}
    current = status(root, selected)
    base.update(paths=current["paths"], missing=current["missing"], ready=current["ready"])
    if current["ready"] or check:
        return base
    if not accept:
        prompt = base["consent"]
        progress(prompt["phase"], prompt["message"], **{key: value for key, value in prompt.items() if key not in ("phase", "message")})
        return {**base, "reason": "consent-required", "consentRequired": True}
    if consent_token is not None and consent_token != fingerprint(selected):
        raise ValueError("The model manifest changed since consent was displayed; check and accept the current offer")
    parent = root
    while not parent.exists():
        parent = parent.parent
    if shutil.disk_usage(parent).free < selected["downloadBytes"] + selected["diskBytes"]:
        raise RuntimeError("Not enough free disk for the model downloads and private inference runtime")
    location = paths(root, selected)
    location["base"].mkdir(parents=True, exist_ok=True)
    consent = {"backend": selected["id"], "manifestHash": fingerprint(selected), "acceptedAt": datetime.now(timezone.utc).isoformat(),
               "license": selected["license"], "licenseClass": selected["licenseClass"], "componentLicenses": selected["componentLicenses"]}
    (location["base"] / "consent.json").write_text(json.dumps(consent, indent=2) + "\n", encoding="utf-8")
    progress("consent", "Model consent recorded", backend=selected["id"], downloadBytes=selected["downloadBytes"], diskBytes=selected["diskBytes"])
    prepare_environment(root, selected, capability["accelerator"]["kind"], location)
    archive = download(location["base"] / "downloads", selected["code"])
    with tempfile.TemporaryDirectory(prefix="source-", dir=location["base"]) as scratch:
        stage = Path(scratch) / "source"
        hashes = extract_source(archive, stage)
        if location["source"].exists():
            shutil.rmtree(location["source"])
        shutil.move(str(stage), location["source"])
    for file in selected["files"]:
        progress("model", f"Preparing {file['name']}")
        download(location["models"], file)
    from run_video_job import media_paths
    ffmpeg, ffprobe = media_paths(root / "media-runtime")
    state = {"manifestHash": fingerprint(selected), "sourceHashes": hashes, "accelerator": capability["accelerator"], "consent": consent,
             "mediaPaths": {"ffmpeg": str(ffmpeg), "ffprobe": str(ffprobe)}, "smokeVerified": not selected.get("requiresSmokeTest")}
    if selected.get("requiresSmokeTest"):
        from avatar_generate import smoke
        try:
            smoke(root, selected, state)
            state["smokeVerified"] = True
        except (OSError, ValueError, RuntimeError) as error:
            fallback = next((row for row in config["backends"] if row["id"] == selected.get("fallbackBackend")), None)
            progress("verify", "MPS inference check failed; compatibility backend is unavailable" if fallback is None else "MPS inference check failed; compatibility backend needs separate consent", error=str(error), fallbackBackend=fallback["id"] if fallback else None)
            return {**base, "reason": "inference-smoke-failed", "error": str(error), "fallbackBackend": fallback["id"] if fallback else None,
                    "fallbackReason": "Compatibility backend is unavailable pending a licensed Basel Face Model replacement" if fallback is None else "Separate model consent is required",
                    "missing": ["inference-smoke-check"]}
    location["state"].write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    progress("complete", "Local presenter backend prepared", backend=selected["id"])
    return {**base, "ready": True, "missing": [], "installedBackends": sorted(set(base["installedBackends"] + [selected["id"]]))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route", choices=["avatar-video"])
    parser.add_argument("--backend")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--accept", action="store_true", help="Explicit acceptance of the selected backend's model downloads and licences")
    parser.add_argument("--allow-restricted", action="store_true")
    parser.add_argument("--consent-token")
    parser.add_argument("--runtime-dir", type=Path, default=runtime_dir())
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        result = ensure(args.runtime_dir.expanduser().resolve(), args.backend, check=args.check, accept=args.accept,
                        allow_restricted=args.allow_restricted, consent_token=args.consent_token)
    except KeyboardInterrupt:
        result = {"ready": False, "status": "cancelled", "error": "Local avatar setup cancelled; verified files are retained"}
    except Exception as error:
        result = {"ready": False, "route": args.route, "backend": args.backend, "error": str(error),
                  "retryCommand": f"python3 tools/avatar_ensure.py avatar-video --backend {args.backend or '<compatible-id>'} --accept"}
    print(json.dumps(result))
    return 0 if result.get("ready") or args.check or result.get("consentRequired") else 1


if __name__ == "__main__":
    raise SystemExit(main())
