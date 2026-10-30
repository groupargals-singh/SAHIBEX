"""Bounded local neural text-to-speech adapter for SAHIBEX.

Uses a locally installed Piper-compatible CLI; never downloads models or sends
text to a cloud service. Backend/model paths are explicit environment settings.
"""
from __future__ import annotations

import io
import os
import shutil
import struct
import subprocess
import threading
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

MAX_TTS_TEXT_CHARS = 4000
MAX_TTS_SECONDS = 90
MAX_TTS_WAV_BYTES = 12 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 45
MAX_SUPERTONIC_TEXT_CHARS = 1200  # phone-side inference budget; longer replies use explicit compatibility fallback
_SUPERTONIC_INIT_LOCK = threading.Lock()
_SUPERTONIC_INFERENCE_LOCK = threading.Lock()
_SUPERTONIC_ENGINE_CACHE: dict[tuple[str, int], object] = {}


class NeuralTTSError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SynthesizedSpeech:
    wav_bytes: bytes
    engine: str
    language: str
    sample_rate: int
    duration_seconds: float


def _language_key(language: str) -> str:
    value = language.strip().lower().replace('_', '-')
    if value.startswith('hi'):
        return 'hi'
    if value.startswith('en'):
        return 'en'
    raise NeuralTTSError('tts_language_unsupported', 'Only Hindi and English are enabled for local neural TTS.')


class LocalPiperTTS:
    """Synthesize speech using Piper CLI with an explicitly configured local model."""

    def __init__(self, *, executable: str | None = None, models: dict[str, str] | None = None,
                 timeout_seconds: int | None = None):
        self.executable = executable or os.getenv('SAHIBEX_PIPER_EXECUTABLE', 'piper')
        self.models = models or {
            'hi': os.getenv('SAHIBEX_PIPER_HI_MODEL', ''),
            'en': os.getenv('SAHIBEX_PIPER_EN_MODEL', ''),
        }
        try:
            configured_timeout = int(os.getenv('SAHIBEX_TTS_TIMEOUT_SECONDS', str(DEFAULT_TIMEOUT_SECONDS)))
        except ValueError:
            configured_timeout = DEFAULT_TIMEOUT_SECONDS
        self.timeout_seconds = max(5, min(timeout_seconds or configured_timeout, 60))

    def synthesize(self, text: str, language: str) -> SynthesizedSpeech:
        if not isinstance(text, str) or not text.strip():
            raise NeuralTTSError('tts_empty_text', 'Speech text must not be empty.')
        if len(text) > MAX_TTS_TEXT_CHARS:
            raise NeuralTTSError('tts_text_too_long', 'Speech text exceeds the 4000-character limit.')
        lang = _language_key(language)
        model_raw = self.models.get(lang, '')
        if not model_raw:
            raise NeuralTTSError('tts_model_unconfigured', f'No local Piper model configured for {lang}.')
        model = Path(model_raw).expanduser()
        if not model.is_file():
            raise NeuralTTSError('tts_model_unavailable', f'Configured local Piper model for {lang} is missing.')
        executable = shutil.which(self.executable) if not os.path.isabs(self.executable) else self.executable
        if not executable or not Path(executable).is_file():
            raise NeuralTTSError('tts_engine_unavailable', 'Piper executable is not installed; no fallback or download was attempted.')

        with tempfile.TemporaryDirectory(prefix='sahibex-tts-') as folder:
            output = Path(folder) / 'speech.wav'
            try:
                completed = subprocess.run(
                    [executable, '--model', str(model), '--output_file', str(output)],
                    input=text.strip() + '\n', text=True, capture_output=True,
                    timeout=self.timeout_seconds, check=False,
                    env={**os.environ, 'PYTHONNOUSERSITE': '1'},
                )
            except subprocess.TimeoutExpired as exc:
                raise NeuralTTSError('tts_timeout', 'Local speech synthesis exceeded its time limit.') from exc
            except OSError as exc:
                raise NeuralTTSError('tts_engine_error', 'Could not start the local speech engine.') from exc
            if completed.returncode != 0:
                raise NeuralTTSError('tts_engine_error', 'Local Piper synthesis failed.')
            if not output.is_file():
                raise NeuralTTSError('tts_empty_audio', 'Speech engine returned no audio file.')
            size = output.stat().st_size
            if size < 44 or size > MAX_TTS_WAV_BYTES:
                raise NeuralTTSError('tts_audio_size_invalid', 'Generated audio size is outside safe limits.')
            try:
                with wave.open(str(output), 'rb') as wav:
                    channels, width, rate, frames = wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()
                    duration = frames / float(rate) if rate else 0.0
                    if channels not in (1, 2) or width not in (1, 2, 3, 4) or not 8000 <= rate <= 48000:
                        raise NeuralTTSError('tts_audio_format_invalid', 'Generated WAV format is unsupported.')
                    if not 0 < duration <= MAX_TTS_SECONDS:
                        raise NeuralTTSError('tts_audio_duration_invalid', 'Generated speech duration is outside safe limits.')
            except (wave.Error, EOFError) as exc:
                raise NeuralTTSError('tts_audio_format_invalid', 'Speech engine did not produce a valid WAV file.') from exc
            return SynthesizedSpeech(output.read_bytes(), 'piper', lang, rate, round(duration, 3))


class LocalSherpaSupertonicTTS:
    """Offline multilingual Supertonic-3 backend via sherpa-onnx Python API.

    The model directory must be installed explicitly; this class never downloads
    model files or falls back to a network service. Supertonic model weights use
    OpenRAIL-M terms; check the bundled model README/license before distribution.
    """

    def __init__(self, *, model_dir: str | None = None, timeout_seconds: int | None = None):
        default_dir = Path.home() / '.local/share/sahibex/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11'
        self.model_dir = Path(model_dir or os.getenv('SAHIBEX_SUPERTONIC_MODEL_DIR', str(default_dir))).expanduser()
        try:
            self.timeout_seconds = max(5, min(int(timeout_seconds or os.getenv('SAHIBEX_TTS_TIMEOUT_SECONDS', '45')), 60))
        except (ValueError, TypeError):
            self.timeout_seconds = 45

    def synthesize(self, text: str, language: str) -> SynthesizedSpeech:
        if not isinstance(text, str) or not text.strip():
            raise NeuralTTSError('tts_empty_text', 'Speech text must not be empty.')
        if len(text) > MAX_TTS_TEXT_CHARS:
            raise NeuralTTSError('tts_text_too_long', 'Speech text exceeds the 4000-character limit.')
        if len(text) > MAX_SUPERTONIC_TEXT_CHARS:
            raise NeuralTTSError('tts_text_too_long', 'Supertonic speech text exceeds the 1200-character on-device inference budget.')
        lang = _language_key(language)
        files = {
            'duration_predictor': 'duration_predictor.int8.onnx',
            'text_encoder': 'text_encoder.int8.onnx',
            'vector_estimator': 'vector_estimator.int8.onnx',
            'vocoder': 'vocoder.int8.onnx',
            'tts_json': 'tts.json',
            'unicode_indexer': 'unicode_indexer.bin',
            'voice_style': 'voice.bin',
        }
        missing = [name for name in files.values() if not (self.model_dir / name).is_file()]
        if missing:
            raise NeuralTTSError('tts_model_unavailable', 'Supertonic model files are missing: ' + ', '.join(missing))
        try:
            # Android/Termux wheels ship libonnxruntime beside the extension but
            # Android's linker may not search that private directory by default.
            import ctypes
            import importlib.util
            spec = importlib.util.find_spec('sherpa_onnx')
            if spec is None or not spec.submodule_search_locations:
                raise NeuralTTSError('tts_engine_unavailable', 'sherpa-onnx is not installed in this Python environment.')
            package_dir = Path(next(iter(spec.submodule_search_locations)))
            native_dir = package_dir / 'lib'
            ort = native_dir / 'libonnxruntime.so'
            if ort.is_file():
                os.environ['LD_LIBRARY_PATH'] = str(native_dir) + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
                try:
                    ctypes.CDLL(str(ort), mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    # Import below supplies the definitive runtime error.
                    pass
            import sherpa_onnx
        except NeuralTTSError:
            raise
        except Exception as exc:
            raise NeuralTTSError('tts_engine_unavailable', 'Could not load local sherpa-onnx runtime.') from exc
        try:
            thread_count = max(1, min(int(os.getenv('SAHIBEX_TTS_THREADS', '2')), 4))
            cache_key = (str(self.model_dir.resolve()), thread_count)
            # One resident model avoids reload cost and model-memory spikes on every
            # answer. Serialize CPU inference so concurrent requests cannot multiply
            # peak RAM or overload this phone's shared CPU.
            if not _SUPERTONIC_INFERENCE_LOCK.acquire(timeout=self.timeout_seconds):
                raise NeuralTTSError('tts_busy', 'Local neural voice is busy; retry after the current response.')
            try:
                tts = _SUPERTONIC_ENGINE_CACHE.get(cache_key)
                if tts is None:
                    if not _SUPERTONIC_INIT_LOCK.acquire(timeout=self.timeout_seconds):
                        raise NeuralTTSError('tts_busy', 'Local neural voice initialization is busy.')
                    try:
                        tts = _SUPERTONIC_ENGINE_CACHE.get(cache_key)
                        if tts is None:
                            cfg = sherpa_onnx.OfflineTtsModelConfig(
                                supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
                                    duration_predictor=str(self.model_dir / files['duration_predictor']),
                                    text_encoder=str(self.model_dir / files['text_encoder']),
                                    vector_estimator=str(self.model_dir / files['vector_estimator']),
                                    vocoder=str(self.model_dir / files['vocoder']),
                                    tts_json=str(self.model_dir / files['tts_json']),
                                    unicode_indexer=str(self.model_dir / files['unicode_indexer']),
                                    voice_style=str(self.model_dir / files['voice_style']),
                                ),
                                num_threads=thread_count,
                                provider='cpu',
                            )
                            tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=cfg))
                            _SUPERTONIC_ENGINE_CACHE[cache_key] = tts
                    finally:
                        _SUPERTONIC_INIT_LOCK.release()
                gen = sherpa_onnx.GenerationConfig()
                gen.sid = max(0, min(int(os.getenv('SAHIBEX_TTS_SPEAKER_ID', '0')), 9))
                gen.num_steps = max(4, min(int(os.getenv('SAHIBEX_TTS_STEPS', '8')), 12))
                gen.speed = 1.0
                gen.extra['lang'] = lang
                audio = tts.generate(text.strip(), gen)
            finally:
                _SUPERTONIC_INFERENCE_LOCK.release()
            rate = int(audio.sample_rate)
            samples = audio.samples
            duration = len(samples) / float(rate) if rate else 0.0
            if not 8000 <= rate <= 48000 or not 0 < duration <= MAX_TTS_SECONDS:
                raise NeuralTTSError('tts_audio_format_invalid', 'Supertonic generated audio outside safe rate/duration limits.')
            out = io.BytesIO()
            with wave.open(out, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(rate)
                frames = bytearray()
                # The quantized model's output often peaks well below full scale.
                # Normalize once with 15% headroom to improve intelligibility on
                # small phone speakers without clipping or dynamic compression.
                for value in _normalize_pcm16_samples(samples):
                    frames.extend(struct.pack('<h', value))
                wav.writeframes(frames)
            data = out.getvalue()
            if len(data) < 44 or len(data) > MAX_TTS_WAV_BYTES:
                raise NeuralTTSError('tts_audio_size_invalid', 'Supertonic WAV exceeds safe size limits.')
            return SynthesizedSpeech(data, 'sherpa-supertonic-3', lang, rate, round(duration, 3))
        except NeuralTTSError:
            raise
        except Exception as exc:
            raise NeuralTTSError('tts_engine_error', 'Local Supertonic synthesis failed.') from exc


def _normalize_pcm16_samples(samples, target_peak: int = 27852) -> list[int]:
    """Peak-normalize generated float samples for clearer phone-speaker playback.

    Leaves silence silent, preserves relative dynamics, and reserves headroom so
    conversion to signed 16-bit PCM cannot clip due to normalization alone.
    """
    values = [max(-1.0, min(1.0, float(sample))) for sample in samples]
    peak = max((abs(value) for value in values), default=0.0)
    if peak <= 1e-7:
        return [0] * len(values)
    gain = min(float(target_peak) / 32767.0 / peak, 8.0)
    return [max(-32768, min(32767, int(round(value * gain * 32767.0)))) for value in values]


def LocalNeuralTTS():
    """Select the explicitly configured local backend; no implicit network fallback."""
    backend = os.getenv('SAHIBEX_TTS_BACKEND', 'sherpa-supertonic').strip().lower()
    if backend in {'sherpa', 'sherpa-supertonic', 'supertonic'}:
        return LocalSherpaSupertonicTTS()
    if backend == 'piper':
        return LocalPiperTTS()
    raise NeuralTTSError('tts_backend_unsupported', 'Configured local TTS backend is unsupported.')
