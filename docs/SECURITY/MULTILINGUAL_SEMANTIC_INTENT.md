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

For an already-running local model provider, set these variables in the SAHIBEX process environment before startup:

- SAHIBEX_MODEL_PROVIDER=local
- SAHIBEX_SEMANTIC_INTENT_ENABLED=1

Remote semantic inference is separately opt-in because it sends request text to a configured remote endpoint:

- SAHIBEX_MODEL_PROVIDER=remote
- SAHIBEX_SEMANTIC_INTENT_ENABLED=1
- SAHIBEX_SEMANTIC_INTENT_ALLOW_REMOTE=1

Remote mode also requires a valid endpoint/model configuration. Do not place secrets in source files or logs. A provider failure or invalid response is not interpreted as a classification.

## Acceptance limits

Passing local unit tests proves the adapter contract and security wiring under the tested fixtures. It does not prove that the currently configured model can fluently understand every language. Live acceptance requires an actual multilingual model to be active and a broad, independently reviewed language/action test set to pass. A small or mock model must not be described as ChatGPT-level or universal.
