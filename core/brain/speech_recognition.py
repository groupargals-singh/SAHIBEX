from __future__ import annotations

"""Offline, local-only speech recognition adapter for SAHIBEX.

The adapter invokes a locally installed whisper.cpp CLI and local multilingual
model. It never sends audio to a network service. Missing runtime/model fails
closed; it does not silently fall back to Android or cloud recognition.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass


MAX_AUDIO_BYTES = 640_044  # 20 seconds of 16 kHz mono PCM16 plus a WAV header
SAMPLE_RATE = 16_000
MAX_DURATION_SECONDS = 20.0
DEFAULT_ASR_PROMPT = (
    "SAHIBEX, Main Brain, Termux, Hindi, Hinglish, dictionary, microphone, "
    "speech recognition, awaaz, akshar, shabd, samjho, samjhao, batao, karo, nahi"
)


class SpeechRecognitionError(RuntimeError):
    """A safe, user-presentable recognition failure with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SpeechRecognitionResult:
    transcript: str
    engine: str
    mode: str
    language: str | None
    duration_seconds: float


class LocalWhisperCppRecognizer:
    """Run whisper.cpp as a bounded local subprocess against a WAV file."""

    def __init__(
        self,
        executable: str | Path | None = None,
        model_path: str | Path | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        configured_executable = executable or os.environ.get("SAHIBEX_WHISPER_CLI")
        self.executable = (
            Path(configured_executable).expanduser()
            if configured_executable
            else Path.home() / ".local" / "bin" / "whisper-cli"
        )
        configured_model = model_path or os.environ.get("SAHIBEX_ASR_MODEL")
        self.model_path = (
            Path(configured_model).expanduser()
            if configured_model
            else Path.home() / ".local" / "share" / "sahibex" / "asr-models" / "ggml-tiny-q5_1.bin"
        )
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 120.0))

    @staticmethod
    def validate_wav(audio_path: str | Path) -> float:
        path = Path(audio_path)
        try:
            if not path.is_file():
                raise SpeechRecognitionError("audio_missing", "Audio file is missing.")
            size = path.stat().st_size
            if size < 44 or size > MAX_AUDIO_BYTES:
                raise SpeechRecognitionError("audio_size_invalid", "Audio size is outside the allowed limit.")
            with wave.open(str(path), "rb") as audio:
                if audio.getcomptype() != "NONE":
                    raise SpeechRecognitionError("audio_format_invalid", "Audio must be uncompressed PCM WAV.")
                if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != SAMPLE_RATE:
                    raise SpeechRecognitionError(
                        "audio_format_invalid", "Audio must be mono, 16-bit PCM at 16 kHz."
                    )
                frames = audio.getnframes()
                rate = audio.getframerate()
                duration = frames / float(rate)
                if frames <= 0 or duration > MAX_DURATION_SECONDS:
                    raise SpeechRecognitionError("audio_duration_invalid", "Audio must be between 0 and 20 seconds.")
                if duration < 0.15:
                    raise SpeechRecognitionError("audio_duration_invalid", "Audio is too short to transcribe.")
                expected_bytes = 44 + frames * audio.getnchannels() * audio.getsampwidth()
                if abs(size - expected_bytes) > 4096:
                    raise SpeechRecognitionError("audio_format_invalid", "WAV file structure is not accepted.")
                return duration
        except SpeechRecognitionError:
            raise
        except (OSError, wave.Error, EOFError) as exc:
            raise SpeechRecognitionError("audio_format_invalid", "Audio is not a valid PCM WAV file.") from exc

    def is_ready(self) -> bool:
        return self.executable.is_file() and os.access(self.executable, os.X_OK) and self.model_path.is_file()

    def transcribe(self, audio_path: str | Path, *, language_hint: str = "auto") -> SpeechRecognitionResult:
        path = Path(audio_path)
        if language_hint not in {"auto", "hi", "en"}:
            raise SpeechRecognitionError("language_hint_invalid", "Language hint must be auto, hi, or en.")
        duration = self.validate_wav(path)
        if not self.executable.is_file() or not os.access(self.executable, os.X_OK):
            raise SpeechRecognitionError(
                "asr_engine_unavailable",
                "SAHIBEX local speech engine is not installed. Run scripts/setup_offline_asr.sh.",
            )
        if not self.model_path.is_file() or self.model_path.stat().st_size < 1_000_000:
            raise SpeechRecognitionError(
                "asr_model_unavailable",
                "SAHIBEX local speech model is missing. Run scripts/setup_offline_asr.sh.",
            )
        with tempfile.TemporaryDirectory(prefix="sahibex-whisper-result-") as temp_dir:
            output_base = str(Path(temp_dir) / "transcript")
            prompt = os.environ.get("SAHIBEX_ASR_INITIAL_PROMPT", DEFAULT_ASR_PROMPT)
            prompt = prompt.strip()[:512] if isinstance(prompt, str) else DEFAULT_ASR_PROMPT
            command = [
                str(self.executable), "-m", str(self.model_path), "-f", str(path),
                "-l", language_hint, "--prompt", prompt, "-oj", "-of", output_base,
                "-np", "-nt", "-ng", "-t", "2",
            ]
            try:
                completed = subprocess.run(
                    command, cwd=temp_dir, capture_output=True, text=True,
                    timeout=self.timeout_seconds, check=False,
                    env={**os.environ, "OMP_NUM_THREADS": "2"},
                )
            except subprocess.TimeoutExpired as exc:
                raise SpeechRecognitionError(
                    "asr_timeout", "SAHIBEX local speech recognition timed out; try a shorter recording."
                ) from exc
            except OSError as exc:
                raise SpeechRecognitionError("asr_engine_error", "SAHIBEX local speech engine could not start.") from exc
            result_file = Path(output_base + ".json")
            if completed.returncode != 0 or not result_file.is_file():
                raise SpeechRecognitionError(
                    "asr_engine_error", "SAHIBEX local speech engine failed to produce a transcript."
                )
            try:
                result_json = json.loads(result_file.read_text(encoding="utf-8"))
                segments = result_json.get("transcription", [])
                transcript = " ".join(
                    str(item.get("text", "")).strip()
                    for item in segments if isinstance(item, dict) and str(item.get("text", "")).strip()
                ).strip()
                result_meta = result_json.get("result", {})
                language = result_meta.get("language") if isinstance(result_meta, dict) else None
                if not language:
                    language = result_json.get("language")
            except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
                raise SpeechRecognitionError("asr_output_invalid", "SAHIBEX received an invalid local transcript result.") from exc
            if not transcript:
                raise SpeechRecognitionError("no_speech_detected", "No clear speech was detected. Please try again.")
            return SpeechRecognitionResult(
                transcript=transcript[:8_192], engine="whisper.cpp",
                mode="local_offline", language=str(language) if language else None,
                duration_seconds=duration,
            )
