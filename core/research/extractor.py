from __future__ import annotations

from dataclasses import dataclass
from typing import List

from core.research.models import ResearchDocument


@dataclass(frozen=True)
class ExtractedFinding:
    """
    Deterministic research finding extracted from a document.

    This layer extracts candidate claims only.
    It does NOT declare the claim true or verified.
    """

    claim: str
    evidence_text: str
    confidence: float


class ResearchExtractor:
    """
    Safe, deterministic first-stage research extractor.

    The extractor does not access the network, modify files,
    create knowledge, or mark anything as verified.
    """

    def extract(self, document: ResearchDocument) -> List[ExtractedFinding]:
        if not isinstance(document, ResearchDocument):
            raise TypeError("document must be a ResearchDocument")

        content = document.content.strip()

        if not content:
            return []

        findings: List[ExtractedFinding] = []

        # First implementation deliberately uses complete non-empty
        # sentences as candidate claims. This gives the research core
        # a deterministic extraction boundary without pretending that
        # semantic truth has already been established.
        sentences = self._split_sentences(content)

        for sentence in sentences:
            normalized = sentence.strip()

            if not normalized:
                continue

            findings.append(
                ExtractedFinding(
                    claim=normalized,
                    evidence_text=normalized,
                    confidence=0.50,
                )
            )

        return findings

    @staticmethod
    def _split_sentences(content: str) -> List[str]:
        """
        Split simple prose deterministically.

        This intentionally avoids NLP dependencies in the first version.
        """
        normalized = " ".join(content.split())

        if not normalized:
            return []

        sentences: List[str] = []
        current: List[str] = []

        for character in normalized:
            current.append(character)

            if character in ".!?":
                sentence = "".join(current).strip()

                if sentence:
                    sentences.append(sentence)

                current = []

        remainder = "".join(current).strip()

        if remainder:
            sentences.append(remainder)

        return sentences
