# SAHIBEX Knowledge Specialist Routing — 2026-11-11

## Scope
Connect explicit user requests to search the persistent Knowledge Brain through Mother Brain's existing authorization and request-verification gates. Ordinary Mother Brain knowledge lookup is verified-only and must not be downgraded by caller context.

## Implemented
- Added conservative English, Hinglish and Hindi route patterns for explicit verified-knowledge searches, including bounded topic extraction (maximum 1,000 characters).
- Generic requests such as "tell me about SAHIBEX" and broad uses of the word "knowledge" do not select this specialist.
- The route selects only the existing `knowledge` role; it does not fan out to other specialists.
- Dispatch uses the already registered `_internal_library_or_knowledge_handler` and its existing `KnowledgeBrain.retrieve()` implementation.
- The Mother Brain handler now enforces `verified_only=True` regardless of a caller's false boolean value. A malformed non-boolean flag still fails closed for compatibility and input validation.
- Retrieval continues through persisted verification-lifecycle, conflict-selection, unresolved-conflict and query-freshness checks in `KnowledgeBrain`.
- Result output is capped at 10 records; each knowledge statement is capped at 2,000 characters. Only selected public fields and counts are exposed; detailed provenance objects are not serialized.
- The result explicitly reports `trust_filter_applied=True`, `verified_only=True`, `permission_granted=False` and `actions_executed=False`.
- No knowledge is written, promoted, re-verified, deleted or bulk-migrated. Existing user authority, Constitution, permission and verification boundaries are unchanged.

## Validation
- Focused router + InternalBrainTeam + KnowledgeBrain runtime regression: **138 passed**.
- Full repository regression: **2,356 passed in 176.95s**, exit 0.
- `compileall -q core app tools scripts tests`: PASS.
- Every repository shell script passed `bash -n`: PASS.
- `git diff --check`: PASS.
- Common secret-pattern scan across changed code/tests/status report: `NO_COMMON_SECRET_PATTERN_MATCH`.
- GitHub publication is completed only after final commit/push and remote hash verification.

## Limitations / not promoted
- This is verified-only retrieval routing, not a new evidence-generation or corroboration pipeline.
- Existing knowledge records without an explicit persisted VERIFIED lifecycle event, records with unresolved conflicts, losing conflict claims, and records failing freshness requirements remain excluded.
- The previously audited legacy knowledge corpus still requires a separate provenance/lifecycle audit and reviewed migration. This change does not make historical candidate records trustworthy.
- No release gate (P6/P7/P8/P10/P11) is promoted by this task.
