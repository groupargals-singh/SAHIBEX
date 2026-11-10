# SAHIBEX Mother Brain Specialist Routing — 2026-11-10

## Scope
Implement the first conservative automatic specialist-selection layer for the text-only Mother Brain request path. This does not claim all 61 roles are automatically routed or semantically complete.

## Implemented
- Added `MotherBrainSpecialistRouter` as a deterministic, bounded selector.
- The selector chooses at most ONE specialist for a request; it does not fan out to all roles.
- Initial explicit routes:
  - bounded arithmetic-looking request → `math`
  - explicit learning/teaching request → `teaching`
  - explicit language-identification request → `language`
- MasterBrain constructs the router and invokes the selected role only after the existing request authorization and verification gates have passed.
- Dispatch remains inside the existing `InternalBrainTeam`; specialist outputs are explicitly returned in the final metadata under `automatic_specialist` and trace under `internal_brain_dispatch`.
- Specialist output remains advisory/unverified. It does not override Mother Brain's response, permission decision, Constitution, or protected tool execution.
- Generic greeting and vague requests do not cause a guessed specialist selection.

## Tests and validation
- Router unit tests cover math, teaching, language, no-route cases, empty/invalid inputs.
- Integration tests prove the selected Language and Teaching handlers are callable through MotherBrain's existing gated dispatch API.
- Focused router + InternalBrainTeam tests: **103 passed**.
- Final full repository regression after all route-selection and false-positive tests: **2,329 passed in 155.78s**, exit 0.
- `compileall -q core app tools scripts tests`: PASS.
- All shell scripts `bash -n`: PASS.
- `git diff --check`: PASS.

## Explicit limitations
- Only three routes are currently implemented. Other registered specialists are not automatically selected by this router yet.
- Math route may be pre-empted by the earlier deterministic arithmetic response path for supported arithmetic; it is primarily a specialist route for requests reaching the full Mother Brain flow.
- Teaching handler creates a lesson outline, not a complete factual lesson; no research/fact verification is claimed.
- Language handler detects language/script; it does not translate. Translation requests are deliberately not routed to this detection-only handler.
- This change does not restore general model-backed Q&A while the configured model API remains offline.
- No protected actions, file operations, external network calls, voice, vision, Accessibility or device control are enabled by this router.
- No P-series release gate is promoted.

## Next
Expand routes only where each specialist has a real, tested input contract and safe output consumer. Priority: conversation/context, reading/document, debugging/testing, knowledge/memory, research and data analysis. Add dispatch acceptance tests per route; avoid speculative role fan-out.


## Final full regression result
- Final full repository regression after tightening route selection and adding false-positive coverage: **2,329 passed in 155.78s**, exit 0.
- This is the final full-suite result for this routing slice.
