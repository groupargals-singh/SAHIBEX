from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BrainResourceState:
    """
    Resource/load state for one specialist brain.

    This contract tracks workload only.
    It does not grant permissions or execute tasks.
    """

    active_tasks: int = 0
    max_concurrent_tasks: int = 4

    def __post_init__(self) -> None:
        if not isinstance(self.active_tasks, int):
            raise TypeError(
                "active_tasks must be an integer."
            )

        if not isinstance(
            self.max_concurrent_tasks,
            int,
        ):
            raise TypeError(
                "max_concurrent_tasks must be an integer."
            )

        if self.active_tasks < 0:
            raise ValueError(
                "active_tasks cannot be negative."
            )

        if self.max_concurrent_tasks <= 0:
            raise ValueError(
                "max_concurrent_tasks must be positive."
            )

        if self.active_tasks > self.max_concurrent_tasks:
            raise ValueError(
                "active_tasks cannot exceed max_concurrent_tasks."
            )
