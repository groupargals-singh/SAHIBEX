"""
SAHIBEX Child Brain Foundation v1.0
Final consolidated integration/regression gate.

This test does not create a real child brain and does not execute
real tools, shell commands, network requests, or filesystem writes.

It runs the already-verified integration tests for each major
Child Brain foundation subsystem.
"""

from tests.unit.test_child_runtime_foundation import (
    main as runtime_foundation_test,
)
from tests.unit.test_child_workers import (
    main as child_workers_test,
)
from tests.unit.test_child_birth_pipeline import (
    main as child_birth_pipeline_test,
)
from tests.unit.test_mother_child_integration import (
    main as mother_child_integration_test,
)
from tests.unit.test_child_tool_security_pipeline import (
    main as child_tool_security_pipeline_test,
)
from tests.unit.test_child_tool_execution_orchestrator import (
    main as child_tool_orchestrator_test,
)


def run_test(name: str, test_function) -> None:
    print(f"\n--- {name} ---")
    test_function()


def main() -> None:
    print("==============================================")
    print("SAHIBEX CHILD BRAIN FOUNDATION v1.0")
    print("CONSOLIDATED INTEGRATION TEST")
    print("==============================================")

    run_test(
        "CHILD RUNTIME FOUNDATION",
        runtime_foundation_test,
    )

    run_test(
        "CHILD ARMY + LABOR WORKERS",
        child_workers_test,
    )

    run_test(
        "CHILD BIRTH PIPELINE",
        child_birth_pipeline_test,
    )

    run_test(
        "MOTHER <-> CHILD INTEGRATION",
        mother_child_integration_test,
    )

    run_test(
        "CHILD TOOL SECURITY PIPELINE",
        child_tool_security_pipeline_test,
    )

    run_test(
        "CHILD TOOL EXECUTION ORCHESTRATOR",
        child_tool_orchestrator_test,
    )

    print("\n==============================================")
    print("SAHIBEX CHILD BRAIN FOUNDATION TEST: PASS")
    print("==============================================")


if __name__ == "__main__":
    main()
