from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class BrainMessage:
    """
    Immutable communication contract between two specialist brains.

    This object only carries a message.

    It does not:
    - grant permissions
    - authorize actions
    - execute tools
    - access memory
    - select models
    - contain credentials
    """

    sender_brain_id: str
    receiver_brain_id: str
    message_type: str
    payload: dict
    message_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.sender_brain_id, str)
            or not self.sender_brain_id.strip()
        ):
            raise ValueError(
                "sender_brain_id must be a non-empty string."
            )

        if (
            not isinstance(self.receiver_brain_id, str)
            or not self.receiver_brain_id.strip()
        ):
            raise ValueError(
                "receiver_brain_id must be a non-empty string."
            )

        if self.sender_brain_id == self.receiver_brain_id:
            raise ValueError(
                "sender and receiver brain IDs must be different."
            )

        if (
            not isinstance(self.message_type, str)
            or not self.message_type.strip()
        ):
            raise ValueError(
                "message_type must be a non-empty string."
            )

        if not isinstance(self.payload, dict):
            raise TypeError(
                "payload must be a dictionary."
            )

        if (
            not isinstance(self.message_id, str)
            or not self.message_id.strip()
        ):
            raise ValueError(
                "message_id must be a non-empty string."
            )

        if (
            not isinstance(self.created_at, str)
            or not self.created_at.strip()
        ):
            raise ValueError(
                "created_at must be a non-empty string."
            )
