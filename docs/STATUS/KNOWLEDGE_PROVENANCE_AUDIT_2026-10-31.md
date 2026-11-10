# SAHIBEX Knowledge Provenance / Lifecycle Audit — 2026-10-31

## Scope and safety
- Audited `data/sahibex_brain.db` using SQLite URI `mode=ro` and `PRAGMA query_only=ON`.
- No candidate, verification, conflict, merge, evidence, source, memory, or user-data row was changed.
- No bulk promotion, flag correction, migration, or deletion was performed.
- Repeatable audit utility: `scripts/audit_knowledge_provenance.py`.
- Regression test: `tests/unit/test_knowledge_provenance_audit_script.py`.
- Aggregate output: `logs/knowledge_provenance_audit_20261031.json`.

## Database counts
| Table | Rows |
|---|---:|
| knowledge_candidates | 83,904 |
| knowledge_verification_records | 3,626 |
| knowledge_conflict_records | 0 |
| knowledge_merge_records | 0 |
| research_sources | 498 |
| research_documents | 496 |
| research_findings | 113,943 |
| research_evidence | 113,941 |

## Candidate / lifecycle findings
- Legacy `knowledge_candidates.verified=1`: **80,198**.
- Candidates with any lifecycle event: **3,626**; latest event status for all 3,626 is **UNVERIFIED**.
- Candidates with no lifecycle event: **80,278**.
- Legacy-true candidates with a latest VERIFIED lifecycle event: **0**.
- Legacy-true candidates without a latest VERIFIED lifecycle event: **80,198**.
- No lifecycle event in this database is VERIFIED; therefore verified-only retrieval must continue to fail closed rather than trust the legacy flag.

## Evidence / provenance linkage
- All 83,904 candidates contain exactly one evidence reference and one finding reference.
- Evidence references valid: **83,904 / 83,904**.
- Finding references valid: **83,904 / 83,904**.
- Evidence-to-source references valid: **83,904 / 83,904**.
- Candidate evidence-to-finding link matches: **83,904 / 83,904**.
- Each candidate currently links to exactly one distinct source record; none links to multiple distinct source records.
- Of 3,630 candidates with verification metadata, 3,471 report one supporting/independent source and 159 report zero. The existing lifecycle rule requires at least two independent supporting source groups, so these records are not eligible for VERIFIED promotion from the current evidence.

## Disposition
**Audit execution: PASS. Data trust remediation: BLOCKED pending corroborating independent sources and an explicitly approved, backed-up migration.**

Do not flip 80,198 legacy flags, manufacture VERIFIED events, or bulk-promote records. A safe next migration must preserve the current database, revalidate each claim against independent source groups, record source/evidence IDs and timestamps, resolve conflicts, and write lifecycle events only after evidence passes the existing policy.

The audit utility is read-only by construction. Its unit test confirms that a stale `verified=1` flag remains unchanged and is reported as unverified when lifecycle evidence is absent or UNVERIFIED.

## 2026-10-31 follow-up — stale verified-only retrieval bypass closed
- The provenance audit exposed a second safety gap: storage-level list/retrieve and ResearchQueryEngine could still accept a legacy verified=true flag when no lifecycle event existed.
- Fixed ResearchStorage.list_knowledge and retrieve_knowledge (including the Indic-script fallback query) so verified_only requires the latest persisted lifecycle event to be VERIFIED. Fixed ResearchQueryEngine so persisted verified-only retrieval requires at least one VERIFIED lifecycle event; in-memory verified-only retrieval requires explicit VERIFIED metadata.
- Added regressions for legacy verified flags with no lifecycle event, including English and Hindi retrieval; updated the persistence test to create an explicit VERIFIED lifecycle event.
- Focused knowledge/lifecycle/provenance suite: 34 passed. The production database remains read-only and unchanged. Because the current DB has zero VERIFIED lifecycle events, verified-only retrieval now correctly returns zero until claims are independently revalidated.
- Full repository regression after this safety fix is running; no P-series gate is promoted.


## Final verification — 2026-10-31 (knowledge lifecycle guard)
- Full repository regression after the retrieval guard: **2,255 passed in 190.03s** (exit 0).
- Read-only provenance audit completed against `data/sahibex_brain.db`: 83,908 candidates; 3,630 lifecycle events, all latest status UNVERIFIED; 80,278 candidates have no lifecycle event; 80,198 legacy verified flags have no latest VERIFIED event; zero candidates have a latest VERIFIED event.
- All 83,908 candidates have one valid evidence reference and one valid finding reference, but the audit found exactly one distinct source per candidate and zero multi-source candidates. Evidence reference validity is not the same as independent corroboration.
- The production database was opened with SQLite `mode=ro`; audit output confirms `read_only=true`, `database_write_attempted=false`. No candidate, evidence, source, or lifecycle rows were modified.
- Therefore the audit itself is COMPLETE, but trust revalidation / promotion remains BLOCKED pending independent source corroboration and an approved, backed-up evidence-based migration. Do not bulk-promote the legacy flags.
- No P-series gate was promoted. The remaining physical-device and historical-specification gates remain separately blocked/pending.
- Machine-readable aggregate report: `logs/knowledge_provenance_audit_20261031.json`; full regression log: `logs/full_regression_20261031_knowledge_lifecycle_guard.log`.

## 2026-10-31 — Corrected latest read-only audit and device checks
- Re-ran the read-only audit against the live DB after retrieval hardening. Exact current counts: 83,908 candidates; 80,198 legacy verified flags without a latest VERIFIED lifecycle event; 3,630 lifecycle records and all are UNVERIFIED; 80,278 candidates have no lifecycle event; 83,908 candidates each have exactly one evidence, one finding, and one distinct source; zero candidates have multiple distinct sources; zero latest VERIFIED records.
- All 83,908 evidence/finding/source references resolve, but a single source is not sufficient independent corroboration. No bulk promotion or DB writes were performed. Verified-only eligible live records: 0.
- Qwen3-4B remains blocked by RAM: current available RAM fell to about 1.2 GiB after the existing Qwen3-1.7B low-RAM fallback was started by the guarded launcher; 4B guard requires 3 GiB. The 1.7B model is online but is not accepted for semantic quality. No guard bypass.
- Media Bridge 38742 health: HTTP 200. Accessibility bridge 38741 is listening; GET /health is not a supported route (404), and an unauthenticated POST /v1/action is correctly rejected with 401. Companion package is installed; signed Termux token probe still returns 401, so pairing/authentication is unresolved.
- Android media diagnostics: Termux speech/tts/camera CLI commands exist, but com.termux.api package was not found and termux-tts-engines timed out. No microphone/camera capture was initiated. Physical voice E2E remains pending.
- Semantic vision model/weights are absent; OCR-only capability remains. P10 remains PARTIAL (v2.0 417-item reference recovered, exact v1.0 provenance unresolved); P11 release remains BLOCKED. No gate promoted.

## Final verification checkpoint — 2026-10-31 (latest code state)
- Verified-only Knowledge retrieval now fails closed at all three paths: persistent SQL list/FTS/Indic fallback requires latest VERIFIED lifecycle event; ResearchQueryEngine persistent results require that lifecycle event; in-memory results require both metadata verification_status=VERIFIED and last_verified_at.
- Latest focused gate suite after the final in-memory rule: 31 passed in 4.22s. Python compileall, shell syntax checks, and git diff --check all PASS.
- Earlier full repository regression before the final in-memory metadata tightening: 2,255 passed in 171.71s. A new full regression was attempted after the final tightening but the pytest process disappeared at 60% without a completion summary or exit code while Qwen3-1.7B remained loaded and available RAM was about 1.2 GiB. Treat this latest full run as INCOMPLETE, not PASS or FAIL.
- Current local model: Qwen3-1.7B online (low-RAM fallback); semantic accuracy acceptance remains BLOCKED/PARTIAL. Qwen3-4B was not launched because the 3 GiB safety guard was not met.
- Live service checks: Media Bridge 38742 HTTP 200; Accessibility Bridge 38741 rejects unauthenticated action with HTTP 401. Authenticated pairing/token validation remains unresolved.
- No P-series promotion. Physical P6 microphone/speaker E2E, P7 semantic vision model/accuracy, P8 authenticated device-control/Emergency Stop acceptance, P10 exact v1.0 provenance reconciliation, and P11 release remain open.
