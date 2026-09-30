#!/usr/bin/env python3
"""Prepare the desktop runner integration patch without writing the app checkout.

Usage: python3 scripts/prepare_devmock_video_patch.py --app /path/to/devmock
"""

import argparse
import difflib
import json
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def prepare(app: Path, output: Path) -> None:
    """Reuse the verified complete patch instead of obsolete source templates."""
    canonical = REPO / "docs/patches/devmock-video-job.patch"
    if not canonical.is_file():
        raise ValueError("Export an integrated app with --from-worktree before preparing this patch")
    forward = subprocess.run(["git", "-C", str(app), "apply", "--check", str(canonical)], capture_output=True, text=True)
    reverse = subprocess.run(["git", "-C", str(app), "apply", "--reverse", "--check", str(canonical)], capture_output=True, text=True) if forward.returncode else None
    if forward.returncode and (reverse is None or reverse.returncode):
        raise ValueError("This app baseline differs from the prepared integration. Export the current integrated checkout with --from-worktree; the app was not changed")
    if output != canonical:
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(canonical, output)
    print(f"Prepared verified integration at {output}; app checkout was read only")


def export_worktree(app: Path, output: Path) -> None:
    """Export the installed integration relative to the app's committed baseline."""
    baseline = subprocess.run(["git", "-C", str(app), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, check=True)
    if Path(baseline.stdout.strip()).resolve() != app:
        raise ValueError("The app path must be its Git repository root")
    paths = ["tsconfig.check.json", "src-tauri/src/lib.rs", "src-tauri/Cargo.toml", "src-tauri/Cargo.lock",
             "src-tauri/tauri.conf.json", "src-tauri/src/video_skill_job.rs",
             "src-tauri/src/video_runtime.rs", "src-tauri/src/video_runtime_requirements.json",
             "src-tauri/src/audio_studio.rs", "src-tauri/src/speech_recognition.rs",
             "src/engine/videoProject.ts", "src/engine/videoProject.test.ts", "src/engine/videoRuntime.ts", "src/engine/videoStudio.ts", "src/engine/videoAi.ts",
             "src/components/VideoStudio.vue", "src/components/VideoCaptionEditor.vue", "src/components/LocalAvatarPanel.vue", "src/components/VideoAssetPanel.vue", "src/components/TextBlockControls.vue", "src/components/converter/ChromaPanel.vue", "src/components/converter/JobProgress.vue", "src/stores/mockupStore.ts", "src/stores/mockupStore.test.ts"]
    paths.extend(str(path.relative_to(app)) for path in sorted(
        (app / "src-tauri/resources/video-tools").iterdir()) if path.suffix in (".py", ".json"))
    patch = []
    for path in paths:
        after = (app / path).read_text(encoding="utf-8")
        result = subprocess.run(["git", "-C", str(app), "show", f"HEAD:{path}"],
                                capture_output=True, text=True)
        exists = result.returncode == 0
        before = result.stdout if exists else ""
        if before == after:
            continue
        patch.append(f"diff --git a/{path} b/{path}\n")
        if not exists:
            patch.append("new file mode 100644\n")
        patch.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                     fromfile="a/" + path if exists else "/dev/null", tofile="b/" + path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(patch), encoding="utf-8")
    print(f"Exported current integration to {output}; app checkout was read only")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=REPO / "docs/patches/devmock-video-job.patch")
    parser.add_argument("--from-worktree", action="store_true",
                        help="Export an already integrated checkout relative to its Git HEAD")
    args = parser.parse_args()
    action = export_worktree if args.from_worktree else prepare
    action(args.app.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
