from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, log_directory: Path):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)

        self.log_file = (
            self.log_directory / "sahibex_audit.jsonl"
        )

        self._lock = threading.Lock()

    def record(
        self,
        *,
        request: str,
        intent: str,
        intent_confidence: float,
        action: str,
        action_confidence: float,
        risk: str,
        permission_allowed: bool,
        confirmation_required: bool,
        reason: str,
        execution_id: str | None = None,
    ) -> dict[str, Any]:

        if not isinstance(request, str) or not request.strip():
            raise ValueError("request cannot be empty.")

        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("intent cannot be empty.")

        if not isinstance(action, str) or not action.strip():
            raise ValueError("action cannot be empty.")

        if not isinstance(risk, str) or not risk.strip():
            raise ValueError("risk cannot be empty.")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason cannot be empty.")

        if not isinstance(
            intent_confidence,
            (int, float),
        ):
            raise TypeError(
                "intent_confidence must be numeric."
            )

        if not isinstance(
            action_confidence,
            (int, float),
        ):
            raise TypeError(
                "action_confidence must be numeric."
            )

        if not isinstance(
            permission_allowed,
            bool,
        ):
            raise TypeError(
                "permission_allowed must be bool."
            )

        if not isinstance(
            confirmation_required,
            bool,
        ):
            raise TypeError(
                "confirmation_required must be bool."
            )

        if execution_id is not None:
            if not isinstance(execution_id, str):
                raise TypeError(
                    "execution_id must be a string or None."
                )

            if not execution_id.strip():
                raise ValueError(
                    "execution_id cannot be empty."
                )

        event: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "request": request,
            "intent": intent,
            "intent_confidence": round(
                float(intent_confidence),
                4,
            ),
            "action": action,
            "action_confidence": round(
                float(action_confidence),
                4,
            ),
            "risk": risk,
            "permission": (
                "allowed"
                if permission_allowed
                else "blocked"
            ),
            "confirmation_required": (
                confirmation_required
            ),
            "reason": reason,
        }

        if execution_id is not None:
            event["execution_id"] = execution_id

        serialized = json.dumps(
            event,
            ensure_ascii=False,
            default=str,
        )

        with self._lock:
            with self.log_file.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(serialized + "\n")

        return event

    def read_recent(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not isinstance(limit, int):
            raise TypeError("limit must be int.")

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if not self.log_file.exists():
            return []

        with self._lock:
            lines = self.log_file.read_text(
                encoding="utf-8"
            ).splitlines()

        events: list[dict[str, Any]] = []

        for line in lines[-limit:]:
            if not line.strip():
                continue

            events.append(json.loads(line))

        return events
