#!/usr/bin/env python3
"""Generate editable renderer projects from imported desktop storyboard media."""
from __future__ import annotations

import html
import json
import math
from pathlib import Path
import re
import shutil

from assemble_video import ASPECTS, probe
from ensure_video_runtime import MANIFEST
from desktop_fonts import family

ENGINES = {"hyperframes", "remotion", "slidev"}


def color(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def author(inputs: Path, renderer: str, ffprobe: Path) -> Path:
    if renderer not in ENGINES:
        raise ValueError(f"Unknown authoring renderer: {renderer}")
    plan = json.loads((inputs / "timing.json").read_text(encoding="utf-8"))
    desktop = json.loads((inputs / "desktop.json").read_text(encoding="utf-8"))
    width, height = ASPECTS[plan["aspect"]]
    projects = inputs / "authoring"
    projects.mkdir()
    entries = []
    for index, (scene, detail) in enumerate(zip(plan["scenes"], desktop["scenes"]), 1):
        folder = projects / f"scene-{index:04}"
        assets = folder / "public"
        assets.mkdir(parents=True)
        visual = inputs / scene["visual"]
        is_video = visual.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp")
        if renderer == "slidev" and is_video:
            raise ValueError("Slidev exports still slides; choose HyperFrames or Remotion to retain uploaded footage")
        source_index = detail.get("sourceAssetIndex")
        media = visual if is_video else inputs / desktop["sourceAssets"][source_index]["file"] if source_index is not None else None
        media_name = ""
        if media:
            media_name = "media" + media.suffix.lower()
            shutil.copy2(media, assets / media_name)
        duration = float(scene["duration_sec"])
        if scene.get("narration"):
            duration = max(duration, probe(ffprobe, inputs / scene["narration"])["duration"])
        elif scene.get("audio_from_visual"):
            info = probe(ffprobe, visual)
            if duration > info["duration"] + 0.001:
                raise ValueError(f"Scene {index} would loop footage audio; shorten it or supply narration")
        frames = math.ceil(duration * plan["fps"])
        spec = {"title": plan["title"], "heading": detail["screenText"] if isinstance(detail.get("screenText"), str) else "" if is_video else (scene.get("caption") or plan["title"])[:160],
                "index": index, "count": len(plan["scenes"]), "width": width, "height": height,
                "fps": plan["fps"], "frames": frames, "duration": frames / plan["fps"],
                "mediaFrames": max(1, math.floor(probe(ffprobe, visual)["duration"] * plan["fps"])) if is_video else 0,
                "primary": color(desktop.get("brandPrimary"), "#2563eb"),
                "surface": color(desktop.get("brandSurface"), "#0f172a"),
                "text": color(desktop.get("brandText"), "#ffffff"), "media": media_name, "video": is_video,
                "headlineFont": family(desktop.get("headlineFont")), "bodyFont": family(desktop.get("bodyFont"))}
        (folder / "package.json").write_text(json.dumps({"private": True, "dependencies": MANIFEST["profiles"][renderer]["packages"]}, indent=2) + "\n", encoding="utf-8")
        (folder / "scene.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / "fonts.css").write_text("/* Local font files are prepared before rendering. */\n", encoding="utf-8")
        (assets / "fonts.css").write_text("/* Local font files are prepared before rendering. */\n", encoding="utf-8")
        if renderer == "hyperframes":
            write_hyperframes(folder, spec)
            entry = "index.html"
        elif renderer == "remotion":
            write_remotion(folder, spec)
            entry = "index.tsx"
        else:
            write_slidev(folder, spec)
            entry = "slides.md"
        entries.append({"id": scene["id"], "folder": folder.name, "entry": entry,
                        "duration_sec": spec["duration"], "frames": frames})
    if sum(entry["duration_sec"] for entry in entries) > 1800:
        raise ValueError("Measured narration extends the project beyond 30 minutes")
    contract = {"renderer": renderer, "aspect": plan["aspect"], "fps": plan["fps"], "scenes": entries}
    (projects / "authoring.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    (projects / "README.md").write_text(
        "# Editable desktop video source\n\nEach scene is a local renderer project. "
        "Timing uses measured narration duration rounded up to a whole video frame. "
        "Media stays local and narration is assembled separately. Selected fonts and their "
        "licences are packaged locally before rendering; fonts.json records their versions.\n", encoding="utf-8")
    return projects / "authoring.json"


def write_hyperframes(folder: Path, s: dict) -> None:
    media = ""
    if s["media"]:
        source = html.escape("public/" + s["media"], quote=True)
        if s["video"]:
            fragments = []
            cursor = 0
            while cursor < s["frames"]:
                window = min(s["mediaFrames"], s["frames"] - cursor)
                fragments.append(f'<video id="footage-{cursor}" class="clip media" src="{source}" data-start="{cursor / s["fps"]}" data-duration="{window / s["fps"]}" data-volume="0" muted playsinline></video>')
                cursor += window
            media = "".join(fragments)
        else:
            media = f'<img id="picture" class="media" src="{source}" alt="">'
    content = f'<h1 id="heading">{html.escape(s["heading"])}</h1>' if s["heading"] else ''
    size = max(38, min(94, int(1100 / max(12, len(s["heading"]) ** 0.6))))
    document = f'''<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(s['title'])}</title>
<script src="vendor/gsap.min.js"></script>
<link rel="stylesheet" href="public/fonts.css">
<style>
html,body{{margin:0;width:100%;height:100%;font-family:'{s['bodyFont']}',sans-serif}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;background:{s['surface']};color:{s['text']}}}
.media{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#shade{{position:absolute;inset:0;background:linear-gradient(0deg,{s['surface']} 0%,transparent 85%);opacity:.85}}
#content{{position:absolute;inset:8%;display:flex;flex-direction:column;justify-content:flex-end}}
#heading{{font-family:'{s['headlineFont']}',sans-serif;font-size:{size}px;line-height:1.1;margin:0 0 8%;max-width:90%;overflow-wrap:anywhere}}
#rule{{width:18%;height:10px;background:{s['primary']};margin-bottom:5%}}
#footer{{font-size:24px;display:flex;justify-content:space-between;gap:24px}}
</style></head><body>
<div id="root" data-composition-id="main" data-width="{s['width']}" data-height="{s['height']}" data-start="0" data-duration="{s['duration']}">
{media}<div id="shade"></div>
<div id="content" class="clip" data-start="0" data-duration="{s['duration']}"><div id="rule"></div>{content}
<div id="footer"><span>{html.escape(s['title'])}</span><span>{s['index']:02d} / {s['count']:02d}</span></div></div>
</div><script>
const tl=gsap.timeline({{paused:true}});
tl.fromTo('#content',{{opacity:0,y:28}},{{opacity:1,y:0,duration:{min(.5,s['duration']/3)},ease:'power2.out'}},0);
window.__timelines['main']=tl;
</script></body></html>
'''
    (folder / "index.html").write_text(document, encoding="utf-8")


def write_remotion(folder: Path, s: dict) -> None:
    # User strings stay in JSON; no user-authored JavaScript is interpolated.
    source = '''import React from 'react';
import {AbsoluteFill, Composition, Img, OffthreadVideo, Loop, registerRoot, staticFile, useCurrentFrame, interpolate} from 'remotion';
import scene from './scene.json';
import './fonts.css';
const Scene=()=>{
 const frame=useCurrentFrame();
 const enter=interpolate(frame,[0,Math.max(1,Math.min(scene.frames/3,scene.fps*.5))],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const mediaStyle={width:'100%',height:'100%',objectFit:'cover' as const};
 return <AbsoluteFill style={{background:scene.surface,color:scene.text,fontFamily:`'${scene.bodyFont}',sans-serif`}}>
 {scene.media && (scene.video ? <Loop durationInFrames={scene.mediaFrames}><OffthreadVideo muted src={staticFile(scene.media)} style={mediaStyle}/></Loop> : <Img src={staticFile(scene.media)} style={mediaStyle}/>)}
 <AbsoluteFill style={{background:`linear-gradient(0deg,${scene.surface},transparent)`,opacity:.85}}/>
 <AbsoluteFill style={{padding:'8%',justifyContent:'flex-end',opacity:enter,transform:`translateY(${(1-enter)*28}px)`}}>
 <div style={{width:'18%',height:10,background:scene.primary,marginBottom:'5%'}}/>
 {scene.heading && <h1 style={{fontFamily:`'${scene.headlineFont}',sans-serif`,fontSize:Math.max(38,Math.min(94,1100/Math.max(12,scene.heading.length**.6))),lineHeight:1.1,margin:'0 0 8%',overflowWrap:'anywhere'}}>{scene.heading}</h1>}
 <div style={{fontSize:24,display:'flex',justifyContent:'space-between',gap:24}}><span>{scene.title}</span><span>{scene.index} / {scene.count}</span></div>
 </AbsoluteFill></AbsoluteFill>;
};
registerRoot(()=> <Composition id="DesktopScene" component={Scene} durationInFrames={scene.frames} fps={scene.fps} width={scene.width} height={scene.height}/>);
'''
    (folder / "index.tsx").write_text(source, encoding="utf-8")


def write_slidev(folder: Path, s: dict) -> None:
    # HTML entity encoding prevents Vue template expressions in form text.
    escaped = lambda value: html.escape(value).replace("{", "&#123;").replace("}", "&#125;")
    media = f'<img src="/{s["media"]}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover" />' if s["media"] else ''
    source = f'''---
theme: default
layout: none
aspectRatio: {s['width']}/{s['height']}
canvasWidth: {s['width']}
fonts:
  provider: none
  sans: system-ui
  local: system-ui
---

<div style="position:absolute;inset:0;background:{s['surface']};color:{s['text']};font-family:'{s['bodyFont']}',sans-serif">
{media}
<div style="position:absolute;inset:0;background:linear-gradient(0deg,{s['surface']},transparent);opacity:.85"></div>
<div style="position:absolute;inset:8%;display:flex;flex-direction:column;justify-content:flex-end">
<div style="width:18%;height:10px;background:{s['primary']};margin-bottom:5%"></div>
<h1 style="font-family:'{s['headlineFont']}',sans-serif;font-size:72px;line-height:1.1;margin:0 0 8%;overflow-wrap:anywhere">{escaped(s['heading'])}</h1>
<div style="font-size:24px;display:flex;justify-content:space-between"><span>{escaped(s['title'])}</span><span>{s['index']} / {s['count']}</span></div>
</div></div>
'''
    (folder / "slides.md").write_text(source, encoding="utf-8")
    (folder / "index.html").write_text('<head><link rel="stylesheet" href="/fonts.css"></head>\n', encoding="utf-8")
