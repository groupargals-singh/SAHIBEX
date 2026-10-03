from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.model_gateway.base import ModelGateway, ModelRequest


@dataclass(frozen=True)
class OperationalModelResult:
    success: bool
    objective: str
    intent: str
    response_text: str
    provider: str
    model: str
    integration_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str")
        if not self.objective.strip():
            raise ValueError("objective must not be empty")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str")
        if not self.intent.strip():
            raise ValueError("intent must not be empty")

        if not isinstance(self.response_text, str):
            raise TypeError("response_text must be str")

        if not isinstance(self.provider, str):
            raise TypeError("provider must be str")
        if not self.provider.strip():
            raise ValueError("provider must not be empty")

        if not isinstance(self.model, str):
            raise TypeError("model must be str")
        if not self.model.strip():
            raise ValueError("model must not be empty")

        if not isinstance(self.integration_id, str):
            raise TypeError("integration_id must be str")
        if not self.integration_id.strip():
            raise ValueError("integration_id must not be empty")


class OperationalModelIntegration:
    """
    Connects the operational brain to the existing ModelGateway.

    This layer:
    - creates ModelRequest objects
    - calls the existing ModelGateway
    - normalizes ModelResponse into an operational result

    This layer does not:
    - grant permissions
    - execute tools
    - execute commands
    - override the constitution
    - perform protected actions
    """

    def __init__(self, gateway: ModelGateway) -> None:
        if not isinstance(gateway, ModelGateway):
            raise TypeError("gateway must be ModelGateway")

        self._gateway = gateway

    def generate(
        self,
        *,
        objective: str,
        intent: str,
        prompt: str,
        provider: str,
    ) -> OperationalModelResult:
        if not isinstance(objective, str):
            raise TypeError("objective must be str")
        if not objective.strip():
            raise ValueError("objective must not be empty")

        if not isinstance(intent, str):
            raise TypeError("intent must be str")
        if not intent.strip():
            raise ValueError("intent must not be empty")

        if not isinstance(prompt, str):
            raise TypeError("prompt must be str")
        if not prompt.strip():
            raise ValueError("prompt must not be empty")

        if not isinstance(provider, str):
            raise TypeError("provider must be str")
        if not provider.strip():
            raise ValueError("provider must not be empty")

        request = ModelRequest(
            prompt=prompt.strip(),
            system_prompt=(
                "You are the reasoning model for SAHIBEX. "
                "Return a useful response to the supplied objective."
            ),
        )

        response = self._gateway.generate(
            request,
            provider=provider.strip(),
        )

        return OperationalModelResult(
            success=response.success,
            objective=objective.strip(),
            intent=intent.strip().lower(),
            response_text=response.text,
            provider=response.provider,
            model=response.model,
        )
