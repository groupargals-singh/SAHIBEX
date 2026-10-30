"""Bounded in-memory event trail for real internal-role dispatches."""
from collections import deque
from threading import Lock
from time import time

_EVENTS = deque(maxlen=200)
_LOCK = Lock()

def record_dispatch(role_id, status, duration_ms=None):
    event = {"timestamp_unix": round(time(), 3), "event": "internal_role_dispatch", "role_id": str(role_id)[:80], "status": str(status)[:48]}
    if duration_ms is not None:
        event["duration_ms"] = round(max(0.0, float(duration_ms)), 2)
    with _LOCK:
        _EVENTS.append(event)

def recent_dispatches(limit=50):
    bounded = min(max(int(limit), 0), 100)
    with _LOCK:
        return list(_EVENTS)[-bounded:] if bounded else []
