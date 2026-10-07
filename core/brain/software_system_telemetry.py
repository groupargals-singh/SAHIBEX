from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class TelemetrySnapshot:
    """
    Read-only software/system telemetry observation.

    This contract records observed system state only.
    It does not execute commands, grant authority, allocate resources,
    access credentials, or modify the system.
    """

    source: str
    timestamp: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    storage_percent: float | None = None
    process_count: int | None = None
    uptime_seconds: float | None = None
    runtime_state: str = ""
    health: str = ""
    metrics: Mapping[str, Any] = field(default_factory=dict)
    telemetry_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string.")

        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string.")

        numeric_fields = {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "storage_percent": self.storage_percent,
        }

        for name, value in numeric_fields.items():
            if value is not None:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"{name} must be numeric or None.")
                if not 0 <= float(value) <= 100:
                    raise ValueError(f"{name} must be between 0 and 100.")

        if self.process_count is not None:
            if not isinstance(self.process_count, int):
                raise TypeError("process_count must be an integer or None.")
            if self.process_count < 0:
                raise ValueError("process_count cannot be negative.")

        if self.uptime_seconds is not None:
            if not isinstance(self.uptime_seconds, (int, float)):
                raise TypeError("uptime_seconds must be numeric or None.")
            if self.uptime_seconds < 0:
                raise ValueError("uptime_seconds cannot be negative.")

        if not isinstance(self.runtime_state, str):
            raise TypeError("runtime_state must be a string.")

        if not isinstance(self.health, str):
            raise TypeError("health must be a string.")

        if not isinstance(self.metrics, Mapping):
            raise TypeError("metrics must be a mapping.")

        if not isinstance(self.telemetry_id, str) or not self.telemetry_id.strip():
            raise ValueError("telemetry_id must be a non-empty string.")

    @property
    def observation_only(self) -> bool:
        return True

    def normalized(self) -> dict[str, Any]:
        return {
            "telemetry_id": self.telemetry_id,
            "source": self.source.strip(),
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "storage_percent": self.storage_percent,
            "process_count": self.process_count,
            "uptime_seconds": self.uptime_seconds,
            "runtime_state": self.runtime_state.strip(),
            "health": self.health.strip(),
            "metrics": dict(self.metrics),
        }


class SoftwareSystemTelemetry:
    """
    Model-independent software/system telemetry normalizer.

    The collector does not access the OS itself. A trusted observation
    provider supplies raw values, and this class validates/normalizes them.

    No execution, permission, credential, network, or system-change
    authority is provided by this component.
    """

    def __init__(self, source: str = "software_system") -> None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string.")

        self.source = source.strip()

    def collect(
        self,
        observation: Mapping[str, Any],
    ) -> TelemetrySnapshot:
        if not isinstance(observation, Mapping):
            raise TypeError("observation must be a mapping.")

        return TelemetrySnapshot(
            source=self.source,
            timestamp=str(
                observation.get(
                    "timestamp",
                    datetime.now(timezone.utc).isoformat(),
                )
            ),
            cpu_percent=observation.get("cpu_percent"),
            memory_percent=observation.get("memory_percent"),
            storage_percent=observation.get("storage_percent"),
            process_count=observation.get("process_count"),
            uptime_seconds=observation.get("uptime_seconds"),
            runtime_state=str(observation.get("runtime_state", "")),
            health=str(observation.get("health", "")),
            metrics=dict(observation.get("metrics", {})),
        )

    def normalize(
        self,
        snapshot: TelemetrySnapshot,
    ) -> dict[str, Any]:
        if not isinstance(snapshot, TelemetrySnapshot):
            raise TypeError("snapshot must be a TelemetrySnapshot.")

        return snapshot.normalized()

    @staticmethod
    def observation_is_read_only() -> bool:
        return True

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def modifies_system() -> bool:
        return False

    @staticmethod
    def accesses_credentials() -> bool:
        return False
