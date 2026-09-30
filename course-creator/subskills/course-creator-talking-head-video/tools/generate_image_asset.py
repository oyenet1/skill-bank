#!/usr/bin/env python3
"""Generate a reusable scene image; credentials stay in process memory/environment."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import sys
import urllib.error
import urllib.request
from network_tls import tls_context
import uuid
import zlib

ENDPOINT = 'https://api.openai.com/v1/images/generations'
MAX_BYTES = 22_000_000
SIZES = {'1024x1024', '1536x1024', '1024x1536'}
QUALITIES = {'auto', 'low', 'medium', 'high'}


def progress(phase, message, **details):
    print(json.dumps({'phase': phase, 'message': message, **details}), file=sys.stderr, flush=True)


def validate_png(data: bytes, size: str) -> None:
    if not 45 <= len(data) <= MAX_BYTES or not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Image provider did not return a valid bounded PNG')
    offset = 8; dimensions = None; has_pixels = False; ended = False; compressed = []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated generated PNG')
        length = struct.unpack('>I', data[offset:offset+4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('Truncated generated PNG chunk')
        kind = data[offset+4:offset+8]; content = data[offset+8:end-4]
        if zlib.crc32(kind + content) & 0xffffffff != struct.unpack('>I', data[end-4:end])[0]:
            raise ValueError('Generated PNG failed checksum verification')
        if offset == 8:
            if kind != b'IHDR' or length != 13:
                raise ValueError('Generated PNG is missing its image header')
            dimensions = struct.unpack('>II', content[:8])
            if dimensions != tuple(map(int, size.split('x'))):
                raise ValueError('Generated PNG has unexpected dimensions')
            depth, color, compression, filtering, interlace = content[8:]
            if compression != 0 or filtering != 0 or interlace not in (0, 1):
                raise ValueError('Generated PNG has an invalid encoding')
        if kind == b'IDAT':
            has_pixels = True
            compressed.append(content)
        if kind == b'IEND':
            ended = length == 0 and end == len(data)
            break
        offset = end
    if dimensions != tuple(map(int, size.split('x'))) or not has_pixels or not ended:
        raise ValueError('Generated PNG has unexpected dimensions or missing pixels')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if channels is None or depth not in (1, 2, 4, 8, 16):
        raise ValueError('Generated PNG has an invalid color format')
    width, height = dimensions
    limit = width * height * 8 + height * 8 + 1024
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(b''.join(compressed), limit + 1)
    except zlib.error:
        raise ValueError('Generated PNG pixel data cannot be decoded') from None
    if len(pixels) > limit or not decoder.eof or decoder.unused_data:
        raise ValueError('Generated PNG pixel data is truncated or too large')
    if interlace == 0:
        row = (width * channels * depth + 7) // 8 + 1
        if len(pixels) != height * row or any(pixels[offset] > 4 for offset in range(0, len(pixels), row)):
            raise ValueError('Generated PNG has malformed scanlines')


def api_open(request, timeout):
    context = tls_context()
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, *_args, **_kwargs):
            raise urllib.error.HTTPError(request.full_url, 302, 'Unexpected authenticated API redirect', {}, None)
    return urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context)).open(request, timeout=timeout)


def generate(spec: dict, output: Path, *, key: str | None = None, opener=None) -> dict:
    prompt = spec.get('prompt'); model = spec.get('model', 'gpt-image-2')
    size = spec.get('size', '1536x1024'); quality = spec.get('quality', 'medium')
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
        raise ValueError('Image generation needs a prompt under 12000 characters')
    if not isinstance(model, str) or not model.startswith('gpt-image-') or len(model) > 100:
        raise ValueError('Choose a GPT image model supported by your OpenAI account')
    if size not in SIZES or quality not in QUALITIES:
        raise ValueError('Choose a supported image size and quality')
    body = {'model': model, 'prompt': prompt.strip(), 'size': size, 'quality': quality, 'n': 1, 'output_format': 'png'}
    identity = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    image = output / 'image.png'; receipt = output / 'asset.json'
    if image.is_file() and receipt.is_file():
        saved = json.loads(receipt.read_text(encoding='utf-8'))
        data = image.read_bytes()
        if saved.get('inputHash') == identity and saved.get('sha256') == hashlib.sha256(data).hexdigest():
            validate_png(data, size)
            progress('assets', 'Reusing verified generated image', artifact=str(image))
            return {'ready': True, 'image': str(image), 'provenance': saved, 'reused': True}
        raise ValueError('Existing generated image changed or belongs to another prompt; choose a fresh output directory')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Image output contains an incomplete or different asset; choose a fresh output directory')
    secret = key if key is not None else os.environ.get('OPENAI_API_KEY', '')
    if not secret or any(ord(char) < 32 for char in secret):
        raise ValueError('Configure an OpenAI image API key before generation; uploaded images and text cards remain available')
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + secret})
    progress('assets', 'Generating scene image with OpenAI', model=model, size=size, quality=quality)
    try:
        with (opener or api_open)(request, timeout=600) as response:
            raw = response.read((MAX_BYTES + 2) // 3 * 4 + 100000)
        payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Image provider returned HTTP {error.code}; check account access, model, quota and API key. No image was published.') from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError('Image request did not finish. Check the connection before retrying; the provider may have processed the request.') from None
    rows = payload.get('data') if isinstance(payload, dict) else None
    encoded = rows[0].get('b64_json') if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict) else None
    if not isinstance(encoded, str) or len(encoded) > (MAX_BYTES + 2) // 3 * 4:
        raise ValueError('Image provider did not return bounded base64 PNG data')
    data = base64.b64decode(encoded, validate=True)
    validate_png(data, size)
    record = {'provider': 'openai', 'model': model, 'prompt': body['prompt'], 'size': size, 'quality': quality,
              'createdAt': datetime.now(timezone.utc).isoformat(), 'inputHash': identity,
              'sha256': hashlib.sha256(data).hexdigest(), 'image': 'image.png',
              'rightsReviewRequired': True, 'sourceType': 'generated', 'termsUrl': 'https://openai.com/policies/terms-of-use/'}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = output.with_name(output.name + '.work-' + uuid.uuid4().hex)
    stage.mkdir()
    (stage / 'image.png').write_bytes(data)
    (stage / 'asset.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    if output.exists(): output.rmdir()
    stage.replace(output)
    progress('assets', 'Generated image verified; review before publishing', artifact=str(image))
    return {'ready': True, 'image': str(image), 'provenance': record, 'reused': False}


def interrupted(_number, _frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted); signal.signal(signal.SIGINT, interrupted)
    try:
        if args.request.stat().st_size > 100000:
            raise ValueError('Image request is too large')
        result = generate(json.loads(args.request.read_text(encoding='utf-8')), args.out.resolve())
    except KeyboardInterrupt:
        result = {'ready': False, 'status': 'cancelled', 'error': 'Image generation cancelled locally. The hosted provider may continue processing.'}
    except Exception as error:
        result = {'ready': False, 'error': str(error)}
    print(json.dumps(result))
    return 0 if result.get('ready') else 1

if __name__ == '__main__': raise SystemExit(main())
