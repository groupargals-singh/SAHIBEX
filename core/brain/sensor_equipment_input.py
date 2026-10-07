from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    SOUND = "sound"
    LIGHT = "light"
    MOTION = "motion"
    PROXIMITY = "proximity"
    ELECTRICAL = "electrical"
    GAS = "gas"
    THERMAL = "thermal"
    GENERIC = "generic"


class EquipmentType(str, Enum):
    SENSOR = "sensor"
    MACHINE = "machine"
    DEVICE = "device"
    INSTRUMENT = "instrument"
    CONTROLLER = "controller"
    GENERIC = "generic"


@dataclass(frozen=True)
class SensorEquipmentInput:
    """
    Read-only observation from a sensor or external equipment.

    This contract carries observations only. It does not control,
    configure, execute, or modify the source equipment.
    """

    source_id: str
    sensor_type: SensorType
    equipment_type: EquipmentType = EquipmentType.SENSOR
    value: Any = None
    unit: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    confidence: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string.")

        if not isinstance(self.sensor_type, SensorType):
            raise TypeError("sensor_type must be SensorType.")

        if not isinstance(self.equipment_type, EquipmentType):
            raise TypeError("equipment_type must be EquipmentType.")

        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string.")

        if not isinstance(self.unit, str):
            raise TypeError("unit must be a string.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric.")

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

    @property
    def observation_only(self) -> bool:
        return True

    def normalized(self) -> dict[str, Any]:
        return {
            "input_id": self.input_id,
            "source_id": self.source_id.strip(),
            "sensor_type": self.sensor_type.value,
            "equipment_type": self.equipment_type.value,
            "value": self.value,
            "unit": self.unit.strip(),
            "timestamp": self.timestamp,
            "confidence": float(self.confidence),
            "metadata": dict(self.metadata),
        }


class SensorEquipmentInputGateway:
    """
    Validates and normalizes externally supplied sensor/equipment data.

    This gateway does not communicate with hardware itself. A separate
    hardware adapter may provide observations later.
    """

    def ingest(
        self,
        observation: Mapping[str, Any],
    ) -> SensorEquipmentInput:
        if not isinstance(observation, Mapping):
            raise TypeError("observation must be a mapping.")

        sensor_type = observation.get(
            "sensor_type",
            SensorType.GENERIC,
        )

        if not isinstance(sensor_type, SensorType):
            sensor_type = SensorType(str(sensor_type))

        equipment_type = observation.get(
            "equipment_type",
            EquipmentType.SENSOR,
        )

        if not isinstance(equipment_type, EquipmentType):
            equipment_type = EquipmentType(str(equipment_type))

        return SensorEquipmentInput(
            source_id=str(observation.get("source_id", "")),
            sensor_type=sensor_type,
            equipment_type=equipment_type,
            value=observation.get("value"),
            unit=str(observation.get("unit", "")),
            timestamp=str(
                observation.get(
                    "timestamp",
                    datetime.now(timezone.utc).isoformat(),
                )
            ),
            confidence=observation.get("confidence", 1.0),
            metadata=dict(observation.get("metadata", {})),
        )

    @staticmethod
    def observation_is_read_only() -> bool:
        return True

    @staticmethod
    def controls_equipment() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def modifies_equipment() -> bool:
        return False
