# SAHIBEX Model Provider Setup

SAHIBEX can use either its local llama.cpp model or an optional OpenAI-compatible remote model.

## Local mode (current default)

The live launcher starts the local model and sets:

- `SAHIBEX_MODEL_PROVIDER=local`
- `SAHIBEX_LOCAL_LLM_ENDPOINT=http://127.0.0.1:8080/v1/chat/completions`

The phone-grade local model is useful for offline work, but it may not reliably solve complex reasoning or factual questions. Shorter prompts and one inference slot reduce contention; they do not make a small model equivalent to a stronger reasoning model.

## Optional remote mode

The remote provider reads configuration from environment variables and does not save credentials in source files:

- `SAHIBEX_MODEL_PROVIDER=remote`
- `SAHIBEX_REMOTE_LLM_ENDPOINT` — full chat-completions URL from the chosen provider
- `SAHIBEX_REMOTE_LLM_MODEL` — exact model identifier supported by that provider
- `SAHIBEX_REMOTE_LLM_API_KEY` — API key, if required
- `SAHIBEX_REMOTE_LLM_TIMEOUT` — optional timeout in seconds (default 45)

Set these variables in the same Termux session before starting the media bridge or SAHIBEX process. Do not paste API keys into chats, screenshots, source files, or logs. Check the provider's pricing, privacy terms, data handling, and model availability before enabling remote inference.

Example template (replace the placeholders locally; do not commit real secrets):

```bash
export SAHIBEX_MODEL_PROVIDER=remote
export SAHIBEX_REMOTE_LLM_ENDPOINT='https://YOUR-PROVIDER/v1/chat/completions'
export SAHIBEX_REMOTE_LLM_MODEL='YOUR-MODEL-ID'
export SAHIBEX_REMOTE_LLM_API_KEY='YOUR-KEY'
bash scripts/start_sahibex_media_bridge.sh
```

The remote provider is opt-in. If endpoint/model configuration is missing, it fails closed instead of silently pretending to answer. This provider currently supports OpenAI-compatible non-streaming chat-completions responses; it is not automatically connected to an account or API key.

## Verification status

`STRUCTURALLY_VALID` means the model returned non-empty text and passed the operational response checks. It does **not** mean the answer's facts have been independently verified. `VERIFIED` should be reserved for flows that actually perform the relevant verification.
