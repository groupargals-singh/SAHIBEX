from __future__ import annotations

from core.model_gateway.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
)


class MockModelProvider(ModelProvider):
    """
    Deterministic provider used for testing the model gateway.

    It does not access the internet, files, shell, credentials,
    or any external service.
    """

    name = "mock"

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not request.prompt.strip():
            return ModelResponse(
                text="",
                provider=self.name,
                model="mock-v1",
                success=False,
                error="Prompt cannot be empty.",
            )

        response = (
            "MOCK MODEL RESPONSE: "
            f"Received request: {request.prompt.strip()}"
        )

        return ModelResponse(
            text=response,
            provider=self.name,
            model=request.model or "mock-v1",
            success=True,
            metadata={
                "temperature": request.temperature,
                "test_mode": True,
            },
        )
