from __future__ import annotations

from core.brain.sensor_equipment_input import (
    EquipmentType,
    SensorEquipmentInput,
    SensorEquipmentInputGateway,
    SensorType,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    gateway = SensorEquipmentInputGateway()

    observation = {
        "source_id": "thermal_sensor_01",
        "sensor_type": "thermal",
        "equipment_type": "sensor",
        "value": 37.5,
        "unit": "celsius",
        "timestamp": "2026-10-05T12:00:00+00:00",
        "confidence": 0.95,
        "metadata": {
            "location": "equipment_zone_a",
            "sample_rate": 10,
        },
    }

    sensor_input = gateway.ingest(observation)

    check(
        isinstance(sensor_input, SensorEquipmentInput),
        "Gateway must produce SensorEquipmentInput.",
    )

    check(
        sensor_input.source_id == "thermal_sensor_01",
        "Source identity must be preserved.",
    )

    check(
        sensor_input.sensor_type is SensorType.THERMAL,
        "Sensor type must be normalized.",
    )

    check(
        sensor_input.equipment_type is EquipmentType.SENSOR,
        "Equipment type must be normalized.",
    )

    check(
        sensor_input.value == 37.5,
        "Sensor value must be preserved.",
    )

    check(
        sensor_input.unit == "celsius",
        "Sensor unit must be preserved.",
    )

    check(
        sensor_input.confidence == 0.95,
        "Sensor confidence must be preserved.",
    )

    normalized = sensor_input.normalized()

    check(
        normalized["sensor_type"] == "thermal",
        "Normalized sensor type must be correct.",
    )

    check(
        normalized["value"] == 37.5,
        "Normalized value must be correct.",
    )

    check(
        normalized["metadata"]["sample_rate"] == 10,
        "Metadata must be preserved.",
    )

    # Security boundary.
    check(
        sensor_input.observation_only is True,
        "Sensor input must be observation-only.",
    )

    check(
        gateway.observation_is_read_only() is True,
        "Sensor gateway must be read-only.",
    )

    check(
        gateway.controls_equipment() is False,
        "Sensor input must not control equipment.",
    )

    check(
        gateway.executes_actions() is False,
        "Sensor input must not execute actions.",
    )

    check(
        gateway.grants_permission() is False,
        "Sensor input must not grant permission.",
    )

    check(
        gateway.modifies_equipment() is False,
        "Sensor input must not modify equipment.",
    )

    # Invalid confidence must fail closed.
    invalid_rejected = False

    try:
        gateway.ingest(
            {
                "source_id": "sensor_bad",
                "sensor_type": "temperature",
                "confidence": 2.0,
            }
        )
    except ValueError:
        invalid_rejected = True

    check(
        invalid_rejected,
        "Invalid sensor confidence must be rejected.",
    )

    print(
        "SAHIBEX PHASE 1 #22 SENSOR/EQUIPMENT "
        "INPUT TEST: PASS"
    )


if __name__ == "__main__":
    main()
