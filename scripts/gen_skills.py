#!/usr/bin/env python3
"""Generate skill targets from skills-src/.

One source per capability emits two install targets:

  bundle      course-creator/subskills/<bundle>/SKILL.md
  standalone  <standalone>/SKILL.md

plus the shared intake modules each capability declares, into that target's
`references/` directory. Maintainer tool -- requires PyYAML.

Usage:
    python scripts/gen_skills.py           # write targets
    python scripts/gen_skills.py --check   # exit 1 if committed output is stale
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import zipfile
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "skills-src"
MANIFEST = SRC / "manifest.yaml"

MODE_BLOCK = re.compile(r"\{\{mode:(\w+)\}\}(.*?)\{\{/mode\}\}", re.S)
TOKEN = re.compile(r"\{\{(ref|doc|sibling|asset):([^}|]+?)(?:\|([^}]+))?\}\}")

# Tool trees are generated too, so the standalone install works alone.
TOOL_COPIES = [
    ("course-creator/tools/kokoro", "motion-graphics-video/tools/kokoro"),
    ("course-creator/tools/kokoro", "voice-narration/tools/kokoro"),
    ("course-creator/tools/kokoro", "explainer-video/tools/kokoro"),
    ("course-creator/tools/kokoro", "product-launch-video/tools/kokoro"),
    ("course-creator/tools/kokoro", "talking-head-video/tools/kokoro"),
    ("course-creator/tools/kokoro", "avatar-video/tools/kokoro"),
]
TOOL_IGNORE = {"models", ".venv", ".tooling", "__pycache__", "node_modules"}

# A capability with a `bootstrap:` manifest block ships these first-use files
# plus a generated tools/dependencies.json next to them.
BOOTSTRAP_TOOLS = ["bootstrap.py", "setup.sh", "setup.cmd", "setup.ps1", "uv_wheels.json", "install_sibling_skill.py"]
DEFAULT_SKILL_REPO = "oyenet1/agent-skills"


def dependencies_document(cap_id: str, spec: dict, mode: str) -> dict:
    boot = spec["bootstrap"]
    name = spec["standalone"] if mode == "standalone" else spec["bundle"]
    return {
        "schemaVersion": 1,
        "skill": name,
        "capability": cap_id,
        "repo": boot.get("repo", DEFAULT_SKILL_REPO),
        "routes": list(boot.get("routes", [])),
        # The course-creator bundle ships its siblings and prepares narration
        # through its own tools; only standalone targets own the full first-use
        # setup.
        "voice": bool(boot.get("voice", False)) and mode == "standalone",
        "transcription": bool(boot.get("transcription", False)),
        "associated": list(boot.get("associated", [])) if mode == "standalone" else [],
    }


def load_manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text())


def parse_skill(path: Path) -> tuple[dict, str]:
    """Split a skill.md into its YAML frontmatter dict and its body."""
    raw = path.read_text()
    if not raw.startswith("---"):
        raise SystemExit(f"{path}: missing frontmatter")
    _, fm, body = raw.split("---", 2)
    return yaml.safe_load(fm), body.strip("\n") + "\n"


def resolve_tokens(text: str, mode: str, caps: dict, modules: dict, depth: int = 0) -> str:
    """Resolve {{...}} tokens. depth=0 is SKILL.md; depth=1 is a file in references/."""

    def sub(m: re.Match) -> str:
        kind, key, label = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        if kind == "ref":
            fname = modules[key]
            prefix = "" if depth else "references/"
            return f"[{label or key}]({prefix}{fname})"
        if kind == "doc":
            # Parent reference docs ship only with the course-creator bundle.
            if mode == "standalone":
                return f"`{key}`"
            return f"[{label or key}](../../references/{key})"
        if kind == "sibling":
            other = caps[key]
            if mode == "bundle":
                return f"[{label or other['bundle']}](../{other['bundle']}/SKILL.md)"
            name = other.get("standalone") or other["bundle"]
            return f"`{name}`"
        if kind == "asset":
            prefix = "../" if depth else "../../"
            return f"{prefix}{key}" if mode == "bundle" else key
        raise SystemExit(f"unknown token {m.group(0)}")

    return TOKEN.sub(sub, text)


def render(skill_dir: Path, mode: str, fm: dict, body: str, caps: dict, modules: dict) -> str:
    if mode not in fm:
        raise SystemExit(f"{skill_dir}: frontmatter has no {mode!r} block")
    head = fm[mode]
    for mode_name, block in MODE_BLOCK.findall(body):
        body = body.replace(f"{{{{mode:{mode_name}}}}}{block}{{{{/mode}}}}", "")
        if mode_name == mode:
            body = body.rstrip("\n") + "\n\n" + block.strip("\n") + "\n"
    body = resolve_tokens(body, mode, caps, modules)
    return (
        "---\n"
        f"name: {head['name']}\n"
        f"description: {head['description'].strip()}\n"
        "---\n\n"
        f"{body.lstrip(chr(10))}"
    )


def build() -> dict[Path, str]:
    """Return {path: expected_content} for every generated file."""
    man = load_manifest()
    caps = man["capabilities"]
    modules = man["modules"]
    shared = SRC / man["shared_dir"]
    out: dict[Path, str] = {
        REPO / "course-creator/tools/kokoro" / name:
            (shared / "tools" / name).read_text()
        for name in ("network_tls.py", "bootstrap_uv.py", "uv_wheels.json")
    }

    for cap_id, spec in caps.items():
        skill_dir = SRC / cap_id
        fm, body = parse_skill(skill_dir / "skill.md")

        targets: list[tuple[str, Path]] = []
        if spec.get("bundle"):
            targets.append(("bundle", REPO / "course-creator" / "subskills" / spec["bundle"]))
        if spec.get("standalone"):
            targets.append(("standalone", REPO / spec["standalone"]))

        for mode, dest in targets:
            rendered = render(skill_dir, mode, fm, body, caps, modules)
            if spec.get("bootstrap"):
                prefix = "../../" if mode == "bundle" and spec["bootstrap"].get("voice") else ""
                setup = (
                    "\n## Automatic first-use setup\n\n"
                    "Before production, run the bundled launcher with `--yes`; it detects the host, "
                    "prepares private runtimes, and installs the declared sibling dependency graph. "
                    "Do not ask the requester to install packages manually.\n\n"
                    f"- Linux/macOS: `sh {prefix}tools/setup.sh --yes`\n"
                    f"- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File {prefix}tools/setup.ps1 --yes`\n\n"
                    "Use `--check` for a read-only readiness check. If prerequisites are missing, "
                    "rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. "
                    "Model-license acceptance, image rights and account credentials remain explicit inputs.\n"
                )
                rendered = re.sub(r"(^# [^\n]+\n)", lambda match: match.group(1) + setup, rendered, count=1, flags=re.M)
            out[dest / "SKILL.md"] = rendered
            for name in spec.get("modules", []):
                if name == "prompts":
                    continue
                fname = modules[name]
                raw = (shared / fname).read_text()
                out[dest / "references" / fname] = resolve_tokens(
                    raw, mode, caps, modules, depth=1
                )
            if "prompts" in spec.get("modules", []):
                for p in sorted((shared / "prompts").rglob("*.md")):
                    rel = p.relative_to(shared / "prompts")
                    out[dest / "references" / "prompts" / rel] = p.read_text()
            for rel in spec.get("ships", []):
                s = skill_dir / rel
                out[dest / Path(rel).relative_to("files")] = resolve_tokens(
                    s.read_text(), mode, caps, modules, depth=1
                )
            for rel in spec.get("shared_tools", []):
                s = shared / "tools" / rel
                out[dest / "tools" / rel] = s.read_text()
            if spec.get("bootstrap"):
                for rel in BOOTSTRAP_TOOLS:
                    out[dest / "tools" / rel] = (shared / "tools" / rel).read_text()
                out[dest / "tools" / "dependencies.json"] = (
                    json.dumps(dependencies_document(cap_id, spec, mode), indent=2) + "\n"
                )
            # Libraries ship verbatim -- they are source text, not templates.
            for name in spec.get("library", []):
                for p in sorted((shared / "library" / name).rglob("*")):
                    if p.is_file():
                        rel = p.relative_to(shared / "library" / name)
                        out[dest / "references" / "library" / name / rel] = p.read_text()
    # The installable course bundle also needs a first-use entry point.
    parent_boot = man.get("bundle_bootstrap")
    if parent_boot:
        parent = REPO / "course-creator/tools"
        for rel in BOOTSTRAP_TOOLS + ["ensure_video_runtime.py", "runtime_requirements.json",
                                     "ensure_python_runtime.py", "transcribe_with_faster_whisper.py",
                                     "network_tls.py", "bootstrap_uv.py"]:
            out[parent / rel] = (shared / "tools" / rel).read_text()
        out[parent / "dependencies.json"] = json.dumps({
            "schemaVersion": 1, "skill": "course-creator", "capability": "course-creator",
            "routes": parent_boot["routes"], "voice": parent_boot.get("voice", False),
            "transcription": parent_boot.get("transcription", False), "associated": []
        }, indent=2) + "\n"

    # Freeze one compact source snapshot before adding payloads, avoiding
    # recursive copies. Every installed sibling receives the same snapshot.
    standalone_names = {spec["standalone"] for spec in caps.values() if spec.get("standalone")}
    files = {str(path.relative_to(REPO)).replace("\\", "/"): content
             for path, content in out.items()
             if path.relative_to(REPO).parts[0] in standalone_names}
    for src_rel, dest_rel in TOOL_COPIES:
        src = REPO / src_rel
        for path in sorted(src.rglob("*")):
            relative = path.relative_to(src)
            if (not path.is_file() or any(part in TOOL_IGNORE for part in relative.parts)
                    or path.suffix in (".onnx", ".bin", ".pyc")):
                continue
            key = (Path(dest_rel) / relative).as_posix()
            # Shared helpers are emitted before the mirror copy is synchronized.
            canonical = out.get(path)
            files[key] = canonical if canonical is not None else path.read_text()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content.encode("utf-8"))
    snapshot = stream.getvalue()
    payload = json.dumps({"schemaVersion": 1, "skills": sorted(standalone_names),
                          "sha256": hashlib.sha256(snapshot).hexdigest(),
                          "zipBase64": base64.b64encode(snapshot).decode()}, separators=(",", ":")) + "\n"
    for spec in caps.values():
        if spec.get("bootstrap"):
            for target in (REPO / spec["standalone"], REPO / "course-creator/subskills" / spec["bundle"]):
                out[target / "tools/sibling_skills.json"] = payload
    if parent_boot:
        out[REPO / "course-creator/tools/sibling_skills.json"] = payload
    return out


def sync_tools() -> list[Path]:
    written = []
    for src_rel, dest_rel in TOOL_COPIES:
        src, dest = REPO / src_rel, REPO / dest_rel
        if dest.exists():
            shutil.rmtree(dest)

        def ignore(_dir: str, names: list[str]) -> set[str]:
            return {n for n in names if n in TOOL_IGNORE or n.endswith((".onnx", ".bin", ".pyc"))}

        shutil.copytree(src, dest, ignore=ignore)
        written.extend(p for p in dest.rglob("*") if p.is_file())
    return written


def check_tools() -> list[str]:
    bad = []
    for src_rel, dest_rel in TOOL_COPIES:
        for name in ("network_tls.py", "bootstrap_uv.py", "uv_wheels.json", "generate.py", "start.py", "start.sh", "ensure_uv.sh", "download_models.sh", "README.md", "requirements.txt", "requirements.lock"):
            s, d = REPO / src_rel / name, REPO / dest_rel / name
            if not d.exists():
                bad.append(f"missing   {dest_rel}/{name}")
            elif s.read_text() != d.read_text():
                bad.append(f"stale     {dest_rel}/{name}  (differs from {src_rel}/{name})")
    return bad


def write_all(out: dict[Path, str]) -> None:
    for path, content in out.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    sync_tools()


def check(out: dict[Path, str]) -> int:
    stale = []
    for path, content in out.items():
        if not path.exists():
            stale.append(f"missing   {path.relative_to(REPO)}")
        elif path.read_text() != content:
            stale.append(f"stale     {path.relative_to(REPO)}")
    stale.extend(check_tools())
    if stale:
        print("generated output is out of date; run: python scripts/gen_skills.py")
        for line in sorted(stale):
            print(" ", line)
        return 1
    print(f"ok: {len(out)} generated files are current")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify output is current")
    args = ap.parse_args()
    out = build()
    if args.check:
        return check(out)
    write_all(out)
    print(f"wrote {len(out)} skill files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
