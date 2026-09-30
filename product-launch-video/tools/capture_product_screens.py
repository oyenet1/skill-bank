#!/usr/bin/env python3
"""Capture real responsive product screens using a private Playwright runtime."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit
from ensure_video_runtime import (MANIFEST, default_runtime_dir, resolve_node,
                                  install_profile, browser_ready, run, environment)


def validate(plan):
    if not isinstance(plan, dict):
        raise ValueError('Capture plan must be an object')
    url = urlsplit(plan.get('baseUrl', ''))
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
        raise ValueError('baseUrl must be an HTTP(S) URL without embedded credentials')
    profiles = plan.get('profiles', ['desktop'])
    if not isinstance(profiles, list) or not profiles or any(p not in ('desktop', 'mobile') for p in profiles) or len(set(profiles)) != len(profiles):
        raise ValueError('profiles must contain desktop, mobile, or both without duplicates')
    screens = plan.get('screens')
    if not isinstance(screens, list) or not screens:
        raise ValueError('Provide at least one named screen')
    import re
    names = set()
    for screen in screens:
        name = screen.get('name', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', name) or name in names:
            raise ValueError('Screen names must be unique filename-safe identifiers')
        names.add(name)
        for action in screen.get('steps', []):
            validate_action(action)
    login = plan.get('login', {})
    for action in login.get('steps', []):
        validate_action(action)
    if login and not login.get('readySelector'):
        raise ValueError('Login requires readySelector to verify success before capture')
    return plan


def validate_action(action):
    if action.get('action') not in ('click', 'fill', 'wait', 'press') or not action.get('selector'):
        raise ValueError('Steps require click/fill/wait/press and a selector')
    if action['action'] == 'fill' and not action.get('valueEnv'):
        raise ValueError('Fill values must reference environment variables via valueEnv')


def capture(plan_path, out, runtime, headed=False, session=None):
    plan_path, out = plan_path.resolve(), out.resolve()
    validate(json.loads(plan_path.read_text(encoding='utf-8')))
    if out.exists() and any(out.iterdir()):
        raise ValueError('Capture output directory must be empty')
    node, npm = resolve_node(runtime, True)
    spec = {'packages': {'playwright-chromium': MANIFEST['profiles']['slidev']['packages']['playwright-chromium']}, 'binary': 'playwright'}
    install_profile('capture', spec, runtime, node, npm, True)
    profile = runtime / 'capture'
    if not browser_ready(profile, node):
        run([node, profile / 'node_modules/playwright-chromium/cli.js', 'install', 'chromium'], node, cwd=profile)
    if session:
        session = session.resolve()
        if session.is_relative_to(out):
            raise ValueError('Session file must stay outside captured/exported assets')
        if not session.is_file():
            raise ValueError('Session file does not exist')
    command = [str(node), str(Path(__file__).with_name('capture_product_screens.cjs')),
               str(profile / 'node_modules/playwright-chromium'), str(plan_path), str(out),
               'headed' if headed else 'headless', str(session) if session else '']
    result = subprocess.run(command, env=environment(node), capture_output=True, text=True)
    if result.returncode:
        # Browser exception text can contain credentials, selector values or URL tokens.
        raise RuntimeError('Capture failed. Check access, login success selector, screen selectors, and browser dependencies. No credential-bearing browser log was saved.')
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runtime-dir', type=Path, default=default_runtime_dir())
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--session', type=Path, help='Existing private Playwright storage-state file')
    args = parser.parse_args()
    try:
        print(json.dumps(capture(args.plan, args.out, args.runtime_dir, args.headed, args.session)))
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({'ready': False, 'error': str(exc)}), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
