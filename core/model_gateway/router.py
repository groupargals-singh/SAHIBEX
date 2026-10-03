from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model_gateway.base import (
    ModelGateway,
    ModelRequest,
    ModelResponse,
)


@dataclass(frozen=True)
class RoutingDecision:
    provider: str
    reason: str
    metadata: dict[str, Any]


class ModelRouter:
    """
    Selects an AI provider for a model request.

    The router only selects a provider.
    It does not bypass permissions, execute tools,
    access credentials, or perform system actions.
    """

    def __init__(
        self,
        gateway: ModelGateway,
        *,
        default_provider: str = "mock",
    ) -> None:
        self.gateway = gateway
        self.default_provider = default_provider

    def decide(
        self,
        request: ModelRequest,
        *,
        preferred_provider: str | None = None,
    ) -> RoutingDecision:
        requested = (
            preferred_provider.strip()
            if preferred_provider
            else ""
        )

        if requested:
            if requested not in self.gateway.providers():
                raise KeyError(
                    f"Unknown model provider: {requested}"
                )

            return RoutingDecision(
                provider=requested,
                reason="User/application explicitly selected provider.",
                metadata={
                    "selection": "explicit",
                },
            )

        if self.default_provider not in self.gateway.providers():
            raise RuntimeError(
                f"Default provider is not registered: "
                f"{self.default_provider}"
            )

        return RoutingDecision(
            provider=self.default_provider,
            reason="Default registered provider selected.",
            metadata={
                "selection": "default",
            },
        )

    def generate(
        self,
        request: ModelRequest,
        *,
        preferred_provider: str | None = None,
    ) -> ModelResponse:
        decision = self.decide(
            request,
            preferred_provider=preferred_provider,
        )

        response = self.gateway.generate(
            request,
            provider=decision.provider,
        )

        return response
