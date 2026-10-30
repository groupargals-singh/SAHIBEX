from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import wave

import pytest

from core.brain.speech_recognition import (
    MAX_AUDIO_BYTES,
    LocalWhisperCppRecognizer,
    SpeechRecognitionError,
)


def make_wav(path: Path, seconds: float = 1.0, rate: int = 16_000, channels: int = 1, width: int = 2) -> Path:
    count = int(seconds * rate)
    path.write_bytes(b"")
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(width)
        stream.setframerate(rate)
        stream.writeframes(b"\x00" * count * channels * width)
    return path


def test_validate_accepts_16khz_pcm_mono_and_computes_duration(tmp_path: Path) -> None:
    path = make_wav(tmp_path / "speech.wav", 2.0)
    assert LocalWhisperCppRecognizer.validate_wav(path) == 2.0


@pytest.mark.parametrize("kwargs", [
    {"rate": 8_000}, {"channels": 2}, {"width": 1},
])
def test_validate_rejects_wrong_wav_format(tmp_path: Path, kwargs: dict) -> None:
    path = make_wav(tmp_path / "bad.wav", **kwargs)
    with pytest.raises(SpeechRecognitionError) as error:
        LocalWhisperCppRecognizer.validate_wav(path)
    assert error.value.code == "audio_format_invalid"


def test_validate_rejects_long_audio(tmp_path: Path) -> None:
    path = make_wav(tmp_path / "long.wav", 21.0)
    with pytest.raises(SpeechRecognitionError) as error:
        LocalWhisperCppRecognizer.validate_wav(path)
    assert error.value.code == "audio_size_invalid"


def test_validate_rejects_malformed_wav(tmp_path: Path) -> None:
    path = tmp_path / "invalid.wav"
    path.write_bytes(b"not a wav file, even though it is longer than forty-four bytes".ljust(60, b"!"))
    with pytest.raises(SpeechRecognitionError) as error:
        LocalWhisperCppRecognizer.validate_wav(path)
    assert error.value.code == "audio_format_invalid"


def test_missing_engine_fails_closed_after_validating_audio(tmp_path: Path) -> None:
    wav = make_wav(tmp_path / "valid.wav")
    recognizer = LocalWhisperCppRecognizer(tmp_path / "missing-whisper", tmp_path / "missing-model")
    with pytest.raises(SpeechRecognitionError) as error:
        recognizer.transcribe(wav)
    assert error.value.code == "asr_engine_unavailable"


def test_local_whisper_adapter_parses_json_without_network_calls(tmp_path: Path) -> None:
    wav = make_wav(tmp_path / "valid.wav", 0.5)
    engine = tmp_path / "fake-whisper-cli"
    engine.write_text(
        "#!/data/data/com.termux/files/usr/bin/bash\n"
        "out=''\nwhile [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = '-of' ]; then shift; out=\"$1\"; fi\n"
        "  shift\ndone\n"
        "printf '%s' '{\"transcription\":[{\"text\":\" Namaste SAHIBEX.\"}],\"result\":{\"language\":\"hi\"}}' > \"$out.json\"\n",
        encoding="utf-8",
    )
    engine.chmod(0o700)
    model = tmp_path / "fake-model.bin"
    model.write_bytes(b"m" * 1_000_001)
    result = LocalWhisperCppRecognizer(engine, model).transcribe(wav)
    assert result.transcript == "Namaste SAHIBEX."
    assert result.engine == "whisper.cpp"
    assert result.mode == "local_offline"
    assert result.language == "hi"
    assert result.duration_seconds == 0.5


def test_ready_requires_executable_and_model(tmp_path: Path) -> None:
    assert not LocalWhisperCppRecognizer(tmp_path / "no", tmp_path / "no-model").is_ready()


def test_transcribe_rejects_unsupported_language_hint(tmp_path: Path) -> None:
    wav = make_wav(tmp_path / "valid.wav", 0.5)
    engine = LocalWhisperCppRecognizer(tmp_path / "missing-whisper", tmp_path / "missing-model")
    with pytest.raises(SpeechRecognitionError) as error:
        engine.transcribe(wav, language_hint="fr")
    assert error.value.code == "language_hint_invalid"


def test_transcribe_accepts_explicit_hindi_and_english_hints(tmp_path: Path) -> None:
    wav = make_wav(tmp_path / "valid.wav", 0.5)
    engine = LocalWhisperCppRecognizer(tmp_path / "missing-whisper", tmp_path / "missing-model")
    for language in ("hi", "en", "auto"):
        with pytest.raises(SpeechRecognitionError) as error:
            engine.transcribe(wav, language_hint=language)
        assert error.value.code == "asr_engine_unavailable"
