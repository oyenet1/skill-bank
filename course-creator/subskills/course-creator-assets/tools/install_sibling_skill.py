"""Install a sibling from the generated snapshot into the requested skill root."""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

PAYLOAD = Path(__file__).with_name('sibling_skills.json')
MAX_BYTES = 32_000_000


def _install_one(name: str, root: Path, payload: Path = PAYLOAD) -> dict:
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}', name):
        raise ValueError('Invalid sibling skill name')
    root = root.expanduser().resolve()
    destination = root / name
    if destination.is_symlink():
        raise ValueError('Sibling destination is a symbolic link; no files were changed')
    if (destination / 'SKILL.md').is_file():
        return {'ready': True, 'skill': name, 'path': str(destination), 'reused': True}
    if destination.exists():
        raise ValueError('Sibling destination already exists without SKILL.md; no files were overwritten')
    if payload.stat().st_size > MAX_BYTES:
        raise ValueError('Sibling snapshot exceeds its allowed size')
    document = json.loads(payload.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or document.get('schemaVersion') != 1 or name not in document.get('skills', []):
        raise ValueError('The bundled snapshot does not contain this sibling skill')
    data = base64.b64decode(document['zipBase64'], validate=True)
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != document['sha256']:
        raise ValueError('Sibling snapshot failed SHA-256 verification')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = []
        expanded = 0
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if (path.is_absolute() or '\\' in member.filename or ':' in member.filename
                    or '..' in path.parts or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('Sibling snapshot contains an unsafe entry')
            if len(path.parts) < 2 or path.parts[0] != name:
                continue
            if member.is_dir():
                continue
            expanded += member.file_size
            if expanded > MAX_BYTES or len(members) >= 5000:
                raise ValueError('Expanded sibling snapshot exceeds its allowed size')
            relative = path.relative_to(name)
            if relative.as_posix() == 'tools/sibling_skills.json':
                raise ValueError('Sibling snapshot contains a recursive payload')
            members.append((member, relative))
        if not any(relative.as_posix() == 'SKILL.md' for _, relative in members):
            raise ValueError('Sibling snapshot is missing SKILL.md')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f'.{name}-install-', dir=root) as scratch:
            staged = Path(scratch) / name
            staged.mkdir()
            for member, relative in members:
                target = staged / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                # Select safe names rather than extracting arbitrary archive paths.
                with archive.open(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
            if (staged / 'tools/bootstrap.py').is_file():
                shutil.copyfile(payload, staged / 'tools/sibling_skills.json')
            if destination.exists() or destination.is_symlink():
                raise ValueError('Sibling destination appeared during installation; no files were overwritten')
            staged.rename(destination)
    return {'ready': True, 'skill': name, 'path': str(destination), 'snapshotSha256': document['sha256'], 'reused': False}


def dependency_order(names: list[str], payload: Path = PAYLOAD) -> list[str]:
    # Resolve the whole declared graph before publishing anything. Cycles are
    # normal for complementary video skills, so visit every skill only once.
    if payload.stat().st_size > MAX_BYTES:
        raise ValueError('Sibling snapshot exceeds its allowed size')
    document = json.loads(payload.read_text(encoding='utf-8'))
    if not isinstance(document, dict):
        raise ValueError('Invalid sibling snapshot')
    if (document.get('schemaVersion') != 1 or not isinstance(document.get('skills'), list)
            or not isinstance(document.get('zipBase64'), str)
            or not isinstance(document.get('sha256'), str)):
        raise ValueError('Invalid sibling snapshot')
    data = base64.b64decode(document['zipBase64'], validate=True)
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != document['sha256']:
        raise ValueError('Sibling snapshot failed SHA-256 verification')
    pending = list(names); ordered = []; seen = set()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        while pending:
            current = pending.pop(0)
            if not isinstance(current, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}', current):
                raise ValueError('Invalid sibling skill name')
            if current in seen:
                continue
            if current not in document['skills']:
                raise ValueError('The bundled snapshot does not contain this sibling skill')
            seen.add(current); ordered.append(current)
            try:
                info = archive.getinfo(f'{current}/tools/dependencies.json')
            except KeyError:
                continue
            if info.file_size > 65536:
                raise ValueError('Sibling dependency manifest is unexpectedly large')
            manifest = json.loads(archive.read(info))
            if not isinstance(manifest, dict) or not isinstance(manifest.get('associated', []), list):
                raise ValueError('Invalid sibling dependency list')
            pending.extend(manifest.get('associated', []))
    return ordered


def install(name: str, root: Path, payload: Path = PAYLOAD) -> dict:
    ordered = dependency_order([name], payload)
    results = [_install_one(current, root, payload) for current in ordered]
    return {**results[0], 'installedSkills': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = install(args.name, args.target)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(json.dumps({'ready': False, 'error': str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
