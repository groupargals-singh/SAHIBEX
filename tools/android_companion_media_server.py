from __future__ import annotations

import base64
import binascii
import hmac
import json
import os
import secrets
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from core.brain.master_brain import MasterBrain
from core.brain.speech_recognition import LocalWhisperCppRecognizer, SpeechRecognitionError, MAX_AUDIO_BYTES
from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.neural_tts import LocalNeuralTTS, NeuralTTSError, MAX_TTS_TEXT_CHARS, MAX_TTS_WAV_BYTES
from core.diagnostics.diagnostic_engine import collect_diagnostics

HOST = "127.0.0.1"
PORT = 38742
MAX_BODY_BYTES = 16_384
MAX_VISION_BODY_BYTES = 2_500_000
MAX_VISION_IMAGE_BYTES = 1_800_000
TOKEN_PATH = Path(__file__).resolve().parents[1] / "data" / "android_companion_media_token"


def load_or_create_token(path: Path = TOKEN_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if len(token) >= 40:
            return token
        raise RuntimeError("Media bridge token file exists but is invalid; rotate it deliberately")
    token = secrets.token_urlsafe(48)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(token + "\n")
    return token


class MediaBridgeHandler(BaseHTTPRequestHandler):
    server_version = "SAHIBEX-MediaBridge/1"
    token: str
    _thread_state = threading.local()

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log voice transcripts or authorization headers.
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            # The Android UI may cancel a slow request. Header writes can fail too;
            # do not leak a handler traceback or attempt a second response.
            return

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"success": True, "service": "sahibex-media-bridge", "host": HOST, "port": PORT})
            return
        if self.path == "/session":
            authorization = self.headers.get("Authorization", "")
            if not hmac.compare_digest(authorization, "Bearer " + self.token):
                self._send(401, {"success": False, "authenticated": False, "error": "unauthorized"})
                return
            self._send(200, {
                "success": True,
                "authenticated": True,
                "service": "sahibex-media-bridge",
                "host": HOST,
                "port": PORT,
            })
            return
        if self.path == "/diagnostics":
            authorization = self.headers.get("Authorization", "")
            if not hmac.compare_digest(authorization, "Bearer " + self.token):
                self._send(401, {"success": False, "error": "unauthorized"})
                return
            try:
                self._send(200, collect_diagnostics())
            except Exception as exc:
                self._send(500, {"success": False, "error": "diagnostics_unavailable", "reason": type(exc).__name__})
            return
        self._send(404, {"success": False, "error": "not_found"})

    def _do_synthesize_audio(self) -> None:
        """Generate bounded local neural TTS audio; never calls a cloud service."""
        authorization = self.headers.get("Authorization", "")
        if not hmac.compare_digest(authorization, "Bearer " + self.token):
            self._send(401, {"success": False, "error": "unauthorized"})
            return
        if self.headers.get_content_type().lower() != "application/json":
            self._send(415, {"success": False, "error": "json_content_type_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"success": False, "error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(413 if length > MAX_BODY_BYTES else 400,
                       {"success": False, "error": "invalid_body_size"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"success": False, "error": "invalid_json"})
            return
        text = payload.get("text") if isinstance(payload, dict) else None
        language = payload.get("language", "") if isinstance(payload, dict) else ""
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TTS_TEXT_CHARS:
            self._send(400, {"success": False, "error": "invalid_text"})
            return
        if not isinstance(language, str) or not language.strip():
            self._send(400, {"success": False, "error": "invalid_language"})
            return
        try:
            speech = LocalNeuralTTS().synthesize(text, language)
            if len(speech.wav_bytes) > MAX_TTS_WAV_BYTES:
                self._send(413, {"success": False, "error": "tts_audio_too_large"})
                return
            try:
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(speech.wav_bytes)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-SAHIBEX-TTS-Engine", speech.engine)
                self.send_header("X-SAHIBEX-TTS-Language", speech.language)
                self.send_header("X-SAHIBEX-TTS-Duration", str(speech.duration_seconds))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(speech.wav_bytes)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return
        except NeuralTTSError as exc:
            status = 503 if exc.code in {"tts_engine_unavailable", "tts_model_unconfigured", "tts_model_unavailable", "tts_backend_unsupported"} else (
                504 if exc.code == "tts_timeout" else (429 if exc.code == "tts_busy" else 422)
            )
            self._send(status, {"success": False, "error": exc.code, "message": str(exc)})
        except Exception as exc:
            print(f"MEDIA_TTS_ERROR={type(exc).__name__}", flush=True)
            self._send(500, {"success": False, "error": "local_synthesis_failed"})

    def _do_transcribe_audio(self) -> None:
        """Transcribe a bounded PCM WAV locally; audio is temporary and never persisted."""
        authorization = self.headers.get("Authorization", "")
        if not hmac.compare_digest(authorization, "Bearer " + self.token):
            self._send(401, {"success": False, "error": "unauthorized"})
            return
        if self.headers.get_content_type().lower() not in {"audio/wav", "audio/x-wav"}:
            self._send(415, {"success": False, "error": "audio_content_type_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"success": False, "error": "invalid_content_length"})
            return
        if length < 44 or length > MAX_AUDIO_BYTES:
            self._send(413 if length > MAX_AUDIO_BYTES else 400,
                       {"success": False, "error": "invalid_audio_size"})
            return
        try:
            audio_bytes = self.rfile.read(length)
            if len(audio_bytes) != length:
                self._send(400, {"success": False, "error": "incomplete_audio_body"})
                return
            # Use a private temporary directory so audio is automatically removed after
            # success or failure. No transcript/audio content is written to the log.
            import tempfile
            with tempfile.TemporaryDirectory(prefix="sahibex-asr-") as folder:
                audio_path = Path(folder) / "input.wav"
                audio_path.write_bytes(audio_bytes)
                language_hint = self.headers.get("X-SAHIBEX-Language", "auto").strip().lower()
                if language_hint not in {"auto", "hi", "en"}:
                    self._send(400, {"success": False, "error": "unsupported_language_hint"})
                    return
                result = LocalWhisperCppRecognizer().transcribe(audio_path, language_hint=language_hint)
            self._send(200, {
                "success": True,
                "transcript": result.transcript,
                "engine": result.engine,
                "mode": result.mode,
                "language": result.language,
                "duration_seconds": round(result.duration_seconds, 2),
                "audio_retained": False,
                "requires_user_confirmation": True,
            })
        except SpeechRecognitionError as exc:
            code = exc.code
            status = 503 if code in {"asr_engine_unavailable", "asr_model_unavailable", "asr_engine_error"} else (
                504 if code == "asr_timeout" else (400 if code.startswith("audio_") else 422)
            )
            self._send(status, {"success": False, "error": code, "message": str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            print(f"MEDIA_ASR_ERROR={type(exc).__name__}", flush=True)
            self._send(500, {"success": False, "error": "local_transcription_failed"})

    def _do_vision_ocr(self) -> None:
        """Analyze a user-requested still image with local OCR only.

        Image bytes are size-bounded, signature-checked by OCRRuntime, held in a
        private temporary directory, and removed after processing. OCR text is
        untrusted evidence, never executable instructions.
        """
        authorization = self.headers.get("Authorization", "")
        if not hmac.compare_digest(authorization, "Bearer " + self.token):
            self._send(401, {"success": False, "error": "unauthorized"})
            return
        if self.headers.get_content_type().lower() != "application/json":
            self._send(415, {"success": False, "error": "json_content_type_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"success": False, "error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_VISION_BODY_BYTES:
            self._send(413 if length > MAX_VISION_BODY_BYTES else 400,
                       {"success": False, "error": "invalid_body_size"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"success": False, "error": "invalid_json"})
            return
        encoded = payload.get("image_base64") if isinstance(payload, dict) else None
        languages = payload.get("languages", "eng+hin") if isinstance(payload, dict) else "eng+hin"
        if not isinstance(encoded, str) or not encoded or len(encoded) > ((MAX_VISION_IMAGE_BYTES + 2) // 3) * 4 + 8:
            self._send(400, {"success": False, "error": "invalid_image_payload"})
            return
        if languages not in {"eng", "hin", "eng+hin"}:
            self._send(400, {"success": False, "error": "unsupported_ocr_languages"})
            return
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            self._send(400, {"success": False, "error": "invalid_image_encoding"})
            return
        if len(image_bytes) < 16 or len(image_bytes) > MAX_VISION_IMAGE_BYTES:
            self._send(413 if len(image_bytes) > MAX_VISION_IMAGE_BYTES else 400,
                       {"success": False, "error": "invalid_image_size"})
            return
        try:
            import tempfile
            from core.brain.ocr_runtime import OCRRuntime
            from core.brain.vision_ocr_integration import VisionOCRPipeline
            with tempfile.TemporaryDirectory(prefix="sahibex-camera-ocr-") as folder:
                capture_dir = Path(folder).resolve()
                image_path = capture_dir / "camera_frame.jpg"
                fd = os.open(str(image_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(image_bytes)
                    stream.flush()
                    os.fsync(stream.fileno())
                pipeline = VisionOCRPipeline(OCRRuntime(capture_dir, max_image_bytes=MAX_VISION_IMAGE_BYTES))
                evidence = pipeline.process_image(image_path, languages=languages)
            self._send(200, {
                "success": True,
                "mode": "local_ocr_only",
                "text": evidence.observation.observation[:12000],
                "source_sha256": evidence.source_sha256,
                "languages": evidence.languages,
                "confidence": evidence.confidence,
                "trust_notice": evidence.trust_notice,
                "image_retained": False,
                "semantic_image_understanding": False,
            })
        except FileNotFoundError:
            self._send(503, {"success": False, "error": "local_ocr_engine_unavailable"})
        except (ValueError, TimeoutError) as exc:
            self._send(422, {"success": False, "error": "image_quality_or_ocr_rejected", "message": str(exc)[:240]})
        except Exception as exc:
            print(f"MEDIA_VISION_OCR_ERROR={type(exc).__name__}", flush=True)
            self._send(500, {"success": False, "error": "local_vision_ocr_failed"})

    def do_POST(self) -> None:
        if self.path == "/vision/ocr":
            self._do_vision_ocr()
            return
        if self.path == "/synthesize":
            self._do_synthesize_audio()
            return
        if self.path == "/transcribe":
            self._do_transcribe_audio()
            return
        if self.path != "/voice":
            self._send(404, {"success": False, "error": "not_found"})
            return
        authorization = self.headers.get("Authorization", "")
        expected = "Bearer " + self.token
        if not hmac.compare_digest(authorization, expected):
            self._send(401, {"success": False, "error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"success": False, "error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(413 if length > MAX_BODY_BYTES else 400, {"success": False, "error": "invalid_body_size"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"success": False, "error": "invalid_json"})
            return
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip() or len(text) > 8192:
            self._send(400, {"success": False, "error": "invalid_text"})
            return
        try:
            # Keep each brain/storage instance confined to the request thread.
            # Tests can inject a fake as a class attribute; production uses thread-local instances.
            brain = getattr(self, "brain", None)
            if brain is None:
                brain = getattr(self._thread_state, "brain", None)
                if brain is None:
                    brain = MasterBrain()
                    self._thread_state.brain = brain
            # Pass the untouched transcript to Master Brain. Typed and voice
            # requests now share one normalization, language and contextual-repair
            # pipeline; the original transcript remains available for audit.
            raw_transcript = text.strip()
            result = brain.process(raw_transcript, user_confirmation=False)
            result_metadata = getattr(result, "metadata", {})
            input_trace = (
                result_metadata.get("input_understanding", {})
                if isinstance(result_metadata, dict) else {}
            )
            if not isinstance(input_trace, dict):
                input_trace = {}
            processed_text = input_trace.get("normalized_text", raw_transcript)
            if not isinstance(processed_text, str):
                processed_text = raw_transcript
            input_corrections = input_trace.get("corrections", [])
            input_suggestions = input_trace.get("suggestions_not_applied", [])
            known_terms = input_trace.get("known_terms", [])
            if not isinstance(input_corrections, list):
                input_corrections = []
            if not isinstance(input_suggestions, list):
                input_suggestions = []
            if not isinstance(known_terms, list):
                known_terms = []
            input_language = input_trace.get("language_code", "und")
            if not isinstance(input_language, str):
                input_language = "und"
            contextual_status = input_trace.get(
                "contextual_repair_status", "NOT_REPORTED_BY_BRAIN"
            )
            contextual_repair = {
                "status": contextual_status,
                "changed": any(
                    isinstance(item, dict)
                    and str(item.get("reason", "")).startswith("contextual_model")
                    for item in input_corrections
                ),
                "confidence": input_trace.get("contextual_repair_confidence") or 0.0,
                "language_code": input_language,
                "intent_summary": "",
            }
            # Voice input is NOT proof of authorization.
            answer_language = UniversalLanguageBrain().detect(str(result.message)).language_code
            # Very short deterministic answers (for example, "Answer: 4") do not
            # contain enough lexical evidence for language identification. For this
            # narrowly verified fast path, inherit the detected input language.
            if (
                answer_language in {"und", "und-Latn"}
                and str(getattr(result, "verification_status", "")).upper() == "DETERMINISTIC_ARITHMETIC"
            ):
                answer_language = input_language
            # Only expose the bounded, secret-free research telemetry prepared
            # by MotherResearchIntegration. Do not serialize arbitrary BrainResult
            # metadata, source page bodies, prompts, or credentials to the phone.
            research_metadata = (
                result_metadata.get("mother_research_integration", {})
                if isinstance(result_metadata, dict) else {}
            )
            research_diagnostics = (
                research_metadata.get("diagnostics", {})
                if isinstance(research_metadata, dict) else {}
            )
            self._send(200, {
                "success": bool(result.success),
                "message": str(result.message)[:12000],
                "heard_text": raw_transcript,
                "processed_text": processed_text,
                "input_corrections": input_corrections,
                "input_suggestions": input_suggestions,
                "known_terms": known_terms,
                "input_language": input_language,
                "contextual_repair": contextual_repair,
                "answer_language": answer_language,
                "intent": str(result.intent),
                "verification_status": str(result.verification_status),
                "permission_allowed": bool(result.permission_allowed),
                "confirmation_required": bool(result.confirmation_required),
                "research_diagnostics": (
                    research_diagnostics if isinstance(research_diagnostics, dict) else {}
                ),
            })
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            # Do not return transcript or stack traces to the phone UI.
            print(f"MEDIA_BRAIN_PROCESSING_ERROR={type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
            self._send(500, {"success": False, "error": "brain_processing_failed"})


def main() -> None:
    os.environ.setdefault("SAHIBEX_MODEL_PROVIDER", "local")
    os.environ.setdefault("SAHIBEX_SEARCH_BACKEND", "google_news_rss")
    token = load_or_create_token()
    handler = type("ConfiguredMediaBridgeHandler", (MediaBridgeHandler,), {"token": token})
    # Each request thread owns its own MasterBrain and SQLite connection.
    server = ThreadingHTTPServer((HOST, PORT), handler)
    server.daemon_threads = True
    print(f"SAHIBEX_MEDIA_BRIDGE=ONLINE host={HOST} port={PORT}", flush=True)
    print(f"PAIRING_TOKEN_FILE={TOKEN_PATH}", flush=True)
    print("Protected actions remain blocked unless separately authorized in the normal SAHIBEX UI.", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
