from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_SPECIAL_TOKENS = ("<pad>", "<unk>", "<bos>", "<eos>")
_TOKEN_PATTERN = re.compile(
    r"<[^>\s]+>|[A-Za-z0-9_]+|[\u0900-\u097F]+|[^\s]",
    flags=re.UNICODE,
)


@dataclass(frozen=True)
class SahibexTokenizer:
    """Deterministic multilingual tokenizer with an explicit, serializable vocabulary.

    This is a lightweight SAHIBEX-owned tokenizer for dataset tooling, not a
    replacement for the subword tokenizer shipped with a production LLM.
    """

    vocab: tuple[str, ...] = _SPECIAL_TOKENS

    def __post_init__(self) -> None:
        if not isinstance(self.vocab, tuple):
            raise TypeError("vocab must be a tuple of tokens")
        if len(set(self.vocab)) != len(self.vocab):
            raise ValueError("vocab tokens must be unique")
        if self.vocab[:len(_SPECIAL_TOKENS)] != _SPECIAL_TOKENS:
            raise ValueError("vocabulary must start with the four special tokens")
        if any(not isinstance(token, str) or not token for token in self.vocab):
            raise ValueError("vocabulary tokens must be non-empty strings")

    def tokenize(self, text: str) -> list[str]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return _TOKEN_PATTERN.findall(text.strip()) if text.strip() else []

    @classmethod
    def from_corpus(cls, texts: Iterable[str]) -> "SahibexTokenizer":
        """Build a deterministic vocabulary from trusted local training text."""
        learned: set[str] = set()
        for text in texts:
            if not isinstance(text, str):
                raise TypeError("corpus entries must be strings")
            learned.update(cls().tokenize(text))
        learned.difference_update(_SPECIAL_TOKENS)
        return cls(_SPECIAL_TOKENS + tuple(sorted(learned)))

    def encode(self, text: str) -> list[int]:
        tokens = self.tokenize(text)
        table = {token: i for i, token in enumerate(self.vocab)}
        unknown_id = table["<unk>"]
        return [table.get(token, unknown_id) for token in tokens]

    def decode(self, ids: list[int]) -> str:
        if not isinstance(ids, list):
            raise TypeError("ids must be a list")
        if any(not isinstance(token_id, int) for token_id in ids):
            raise TypeError("token IDs must be integers")
        tokens = [
            self.vocab[token_id] if 0 <= token_id < len(self.vocab) else "<unk>"
            for token_id in ids
        ]
        # Whitespace is not currently encoded; joining is explicit and stable.
        return " ".join(tokens)
