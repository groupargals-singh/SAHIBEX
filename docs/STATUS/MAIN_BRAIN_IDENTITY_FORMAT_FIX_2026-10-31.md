# Main Brain identity format resolver fix — 2026-10-31

## Defect
The deterministic SAHIBEX identity resolver accepted short prompts such as "SAHIBEX kya hai?" but rejected the user's full Hinglish request "SAHIBEX kya hai? Hindi mein 3 numbered points mein batao." The resolver's strict full-match suffix grammar did not include the "numbered points mein batao" response-format variant. The request then fell through to the factual-evidence gate and returned INSUFFICIENT_EVIDENCE despite a matching project-identity curated response already being available.

## Change
- Extended only the SAHIBEX identity prompt-format grammar for Hindi/Hinglish and English numbered-point instructions.
- Preserved strict full-match behavior. Compound semantic questions are not partially answered from the identity fact.
- Added resolver tests for Hindi/Hinglish and English numbered-point variants.
- Added a Main Brain integration regression test for the exact Hinglish prompt.
- Pre-edit source backup: `backups/main_brain_identity_format_fix_20261031/factual_resolver.py.pre_fix`.

## Verification
- Focused resolver + Main Brain reliability suite: **17 passed in 4.56s**.
- Full repository regression after the source change: **2205 passed in 207.29s**, exit code 0.
- Changed-file compileall: PASS.
- `git diff --check`: PASS.
- Restarted only the verified existing Media Bridge process after checking its command line; bridge health returned ONLINE.
- Live authenticated Hindi/Hinglish Companion `/voice` request with the exact user prompt: HTTP 200, success=true, verification `CURATED_KNOWLEDGE`, input/answer language `hi-Latn`, three numbered points returned, **0.22s**, PASS.
- The live request did not require a model generation call; this is a deterministic curated project-identity fast path, not proof of general model answer quality.

## Trust boundary / remaining work
- No database rows, knowledge verification records, credentials, APK, permissions, or backups were changed.
- Read-only inspection found many historical knowledge candidates with a legacy `verified=true` candidate flag but no persisted VERIFIED lifecycle event. The Knowledge Brain correctly excludes those records from trusted retrieval. No trust filter was weakened and no bulk knowledge was promoted.
- Broader factual research/retrieval coverage remains a separate open issue. Unknown compound identity questions must continue to disclose insufficient evidence rather than partially invent an answer.
- This bounded resolver fix does **not** promote P6 or any P-series gate. P6 still needs installed-app acceptance and physical microphone → ASR → transcript confirmation → Main Brain → audible TTS testing; other open gates remain unchanged.

## Disposition
**Scoped defect: PASS.**
**General factual retrieval and physical voice E2E: still PARTIAL/BLOCKED.**
No P-series gate promoted.
