from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.model_gateway.base import ModelGateway, ModelRequest
from core.brain.universal_language_brain import UniversalLanguageBrain


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

    @property
    def gateway(self) -> ModelGateway:
        """Expose the configured gateway for other advisory model services."""
        return self._gateway

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

        language_brain = UniversalLanguageBrain()
        language_instruction = language_brain.reply_instruction(objective)
        request = ModelRequest(
            prompt=prompt.strip(),
            system_prompt=(
                "You are SAHIBEX, a female-presenting AI assistant with a consistent feminine persona, and a concise, accurate conversational reasoning engine. "
                "In Hindi, use grammatically feminine first-person forms for yourself, for example 'main kar sakti hoon', 'main bataungi', 'main jaanch karungi'; avoid masculine self-reference such as 'kar sakta hoon' or 'karunga'. "
                "In Romanized Hindi/Hinglish, preserve the same feminine grammar (sakti hoon, bataungi, karungi) while matching the user's script and register. "
                "In English, identify as SAHIBEX and maintain a warm, clear, confident female-presenting assistant persona without gender stereotypes. "
                + language_instruction + " "
                "Do not merely rephrase the question, repeat phrases, or produce vague filler. "
                "You can converse in Hindi, Romanized Hindi/Hinglish, and English; do not falsely claim that Hindi support is unavailable. "
                "For Romanized Hindi/Hinglish, reply naturally in the same style unless the user asks for Devanagari Hindi. "
                "For requests to improve/build SAHIBEX, explain concrete next steps and clearly distinguish completed work from planned work; never claim a file was changed unless a tool confirms it. "
                "For factual questions, give the specific fact first, then a brief clarification if needed. "
                "If unsure, say so rather than inventing facts. Usually answer in 1-3 sentences."
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
