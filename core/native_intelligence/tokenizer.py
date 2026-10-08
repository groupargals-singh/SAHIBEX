from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SahibexTokenizer:
    """Deterministic, dependency-free tokenizer owned by SAHIBEX."""

    vocab: tuple[str, ...] = ("<pad>", "<unk>", "<bos>", "<eos>")

    def tokenize(self, text: str) -> list[str]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        text = text.strip()
        if not text:
            return []
        return re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text, flags=re.UNICODE)

    def encode(self, text: str) -> list[int]:
        tokens = self.tokenize(text)
        table = {token: i for i, token in enumerate(self.vocab)}
        return [table.get(token, table["<unk>"]) for token in tokens]

    def decode(self, ids: list[int]) -> str:
        if not isinstance(ids, list):
            raise TypeError("ids must be a list")
        return " ".join(self.vocab[i] if 0 <= i < len(self.vocab) else "<unk>" for i in ids)
