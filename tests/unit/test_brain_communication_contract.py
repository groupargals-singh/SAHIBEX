from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-7 Brain Communication Contract
    # ---------------------------------------------------------

    sender = SpecialistBrain(
        name="Research Specialist",
        description="Research specialist brain.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    receiver = SpecialistBrain(
        name="Verification Specialist",
        description="Verification specialist brain.",
        specialization="verification",
        capabilities={
            BrainCapability.VERIFY,
        },
    )

    # 1. Communication object must exist.
    from core.brain.communication import BrainMessage

    message = BrainMessage(
        sender_brain_id=sender.brain_id,
        receiver_brain_id=receiver.brain_id,
        message_type="finding",
        payload={
            "topic": "test",
            "content": "Research finding",
        },
    )

    # 2. Sender identity must be preserved.
    check(
        message.sender_brain_id == sender.brain_id,
        "Message must preserve sender brain identity.",
    )

    # 3. Receiver identity must be preserved.
    check(
        message.receiver_brain_id == receiver.brain_id,
        "Message must preserve receiver brain identity.",
    )

    # 4. Message must have stable unique identity.
    check(
        isinstance(message.message_id, str)
        and bool(message.message_id.strip()),
        "Message must have a non-empty message_id.",
    )

    # 5. Message type must be preserved.
    check(
        message.message_type == "finding",
        "Message type must be preserved.",
    )

    # 6. Payload must be preserved.
    check(
        message.payload["topic"] == "test",
        "Message payload must be preserved.",
    )

    # 7. Sender and receiver cannot be the same brain.
    same_brain_rejected = False

    try:
        BrainMessage(
            sender_brain_id=sender.brain_id,
            receiver_brain_id=sender.brain_id,
            message_type="finding",
            payload={"content": "invalid"},
        )
    except ValueError:
        same_brain_rejected = True

    check(
        same_brain_rejected,
        "A brain must not send a message to itself.",
    )

    # 8. Empty sender identity must be rejected.
    empty_sender_rejected = False

    try:
        BrainMessage(
            sender_brain_id="",
            receiver_brain_id=receiver.brain_id,
            message_type="finding",
            payload={"content": "invalid"},
        )
    except ValueError:
        empty_sender_rejected = True

    check(
        empty_sender_rejected,
        "Empty sender identity must be rejected.",
    )

    # 9. Empty receiver identity must be rejected.
    empty_receiver_rejected = False

    try:
        BrainMessage(
            sender_brain_id=sender.brain_id,
            receiver_brain_id="",
            message_type="finding",
            payload={"content": "invalid"},
        )
    except ValueError:
        empty_receiver_rejected = True

    check(
        empty_receiver_rejected,
        "Empty receiver identity must be rejected.",
    )

    # 10. Communication must not grant permissions.
    message_fields = set(message.__dataclass_fields__)

    check(
        "permission" not in message_fields,
        "Communication message must not contain permission fields.",
    )

    check(
        "authorization" not in message_fields,
        "Communication message must not contain authorization fields.",
    )

    # 11. Communication must not contain model/provider authority.
    check(
        "api_key" not in message_fields,
        "Communication message must not contain API keys.",
    )

    check(
        "credential" not in message_fields,
        "Communication message must not contain credentials.",
    )

    print(
        "SAHIBEX 6L-7 BRAIN COMMUNICATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
