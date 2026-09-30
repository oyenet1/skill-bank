#!/usr/bin/env python3
"""Prepare the desktop runner integration patch without writing the app checkout.

Usage: python3 scripts/prepare_devmock_video_patch.py --app /path/to/devmock
"""

import argparse
import difflib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def replace_once(content: str, before: str, after: str, path: str) -> str:
    if content.count(before) != 1:
        raise ValueError(f"Cannot patch {path}: expected one matching source block")
    return content.replace(before, after, 1)


def prepare(app: Path, output: Path) -> None:
    edits = {}
    path = "src-tauri/src/lib.rs"
    content = (app / path).read_text(encoding="utf-8")
    content = replace_once(content, "mod video_runtime;", "mod video_runtime;\nmod video_skill_job;", path)
    content = replace_once(content, ".manage(video_runtime::RuntimeState::default())", ".manage(video_runtime::RuntimeState::default())\n        .manage(video_skill_job::SkillJobState::default())", path)
    content = replace_once(content, "            video_runtime::video_runtime_cancel,", "            video_runtime::video_runtime_cancel,\n            video_skill_job::video_skill_render,\n            video_skill_job::video_skill_cancel,", path)
    edits[path] = content

    path = "src-tauri/Cargo.toml"
    content = (app / path).read_text(encoding="utf-8")
    if "[target.'cfg(unix)'.dependencies]" in content:
        raise ValueError("The app's Unix dependency section changed; review before adding libc")
    edits[path] = content.rstrip() + "\n\n[target.'cfg(unix)'.dependencies]\nlibc = \"0.2\"\n"

    path = "src-tauri/Cargo.lock"
    content = (app / path).read_text(encoding="utf-8")
    start = content.index('name = "progravity"\n')
    end = content.index("\n[[package]]", start)
    block = replace_once(content[start:end], ' "hound",\n', ' "hound",\n "libc",\n', path)
    edits[path] = content[:start] + block + content[end:]

    path = "src-tauri/tauri.conf.json"
    config = json.loads((app / path).read_text(encoding="utf-8"))
    config["bundle"]["resources"]["resources/video-tools/"] = "video-tools/"
    edits[path] = json.dumps(config, indent=2) + "\n"

    path = "src/engine/videoProject.ts"
    content = (app / path).read_text(encoding="utf-8")
    content = replace_once(content, "  sizeBytes: number;\n", "  sizeBytes: number;\n  reviewRequired: boolean;\n  mixedAudio: string | null;\n  transcript: string | null;\n", path)
    content = replace_once(content, "  fps: number;\n", "  fps: number;\n  jobRoute?: 'explainer-video' | 'product-launch-video' | 'talking-head-video';\n", path)
    content = replace_once(content, "  const channel = new Channel<VideoProjectProgress>();", "  if (cancelled.value) throw new Error('Video job cancelled');\n  const channel = new Channel<VideoProjectProgress>();", path)
    content = replace_once(content, "  channel.onmessage = (value) => onProgress({ ...value, percent: 45 + Math.round(value.percent * 0.55) });", "  let lastPercent = 45;\n  channel.onmessage = (value) => {\n    lastPercent = Math.max(lastPercent, 45 + Math.round(value.percent * 0.55));\n    onProgress({ ...value, percent: lastPercent });\n  };", path)
    content = replace_once(content, "'video_project_render'", "'video_skill_render'", path)
    content = replace_once(content, "      sourceAssets, scenes,", "      sourceAssets, scenes, jobRoute: options.jobRoute,", path)
    content = replace_once(content, "invoke('video_project_cancel')", "invoke('video_skill_cancel')", path)
    edits[path] = content

    path = "src/components/VideoStudio.vue"
    content = (app / path).read_text(encoding="utf-8")
    content = replace_once(content, "import { AI_PROVIDERS, aiProvider, readSavedAiKey }", "import { AI_PROVIDERS, aiProvider, readSavedAiKey, type AiProviderId }", path)
    content = replace_once(content, "const aiProviderId = ref('ollama-local');", "const aiProviderId = ref<AiProviderId>('ollama-local');", path)
    content = replace_once(content, "    if (selected && AI_PROVIDERS.some((provider) => provider.id === selected)) aiProviderId.value = selected;", "    const selectedProvider = AI_PROVIDERS.find((provider) => provider.id === selected);\n    if (selectedProvider) aiProviderId.value = selectedProvider.id;", path)
    content = content.replace('size="2xs"', 'size="xs"')
    content = replace_once(content, "        bodyFont: bodyFont.value,\n        fps: fps.value,", "        bodyFont: bodyFont.value,\n        fps: fps.value,\n        jobRoute: kind.value?.id === 'talking-head' ? 'talking-head-video'\n          : plan.value.category === 'product' || ['product-promo', 'launch-video', 'product-film', 'unboxing-demo'].includes(kind.value?.id ?? '')\n            ? 'product-launch-video' : 'explainer-video',", path)
    content = replace_once(content, '<UAlert color="success" variant="subtle" icon="i-lucide-circle-check" title="Video project complete" :description="`${realOutcome.durationSec.toFixed(1)}s MP4 · ${(realOutcome.sizeBytes / 1048576).toFixed(1)} MB`" />', '<UAlert :color="realOutcome.reviewRequired ? \'warning\' : \'success\'" variant="subtle" icon="i-lucide-circle-check" :title="realOutcome.reviewRequired ? \'Video ready for caption review\' : \'Video project complete\'" :description="`${realOutcome.durationSec.toFixed(1)}s MP4 · ${(realOutcome.sizeBytes / 1048576).toFixed(1)} MB`" />', path)
    content = replace_once(content, '<li v-if="realOutcome.narration.length">Narration: {{ realOutcome.narration.length }} WAV scene files</li>', '<li v-if="realOutcome.narration.length">Narration: {{ realOutcome.narration.length }} scene files</li>\n              <li v-if="realOutcome.mixedAudio">Final audio: {{ realOutcome.mixedAudio }}</li>\n              <li v-if="realOutcome.transcript">Transcript for review: {{ realOutcome.transcript }}</li>', path)
    edits[path] = content
    edits["src-tauri/src/video_skill_job.rs"] = (REPO / "integrations/devmock/video_skill_job.rs").read_text(encoding="utf-8")
    tools = REPO / "skills-src/_shared/tools"
    for tool in sorted(tools.iterdir()):
        if tool.suffix in (".py", ".json"):
            edits[f"src-tauri/resources/video-tools/{tool.name}"] = tool.read_text(encoding="utf-8")
    patch = []
    for path, after in edits.items():
        original = app / path
        before = original.read_text(encoding="utf-8") if original.is_file() else ""
        patch.append(f"diff --git a/{path} b/{path}\n")
        if not original.exists():
            patch.append("new file mode 100644\n")
        patch.extend(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                        fromfile="a/" + path if original.exists() else "/dev/null", tofile="b/" + path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(patch), encoding="utf-8")
    print(f"Prepared {len(edits)} files in {output}; app checkout was read only")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=REPO / "docs/patches/devmock-video-job.patch")
    args = parser.parse_args()
    prepare(args.app.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
