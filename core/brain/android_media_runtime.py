from __future__ import annotations

import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaCapability:
    name: str
    available: bool
    executable: str | None
    detail: str


class AndroidMediaRuntime:
    """Opt-in Termux:API bridge. Never opens mic/camera or speaks without explicit consent."""

    COMMANDS = {
        "speech_to_text": "termux-speech-to-text",
        "text_to_speech": "termux-tts-speak",
        "camera_photo": "termux-camera-photo",
        "microphone_record": "termux-microphone-record",
    }

    def __init__(self, *, capture_dir: str | Path | None = None, timeout_seconds: int = 45):
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 180:
            raise ValueError("timeout_seconds must be an integer from 1 to 180")
        self.capture_dir = Path(capture_dir or (Path.home() / "SAHIBEX" / "data" / "captures")).expanduser().resolve()
        self.timeout_seconds = timeout_seconds

    def status(self) -> dict[str, MediaCapability]:
        result = {}
        for name, command in self.COMMANDS.items():
            executable = shutil.which(command)
            result[name] = MediaCapability(
                name=name,
                available=executable is not None,
                executable=executable,
                detail="CLI found; Android API app/permissions still require a real operation" if executable else "CLI missing; install a compatible Termux:API app and termux-api package",
            )
        return result

    @staticmethod
    def _require_consent(consent: bool) -> None:
        if consent is not True:
            raise PermissionError("Explicit user consent is required for microphone, camera, or speaker access")

    @staticmethod
    def _run(args: list[str], timeout: int, *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        """Run without a shell and kill the whole child process group on timeout."""
        try:
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except OSError as exc:
            raise RuntimeError(f"Unable to launch Android media command: {exc}") from exc
        try:
            stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate()
            raise TimeoutError(f"Android media command timed out after {timeout}s") from exc
        return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)

    def transcribe_once(self, *, consent: bool = False) -> str:
        self._require_consent(consent)
        command = shutil.which(self.COMMANDS["speech_to_text"])
        if not command:
            raise RuntimeError("termux-speech-to-text is unavailable")
        result = self._run([command], self.timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Speech recognition failed")[:1000])
        text = result.stdout.strip()
        if not text:
            raise RuntimeError("Speech recognition returned no text")
        return text[:8192]

    def speak(self, text: str, *, consent: bool = False) -> None:
        self._require_consent(consent)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        if len(text) > 4000:
            raise ValueError("text exceeds 4000 characters")
        command = shutil.which(self.COMMANDS["text_to_speech"])
        if not command:
            raise RuntimeError("termux-tts-speak is unavailable")
        # Termux:API's documented interface reads the utterance from stdin.
        result = self._run([command], self.timeout_seconds, input_text=text.strip() + "\n")
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Text-to-speech failed")[:1000])

    def capture_photo(self, *, consent: bool = False, camera_id: int = 0) -> Path:
        self._require_consent(consent)
        if camera_id not in (0, 1):
            raise ValueError("camera_id must be 0 (back) or 1 (front)")
        command = shutil.which(self.COMMANDS["camera_photo"])
        if not command:
            raise RuntimeError("termux-camera-photo is unavailable")
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        target = (self.capture_dir / "latest_capture.jpg").resolve()
        if target.parent != self.capture_dir:
            raise ValueError("Capture path escaped the configured capture directory")
        result = self._run([command, "-c", str(camera_id), str(target)], self.timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Camera capture failed")[:1000])
        if not target.is_file() or target.stat().st_size <= 0:
            raise RuntimeError("Camera command returned without a non-empty image")
        return target
