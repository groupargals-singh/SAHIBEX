# SAHIBEX Memory Specialist Routing — 2026-11-11

## Scope
Connect explicit memory-recall questions to the existing trust-filtered `MemoryBrain` retrieval path and return bounded, serialization-safe results.

## Implemented
- Explicit English recall patterns and supported Hinglish recall wording select the `memory` role.
- The query is extracted from the recall phrase and capped at 1,000 characters.
- Existing `MemoryBrain.retrieve()` remains the source of results; its factual provenance/trust filtering is not bypassed.
- Handler output is capped at 10 matches; each content field is capped at 2,000 characters and tags at 10.
- Only selected public fields are returned. Internal metadata is excluded.
- Retrieval is read-only: no memory write/delete, no permission grant and no Constitution override.
- Existing `MEMORY_RETRIEVAL_ONLY` status is preserved for compatibility; `trust_filter_applied` explicitly reports the trust-filter boundary.
- Dispatch remains behind the existing Mother Brain permission and verification gates.

## Validation
- Focused router + InternalBrainTeam regression: **123 passed**.
- Full repository regression: **2,349 passed in 164.92s**, exit 0. `compileall -q core app tools scripts tests`: PASS. All repository shell scripts passed `bash -n`. `git diff --check`: PASS. GitHub publication pending final review/commit/push/hash verification.

## Limitations
- This route does not reconstruct full conversation history or infer an ambiguous reference. It only retrieves trusted stored memories matching the extracted query.
- It does not create, update, consolidate or delete memory records.
- No release gate is promoted.
