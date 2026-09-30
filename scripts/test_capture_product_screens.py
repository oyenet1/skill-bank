import importlib.util
import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'skills-src/_shared/tools'
sys.path.insert(0, str(TOOLS))
import capture_product_screens as capture

class CapturePlanTests(unittest.TestCase):
    def test_desktop_mobile_plan(self):
        plan = {'baseUrl': 'http://localhost:3000', 'profiles': ['desktop', 'mobile'], 'screens': [{'name': 'home'}]}
        self.assertEqual(capture.validate(plan), plan)

    def test_rejects_credential_url_and_unsafe_names(self):
        for url, name in [('https://user:secret@example.com', 'home'), ('https://example.com', '../secret')]:
            with self.assertRaises(ValueError):
                capture.validate({'baseUrl': url, 'screens': [{'name': name}]})

    def test_requires_login_success_and_environment_credentials(self):
        for login in [ {'steps': []}, {'readySelector': 'main', 'steps': [{'action': 'fill', 'selector': '#password', 'value': 'secret'}]} ]:
            with self.assertRaises(ValueError):
                capture.validate({'baseUrl': 'https://example.com', 'screens': [{'name': 'home'}], 'login': login})

    def test_duplicate_names_and_profiles(self):
        for changes in [{'profiles': ['mobile', 'mobile']}, {'screens': [{'name': 'home'}, {'name': 'home'}]}]:
            with self.assertRaises(ValueError):
                capture.validate({'baseUrl': 'https://example.com', 'screens': [{'name': 'home'}], **changes})

    def test_generated_capture_files(self):
        root = TOOLS.parents[2]
        for target in ['explainer-video', 'product-launch-video', 'course-creator/subskills/course-creator-explainer-video', 'course-creator/subskills/course-creator-product-launch-video']:
            self.assertTrue((root / target / 'tools/capture_product_screens.cjs').is_file())
            self.assertIn('30-second fallback', (root / target / 'references/intake.md').read_text())

if __name__ == '__main__':
    unittest.main()
