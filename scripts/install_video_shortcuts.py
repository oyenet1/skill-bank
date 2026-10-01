#!/usr/bin/env python3
"""Install generated native slash-command adapters without replacing user files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent


def install(host: str, target: Path, overwrite: bool = False) -> list[Path]:
    source = REPO / "commands" / host
    templates = sorted(source.glob("*.md"))
    if not templates:
        raise ValueError(f"No {host} command templates; run scripts/gen_skills.py first")
    # Check all destinations before changing any files.
    for template in templates:
        dest = target / template.name
        if dest.is_symlink() or (dest.exists() and not dest.is_file()):
            raise ValueError(f"Refusing non-regular destination: {dest}")
        if dest.exists() and dest.read_text() != template.read_text() and not overwrite:
            raise ValueError(f"Existing shortcut differs: {dest}; use --overwrite to replace it")
    target.mkdir(parents=True, exist_ok=True)
    installed = []
    for template in templates:
        dest = target / template.name
        dest.write_text(template.read_text())
        installed.append(dest)
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "claude"), required=True)
    parser.add_argument("--target", type=Path, help="Override the host's user command directory")
    parser.add_argument("--overwrite", action="store_true", help="Replace conflicting shortcut files")
    args = parser.parse_args()
    target = args.target or Path.home() / (
        ".codex/prompts" if args.host == "codex" else ".claude/commands"
    )
    try:
        installed = install(args.host, target, args.overwrite)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    prefix = "/prompts:" if args.host == "codex" else "/"
    print(f"Installed {len(installed)} shortcuts in {target}")
    print(f"Restart your agent, then use {prefix}tutorial followed by your prompt.")
    print("Install the matching production skills separately; these adapters route requests only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
