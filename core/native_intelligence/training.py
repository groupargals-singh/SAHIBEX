from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class TrainingExample:
    prompt: str
    target: str
    task: str
    metadata: dict[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.prompt.strip() or not self.target.strip() or not self.task.strip():
            raise ValueError("training example requires prompt, target and task")


@dataclass(frozen=True)
class TrainingConfig:
    name: str = "sahibex-native-v1"
    epochs: int = 1
    max_sequence_length: int = 4096
    learning_rate: float = 1e-4
    local_only: bool = True

    def validate(self) -> None:
        if self.epochs < 1 or self.max_sequence_length < 1 or self.learning_rate <= 0:
            raise ValueError("invalid training configuration")


@dataclass
class TrainingDataset:
    examples: list[TrainingExample] = field(default_factory=list)

    def add(self, example: TrainingExample) -> None:
        example.validate()
        self.examples.append(example)

    def validate(self) -> None:
        if not self.examples:
            raise ValueError("training dataset is empty")
        for example in self.examples:
            example.validate()

    def by_task(self, task: str) -> list[TrainingExample]:
        return [x for x in self.examples if x.task == task]

    def tasks(self) -> set[str]:
        return {x.task for x in self.examples}

    def __len__(self) -> int:
        return len(self.examples)
