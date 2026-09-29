#!/usr/bin/env python3
"""Extract a brand profile from a local project directory.

Reads only design surfaces and writes a `brand.md` draft with per-field
provenance. It never reads `.env`, any dotfile that looks like a secret, or any
file outside the given root.

Usage:
    python scripts/extract_brand.py <project-path> [--out brand.md] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NEVER_READ = {
    ".env",
    ".env.local",
    ".env.production",
    ".npmrc",
    ".netrc",
    "id_rsa",
    "credentials",
    "credentials.json",
    "secrets.json",
    "service-account.json",
}
NEVER_SUFFIX = (".pem", ".key", ".p12", ".pfx", ".onnx", ".bin", ".sqlite", ".db")
DIR_SKIP = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".next",
    ".output",
    "coverage",
}

HEADING = re.compile(r"^#\s+(.+)$", re.M)
CSS_VAR = re.compile(r"--((?:color|font|typo)[\w-]*)\s*:\s*([^;]+);", re.I)
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_STACK = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)
NAMED_HEX = re.compile(r"""["']?([\w-]+)["']?\s*:\s*["'](#[0-9a-fA-F]{3,8})["']""")
NAMED_FONT = re.compile(r"""["']?([\w-]+)["']?\s*:\s*\[?\s*["']([^"']+)["']""")
LOGO_NAME = re.compile(r"logo|brand|mark|wordmark", re.I)
IMG_EXT = {".svg", ".png", ".webp", ".jpg", ".jpeg", ".ico"}

PALETTE_ROLES = (
    "Background",
    "Surface",
    "Text primary",
    "Text secondary",
    "Accent",
    "Accent alt",
    "Positive",
    "Negative",
)

# Map a colour key name onto a palette role. Order matters: first match wins.
ROLE_HINTS = (
    ("Background", r"(^|[-_])(bg|background|base|canvas|page)([-_]|$)"),
    ("Surface", r"(^|[-_])(surface|card|panel|elevated|muted-bg)([-_]|$)"),
    ("Text primary", r"(^|[-_])(text|ink|fg|foreground|body)([-_]|$)"),
    ("Text secondary", r"(^|[-_])(muted|subtle|dim|secondary-text|caption)([-_]|$)"),
    ("Accent alt", r"(^|[-_])(accent-alt|secondary|highlight-alt|brand-alt)([-_]|$)"),
    ("Accent", r"(^|[-_])(accent|brand|primary|highlight|link|action)([-_]|$)"),
    ("Positive", r"(^|[-_])(success|good|positive|ok|safe)([-_]|$)"),
    ("Negative", r"(^|[-_])(error|danger|bad|negative|warn|alert|critical)([-_]|$)"),
)


def role_for(key: str) -> str | None:
    k = key.lower()
    for role, pattern in ROLE_HINTS:
        if re.search(pattern, k):
            return role
    return None


def is_secret(path: Path) -> bool:
    name = path.name
    return name in NEVER_READ or name.endswith(NEVER_SUFFIX) or name.startswith(".env")


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or is_secret(p):
            continue
        if any(part in DIR_SKIP for part in p.relative_to(root).parts):
            continue
        yield p


def read_safe(path: Path, limit: int = 400_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def from_package_json(root: Path, out: dict) -> None:
    p = root / "package.json"
    text = read_safe(p)
    if not text:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return
    name = data.get("name")
    if name:
        out.setdefault("product_name", (name, "extracted-from package.json"))


def from_readme(root: Path, out: dict) -> None:
    for candidate in ("README.md", "readme.md", "README.rst"):
        text = read_safe(root / candidate)
        if not text:
            continue
        m = HEADING.search(text)
        if m:
            out.setdefault("brand_name", (m.group(1).strip(), f"extracted-from {candidate}"))
        for line in text.splitlines()[1:12]:
            s = line.strip()
            if s and not s.startswith(("#", "!", "|", "-", ">", "[", "`")):
                out.setdefault("tagline", (s, f"extracted-from {candidate}"))
                break
        return


def from_tailwind(root: Path, out: dict) -> None:
    for name in ("tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs"):
        text = read_safe(root / name)
        if not text:
            continue
        src = f"extracted-from {name}"
        colors_block = re.search(r"colors\s*:\s*\{(.*?)\n\s*\}", text, re.S)
        if colors_block:
            named = NAMED_HEX.findall(colors_block.group(1))
            assigned = set()
            for key, hexv in named:
                role = role_for(key)
                if role and role not in assigned:
                    out.setdefault(f"palette.{role}", (hexv, src))
                    assigned.add(role)
            # Only guess by position when the key names told us nothing.
            if not assigned:
                for hexv in HEX.findall(colors_block.group(1)):
                    for role in PALETTE_ROLES:
                        if f"palette.{role}" not in out:
                            out[f"palette.{role}"] = (hexv, src)
                            break
        fonts_block = re.search(r"fontFamily\s*:\s*\{(.*?)\n\s*\}", text, re.S)
        if fonts_block:
            for key, family in NAMED_FONT.findall(fonts_block.group(1)):
                out.setdefault(f"font.{key}", (family.strip(), src))
        return


def from_css(root: Path, out: dict) -> None:
    for p in iter_files(root):
        if p.suffix.lower() not in {".css", ".scss", ".less"}:
            continue
        text = read_safe(p)
        if not text:
            continue
        src = f"extracted-from {p.relative_to(root)}"
        for var, value in CSS_VAR.findall(text):
            value = value.strip()
            key = var.strip().lstrip("-")
            field = re.sub(r"^(?:color|font|typo)-", "", key)
            hexv = HEX.search(value)
            if hexv:
                role = role_for(key)
                out.setdefault(f"palette.{role or field}", (hexv.group(0), src))
            else:
                family = value.split(",")[0].strip().strip("'\"")
                if family and not family.startswith(("var(", "inherit", "system")):
                    out.setdefault(f"font.{field}", (family, src))
        for stack in FONT_STACK.findall(text):
            family = stack.split(",")[0].strip().strip("'\"")
            if family and not family.startswith(("var(", "inherit", "system")):
                out.setdefault("font.body", (family, src))


def from_theme_files(root: Path, out: dict) -> None:
    for name in ("tokens.json", "theme.json", "theme.config.js", "stitches.config.js"):
        for p in root.rglob(name):
            if any(part in DIR_SKIP for part in p.relative_to(root).parts):
                continue
            text = read_safe(p)
            if not text:
                continue
            src = f"extracted-from {p.relative_to(root)}"
            assigned = set()
            for key, hexv in NAMED_HEX.findall(text):
                role = role_for(key)
                if role and role not in assigned:
                    out.setdefault(f"palette.{role}", (hexv, src))
                    assigned.add(role)
            for key, family in NAMED_FONT.findall(text):
                if re.search(r"font|type", key, re.I):
                    out.setdefault(f"font.{key}", (family.split(",")[0].strip(), src))


def from_logos(root: Path, out: dict) -> None:
    hits = []
    for p in iter_files(root):
        if p.suffix.lower() in IMG_EXT and LOGO_NAME.search(p.name):
            hits.append(str(p.relative_to(root)))
    if hits:
        out["logos"] = (hits[:8], "extracted-from project assets")


def extract(root: Path) -> dict:
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    out: dict = {}
    from_package_json(root, out)
    from_readme(root, out)
    from_tailwind(root, out)
    from_css(root, out)
    from_theme_files(root, out)
    from_logos(root, out)
    return out


def to_markdown(data: dict, root: Path) -> str:
    def get(key: str) -> tuple[str, str] | None:
        return data.get(key)

    brand_name = get("brand_name") or get("product_name") or ("", "")
    lines = [
        f"# Brand: {brand_name[0] or '(unset)'}",
        "",
        "<!-- Generated by scripts/extract_brand.py. Review before use.",
        "     Every value below records where it came from. -->",
        "",
        "## Product",
        f"- Product name: {get('product_name')[0] if get('product_name') else ''}",
        "- What it is: ",
        "- One-line promise: ",
        "",
        "## Brand",
        f"- Brand name: {brand_name[0]}",
        f"- Tagline: {get('tagline')[0] if get('tagline') else ''}",
        "- URL: ",
        "- Contact: ",
        "",
        "## Vertical",
        "- ",
        "",
        "## Logo",
    ]
    logos = data.get("logos", ([], ""))
    for logo in logos[0]:
        lines.append(f"- {logo}")
    if not logos[0]:
        lines.append("- ")
    lines += [
        "",
        "## Palette",
        "| Role | Hex | Use |",
        "|---|---|---|",
    ]
    for role in PALETTE_ROLES:
        hit = data.get(f"palette.{role}")
        lines.append(f"| {role} | {hit[0] if hit else ''} | |")
    lines += [
        "",
        "## Typography",
        "| Role | Family | Weight | Size |",
        "|---|---|---|---|",
    ]
    for role in ("display", "body", "caption", "mono"):
        hit = data.get(f"font.{role}")
        lines.append(f"| {role} | {hit[0] if hit else ''} | | |")
    lines += [
        "",
        "## Voice and tone",
        "- Tone words: ",
        "- Person: ",
        "- Reading level: ",
        "- Words we use: []",
        "- Words we never use: []",
        "- Preferred TTS voice: ",
        "",
        "## Imagery",
        "- Style: ",
        "- Icon rules: ",
        "- Illustration rules: ",
        "",
        "## Claims",
        "- Evidence required before a claim: ",
        "- Never claim: []",
        "- Competitor references: ",
        "",
        "## Accessibility",
        "- Minimum contrast: ",
        "- Caption style: ",
        "- Reduced motion: ",
        "",
        "## Provenance",
        "| Field | Value | Source |",
        "|---|---|---|",
    ]
    for key in sorted(data):
        val, src = data[key]
        if isinstance(val, list):
            val = ", ".join(val)
        lines.append(f"| {key} | {val} | {src} |")
    lines += ["", f"_Scanned: `{root}`. Secrets and dotfiles were never read._", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = extract(args.root.resolve())
    if args.json:
        print(json.dumps(data, indent=2, default=str))
        return 0
    text = to_markdown(data, args.root.resolve())
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.out} ({len(data)} fields)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
