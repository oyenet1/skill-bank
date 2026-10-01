#!/usr/bin/env python3
"""Install a private Node/video toolchain for Slidev, Remotion and HyperFrames skills.

Usage: python3 tools/ensure_video_runtime.py explainer-video [--check]
The final stdout line is JSON. Progress and install logs go to stderr.
This tool does not modify PATH, shell profiles, or global npm packages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from network_tls import tls_context
import zipfile


MANIFEST = json.loads((Path(__file__).with_name("runtime_requirements.json")).read_text())
NODE_INDEX = "https://nodejs.org/dist/index.json"


def progress(phase: str, message: str, **details: object) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def default_runtime_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    elif platform.system() == "Darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return base / "skill-bank" / "video-runtime"


def platform_archive(version: str, system: str | None = None, machine: str | None = None) -> str:
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    arch = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    if not arch or system not in ("Linux", "Darwin", "Windows"):
        raise RuntimeError(f"No managed Node binary for {system}/{machine}")
    os_tag = {"Linux": "linux", "Darwin": "darwin", "Windows": "win"}[system]
    extension = ".zip" if system == "Windows" else ".tar.xz"
    return f"node-{version}-{os_tag}-{arch}{extension}"


def parse_version(value: str) -> tuple[int, int, int]:
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"Could not parse version: {value!r}")
    return tuple(int(piece) for piece in match.groups())


def command_version(binary: Path | str) -> str | None:
    try:
        result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=20)
        return (result.stdout or result.stderr).strip().splitlines()[0] if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


def media_version(binary: Path | str) -> str | None:
    try:
        result = subprocess.run([str(binary), "-version"], capture_output=True, text=True, timeout=20)
        return (result.stdout or result.stderr).strip().splitlines()[0] if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


def tool_command(command: list[str | Path], node: Path) -> list[str]:
    """Resolve npm batch wrappers to Node entry points without invoking a shell."""
    args = [str(value) for value in command]
    binary = Path(args[0])
    if platform.system() != "Windows" or binary.suffix.lower() != ".cmd":
        return args
    name = binary.stem
    packages = {"slidev": "@slidev/cli", "remotion": "@remotion/cli",
                "hyperframes": "hyperframes", "playwright": "playwright-chromium"}
    if name == "npm":
        package = binary.parent / "node_modules/npm"
    elif name in packages:
        package = binary.parent.parent / packages[name]
    else:
        raise RuntimeError(f"Unsupported Windows video tool: {name}")
    metadata = json.loads((package / "package.json").read_text(encoding="utf-8"))
    declared = metadata.get("bin")
    entry = declared if isinstance(declared, str) else declared.get(name) if isinstance(declared, dict) else None
    if not isinstance(entry, str) or not (package / entry).is_file():
        raise RuntimeError(f"Missing {name} JavaScript entry point")
    return [str(node), str(package / entry), *args[1:]]


def cli_ready(binary: Path, ready_args: list[str], node: Path, profile: Path) -> bool:
    try:
        arguments = tool_command([binary, *ready_args], node)
        return subprocess.run(arguments, cwd=profile, capture_output=True, text=True, timeout=30, env=environment(node)).returncode == 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return False


def node_paths(root: Path) -> tuple[Path, Path]:
    if platform.system() == "Windows":
        return root / "node.exe", root / "npm.cmd"
    return root / "bin/node", root / "bin/npm"


def suitable_node(node: Path | str | None, npm: Path | str | None) -> bool:
    if not node or not npm:
        return False
    version = command_version(node)
    return bool(version and parse_version(version) >= parse_version(MANIFEST["minimumNode"]) and Path(npm).is_file())


def extract_node_archive(archive: Path, destination: Path) -> None:
    """Reject archive members that could escape the private install directory."""
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise RuntimeError("Node archive contains an unsafe path")
            bundle.extractall(destination)
    else:
        with tarfile.open(archive, "r:xz") as bundle:
            for member in bundle.getmembers():
                target = (destination / member.name).resolve()
                if not target.is_relative_to(destination.resolve()) or not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise RuntimeError("Node archive contains an unsafe member")
                if member.issym() or member.islnk():
                    link = (target.parent / member.linkname).resolve() if member.issym() else (destination / member.linkname).resolve()
                    if not link.is_relative_to(destination.resolve()):
                        raise RuntimeError("Node archive contains an unsafe link")
            bundle.extractall(destination)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": "skill-bank-runtime/1"})
    with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "skill-bank-runtime/1"})
    with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response:
        return response.read().decode("utf-8")


def download_verified(url: str, target: Path, sha256: str) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "skill-bank-runtime/1"})
    digest = hashlib.sha256()
    received = 0
    with urllib.request.urlopen(request, timeout=60, context=tls_context()) as response, target.open("wb") as output:
        total = int(response.headers.get("Content-Length") or 0)
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
            received += len(chunk)
            if total and (received == total or received % (16 * 1024 * 1024) < len(chunk)):
                progress("node-download", "Downloading managed Node", downloadedBytes=received, totalBytes=total)
    if digest.hexdigest() != sha256:
        raise RuntimeError("Node archive failed SHA-256 verification")


def node_release() -> tuple[str, str, str]:
    releases = fetch_json(NODE_INDEX)
    if not isinstance(releases, list):
        raise RuntimeError("Node release index has an invalid format")
    release = next((item for item in releases if isinstance(item, dict) and item.get("lts")), None)
    if not release:
        raise RuntimeError("No Node LTS release found")
    version = release["version"]
    archive = platform_archive(version)
    shasums = fetch_text(f"https://nodejs.org/dist/{version}/SHASUMS256.txt")
    sha256 = next((line.split()[0] for line in shasums.splitlines() if line.split()[1:] == [archive]), None)
    if not sha256:
        raise RuntimeError(f"Node release {version} has no checksum for {archive}")
    return version, archive, sha256


def install_node(runtime: Path) -> tuple[Path, Path]:
    version, archive, sha256 = node_release()
    if parse_version(version) < parse_version(MANIFEST["minimumNode"]):
        raise RuntimeError(f"Latest Node LTS {version} is older than the required version")
    target = runtime / "node" / version
    node, npm = node_paths(target)
    if suitable_node(node, npm):
        return node, npm
    progress("node", f"Installing Node {version} into {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="node-install-", dir=target.parent) as scratch:
        scratch_dir = Path(scratch)
        downloaded = scratch_dir / archive
        download_verified(f"https://nodejs.org/dist/{version}/{archive}", downloaded, sha256)
        extracted = scratch_dir / "unpacked"
        extracted.mkdir()
        extract_node_archive(downloaded, extracted)
        folder = extracted / archive.removesuffix(".zip").removesuffix(".tar.xz")
        if not folder.is_dir():
            raise RuntimeError("Node archive has an unexpected layout")
        test_node, test_npm = node_paths(folder)
        if not suitable_node(test_node, test_npm):
            raise RuntimeError("Downloaded Node or npm did not verify")
        if target.exists():
            shutil.rmtree(target)
        folder.rename(target)
    return node_paths(target)


def resolve_node(runtime: Path, ensure: bool) -> tuple[Path, Path] | None:
    system_node, system_npm = shutil.which("node"), shutil.which("npm")
    if suitable_node(system_node, system_npm):
        progress("node", f"Using Node {command_version(system_node)} from PATH")
        return Path(system_node), Path(system_npm)
    managed_dir = runtime / "node"
    for folder in sorted(managed_dir.glob("v*"), reverse=True) if managed_dir.exists() else []:
        node, npm = node_paths(folder)
        if suitable_node(node, npm):
            progress("node", f"Using managed Node {command_version(node)}")
            return node, npm
    return install_node(runtime) if ensure else None


def environment(node: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(node.parent) + os.pathsep + env.get("PATH", "")
    return env


def run(command: list[str | Path], node: Path, *, cwd: Path | None = None) -> str:
    args = tool_command(command, node)
    progress("command", "Running " + " ".join(args[:3]))
    started = time.monotonic()
    process = subprocess.Popen(args, cwd=cwd, env=environment(node), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=15)
                break
            except subprocess.TimeoutExpired:
                progress("command", "Still running " + " ".join(args[:3]), elapsedSeconds=round(time.monotonic() - started))
    except KeyboardInterrupt:
        process.kill()
        process.communicate()
        raise
    if process.returncode:
        raise RuntimeError(f"{' '.join(args[:3])} failed: {(stderr or stdout)[-3000:]}")
    return stdout.strip()


def package_file(profile: Path, packages: dict[str, str]) -> Path:
    return profile / "package.json"


def install_profile(name: str, spec: dict, runtime: Path, node: Path, npm: Path, ensure: bool) -> Path | None:
    packages, binary_name = spec["packages"], spec["binary"]
    ready_args = spec.get("readyArgs", ["--version"])
    profile = runtime / name
    binary = profile / "node_modules" / ".bin" / (binary_name + (".cmd" if platform.system() == "Windows" else ""))
    wanted = {"private": True, "name": f"skill-bank-{name}", "version": "1.0.0", "dependencies": packages}
    try:
        current = json.loads(package_file(profile, packages).read_text()) if package_file(profile, packages).is_file() else None
    except (OSError, ValueError):
        current = None
    if binary.is_file() and current == wanted and cli_ready(binary, ready_args, node, profile):
        return binary
    if not ensure:
        return None
    profile.mkdir(parents=True, exist_ok=True)
    if current != wanted:
        (profile / ".browser-ready").unlink(missing_ok=True)
    package_file(profile, packages).write_text(json.dumps(wanted, indent=2) + "\n")
    progress(name, f"Installing {name} packages into {profile}")
    run([npm, "install", "--prefix", profile, "--no-audit", "--no-fund"], node)
    if not binary.is_file() or not cli_ready(binary, ready_args, node, profile):
        raise RuntimeError(f"{name} install finished without {binary_name}")
    return binary


def resolve_media(runtime: Path, node: Path, npm: Path, ensure: bool) -> tuple[Path, Path] | None:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ffmpeg and ffprobe and media_version(ffmpeg) and media_version(ffprobe):
        return Path(ffmpeg), Path(ffprobe)
    packages = MANIFEST["mediaPackages"]
    profile = runtime / "media"
    marker = profile / "package.json"
    wanted = {"private": True, "name": "skill-bank-media", "version": "1.0.0", "dependencies": packages}
    try:
        current = json.loads(marker.read_text()) if marker.is_file() else None
    except (OSError, ValueError):
        current = None
    if current != wanted or not (profile / "node_modules" / "ffmpeg-static").is_dir() or not (profile / "node_modules" / "@derhuerst" / "ffprobe-static").is_dir():
        if not ensure:
            return None
        profile.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps(wanted, indent=2) + "\n")
        progress("media", "Installing managed FFmpeg and FFprobe")
        run([npm, "install", "--prefix", profile, "--no-audit", "--no-fund"], node)
    try:
        output = run([node, "-e", "const f=require('ffmpeg-static'); const p=require('@derhuerst/ffprobe-static').path; console.log(JSON.stringify([f,p]))"], node, cwd=profile)
        paths = tuple(Path(item) for item in json.loads(output))
        return paths if len(paths) == 2 and all(media_version(path) for path in paths) else None
    except (OSError, ValueError, RuntimeError):
        if ensure:
            raise
        return None


def browser_ready(profile: Path, node: Path) -> bool:
    try:
        output = run([node, "-e", "console.log(require('playwright-chromium').chromium.executablePath())"], node, cwd=profile)
        return Path(output).is_file()
    except (OSError, RuntimeError):
        return False


def renderer_browser_ready(name: str, binary: Path, node: Path, profile: Path) -> bool:
    """Check a renderer's browser without downloading or trusting a marker."""
    try:
        if name == "remotion":
            script = (
                "const {ensureBrowser}=require('@remotion/renderer');"
                "ensureBrowser({logLevel:'error',onBrowserDownload:()=>{throw Error('browser missing')}})"
                ".then(()=>process.stdout.write('ready')).catch(()=>process.exit(1))"
            )
            result = subprocess.run([str(node), "-e", script], cwd=profile, env=environment(node),
                                    capture_output=True, text=True, timeout=30)
            return result.returncode == 0 and result.stdout.strip() == "ready"
        if name == "hyperframes":
            result = subprocess.run(tool_command([binary, "browser", "path"], node), cwd=profile, env=environment(node),
                                    capture_output=True, text=True, timeout=30)
            path = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
            return result.returncode == 0 and bool(path) and Path(path).is_file()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return False
    raise ValueError(f"Unknown renderer browser: {name}")


def ensure_profiles(route: str, runtime: Path, node: Path, npm: Path, ensure: bool, only: str | None = None) -> tuple[dict[str, str], list[str]]:
    paths: dict[str, str] = {}
    missing: list[str] = []
    names = MANIFEST["routes"][route]
    if only:
        if only not in names:
            raise RuntimeError(f"Renderer {only!r} is not available for route {route!r}")
        names = [only]
    for name in names:
        spec = MANIFEST["profiles"][name]
        binary = install_profile(name, spec, runtime, node, npm, ensure)
        if not binary:
            missing.append(name)
            continue
        paths[name] = str(binary)
        profile = runtime / name
        if name == "slidev" and not browser_ready(profile, node):
            if ensure:
                progress("browser", "Installing Chromium for Slidev export")
                playwright = profile / "node_modules" / ".bin" / ("playwright.cmd" if platform.system() == "Windows" else "playwright")
                run([playwright, "install", "chromium"], node, cwd=profile)
            if not browser_ready(profile, node):
                missing.append("slidev-browser")
        if name in ("remotion", "hyperframes"):
            ready = renderer_browser_ready(name, binary, node, profile)
            if not ready and ensure:
                progress("browser", f"Ensuring {name} browser")
                run([binary, "browser", "ensure"], node, cwd=profile)
                ready = renderer_browser_ready(name, binary, node, profile)
            if ensure:
                if ready:
                    (profile / ".browser-ready").write_text(f"verified {name} browser path\n")
                else:
                    (profile / ".browser-ready").unlink(missing_ok=True)
            if not ready:
                missing.append(f"{name}-browser")
    return paths, missing


def setup(route: str, runtime: Path, ensure: bool, only: str | None = None) -> dict[str, object]:
    if route not in MANIFEST["routes"]:
        raise RuntimeError(f"Unknown video route: {route}")
    missing: list[str] = []
    paths: dict[str, str] = {}
    selected = resolve_node(runtime, ensure)
    if not selected:
        missing.append("node")
        return {"ready": False, "route": route, "paths": paths, "missing": missing}
    node, npm = selected
    paths.update(node=str(node), npm=str(npm))
    media = resolve_media(runtime, node, npm, ensure)
    if media:
        paths.update(ffmpeg=str(media[0]), ffprobe=str(media[1]))
    else:
        missing.extend(("ffmpeg", "ffprobe"))
    profiles, profile_missing = ensure_profiles(route, runtime, node, npm, ensure, only)
    paths.update(profiles)
    missing.extend(profile_missing)
    return {"ready": not missing, "route": route, "paths": paths, "missing": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route", choices=MANIFEST["routes"])
    parser.add_argument("--check", action="store_true", help="Read only; report missing prerequisites")
    parser.add_argument("--renderer", help="Install and verify only this renderer profile")
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    args = parser.parse_args()
    try:
        result = setup(args.route, args.runtime_dir, ensure=not args.check, only=args.renderer)
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        result = {"ready": False, "route": args.route, "paths": {}, "missing": [], "error": str(error)}
    print(json.dumps(result, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
