"""Kokoro TTS audio generator for course-creator (CPU, offline).

Usage:
  python generate.py --text "Hello class" --out /path/to/lesson.mp3
  python generate.py --text-file lesson.txt --voice af_sky --out lesson.mp3 --speed 1.0

Output is WAV or MP3 (MP3 uses system or bundled ffmpeg).

Needs model files in --models-dir (see download_models.sh):
  kokoro-v1.0.onnx + voices-v1.0.bin
"""
import argparse
import os
import math
import shutil
import subprocess
import sys
import tempfile

try:
    import espeakng_loader  # noqa: F401  (bundled libespeak, for machines without apt espeak-ng)
except ImportError:
    pass  # Docker image has system espeak-ng instead

from kokoro_onnx import Kokoro
import soundfile as sf

DEFAULT_VOICE = "af_bella"
DEFAULT_LANG = "en-us"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Generate course narration audio with local Kokoro TTS.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Text to narrate (quote it).")
    src.add_argument("--text-file", help="Path to a .txt/.md file to narrate.")
    p.add_argument("--out", required=True, help="Output path: .mp3 (default) or .wav.")
    p.add_argument("--voice", default=DEFAULT_VOICE, help=f"Voice id (default: {DEFAULT_VOICE}).")
    p.add_argument("--speed", type=float, default=1.0, help="Speech speed (default: 1.0).")
    p.add_argument("--lang", default=DEFAULT_LANG, help=f"Lang tag (default: {DEFAULT_LANG}).")
    p.add_argument("--models-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"))
    return p.parse_args(argv)


def generate(argv=None):
    args = parse_args(argv)
    suffix = os.path.splitext(args.out)[1].lower()
    if suffix not in (".wav", ".mp3"):
        raise ValueError("Narration output must end in .wav or .mp3")
    if not math.isfinite(args.speed) or args.speed <= 0:
        raise ValueError("Speech speed must be finite and positive")
    if args.text_file:
        with open(args.text_file, encoding="utf-8") as f:
            text = f.read().strip()
    else:
        text = args.text.strip()
    if not text:
        print("error: empty text", file=sys.stderr)
        return 1

    model_path = os.path.join(args.models_dir, "kokoro-v1.0.onnx")
    voices_path = os.path.join(args.models_dir, "voices-v1.0.bin")
    for path in (model_path, voices_path):
        if not os.path.isfile(path):
            print(f"error: missing {path} — run ./download_models.sh first", file=sys.stderr)
            return 1

    kokoro = Kokoro(model_path, voices_path)
    samples, sample_rate = kokoro.create(text, voice=args.voice, speed=args.speed, lang=args.lang)

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if sample_rate <= 0 or len(samples) == 0:
        raise ValueError("Narration backend returned empty audio")
    duration = len(samples) / sample_rate
    handle, staged = tempfile.mkstemp(prefix=".audio-", suffix=suffix, dir=os.path.dirname(out))
    os.close(handle)
    try:
        if suffix == ".mp3":
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            handle, tmp_wav = tempfile.mkstemp(suffix=".wav")
            os.close(handle)
            try:
                sf.write(tmp_wav, samples, sample_rate)
                subprocess.run([ffmpeg, "-y", "-v", "error", "-i", tmp_wav,
                                "-codec:a", "libmp3lame", "-q:a", "3", staged], check=True)
            finally:
                os.unlink(tmp_wav)
        else:
            sf.write(staged, samples, sample_rate)
        if os.path.getsize(staged) == 0:
            raise ValueError("Narration encoder produced an empty file")
        os.replace(staged, out)
    finally:
        if os.path.exists(staged):
            os.unlink(staged)
    print(f"wrote {out} ({duration:.1f}s, {sample_rate}Hz, voice={args.voice})")
    return 0


def main(argv=None):
    try:
        return generate(argv)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
