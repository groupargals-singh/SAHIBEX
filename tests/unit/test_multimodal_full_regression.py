from __future__ import annotations

import importlib


TEST_MODULES = [
    "tests.unit.test_file_input_unified_pipeline",
    "tests.unit.test_multimodal_input_contract",
    "tests.unit.test_voice_input_contract",
    "tests.unit.test_voice_output_contract",
    "tests.unit.test_vision_input_contract",
    "tests.unit.test_multimodal_context_contract",
    "tests.unit.test_speech_text_integration_contract",
    "tests.unit.test_vision_reasoning_integration_contract",
    "tests.unit.test_multimodal_memory_integration_contract",
    "tests.unit.test_multimodal_permission_safety_contract",
    "tests.unit.test_multimodal_intelligence_contract",
]


def main() -> None:
    for module_name in TEST_MODULES:
        module = importlib.import_module(module_name)

        test_main = getattr(
            module,
            "main",
            None,
        )

        if test_main is None:
            raise AssertionError(
                f"Test module has no main(): {module_name}"
            )

        test_main()

    print(
        "SAHIBEX 6M-11 FULL MULTIMODAL REGRESSION: PASS"
    )


if __name__ == "__main__":
    main()
