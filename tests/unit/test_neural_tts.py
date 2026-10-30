from __future__ import annotations

import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from core.brain.neural_tts import LocalPiperTTS, LocalSherpaSupertonicTTS, NeuralTTSError, _language_key, _normalize_pcm16_samples


class NeuralTTSTests(unittest.TestCase):
    def test_language_normalization_supports_hindi_and_english(self):
        self.assertEqual(_language_key('hi-IN'), 'hi')
        self.assertEqual(_language_key('en-IN'), 'en')
        with self.assertRaises(NeuralTTSError):
            _language_key('fr-FR')

    def test_pcm_normalization_raises_quiet_audio_without_clipping(self):
        samples = [0.0, 0.1, -0.2, 0.4, -0.4]
        result = _normalize_pcm16_samples(samples)
        self.assertEqual(len(result), len(samples))
        self.assertEqual(result[0], 0)
        self.assertEqual(max(abs(value) for value in result), 27852)
        self.assertTrue(all(-32768 <= value <= 32767 for value in result))

    def test_pcm_normalization_preserves_silence_and_limits_gain(self):
        self.assertEqual(_normalize_pcm16_samples([0.0, 0.0]), [0, 0])
        result = _normalize_pcm16_samples([1e-9, -1e-9])
        self.assertEqual(result, [0, 0])
        quiet = _normalize_pcm16_samples([0.00001, -0.00001])
        self.assertTrue(all(abs(value) <= 2622 for value in quiet))

    def test_empty_and_oversized_text_fail_closed(self):
        tts = LocalPiperTTS(models={'hi': '/missing', 'en': '/missing'})
        with self.assertRaisesRegex(NeuralTTSError, 'must not be empty'):
            tts.synthesize('  ', 'hi')
        with self.assertRaisesRegex(NeuralTTSError, '4000-character'):
            tts.synthesize('x' * 4001, 'en')

    def test_missing_model_and_engine_fail_closed_without_network_fallback(self):
        tts = LocalPiperTTS(executable='/definitely/missing/piper', models={'hi': '/missing/model.onnx'})
        with self.assertRaises(NeuralTTSError) as caught:
            tts.synthesize('नमस्ते', 'hi')
        self.assertEqual(caught.exception.code, 'tts_model_unavailable')

    def test_model_unconfigured_is_explicit(self):
        tts = LocalPiperTTS(executable='/definitely/missing/piper', models={'hi': '', 'en': ''})
        with self.assertRaises(NeuralTTSError) as caught:
            tts.synthesize('hello', 'en')
        self.assertEqual(caught.exception.code, 'tts_model_unconfigured')

    def test_supertonic_rejects_empty_or_over_budget_text_before_loading_engine(self):
        tts = LocalSherpaSupertonicTTS(model_dir='/definitely/missing/supertonic-model')
        with self.assertRaisesRegex(NeuralTTSError, 'must not be empty'):
            tts.synthesize('  ', 'hi')
        with self.assertRaisesRegex(NeuralTTSError, '1200-character'):
            tts.synthesize('x' * 1201, 'en')

    def test_supertonic_missing_model_fails_closed(self):
        tts = LocalSherpaSupertonicTTS(model_dir='/definitely/missing/supertonic-model')
        with self.assertRaises(NeuralTTSError) as caught:
            tts.synthesize('hello', 'en')
        self.assertEqual(caught.exception.code, 'tts_model_unavailable')

    def test_supertonic_language_is_restricted_to_hindi_and_english(self):
        tts = LocalSherpaSupertonicTTS(model_dir='/definitely/missing/supertonic-model')
        with self.assertRaises(NeuralTTSError) as caught:
            tts.synthesize('bonjour', 'fr')
        self.assertEqual(caught.exception.code, 'tts_language_unsupported')

    def test_configured_model_requires_real_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / 'model.onnx'
            model.write_bytes(b'model fixture')
            tts = LocalPiperTTS(executable='missing-piper-fixture-should-not-exist', models={'en': str(model)})
            with patch('core.brain.neural_tts.shutil.which', return_value=None):
                with self.assertRaises(NeuralTTSError) as caught:
                    tts.synthesize('hello', 'en')
            self.assertEqual(caught.exception.code, 'tts_engine_unavailable')


if __name__ == '__main__':
    unittest.main()
