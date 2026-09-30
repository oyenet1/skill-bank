"""Install a hash-pinned PyPI UV binary privately, without pip or compilation."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import tempfile
import urllib.request
import zipfile

from network_tls import tls_context

PINS = json.loads(Path(__file__).with_name('uv_wheels.json').read_text(encoding='utf-8'))


def platform_key():
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {'amd64': 'x86_64', 'arm64': 'aarch64'}.get(machine, machine)
    if system == 'linux' and arch == 'x86_64':
        libc = platform.libc_ver()[0].lower()
        if libc == 'musl' or (not libc and any(Path('/lib').glob('ld-musl-*.so.1'))):
            return 'linux-musl-x86_64'
    return f'{system}-{arch}'


def install_pinned_uv(target: Path, *, opener=None, key=None):
    key = key or platform_key()
    spec = PINS['platforms'].get(key)
    if not spec:
        raise RuntimeError(f'No prebuilt private Python manager for {key}')
    binary = 'uv.exe' if key.startswith('windows-') else 'uv'
    member = f"uv-{PINS['version']}.data/scripts/{binary}"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='uv-wheel-', dir=target.parent) as scratch:
        scratch = Path(scratch)
        archive = scratch / 'uv.whl'
        digest = hashlib.sha256(); size = 0
        with (opener or urllib.request.urlopen)(spec['url'], timeout=60, context=tls_context()) as response, archive.open('wb') as output:
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > spec['size']:
                    raise RuntimeError('Python manager wheel exceeds its pinned size')
                digest.update(block); output.write(block)
        if size != spec['size'] or digest.hexdigest() != spec['sha256']:
            raise RuntimeError('Python manager wheel failed pinned SHA-256 verification')
        with zipfile.ZipFile(archive) as wheel:
            info = wheel.getinfo(member)
            if not 0 < info.file_size <= 150_000_000:
                raise RuntimeError('Python manager binary has an invalid size')
            staged = scratch / binary
            with wheel.open(info) as source, staged.open('wb') as output:
                shutil.copyfileobj(source, output)
            staged.chmod(0o755)
            # Preserve the distributed licenses beside the private executable.
            for license_name in ('LICENSE-APACHE', 'LICENSE-MIT'):
                license_member = f"uv-{PINS['version']}.dist-info/licenses/{license_name}"
                content = wheel.read(license_member)
                if len(content) > 100_000:
                    raise RuntimeError('Python manager license is unexpectedly large')
                (target.parent / f'uv-{license_name}').write_bytes(content)
            os.replace(staged, target)
    return target
