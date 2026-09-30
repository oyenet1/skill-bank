#!/usr/bin/env python3
"""Pre-generate presenter footage while retaining source and verified resume data."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import shutil


def prepare(request: Path, config: dict) -> list[dict]:
    from run_video_job import command_result, fingerprint, media_paths, progress, TOOLS
    from avatar_runtime import fingerprint as metadata_hash
    from assemble_video import probe
    spec = config.get('avatar')
    if not isinstance(spec, dict) or spec.get('mode') != 'photo' or spec.get('provider') != 'local' or spec.get('rightsConfirmed') is not True:
        raise ValueError('Local presenter jobs require photo mode, an explicit local provider, and image rights confirmation')
    if config['route'] != 'avatar-video' or config['renderer'] not in ('scenes', 'storyboard'):
        raise ValueError('Avatar pre-generation supports scene and authored storyboard jobs on the avatar-video route')
    inputs = config['timing'].parent
    image = (request.parent / spec['image']).resolve()
    if not image.is_file():
        raise ValueError('Presenter portrait is missing')
    timing = json.loads(config['timing'].read_text(encoding='utf-8'))
    originals = inputs / 'avatar-original-timing.json'
    if originals.exists():
        timing = json.loads(originals.read_text(encoding='utf-8'))
    else:
        originals.write_text(json.dumps(timing, indent=2) + '\n', encoding='utf-8')
    from ensure_video_runtime import default_runtime_dir
    ffmpeg, ffprobe = media_paths(config.get('runtimeDir') or default_runtime_dir())
    # Deliver editable assets before inference, including when generation fails.
    fallback = inputs / 'avatar-fallback'
    fallback.mkdir(exist_ok=True)
    scenes = timing['scenes']
    audios = []
    script = ['# ' + timing.get('title', 'Presenter script'), '']
    storyboard = ['# Presenter storyboard', '']
    for index, scene in enumerate(scenes, 1):
        narration = inputs / scene.get('narration', '')
        if not scene.get('narration') or not narration.is_file():
            raise ValueError(f'Presenter scene {index} needs narration; enable local voice or upload audio')
        audios.append(narration)
        script.extend([f'## Scene {index}', scene.get('caption', ''), ''])
        storyboard.extend([f'## Scene {index}', f"Portrait: {image.name}", scene.get('caption', ''), ''])
    (fallback / 'script.md').write_text('\n'.join(script), encoding='utf-8')
    (fallback / 'storyboard.md').write_text('\n'.join(storyboard), encoding='utf-8')
    args = [str(ffmpeg), '-v', 'error', '-y']
    for audio in audios:
        args.extend(['-protocol_whitelist', 'file,pipe', '-i', str(audio)])
    filters = ';'.join(f'[{i}:a]aformat=sample_rates=24000:channel_layouts=mono[a{i}]' for i in range(len(audios)))
    filters += ';' + ''.join(f'[a{i}]' for i in range(len(audios))) + f'concat=n={len(audios)}:v=0:a=1[out]'
    # Use the job child manager so desktop cancellation includes media processing.
    from run_video_job import command_result as execute
    # FFmpeg writes no JSON; a tiny subprocess wrapper emits a completion object.
    wrapper = 'import subprocess,sys,json; subprocess.run(sys.argv[1:],check=True); print(json.dumps({"ready":True}))'
    execute([sys.executable, '-c', wrapper, *args, '-filter_complex', filters, '-map', '[out]', str(fallback / 'narration.wav')], fallback / 'audio.log')
    execute([sys.executable, '-c', wrapper, str(ffmpeg), '-v', 'error', '-y', '-i', str(fallback / 'narration.wav'), str(fallback / 'audio.mp3')], fallback / 'mp3.log')
    for name in ('narration.wav', 'audio.mp3'):
        info = probe(ffprobe, fallback / name)
        if 'audio' not in info['streams'] or info['duration'] <= 0:
            raise RuntimeError('Fallback narration failed media verification')
    records = []
    for index, (scene, audio) in enumerate(zip(scenes, audios), 1):
        identity = metadata_hash({'backend': spec['backend'], 'image': fingerprint(image), 'audio': fingerprint(audio), 'rightsConfirmed': True})
        directory = inputs / 'avatar-clips' / f'{index:04}-{identity[:16]}'
        receipt = directory / 'receipt.json'
        video = directory / 'video.mp4'
        reused = False
        if receipt.is_file() and video.is_file():
            record = json.loads(receipt.read_text(encoding='utf-8'))
            reused = record.get('inputHash') == identity and record.get('videoSha256') == fingerprint(video)
        if not reused:
            progress('avatar-generate', f'Generating presenter scene {index} of {len(scenes)}', artifact=str(fallback))
            command = [sys.executable, str(TOOLS / 'avatar_generate.py'), '--backend', spec['backend'], '--mode', 'photo', '--image', str(image), '--audio', str(audio), '--out', str(directory), '--rights-confirmed']
            try:
                result = command_result(command, inputs / f'avatar-scene-{index:04}.log')
            except RuntimeError as error:
                raise RuntimeError(f"{error}. Presenter generation is blocked; script, WAV, MP3 and storyboard are retained at {fallback}. Retry the original job with --resume after repairing the backend.") from error
            if not result.get('ready'):
                raise RuntimeError(f'Presenter generation failed; editable fallback is retained at {fallback}')
            record = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
            record.update(inputHash=identity, videoSha256=fingerprint(video))
            receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        info = probe(ffprobe, video)
        if not {'video', 'audio'}.issubset(info['streams']) or info['duration'] <= 0:
            raise RuntimeError('Presenter clip failed verification')
        scene['visual'] = str(video.relative_to(inputs))
        scene.pop('audio_from_visual', None)
        record.update(sceneId=scene.get('id', str(index)), clipPath=str(video.relative_to(inputs)))
        records.append(record)
    config['timing'].write_text(json.dumps(timing, indent=2) + '\n', encoding='utf-8')
    if config['renderer'] == 'storyboard':
        from author_desktop_video import author
        existing = inputs / 'authoring'
        if existing.exists():
            original = inputs / 'authoring-original'
            if not original.exists():
                existing.rename(original)
            else:
                shutil.rmtree(existing)
        author(inputs, config['authoringRenderer'], ffprobe)
    return records
