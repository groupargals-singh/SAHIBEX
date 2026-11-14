# SAHIBEX Autonomous Engineering Controller v2 — 2026-11-14

## Scope delivered

- Preserved v1 bounded repository inspection and test/compile commands.
- Added `core/agent/engineering_patch_engine.py` for controlled unified-diff preflight, application, content-addressed backup and guarded rollback.
- Added Termux CLI commands:
  - `engineering patch-check <patch-file>` — validates and runs `git apply --check`; makes no repository changes.
  - `engineering patch-apply <patch-file>` — explicit command applies a validated patch after backup.
  - `engineering patch-rollback <backup-id>` — restores only when every target still matches the recorded post-patch SHA-256.
- Patch scope is deliberately limited to 1–20 existing tracked regular files, maximum 256 KiB patch and 2 MiB per file.
- Rejects absolute/traversal/non-canonical paths, symlinks, binary patches, add/delete/rename/copy/mode changes, duplicate targets, untracked targets and pre-existing user modifications.
- Backups are stored outside the Git repository under `~/.cache/sahibex/engineering-backups`; each original file is SHA-256 verified.
- Rollback uses atomic replacement and refuses to overwrite any later modification.
- Existing user work and the pre-existing untracked `.fix_research_multi_finding.py` and `backups/` remain untouched.

## Verification

- Focused v1 + v2 regression: **14 passed**.
- Python compile check: PASS.
- Full repository regression: **2,393 passed in 208.38s**, exit 0.
- CLI wiring is compiled; patch operations are also directly covered by isolated temporary-Git-repository tests.

## Boundaries still open

- Patch generation is not yet model-backed or autonomously approved. A patch must be supplied as a file and the user must explicitly issue `engineering patch-apply`.
- This is not yet a full unattended build-fix-test-publish loop.
- GitHub commit/push remains a separate explicit publishing layer; browser/cloud and Android UI control are not granted.
- No P6/P7/P8/P10/P11 release gate is promoted.
