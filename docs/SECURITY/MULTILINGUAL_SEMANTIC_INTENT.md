# SAHIBEX Multilingual Semantic Intent and Security Gate

## Runtime flow

1. Universal Language Understanding uses script/language clues and records mixed-script or mixed-language signals. It is a heuristic language assessment, not proof of semantic comprehension.
2. Deterministic Intent Engine handles high-confidence supported patterns.
3. Semantic Intent Brain is an optional fallback for uncertain/general requests. It asks the configured model for strict JSON containing intent, action, confidence, language code, and clarification status. The request is treated as untrusted input.
4. Independent Security Gate remains authoritative: semantic output is only a classification. The existing Constitution, Permission Gateway, verification, confirmation, and Tool Brain paths still decide whether an action may proceed.
5. Denial Audit records protected-action blocks and semantic clarification stops. An audit write failure never grants permission.
6. Multilingual Regression Lab tests language identification, malformed model outputs, clarification, protected-action routing, permission denial, and audit evidence.

## Model configuration

The default provider is mock; it is deliberately not treated as real semantic understanding.

When the configured provider is local, MasterBrain enables the semantic fallback by default. It can be explicitly disabled with `SAHIBEX_SEMANTIC_INTENT_ENABLED=0`. The fallback is invoked for general requests and deterministic intent results below the 0.72 acceptance threshold. Local model health is checked before inference; offline/failed providers return no semantic classification and do not authorize or execute anything.

The local llama.cpp provider discovers the actually loaded model ID from `/v1/models` when no explicit model ID is configured. Semantic classification and contextual input repair use a 45-second request ceiling, while offline health preflight is capped at one second. Clarification outputs must be actual questions; an echoed request or imperative sentence is rejected.

Remote semantic inference is separately opt-in because it sends request text to a configured remote endpoint:

- SAHIBEX_MODEL_PROVIDER=remote
- SAHIBEX_SEMANTIC_INTENT_ENABLED=1
- SAHIBEX_SEMANTIC_INTENT_ALLOW_REMOTE=1

Remote mode also requires a valid endpoint/model configuration. Do not place secrets in source files or logs. A provider failure or invalid response is not interpreted as a classification.

## Acceptance limits

Passing local unit tests proves the adapter contract and security wiring under the tested fixtures. It does not prove that the currently configured model can fluently understand every language. Live acceptance requires an actual multilingual model to be active and a broad, independently reviewed language/action test set to pass. A small or mock model must not be described as ChatGPT-level or universal.
