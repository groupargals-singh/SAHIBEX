from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

from core.brain.brain_registry import BrainRegistry
from core.brain.intelligence import BrainIntelligence
from core.brain.specialist_brain import BrainCapability, BrainStatus


SpecialistHandler = Callable[[str, dict[str, Any]], Any]


@dataclass(frozen=True)
class SpecialistDispatchResult:
    success: bool
    brain_id: str | None
    request: str
    result: Any
    error: str | None
    dispatch_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if self.brain_id is not None:
            if not isinstance(self.brain_id, str):
                raise TypeError("brain_id must be a string when provided.")
            if not self.brain_id.strip():
                raise ValueError("brain_id must not be empty when provided.")

        if not isinstance(self.request, str):
            raise TypeError("request must be a string.")
        if not self.request.strip():
            raise ValueError("request must be a non-empty string.")

        if self.success and self.error is not None:
            raise ValueError("successful dispatch cannot contain an error.")

        if not self.success and self.error is None:
            raise ValueError("failed dispatch must contain an error.")

        if not isinstance(self.dispatch_id, str) or not self.dispatch_id.strip():
            raise ValueError("dispatch_id must be a non-empty string.")


class OperationalSpecialistDispatcher:
    """Runtime dispatch boundary for registered specialist brain handlers.

    Selection remains the responsibility of BrainIntelligence.
    SpecialistBrain remains the identity/lifecycle contract.
    This layer only connects selected brains to explicitly registered
    runtime handlers.

    It does not grant permissions, execute protected actions directly,
    modify the constitution, or bypass the existing safety pipeline.
    """

    def __init__(
        self,
        registry: BrainRegistry,
        intelligence: BrainIntelligence | None = None,
    ) -> None:
        if not isinstance(registry, BrainRegistry):
            raise TypeError("registry must be a BrainRegistry.")

        if intelligence is not None and not isinstance(
            intelligence,
            BrainIntelligence,
        ):
            raise TypeError(
                "intelligence must be a BrainIntelligence when provided."
            )

        self.registry = registry
        self.intelligence = intelligence or BrainIntelligence(registry)
        self._handlers: dict[str, SpecialistHandler] = {}

    def register_handler(
        self,
        brain_id: str,
        handler: SpecialistHandler,
    ) -> None:
        if not isinstance(brain_id, str):
            raise TypeError("brain_id must be a string.")

        normalized_id = brain_id.strip()

        if not normalized_id:
            raise ValueError("brain_id cannot be empty.")

        if not callable(handler):
            raise TypeError("handler must be callable.")

        brain = self.registry.get(normalized_id)

        if brain is None:
            raise ValueError(
                f"Cannot register handler for unknown brain: {normalized_id}"
            )

        if normalized_id in self._handlers:
            raise ValueError(
                f"Handler already registered for brain: {normalized_id}"
            )

        self._handlers[normalized_id] = handler

    def unregister_handler(self, brain_id: str) -> bool:
        if not isinstance(brain_id, str):
            raise TypeError("brain_id must be a string.")

        return self._handlers.pop(brain_id.strip(), None) is not None

    def has_handler(self, brain_id: str) -> bool:
        if not isinstance(brain_id, str):
            raise TypeError("brain_id must be a string.")

        return brain_id.strip() in self._handlers

    def dispatch(
        self,
        *,
        request: str,
        specialization: str | None = None,
        capability: BrainCapability | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SpecialistDispatchResult:
        if not isinstance(request, str):
            raise TypeError("request must be a string.")

        normalized_request = request.strip()

        if not normalized_request:
            raise ValueError("request must be a non-empty string.")

        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary when provided.")

        selection = self.intelligence.select_brain(
            specialization=specialization,
            capability=capability,
        )

        if selection.selected_brain_id is None:
            return SpecialistDispatchResult(
                success=False,
                brain_id=None,
                request=normalized_request,
                result=None,
                error=selection.reason,
            )

        brain_id = selection.selected_brain_id
        brain = self.registry.get(brain_id)

        if brain is None:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=normalized_request,
                result=None,
                error="Selected specialist brain is no longer registered.",
            )

        handler = self._handlers.get(brain_id)

        if handler is None:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=normalized_request,
                result=None,
                error="Selected specialist brain has no registered runtime handler.",
            )

        if brain.status not in {BrainStatus.READY, BrainStatus.ACTIVE}:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=normalized_request,
                result=None,
                error=(
                    "Selected specialist brain is not READY/ACTIVE: "
                    f"{brain.status.value}."
                ),
            )

        if not brain.can_accept_work():
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=normalized_request,
                result=None,
                error="Selected specialist brain cannot accept more work.",
            )

        started_from_ready = brain.status == BrainStatus.READY
        if started_from_ready:
            brain.transition_to(BrainStatus.ACTIVE)
        brain.update_load(
            active_tasks=brain.resource_state.active_tasks + 1
        )

        try:
            handler_metadata = dict(metadata or {})
            handler_metadata["brain_id"] = brain_id
            handler_metadata["specialization"] = brain.specialization

            handler_result = handler(
                normalized_request,
                handler_metadata,
            )

            return SpecialistDispatchResult(
                success=True,
                brain_id=brain_id,
                request=normalized_request,
                result=handler_result,
                error=None,
            )

        except Exception as exc:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=normalized_request,
                result=None,
                error=f"Specialist handler failed: {exc}",
            )

        finally:
            brain.update_load(
                active_tasks=brain.resource_state.active_tasks - 1
            )

            if started_from_ready:
                brain.transition_to(BrainStatus.READY)
