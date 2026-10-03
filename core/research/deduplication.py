from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class DeduplicationResult:
    document_id: str
    is_duplicate: bool
    matched_document_id: Optional[str]
    content_hash: str
    normalized_hash: str


class DocumentDeduplicator:
    """
    Detects duplicate research documents.

    Two fingerprints are maintained:

    1. Exact content hash
       - Detects byte-for-byte equivalent text.

    2. Normalized content hash
       - Detects harmless formatting differences such as
         repeated whitespace or leading/trailing spaces.
    """

    def __init__(self) -> None:
        self._exact_index: Dict[str, str] = {}
        self._normalized_index: Dict[str, str] = {}

    @staticmethod
    def _validate_content(content: str) -> str:
        if not isinstance(content, str):
            raise TypeError("content must be a string")

        if not content.strip():
            raise ValueError("content cannot be empty")

        return content

    @staticmethod
    def exact_hash(content: str) -> str:
        content = DocumentDeduplicator._validate_content(content)

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def normalize(content: str) -> str:
        content = DocumentDeduplicator._validate_content(content)

        normalized = content.strip().lower()

        # Collapse all whitespace into a single space.
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    @classmethod
    def normalized_hash(cls, content: str) -> str:
        normalized = cls.normalize(content)

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

    def check(
        self,
        document_id: str,
        content: str,
    ) -> DeduplicationResult:
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("document_id cannot be empty")

        content = self._validate_content(content)

        exact = self.exact_hash(content)
        normalized = self.normalized_hash(content)

        matched_id = self._exact_index.get(exact)

        if matched_id is None:
            matched_id = self._normalized_index.get(normalized)

        is_duplicate = matched_id is not None

        return DeduplicationResult(
            document_id=document_id,
            is_duplicate=is_duplicate,
            matched_document_id=matched_id,
            content_hash=exact,
            normalized_hash=normalized,
        )

    def register(
        self,
        document_id: str,
        content: str,
    ) -> DeduplicationResult:
        result = self.check(document_id, content)

        if result.is_duplicate:
            return result

        self._exact_index[result.content_hash] = document_id
        self._normalized_index[result.normalized_hash] = document_id

        return result

    def contains(self, content: str) -> bool:
        content = self._validate_content(content)

        exact = self.exact_hash(content)
        normalized = self.normalized_hash(content)

        return (
            exact in self._exact_index
            or normalized in self._normalized_index
        )

    def find_document(
        self,
        content: str,
    ) -> Optional[str]:
        content = self._validate_content(content)

        exact = self.exact_hash(content)

        document_id = self._exact_index.get(exact)

        if document_id is not None:
            return document_id

        normalized = self.normalized_hash(content)

        return self._normalized_index.get(normalized)

    def count(self) -> int:
        return len(self._exact_index)

    def summary(self) -> dict:
        return {
            "registered_documents": self.count(),
            "exact_hashes": len(self._exact_index),
            "normalized_hashes": len(self._normalized_index),
        }

    def clear(self) -> None:
        self._exact_index.clear()
        self._normalized_index.clear()
