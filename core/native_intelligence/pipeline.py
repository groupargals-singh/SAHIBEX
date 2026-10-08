from __future__ import annotations

from dataclasses import dataclass

from .evaluation import EvaluationResult, EvaluationSuite
from .tokenizer import SahibexTokenizer
from .training import TrainingConfig, TrainingDataset


@dataclass
class NativeIntelligencePipeline:
    tokenizer: SahibexTokenizer
    config: TrainingConfig
    dataset: TrainingDataset

    def validate(self) -> None:
        self.config.validate()
        self.dataset.validate()
        if not self.tokenizer.tokenize("SAHIBEX native intelligence"):
            raise ValueError("tokenizer is not operational")

    def dataset_evaluation(self) -> EvaluationResult:
        self.validate()
        return EvaluationSuite().run_dataset_contract(self.dataset.tasks())
