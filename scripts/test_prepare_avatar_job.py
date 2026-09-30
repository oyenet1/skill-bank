"""Exercise presenter pre-generation handoff with actual media and stub inference."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts import test_run_desktop_video_job as desktop_tests
DESKTOP = desktop_tests.DESKTOP
import run_video_job as runner

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class AvatarJobTests(unittest.TestCase):
    def request(self, root):
        payload = desktop_tests.DesktopVideoJobTests().payload(root)
        wav = root / 'voice.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.7', str(wav)], check=True)
        payload['request'].update(jobRoute='avatar-video', renderer='scenes', avatar={
            'provider': 'local', 'mode': 'photo', 'backend': 'fixture', 'rightsConfirmed': True,
            'image': {'name': 'portrait.png', 'mime': 'image/png', 'dataBase64': base64.b64encode((root/'card.png').read_bytes()).decode()}})
        payload['request']['scenes'][0]['audioWavBase64'] = base64.b64encode(wav.read_bytes()).decode()
        source = root/'form.json'; source.write_text(json.dumps(payload))
        return source

    def test_verified_clip_handoff_resume_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = self.request(root)
            execute = runner.command_result
            calls = []
            def generate(command, log):
                if any(str(arg).endswith('avatar_generate.py') for arg in command):
                    calls.append(command)
                    directory = Path(command[command.index('--out')+1]); directory.mkdir(parents=True)
                    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=green:s=320x180:d=0.7', '-i', str(root/'voice.wav'), '-c:v', 'libx264', '-c:a', 'aac', '-shortest', str(directory/'video.mp4')], check=True)
                    private = directory/'.work-fixture/models'; private.mkdir(parents=True); (private/'large-weight.bin').write_bytes(b'private runtime fixture')
                    (directory/'manifest.json').write_text(json.dumps({'provider':'local', 'backend':'fixture', 'accelerator':{'kind':'cuda'}, 'consent':{'acceptedAt':'fixture'}}))
                    return {'ready':True}
                return execute(command, log)
            with patch.object(runner, 'command_result', side_effect=generate):
                result = DESKTOP.run_desktop_job(source, root/'job')
                self.assertTrue(result['ready'])
                manifest = json.loads((Path(result['directory'])/'manifest.json').read_text())
                self.assertEqual(manifest['avatar'][0]['provider'], 'local')
                self.assertTrue((root/'job/inputs/avatar-fallback/narration.wav').is_file())
                self.assertTrue((root/'job/inputs/avatar-fallback/audio.mp3').is_file())
                self.assertTrue(DESKTOP.run_desktop_job(source, root/'job', resume=True)['ready'])
                self.assertEqual(len(calls), 1)
                self.assertEqual(list((Path(result['directory'])/'source/desktop').rglob('large-weight.bin')), [])

    def test_failed_inference_preserves_real_fallback_and_job_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = self.request(root)
            execute = runner.command_result
            def fail(command, log):
                if any(str(arg).endswith('avatar_generate.py') for arg in command):
                    raise RuntimeError('fixture inference failed')
                return execute(command, log)
            with patch.object(runner, 'command_result', side_effect=fail), self.assertRaisesRegex(RuntimeError, 'inference failed'):
                DESKTOP.run_desktop_job(source, root/'job')
            fallback = root/'job/inputs/avatar-fallback'
            for name in ('script.md', 'storyboard.md', 'narration.wav', 'audio.mp3'):
                self.assertTrue((fallback/name).is_file())
            self.assertFalse((root/'job/output/video.mp4').exists())
            self.assertEqual(json.loads((root/'job/output.job-state.json').read_text())['status'], 'failed')

if __name__ == '__main__': unittest.main()
