"""Real bundled sibling installation and refusal of corrupt/unsafe input."""
import base64
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills-src/_shared/tools'))
import install_sibling_skill as siblings


class SiblingSkillTests(unittest.TestCase):
    def payload(self, root, entries, digest=None):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name, contents in entries:
                if isinstance(name, zipfile.ZipInfo):
                    archive.writestr(name, contents)
                else:
                    archive.writestr(name, contents)
        data = stream.getvalue()
        path = root / 'payload.json'
        path.write_text(json.dumps({'schemaVersion': 1, 'skills': ['fixture'],
            'sha256': digest or hashlib.sha256(data).hexdigest(),
            'zipBase64': base64.b64encode(data).decode()}))
        return path

    def test_real_snapshot_installs_to_exact_target_and_preserves_bootstrap_and_kokoro(self):
        payload = ROOT / 'explainer-video/tools/sibling_skills.json'
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'skills with spaces'
            result = siblings.install('voice-narration', target, payload)
            skill = target / 'voice-narration'
            self.assertTrue(result['ready'])
            self.assertEqual((skill / 'SKILL.md').read_bytes(), (ROOT / 'voice-narration/SKILL.md').read_bytes())
            self.assertEqual((skill / 'tools/kokoro/start.py').read_bytes(), (ROOT / 'course-creator/tools/kokoro/start.py').read_bytes())
            self.assertEqual((skill / 'tools/sibling_skills.json').read_bytes(), payload.read_bytes())
            (skill / 'SKILL.md').write_text('User edits')
            self.assertTrue(siblings.install('voice-narration', target, payload)['reused'])
            self.assertEqual((skill / 'SKILL.md').read_text(), 'User edits')
            self.assertEqual(set(path.name for path in target.iterdir()), {'voice-narration'})

    def test_invalid_digest_and_missing_skill_do_not_create_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root / 'target'
            payload = self.payload(root, [('fixture/SKILL.md', 'fixture')], digest='0' * 64)
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                siblings.install('fixture', target, payload)
            self.assertFalse(target.exists())
            with self.assertRaisesRegex(ValueError, 'does not contain'):
                siblings.install('missing', target, payload)

    def test_unsafe_entries_and_recursive_payloads_are_refused(self):
        link = zipfile.ZipInfo('fixture/link'); link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for name in ('fixture/../../outside', '/absolute', 'fixture\\outside', 'fixture/C:bad', 'fixture/tools/sibling_skills.json', link):
            with self.subTest(name=str(name)), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); target = root / 'target'
                payload = self.payload(root, [('fixture/SKILL.md', 'fixture'), (name, 'bad')])
                with self.assertRaises(ValueError):
                    siblings.install('fixture', target, payload)
                self.assertFalse(target.exists())

    def test_existing_incomplete_directory_and_symlink_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root / 'target'; destination = target / 'fixture'
            destination.mkdir(parents=True); (destination / 'user.txt').write_text('Keep')
            payload = self.payload(root, [('fixture/SKILL.md', 'fixture')])
            with self.assertRaisesRegex(ValueError, 'already exists'):
                siblings.install('fixture', target, payload)
            self.assertEqual((destination / 'user.txt').read_text(), 'Keep')
            destination.rename(target / 'old')
            try:
                destination.symlink_to(target / 'old', target_is_directory=True)
            except OSError:
                return  # Windows can forbid symlinks without developer mode.
            with self.assertRaisesRegex(ValueError, 'symbolic link'):
                siblings.install('fixture', target, payload)

    def test_bad_names_and_missing_manifest_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); target = root / 'target'
            payload = self.payload(root, [('fixture/not-skill.md', 'fixture')])
            for name in ('../outside', '', 'C:bad'):
                with self.assertRaisesRegex(ValueError, 'Invalid'):
                    siblings.install(name, target, payload)
            with self.assertRaisesRegex(ValueError, 'SKILL.md'):
                siblings.install('fixture', target, payload)
            self.assertFalse(target.exists())


if __name__ == '__main__': unittest.main()
