from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from security.audit.execution_freshness import (
    ExecutionFreshnessGuard,
)

from security.audit.execution_provenance import (
    ExecutionProvenance,
)


@dataclass(frozen=True)
class ExecutionTraceResult:
    """
    Result of validating one execution evidence trace.

    This verifier only validates evidence consistency
    and, when explicitly requested, authenticated
    execution provenance.

    It does not:
    - execute tools
    - grant permissions
    - change confirmation
    - modify the SAHIBEX constitution
    """

    verified: bool
    execution_id: str
    checks_passed: int
    checks_failed: int
    reasons: tuple[str, ...]


class ExecutionTraceVerifier:
    """
    Validates execution evidence identity and consistency.

    Security boundary:
    - never executes tools
    - never grants permission
    - never changes confirmation
    - never modifies constitution
    - provenance verification never grants authority
    """

    REQUIRED_FIELDS = (
        "execution_id",
        "tool",
        "action",
        "permission_allowed",
        "confirmation_required",
        "confirmation_provided",
        "attempts",
        "verification_status",
        "recovery_status",
        "final_status",
        "risk",
        "reason",
    )

    def verify(
        self,
        evidence: dict[str, Any],
    ) -> ExecutionTraceResult:
        """
        Validate internal execution-evidence consistency.

        This is the original 6P-11 consistency contract.

        It intentionally does NOT require provenance so that
        existing synthetic/legacy evidence tests remain valid.
        """

        if not isinstance(evidence, dict):
            raise TypeError(
                "evidence must be a dictionary."
            )

        execution_id = str(
            evidence.get("execution_id", "")
        ).strip()

        if not execution_id:
            raise ValueError(
                "execution_id cannot be empty."
            )

        passed = 0
        failed = 0
        reasons: list[str] = []

        for field_name in self.REQUIRED_FIELDS:
            if field_name not in evidence:
                failed += 1
                reasons.append(
                    f"Missing required field: {field_name}"
                )
            else:
                passed += 1

        if failed:
            return ExecutionTraceResult(
                verified=False,
                execution_id=execution_id,
                checks_passed=passed,
                checks_failed=failed,
                reasons=tuple(reasons),
            )

        if not str(evidence["tool"]).strip():
            failed += 1
            reasons.append(
                "tool cannot be empty."
            )
        else:
            passed += 1

        if not str(evidence["action"]).strip():
            failed += 1
            reasons.append(
                "action cannot be empty."
            )
        else:
            passed += 1

        if not isinstance(
            evidence["permission_allowed"],
            bool,
        ):
            failed += 1
            reasons.append(
                "permission_allowed must be bool."
            )
        else:
            passed += 1

        if not isinstance(
            evidence["confirmation_required"],
            bool,
        ):
            failed += 1
            reasons.append(
                "confirmation_required must be bool."
            )
        else:
            passed += 1

        if not isinstance(
            evidence["confirmation_provided"],
            bool,
        ):
            failed += 1
            reasons.append(
                "confirmation_provided must be bool."
            )
        else:
            passed += 1

        if (
            evidence["confirmation_provided"]
            and not evidence["confirmation_required"]
        ):
            failed += 1
            reasons.append(
                "Confirmation provided without "
                "confirmation requirement."
            )
        else:
            passed += 1

        if not isinstance(
            evidence["attempts"],
            int,
        ):
            failed += 1
            reasons.append(
                "attempts must be an integer."
            )
        elif evidence["attempts"] < 1:
            failed += 1
            reasons.append(
                "attempts must be greater than zero."
            )
        else:
            passed += 1

        verification_status = str(
            evidence["verification_status"]
        ).strip()

        recovery_status = str(
            evidence["recovery_status"]
        ).strip()

        final_status = str(
            evidence["final_status"]
        ).strip()

        if not verification_status:
            failed += 1
            reasons.append(
                "verification_status cannot be empty."
            )
        else:
            passed += 1

        if not recovery_status:
            failed += 1
            reasons.append(
                "recovery_status cannot be empty."
            )
        else:
            passed += 1

        if not final_status:
            failed += 1
            reasons.append(
                "final_status cannot be empty."
            )
        else:
            passed += 1

        if final_status == "SUCCESS":
            if evidence["permission_allowed"] is not True:
                failed += 1
                reasons.append(
                    "SUCCESS requires allowed permission."
                )
            else:
                passed += 1

            if verification_status != "VERIFIED":
                failed += 1
                reasons.append(
                    "SUCCESS requires VERIFIED status."
                )
            else:
                passed += 1

            if recovery_status != "SUCCESS":
                failed += 1
                reasons.append(
                    "SUCCESS requires SUCCESS recovery."
                )
            else:
                passed += 1

            if evidence.get("error") is not None:
                failed += 1
                reasons.append(
                    "SUCCESS cannot contain an error."
                )
            else:
                passed += 1

        if final_status == "BLOCKED":
            if evidence["permission_allowed"] is True:
                failed += 1
                reasons.append(
                    "BLOCKED cannot report allowed permission."
                )
            else:
                passed += 1

        if final_status == "FAILED":
            if verification_status == "VERIFIED":
                failed += 1
                reasons.append(
                    "FAILED cannot report VERIFIED status."
                )
            else:
                passed += 1

        return ExecutionTraceResult(
            verified=failed == 0,
            execution_id=execution_id,
            checks_passed=passed,
            checks_failed=failed,
            reasons=tuple(reasons),
        )

    def verify_provenance(
        self,
        evidence: dict[str, Any],
        provenance_directory: Path,
    ) -> ExecutionTraceResult:
        """
        Strict 6P-22 verification.

        First validates normal execution consistency.
        Then validates the authenticated provenance proof.

        The provenance key is loaded from the supplied trusted
        provenance directory or from the configured environment.

        Provenance does NOT:
        - grant permission
        - authorize execution
        - modify evidence
        - modify constitution
        """

        trace = self.verify(evidence)

        if not trace.verified:
            return trace

        if not isinstance(
            provenance_directory,
            Path,
        ):
            provenance_directory = Path(
                provenance_directory
            )

        provenance = ExecutionProvenance(
            provenance_directory
        )

        result = provenance.verify(
            evidence
        )

        if not result.verified:
            return ExecutionTraceResult(
                verified=False,
                execution_id=trace.execution_id,
                checks_passed=trace.checks_passed,
                checks_failed=(
                    trace.checks_failed + 1
                ),
                reasons=(
                    *trace.reasons,
                    result.reason,
                ),
            )

        return trace

    def verify_fresh(
        self,
        evidence: dict[str, Any],
        provenance_directory: Path,
    ) -> ExecutionTraceResult:
        """
        Strict 6P-24 fresh-execution verification.

        Validation order:
        1. normal execution consistency
        2. authenticated provenance
        3. persistent replay/freshness check

        First valid use of an execution identity is accepted
        and consumed.

        A second use of the same execution identity is rejected
        as replay.

        Historical verification remains available through
        verify() and verify_provenance().

        Freshness does NOT:
        - grant permission
        - authorize execution
        - execute tools
        - change confirmation
        - modify evidence
        - modify constitution
        """

        trace = self.verify_provenance(
            evidence,
            provenance_directory,
        )

        if not trace.verified:
            return trace

        freshness = ExecutionFreshnessGuard(
            provenance_directory
        )

        consumed = freshness.consume(evidence)

        if not consumed:
            return ExecutionTraceResult(
                verified=False,
                execution_id=trace.execution_id,
                checks_passed=trace.checks_passed,
                checks_failed=trace.checks_failed + 1,
                reasons=(
                    *trace.reasons,
                    "Execution replay detected: "
                    "execution_id was already consumed.",
                ),
            )

        return ExecutionTraceResult(
            verified=True,
            execution_id=trace.execution_id,
            checks_passed=trace.checks_passed + 1,
            checks_failed=trace.checks_failed,
            reasons=trace.reasons,
        )
