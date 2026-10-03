from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.multimodal import (
    InputModality,
    MultimodalInput,
)
from core.brain.operational_brain import OperationalBrain
from core.brain.operational_end_to_end import (
    OperationalEndToEndBrain,
)
from core.brain.operational_memory_knowledge import (
    OperationalMemoryKnowledgeIntegration,
)
from core.brain.operational_model import (
    OperationalModelIntegration,
)
from core.brain.operational_multimodal import (
    OperationalMultimodalIntegration,
)
from core.brain.operational_reasoning import (
    OperationalReasoningEngine,
)
from core.brain.operational_verification import (
    OperationalVerificationRecovery,
)
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider
from core.research.storage import ResearchStorage


def build_brain():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())

    model = OperationalModelIntegration(gateway)

    reasoning = OperationalReasoningEngine(
        model_integration=model,
    )

    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(
            Path(temp_dir) / "sahibex_e2e.db"
        )

        memory_knowledge = OperationalMemoryKnowledgeIntegration(
            storage
        )

        verification = OperationalVerificationRecovery()

        multimodal = OperationalMultimodalIntegration(
            reasoning_engine=reasoning,
        )

        brain = OperationalEndToEndBrain(
            operational_brain=OperationalBrain(),
            memory_knowledge=memory_knowledge,
            reasoning_engine=reasoning,
            verification=verification,
            multimodal=multimodal,
        )

        yield brain


def main() -> None:
    for brain in build_brain():
        result = brain.process(
            objective="Explain how SAHIBEX operational reasoning works.",
            intent="explain",
            provider="mock",
        )

        assert result.success is True
        assert result.status == "COMPLETED"
        assert result.intent == "explain"
        assert result.brain.success is True
        assert result.retrieval.success is True
        assert result.reasoning is not None
        assert result.reasoning.success is True
        assert result.verification.success is True
        assert result.verification.verified is True
        assert result.verification.verification_status == "VERIFIED"
        assert result.final_response
        assert "MOCK MODEL RESPONSE" in result.final_response

        multimodal_result = brain.process(
            objective="Analyze this multimodal SAHIBEX context.",
            intent="explain",
            provider="mock",
            inputs=[
                MultimodalInput(
                    modality=InputModality.TEXT,
                    content="The system should verify its reasoning.",
                ),
                MultimodalInput(
                    modality=InputModality.IMAGE,
                    content="A diagram showing the verification pipeline.",
                ),
            ],
        )

        assert multimodal_result.success is True
        assert multimodal_result.status == "COMPLETED"
        assert multimodal_result.multimodal is not None
        assert multimodal_result.multimodal.success is True
        assert multimodal_result.reasoning is not None
        assert multimodal_result.verification.verified is True
        assert multimodal_result.final_response

        try:
            brain.process(
                objective="",
                intent="explain",
                provider="mock",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty objective must raise ValueError."
            )

        try:
            brain.process(
                objective="Valid objective",
                intent="",
                provider="mock",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty intent must raise ValueError."
            )

        try:
            brain.process(
                objective="Valid objective",
                intent="explain",
                provider="",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty provider must raise ValueError."
            )

        try:
            brain.process(
                objective="Valid objective",
                intent="explain",
                provider="mock",
                inputs=["not-a-multimodal-input"],
            )
        except TypeError:
            pass
        else:
            raise AssertionError(
                "Invalid multimodal input must raise TypeError."
            )

        forbidden_methods = (
            "execute_shell",
            "grant_permission",
            "modify_constitution",
            "execute_protected_action",
            "access_credentials",
        )

        for method_name in forbidden_methods:
            assert not hasattr(brain, method_name)

    print(
        "SAHIBEX 6O-10 END-TO-END OPERATIONAL BRAIN TEST: PASS"
    )


if __name__ == "__main__":
    main()
