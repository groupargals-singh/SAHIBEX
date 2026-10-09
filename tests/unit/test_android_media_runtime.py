from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.brain.android_media_runtime import AndroidMediaRuntime


class AndroidMediaRuntimeTests(unittest.TestCase):
    def test_hardware_requires_explicit_consent(self):
        runtime = AndroidMediaRuntime()
        with self.assertRaises(PermissionError):
            runtime.transcribe_once()
        with self.assertRaises(PermissionError):
            runtime.speak("hello")
        with self.assertRaises(PermissionError):
            runtime.capture_photo()

    def test_status_reports_missing_tools_without_crashing(self):
        runtime = AndroidMediaRuntime()
        with patch("core.brain.android_media_runtime.shutil.which", return_value=None):
            status = runtime.status()
        self.assertEqual(set(status), {"speech_to_text", "text_to_speech", "camera_photo", "microphone_record"})
        self.assertTrue(all(not item.available for item in status.values()))

    def test_transcription_uses_argument_list_and_bounds_output(self):
        runtime = AndroidMediaRuntime()
        completed = subprocess.CompletedProcess([], 0, "  hello Sahibex  ", "")
        with patch("core.brain.android_media_runtime.shutil.which", return_value="/fake/speech"), patch.object(runtime, "_run", return_value=completed) as run:
            self.assertEqual(runtime.transcribe_once(consent=True), "hello Sahibex")
            run.assert_called_once_with(["/fake/speech"], runtime.timeout_seconds)

    def test_tts_sends_text_via_stdin(self):
        runtime = AndroidMediaRuntime()
        completed = subprocess.CompletedProcess([], 0, "", "")
        with patch("core.brain.android_media_runtime.shutil.which", return_value="/fake/tts"), patch.object(runtime, "_run", return_value=completed) as run:
            runtime.speak("hello Sahibex", consent=True)
            run.assert_called_once_with(["/fake/tts"], runtime.timeout_seconds, input_text="hello Sahibex\n")

    def test_tts_rejects_empty_or_oversized_text(self):
        runtime = AndroidMediaRuntime()
        with self.assertRaises(ValueError):
            runtime.speak(" ", consent=True)
        with self.assertRaises(ValueError):
            runtime.speak("x" * 4001, consent=True)

    def test_camera_requires_real_nonempty_output(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = AndroidMediaRuntime(capture_dir=temp)
            completed = subprocess.CompletedProcess([], 0, "", "")
            def fake_run(args, timeout):
                Path(args[-1]).write_bytes(b"jpeg-test")
                return completed
            with patch("core.brain.android_media_runtime.shutil.which", return_value="/fake/camera"), patch.object(runtime, "_run", side_effect=fake_run):
                path = runtime.capture_photo(consent=True)
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), b"jpeg-test")

    def test_invalid_camera_id_is_rejected(self):
        runtime = AndroidMediaRuntime()
        with self.assertRaises(ValueError):
            runtime.capture_photo(consent=True, camera_id=2)

    def test_timeout_kills_child_process_group(self):
        runtime = AndroidMediaRuntime(timeout_seconds=1)
        with patch("core.brain.android_media_runtime.subprocess.Popen") as popen, patch("core.brain.android_media_runtime.os.killpg") as killpg:
            process = popen.return_value
            process.pid = 1234
            process.communicate.side_effect = [subprocess.TimeoutExpired(["fake"], 1), ("", "")]
            with self.assertRaises(TimeoutError):
                runtime._run(["fake"], 1)
            killpg.assert_called_once()
            process.communicate.assert_called_with()


if __name__ == "__main__":
    unittest.main()
