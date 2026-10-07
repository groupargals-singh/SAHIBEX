from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.brain.mother_sandbox_runtime import (
    MotherSandboxDecision,
    MotherSandboxRequest,
    MotherSandboxRuntime,
)


def main() -> None:
    sandbox = MotherSandboxRuntime()

    print("=" * 60)
    print("SAHIBEX 6S-1 MOTHER SANDBOX RUNTIME TEST")
    print("=" * 60)

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-001",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.ALLOW
    assert result.allowed is True
    assert result.missing_isolation == ()
    print("[PASS] fully isolated sandbox request allowed")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-002",
            action="protected_execution",
            isolated_filesystem=False,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    assert result.allowed is False
    assert "isolated_filesystem" in result.missing_isolation
    print("[PASS] filesystem isolation failure blocked")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-003",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=False,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    assert "isolated_credentials" in result.missing_isolation
    print("[PASS] credential isolation failure blocked")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-004",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=False,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    assert "isolated_network" in result.missing_isolation
    print("[PASS] network isolation failure blocked")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-005",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=False,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    assert "isolated_runtime" in result.missing_isolation
    print("[PASS] live-runtime isolation failure blocked")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    print("[PASS] missing request ID blocked")

    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="sandbox-test-007",
            action="",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    assert result.decision == MotherSandboxDecision.BLOCK
    print("[PASS] missing action blocked")

    print("=" * 60)
    print("SAHIBEX 6S-1 MOTHER SANDBOX RUNTIME TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
