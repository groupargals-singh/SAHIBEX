from __future__ import annotations

from core.brain.software_system_telemetry import (
    SoftwareSystemTelemetry,
    TelemetrySnapshot,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    telemetry = SoftwareSystemTelemetry(
        source="test_system"
    )

    observation = {
        "timestamp": "2026-10-05T12:00:00+00:00",
        "cpu_percent": 42.5,
        "memory_percent": 61.0,
        "storage_percent": 55.0,
        "process_count": 128,
        "uptime_seconds": 3600,
        "runtime_state": "running",
        "health": "healthy",
        "metrics": {
            "temperature": 48.0,
            "active_services": 12,
        },
    }

    snapshot = telemetry.collect(observation)

    check(
        isinstance(snapshot, TelemetrySnapshot),
        "Telemetry must produce TelemetrySnapshot.",
    )

    check(
        snapshot.source == "test_system",
        "Telemetry source must be preserved.",
    )

    check(
        snapshot.cpu_percent == 42.5,
        "CPU telemetry must be preserved.",
    )

    check(
        snapshot.memory_percent == 61.0,
        "Memory telemetry must be preserved.",
    )

    check(
        snapshot.storage_percent == 55.0,
        "Storage telemetry must be preserved.",
    )

    check(
        snapshot.process_count == 128,
        "Process count must be preserved.",
    )

    check(
        snapshot.uptime_seconds == 3600,
        "Uptime must be preserved.",
    )

    check(
        snapshot.health == "healthy",
        "Health state must be preserved.",
    )

    normalized = telemetry.normalize(snapshot)

    check(
        normalized["source"] == "test_system",
        "Normalized source must be preserved.",
    )

    check(
        normalized["metrics"]["temperature"] == 48.0,
        "Custom metrics must be preserved.",
    )

    # Telemetry is observation only.
    check(
        snapshot.observation_only is True,
        "Telemetry must be observation-only.",
    )

    check(
        telemetry.observation_is_read_only() is True,
        "Telemetry must be read-only.",
    )

    check(
        telemetry.grants_permission() is False,
        "Telemetry must not grant permission.",
    )

    check(
        telemetry.executes_actions() is False,
        "Telemetry must not execute actions.",
    )

    check(
        telemetry.modifies_system() is False,
        "Telemetry must not modify the system.",
    )

    check(
        telemetry.accesses_credentials() is False,
        "Telemetry must not access credentials.",
    )

    # Invalid values must fail closed.
    invalid_rejected = False

    try:
        telemetry.collect(
            {
                "cpu_percent": 150,
            }
        )
    except ValueError:
        invalid_rejected = True

    check(
        invalid_rejected,
        "Invalid CPU telemetry must be rejected.",
    )

    print(
        "SAHIBEX PHASE 1 #21 SOFTWARE/SYSTEM "
        "TELEMETRY INPUT TEST: PASS"
    )


if __name__ == "__main__":
    main()
