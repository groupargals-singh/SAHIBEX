from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class PromptInjectionStatus(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class PromptInjectionResult:
    status: PromptInjectionStatus
    safe_to_follow: bool
    matched_rules: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return self.status == PromptInjectionStatus.BLOCKED

    @property
    def suspicious(self) -> bool:
        return self.status == PromptInjectionStatus.SUSPICIOUS


class PromptInjectionGuard:
    """
    Runtime guard for detecting instruction-hijacking patterns
    in untrusted content.

    This component:
    - detects prompt-injection indicators,
    - never grants authority,
    - never changes permissions,
    - never executes actions,
    - treats untrusted content as data rather than authority.
    """

    BLOCK_PATTERNS = {
        "ignore_previous_instructions": (
            r"\b(ignore|disregard|forget|override)\b"
            r".{0,80}\b(previous|prior|earlier|system|developer)\b"
            r".{0,80}\b(instruction|instructions|rules|prompt)\b"
        ),
        "reveal_hidden_prompt": (
            r"\b(reveal|show|print|display|output)\b"
            r".{0,80}\b(system prompt|developer prompt|hidden prompt|"
            r"secret instructions)\b"
        ),
        "authority_override": (
            r"\b(you must obey|you are now|new system message|"
            r"system instruction|developer instruction)\b"
        ),
        "safety_bypass": (
            r"\b(disable|bypass|circumvent|remove)\b"
            r".{0,80}\b(safety|security|permission|authorization|"
            r"guard|restriction)\b"
        ),
        "tool_control_hijack": (
            r"\b(run|execute|call|invoke)\b"
            r".{0,80}\b(tool|command|function)\b"
            r".{0,80}\b(without|skip|bypass)\b"
            r".{0,80}\b(permission|approval|confirmation)\b"
        ),
    }

    SUSPICIOUS_PATTERNS = {
        "role_impersonation": (
            r"\b(system|developer|assistant)\s*:\s*"
        ),
        "instruction_delimiter": (
            r"\b(begin|end)\s+(system|developer)\s+instructions?\b"
        ),
        "secret_request": (
            r"\b(secret|confidential|hidden)\b"
            r".{0,60}\b(prompt|instruction|policy|rule)\b"
        ),
    }

    def inspect(
        self,
        content: str,
        *,
        source: str = "untrusted",
    ) -> PromptInjectionResult:
        if not isinstance(content, str):
            raise TypeError("content must be str.")

        if not isinstance(source, str):
            raise TypeError("source must be str.")

        normalized = content.strip().lower()

        if not normalized:
            return PromptInjectionResult(
                status=PromptInjectionStatus.SAFE,
                safe_to_follow=True,
            )

        blocked_rules = self._match(
            normalized,
            self.BLOCK_PATTERNS,
        )

        if blocked_rules:
            return PromptInjectionResult(
                status=PromptInjectionStatus.BLOCKED,
                safe_to_follow=False,
                matched_rules=blocked_rules,
            )

        suspicious_rules = self._match(
            normalized,
            self.SUSPICIOUS_PATTERNS,
        )

        if suspicious_rules:
            return PromptInjectionResult(
                status=PromptInjectionStatus.SUSPICIOUS,
                safe_to_follow=False,
                matched_rules=suspicious_rules,
            )

        return PromptInjectionResult(
            status=PromptInjectionStatus.SAFE,
            safe_to_follow=True,
        )

    @staticmethod
    def _match(
        content: str,
        patterns: dict[str, str],
    ) -> tuple[str, ...]:
        matches: list[str] = []

        for name, pattern in patterns.items():
            if re.search(
                pattern,
                content,
                flags=re.IGNORECASE | re.DOTALL,
            ):
                matches.append(name)

        return tuple(matches)
