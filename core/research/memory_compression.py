from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


MEMORY_COMPRESSION_VERSION = "P2-MCOMP-1"


@dataclass(frozen=True)
class MemoryCompressionInput:
    memory_id: str
    content: str
    importance: float = 0.5
    preserve_exact_source: bool = True
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.memory_id, str) or not self.memory_id.strip():
            raise ValueError("memory_id must not be empty.")

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content must not be empty.")

        if not 0.0 <= float(self.importance) <= 1.0:
            raise ValueError("importance must be between 0 and 1.")

        if not isinstance(self.preserve_exact_source, bool):
            raise TypeError("preserve_exact_source must be bool.")


@dataclass(frozen=True)
class MemoryCompressionResult:
    memory_id: str
    original_content: str
    compressed_content: str
    original_length: int
    compressed_length: int
    compression_ratio: float
    information_preserved: bool
    exact_source_preserved: bool
    action: str
    reason: str
    input_id: str

    result_id: str = field(default_factory=lambda: str(uuid4()))


class MemoryCompressionEngine:
    """
    SAHIBEX Memory Compression Engine.

    Produces a non-destructive compression proposal.

    The engine never:
    - deletes memory
    - overwrites original memory
    - removes provenance
    - removes exact source when preservation is requested
    - executes actions
    - grants authority
    - modifies the Constitution
    """

    VERSION = MEMORY_COMPRESSION_VERSION

    def compress(
        self,
        compression_input: MemoryCompressionInput,
    ) -> MemoryCompressionResult:
        if not isinstance(
            compression_input,
            MemoryCompressionInput,
        ):
            raise TypeError(
                "compression_input must be "
                "MemoryCompressionInput."
            )

        original = compression_input.content

        # Safe deterministic whitespace normalization.
        compressed = " ".join(original.split())

        changed = compressed != original

        if (
            compression_input.preserve_exact_source
            and changed
        ):
            action = "PROPOSAL_ONLY"
            reason = (
                "Compact representation proposed while "
                "preserving the exact original source."
            )
            exact_source_preserved = True
        elif changed:
            action = "PROPOSAL_ONLY"
            reason = (
                "Compact representation proposed without "
                "destructive modification of the original memory."
            )
            exact_source_preserved = False
        else:
            action = "NO_CHANGE"
            reason = (
                "Memory is already compact under the "
                "deterministic compression rule."
            )
            exact_source_preserved = (
                compression_input.preserve_exact_source
            )

        original_length = len(original)
        compressed_length = len(compressed)

        ratio = (
            compressed_length / original_length
            if original_length
            else 1.0
        )

        return MemoryCompressionResult(
            memory_id=compression_input.memory_id,
            original_content=original,
            compressed_content=compressed,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=round(ratio, 6),
            information_preserved=True,
            exact_source_preserved=exact_source_preserved,
            action=action,
            reason=reason,
            input_id=compression_input.input_id,
        )
