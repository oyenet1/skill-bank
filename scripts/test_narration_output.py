"""Failed narration must preserve the user's previous output."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class NarrationOutput(unittest.TestCase):
    def load_generator(self):
        spec = importlib.util.spec_from_file_location('audit_kokoro_generate', ROOT / 'course-creator/tools/kokoro/generate.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'kokoro_onnx': Mock(), 'soundfile': Mock(), 'espeakng_loader': Mock()}):
            spec.loader.exec_module(module)
        return module

    def test_failed_encoding_preserves_previous_output_and_cleans_staging(self):
        module = self.load_generator()
        module.Kokoro.return_value.create.return_value = ([0.1, 0.2], 24000)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
                (root / name).write_bytes(b'fixture')
            output = root / 'existing.wav'
            output.write_bytes(b'previous narration')
            module.sf.write.side_effect = OSError('disk write failed')
            with patch.object(module.sys, 'stderr', new_callable=io.StringIO):
                code = module.main(['--text', 'hello', '--models-dir', str(root), '--out', str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(output.read_bytes(), b'previous narration')
            self.assertEqual(list(root.glob('.audio-*')), [])

    def test_invalid_speed_fails_before_loading_models(self):
        module = self.load_generator()
        for speed in ('0', '-1', 'nan', 'inf'):
            with self.subTest(speed=speed), patch.object(module.sys, 'stderr', new_callable=io.StringIO):
                self.assertEqual(module.main(['--text', 'hello', '--speed', speed, '--out', 'audio.wav']), 1)
        module.Kokoro.assert_not_called()


if __name__ == '__main__':
    unittest.main()
