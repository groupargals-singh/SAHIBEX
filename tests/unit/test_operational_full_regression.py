from __future__ import annotations

import subprocess
import sys


OPERATIONAL_TESTS = [
    "tests.unit.test_operational_brain_contract",
    "tests.unit.test_operational_model_integration",
    "tests.unit.test_operational_reasoning",
    "tests.unit.test_operational_memory_knowledge",
    "tests.unit.test_operational_specialist_dispatch",
    "tests.unit.test_operational_tool_execution",
    "tests.unit.test_operational_protected_action",
    "tests.unit.test_operational_multimodal",
    "tests.unit.test_operational_verification",
    "tests.unit.test_operational_end_to_end",
]


def run_test(module_name: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        print(f"\nFAILED: {module_name}")
        print("----- STDOUT -----")
        print(completed.stdout)
        print("----- STDERR -----")
        print(completed.stderr)
        raise SystemExit(completed.returncode)

    print(f"PASS: {module_name}")

    if completed.stdout.strip():
        print(completed.stdout.strip())


def main() -> None:
    print("SAHIBEX 6O-11 FULL OPERATIONAL REGRESSION")
    print("=" * 60)

    for module_name in OPERATIONAL_TESTS:
        run_test(module_name)

    print("=" * 60)
    print("SAHIBEX 6O-11 FULL OPERATIONAL REGRESSION: PASS")


if __name__ == "__main__":
    main()
