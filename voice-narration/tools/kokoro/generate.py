"""Kokoro TTS audio generator for course lessons (CPU, offline).

Usage:
  python generate.py --text "Hello class" --out /path/to/lesson.wav
  python generate.py --text-file lesson.txt --voice af_sky --out lesson.wav --speed 1.0

Needs model files in --models-dir (see download_models.sh):
  kokoro-v1.0.onnx + voices-v1.0.bin
"""
import argparse
import os
import sys

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
    p.add_argument("--out", required=True, help="Output .wav path.")
    p.add_argument("--voice", default=DEFAULT_VOICE, help=f"Voice id (default: {DEFAULT_VOICE}).")
    p.add_argument("--speed", type=float, default=1.0, help="Speech speed (default: 1.0).")
    p.add_argument("--lang", default=DEFAULT_LANG, help=f"Lang tag (default: {DEFAULT_LANG}).")
    p.add_argument("--models-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"))
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
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
    sf.write(out, samples, sample_rate)
    print(f"wrote {out} ({len(samples) / sample_rate:.1f}s, {sample_rate}Hz, voice={args.voice})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
