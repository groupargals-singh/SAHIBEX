from __future__ import annotations

import subprocess
import sys


TEST_MODULES = [
    "tests.unit.test_specialist_brain_contract",
    "tests.unit.test_brain_registry_contract",
    "tests.unit.test_brain_capability_contract",
    "tests.unit.test_brain_selection_contract",
    "tests.unit.test_brain_lifecycle_contract",
    "tests.unit.test_brain_memory_isolation_contract",
    "tests.unit.test_brain_communication_contract",
    "tests.unit.test_brain_verification_trust_contract",
    "tests.unit.test_brain_resource_load_contract",
    "tests.unit.test_brain_intelligence_contract",
]


def main() -> None:
    for module in TEST_MODULES:
        result = subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stdout, end="")
            print(result.stderr, end="")
            raise AssertionError(
                f"Specialist Brain regression failed: {module}"
            )

        print(result.stdout, end="")

    print("SAHIBEX 6L-11 FULL SPECIALIST BRAIN REGRESSION: PASS")


if __name__ == "__main__":
    main()
