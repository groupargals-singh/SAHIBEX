# SAHIBEX Model Integration + Text/Development Brain

Date: 2026-10-30

## Current runtime facts

- SAHIBEX Master Brain owns permissions, planning, verification, and promotion decisions.
- Text/Development Brain is a candidate authoring module. It stores bounded proposals under `data/development_lab/candidates/` and does not execute code, install packages, download/train models, access credentials, or write production source.
- Candidate records are SHA-256 fingerprinted and start in `PROPOSED_PENDING_MOTHER_REVIEW`. Static Python review can run through the existing Coding Brain; passing static analysis does not mean tests passed or that promotion is approved.
- Production promotion is not implemented by this module. Any future promotion must use an isolated staging copy, Mother verification, security checks, tests, regression checks, human approval for protected changes, atomic commit, health check, and verified rollback.
- Internet research results are untrusted input until source quality, freshness, provenance, and conflict checks pass. Internet access must not imply permission to execute downloaded code or modify live source.

## Model registry (planned, not installed by this checkpoint)

| Specialist | Candidate | Current status | Gate before activation |
|---|---|---|---|
| Language/reasoning | Existing local Qwen3-1.7B or Qwen3-4B GGUF | Present on disk; runtime OFFLINE | RAM guard, model health, Hindi/English quality, latency, hallucination tests |
| Vision | Qwen3-VL-8B-Instruct or compatible GGUF + vision projector | NOT DOWNLOADED / NOT CONNECTED | Verify license, artifact integrity, llama.cpp vision support, storage and RAM headroom |
| Speech recognition | Local Whisper-compatible or existing offline ASR | Availability must be audited | Hindi/Hinglish corpus and physical mic-to-transcript test |
| Speech output | Existing local TTS implementation | Software exists; acoustic acceptance pending | Hindi pronunciation and actual device playback acceptance |
| Native SAHIBEX model | New model trained from scratch or fine-tuned from license-compatible base | RESEARCH / DEVELOPMENT ONLY | Data provenance, license, reproducible training, benchmark, safety and rollback |

## Privacy requirements

- Prefer local inference for sensitive text, images, and audio.
- Keep local model servers loopback-bound unless a separately authorized network design exists.
- Never transmit credentials, private memories, or full conversation history to an external API by default.
- For any optional cloud provider, require explicit per-provider opt-in, minimum necessary context, documented retention/training terms, and redacted logs.
- Downloaded weights, model metadata, and model-generated text are untrusted; validate file integrity and never execute model-supplied code automatically.

## Resource policy

Do not start a model if `scripts/start_local_model.sh` memory checks fail. Do not load multiple large models concurrently on the phone. Specialist models are on-demand candidates; not every brain must stay resident in RAM. Keep the low-RAM fallback opt-in/disabled where its answer quality is known to be inadequate.

## Verification status

This document records design and current constraints only. It does not claim the vision model is installed, all specialist models are online, the native model is trained, or physical voice/vision acceptance has passed.
