# SAHIBEX MASTER ROADMAP - RECONCILED SOURCE OF TRUTH

Status: RECONCILIATION BASELINE
Branch: main

## 0. NON-NEGOTIABLE GOVERNANCE
- Human Authority remains supreme.
- Protected actions require explicit permission/approval.
- Constitution cannot be modified by SAHIBEX itself.
- PASS is not the same as COMPLETE.
- BLOCKED items are never silently marked complete.
- No engineering milestone number replaces the master architecture roadmap.

## 1. ORIGINAL ARCHITECTURE BASELINE
Original baseline: 417 items across Phase A-AC (29 phase labels).

Repository implementation checkpoints exist for:
A, B, C, D, E, F, H, I, J, L, M, N, O, P, Q, R, S, W, X, Y, Z, AA, AB.

Missing/unreconciled labels:
G, K, T, U, V, AC.

These six labels are NOT declared failed or unnecessary. Their original specifications must be recovered/reconciled before completion can be claimed.

A  IMPLEMENTED CHECKPOINT - brain foundation
B  IMPLEMENTED CHECKPOINT - input validation / sensory-input coverage
C  IMPLEMENTED CHECKPOINT - perception
D  IMPLEMENTED CHECKPOINT - attention
E  IMPLEMENTED CHECKPOINT - working memory
F  IMPLEMENTED CHECKPOINT - long-term memory
G  NEEDS SPECIFICATION RECONCILIATION
H  IMPLEMENTED CHECKPOINT - reasoning
I  IMPLEMENTED CHECKPOINT - executive brain
J  IMPLEMENTED CHECKPOINT - inhibition/control
K  NEEDS SPECIFICATION RECONCILIATION
L  IMPLEMENTED CHECKPOINT - verification
M  IMPLEMENTED CHECKPOINT - learning
N  IMPLEMENTED CHECKPOINT - sleep/consolidation
O  IMPLEMENTED CHECKPOINT - computational state
P  IMPLEMENTED CHECKPOINT - child genesis
Q  IMPLEMENTED CHECKPOINT - independent child brain
R  IMPLEMENTED CHECKPOINT - mother-child integration
S  IMPLEMENTED CHECKPOINT - living child loop
T  NEEDS SPECIFICATION RECONCILIATION
U  NEEDS SPECIFICATION RECONCILIATION
V  NEEDS SPECIFICATION RECONCILIATION
W  IMPLEMENTED CHECKPOINT - model independence
X  IMPLEMENTED CHECKPOINT - continuous runtime
Y  IMPLEMENTED CHECKPOINT - observability
Z  IMPLEMENTED CHECKPOINT - backup/recovery
AA IMPLEMENTED CHECKPOINT - audit/provenance
AB IMPLEMENTED CHECKPOINT - failure/recovery
AC NEEDS SPECIFICATION RECONCILIATION

## 2. MAYA / HUNTER EXPANSION TRACK
E01 Tool/skill genesis
E02 Self-generated skills
E03 Pre-use skill/tool testing
E04 Long-running jobs
E05 Checkpoint/resume
E06 Intelligent task decomposition
E07 Multi-step execution chains
E08 Background workers
E09 Job lifecycle/history/audit
E10 Human intervention points
E11 Advanced computer/UI automation
E12 Routine/macro learning
E13 Controlled capability expansion/adaptation

These additions must be mapped into the original architecture rather than replacing it.

## 3. 6P ENGINEERING OVERLAY
6P is an engineering overlay, not a replacement for A-AC.

Repository tests contain 6P-1 through 6P-29. The maintained 6P roadmap document defines 6P-1 through 6P-12, while later 6P-13..29 exist in tests; therefore the later extension needs reconciliation.

Evidence already found:
- 6P-1 objective/task intake implemented
- 6P-2 decomposition implemented
- 6P-3 planning implemented
- 6P-6 long-running jobs implemented
- 6P-7 checkpoint/resume implemented
- 6P-8 background workers implemented
- 6P-15 adversarial execution integrity PASS
- 6P-16 cross-layer tamper integrity PASS
- 6P-17 identity correlation integrity PASS
- 6P-18 cross-layer identity binding PASS
- 6P-19 real audit identity binding PASS
- 6P-20 real 3-layer identity binding PASS
- 6P-21 real execution result integrity PASS
- 6P-22 execution provenance/authenticity PASS
- 6P-23 provenance/trace/audit test exists
- 6P-24 replay/freshness test exists
- 6P-25 brain-trust provenance tests exist
- 6P-26 trust invalidation/lifecycle tests exist
- 6P-27 trust replacement tests exist
- 6P-28 trust lineage tests exist
- 6P-29 current trust binding/currentness tests exist

These are evidence records, not blanket completion claims.

## 4. ANDROID / COMPUTER CONTROL
Android Companion source and gated computer-control implementation exist.

Current blocker:
- Real Android screenshot runtime test is BLOCKED.
- Companion bridge is not currently observed running on the device.
- Device-level screenshot/UI-control end-to-end verification is still required.

ANDROID REAL RUNTIME = BLOCKED until the actual device-level test passes.

## 5. CURRENT REPOSITORY SCALE
- Branch: main
- Working tree was clean before this roadmap document
- 745 Python files excluding virtualenv/git
- 431 test files
- Full regression baseline: 1077 passed, 6 warnings (latest run)
- Core, research, memory, specialist-brain, security, verification, tools, agent, and Android companion layers exist.
- Working tree was clean before and after the verification run.

## 6. STATUS DEFINITIONS
PASS = a specific test/verification passed.
IMPLEMENTED = relevant code exists and is integrated; final system verification may remain.
COMPLETE = specification mapped + implementation integrated + dedicated verification passed + required security/authority/regression evidence complete.
BLOCKED = an external/device/dependency condition prevents completion.
NEEDS RECONCILIATION = specification/mapping is incomplete; no completion claim is allowed.

## 7. NEXT MASTER WORKSTREAM
Do NOT continue blindly with 6P-23.

First:
1. Recover/reconstruct the original A-AC 417-item specification.
2. Map every phase/item to current files and tests.
3. Reconcile G/K/T/U/V/AC.
4. Map E01-E13 into the 417 baseline.
5. Reconcile 6P-1..29 against the architecture.
6. Classify every item: COMPLETE / IMPLEMENTED-PENDING-VERIFICATION / PARTIAL / BLOCKED / NEEDS-RECONCILIATION.
7. Identify duplicate/historical tests so they are not counted as separate architecture requirements.
8. Produce the final remaining-work list.
9. Only then resume numbered implementation milestones.

## 8. SAFETY RULE
No milestone is complete merely because a test file exists or prints PASS.
Do not overwrite working implementation merely to satisfy a roadmap label.
Protected actions remain permission-gated.
All changes remain auditable and reversible.
