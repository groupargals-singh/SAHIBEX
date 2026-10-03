from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ComputerAction(str, Enum):
    MOVE_MOUSE = "move_mouse"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True)
class ComputerControlRequest:
    action: ComputerAction
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(
            self.action,
            ComputerAction,
        ):
            raise TypeError(
                "action must be ComputerAction"
            )

        if not isinstance(
            self.parameters,
            dict,
        ):
            raise TypeError(
                "parameters must be a dictionary"
            )


@dataclass(frozen=True)
class ComputerControlResult:
    action: ComputerAction
    success: bool
    result: Any
    error: str | None


class ComputerControlProvider:
    """
    Safe computer-control abstraction.

    This milestone defines the interface only.

    It does NOT:
    - move the mouse
    - click
    - type text
    - press keys
    - capture the screen
    - access the operating system

    Actual computer control will be connected only
    through later permission and approval layers.
    """

    def execute(
        self,
        request: ComputerControlRequest,
    ) -> ComputerControlResult:

        if not isinstance(
            request,
            ComputerControlRequest,
        ):
            raise TypeError(
                "request must be ComputerControlRequest"
            )

        return ComputerControlResult(
            action=request.action,
            success=False,
            result=None,
            error=(
                "Computer control provider is not "
                "connected."
            ),
        )
