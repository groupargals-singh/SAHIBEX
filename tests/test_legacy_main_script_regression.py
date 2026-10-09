"""Run legacy main()-style test scripts as part of normal pytest regression.

Historically, many files named test_*.py only executed assertions from main()
and were silently skipped by pytest collection. This harness keeps those
scripts in the automated regression suite without importing their side effects.
Device-interactive acceptance probes remain separate and must be run manually.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_SCRIPT_NAMES = {
    "test_android_real_runtime_probe.py",
    "test_live_persistent_memory_context.py",
}


def _legacy_main_scripts() -> list[str]:
    scripts: list[str] = []
    for path in sorted((PROJECT_ROOT / "tests").rglob("test_*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.name in EXCLUDED_SCRIPT_NAMES or "live_" in path.name:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        has_pytest_tests = any(
            line.lstrip().startswith(("def test_", "async def test_"))
            for line in source.splitlines()
        )
        if "def main(" in source and not has_pytest_tests:
            scripts.append(str(path.relative_to(PROJECT_ROOT)))
    return scripts


LEGACY_MAIN_SCRIPTS = _legacy_main_scripts()


@pytest.mark.parametrize("script", LEGACY_MAIN_SCRIPTS, ids=LEGACY_MAIN_SCRIPTS)
def test_legacy_main_script_passes(script: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, (
        f"Legacy test script failed: {script}\n"
        f"exit code: {completed.returncode}\n"
        f"output tail:\n{completed.stdout[-6000:]}"
    )
