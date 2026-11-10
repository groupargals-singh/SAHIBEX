# SAHIBEX Debugging Specialist Routing — 2026-11-11

## Scope
Wire a narrowly scoped automatic route from explicit code-related bug/error diagnosis requests to the existing Debugging specialist handler.

## Implementation
- `MotherBrainSpecialistRouter` selects `debugging` only when the request is classified as code intent and matches an explicit diagnosis/repair pattern.
- English, Hinglish and Hindi repair phrases are covered.
- The route passes one bounded failure envelope based only on the request text. It does not invent reproduction steps, expected behavior, observed behavior or logs.
- Existing `MasterBrain.process()` invokes the selected specialist only after the existing permission and request-verification checks.
- The output is advisory metadata and does not override Mother Brain, permission, Constitution, tool execution or final response.

## Acceptance
- Explicit Python bug repair request → Debugging.
- Hinglish bug repair request → Debugging.
- Hindi error repair request → Debugging.
- Ordinary HTTP error explanation → no Debugging route.
- Generic code creation → no Debugging route.
- Integration dispatch → `SUPPLIED_FAILURE_REPORTS_TRIAGED_NOT_EXECUTED` with `EVIDENCE_INCOMPLETE` when reproduction evidence is absent.
- Safety assertions: no code execution, filesystem reads/writes, runtime mutation or root-cause confirmation.

## Validation
- Focused router + InternalBrainTeam regression: **109 passed**. Full repository regression: **2,335 passed in 158.71s**, exit 0. `compileall -q core app tools scripts tests`: PASS. All repository shell scripts passed `bash -n`. `git diff --check`: PASS. GitHub publication remains pending final review/commit/push/hash verification.

## Limitations
This is triage routing only. It does not inspect the repository, run tests, edit code, repair bugs or prove autonomous debugging. A real repair must use a separately authorized and verified code/file workflow. No release gate is promoted.
