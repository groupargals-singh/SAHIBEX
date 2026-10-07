from __future__ import annotations
from dataclasses import dataclass
from core.model_gateway.base import ModelResponse

@dataclass(frozen=True)
class ModelVerificationResult:
    valid: bool
    provider: str
    model: str
    reasons: tuple[str, ...]

class ModelResponseVerifier:
    """Structural post-response verification; never treats output as permission."""
    def verify(self, response: ModelResponse) -> ModelVerificationResult:
        reasons=[]
        if not response.provider.strip(): reasons.append("missing provider")
        if not response.model.strip(): reasons.append("missing model")
        if response.success and not response.text.strip(): reasons.append("successful response has empty text")
        return ModelVerificationResult(not reasons, response.provider, response.model, tuple(reasons))
