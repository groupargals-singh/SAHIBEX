from core.native_intelligence import (
    EvaluationSuite, LocalDeploymentContract, NativeIntelligencePipeline,
    SahibexTokenizer, TrainingConfig, TrainingDataset, TrainingExample,
)


def build_dataset() -> TrainingDataset:
    dataset = TrainingDataset()
    for task in ("reasoning", "tool_use", "memory_use", "verification"):
        dataset.add(TrainingExample(
            prompt=f"SAHIBEX {task} task",
            target=f"verified {task} result",
            task=task,
        ))
    return dataset


def test_phase_14_native_intelligence_contract() -> None:
    tokenizer = SahibexTokenizer()
    assert tokenizer.tokenize("SAHIBEX can think.")[:2] == ["SAHIBEX", "can"]
    assert tokenizer.encode("unknown-token")
    assert tokenizer.decode([0, 1]).startswith("<pad>")

    dataset = build_dataset()
    config = TrainingConfig()
    pipeline = NativeIntelligencePipeline(tokenizer, config, dataset)
    pipeline.validate()
    result = pipeline.dataset_evaluation()
    result.require_pass()
    assert result.score == 1.0

    deployment = LocalDeploymentContract(
        endpoint="http://127.0.0.1:8080/v1/chat/completions",
        model="Qwen3-1.7B-Q4_K_M.gguf",
    )
    deployment.validate()

    suite = EvaluationSuite()
    suite.add_check("reasoning", lambda: True)
    suite.add_check("tool_use", lambda: True)
    suite.add_check("memory_use", lambda: True)
    suite.add_check("verification", lambda: True)
    final = suite.run()
    final.require_pass()
    assert final.score == 1.0
