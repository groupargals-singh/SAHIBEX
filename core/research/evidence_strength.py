from __future__ import annotations

from dataclasses import dataclass

from core.research.models import (
    Evidence,
    ResearchFinding,
    ResearchSource,
)


EVIDENCE_STRENGTH_VERSION = "6G-3"

DIRECTNESS_WEIGHT = 0.25
SPECIFICITY_WEIGHT = 0.20
FINDING_LINKAGE_WEIGHT = 0.20
SOURCE_LINKAGE_WEIGHT = 0.15
EXTRACTION_CONFIDENCE_WEIGHT = 0.20


@dataclass(frozen=True)
class EvidenceStrengthAssessment:
    """
    Transparent evidence-strength assessment.

    This score measures evidence characteristics only.
    It is not a truth score and does not replace:
        - source reliability
        - source quality
        - verification
        - conflict resolution
    """

    evidence_id: str
    strength_score: float
    directness_score: float
    specificity_score: float
    finding_linkage_score: float
    source_linkage_score: float
    extraction_confidence_score: float
    version: str = EVIDENCE_STRENGTH_VERSION

    def __post_init__(self) -> None:
        values = (
            self.strength_score,
            self.directness_score,
            self.specificity_score,
            self.finding_linkage_score,
            self.source_linkage_score,
            self.extraction_confidence_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "evidence strength scores must be between 0 and 1"
                )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _text_present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _directness_score(
    evidence: Evidence,
    finding: ResearchFinding,
) -> float:
    """
    Estimate how directly the evidence text relates to the finding claim.

    This is intentionally conservative and deterministic.
    It does not attempt to determine whether the claim is true.
    """
    evidence_text = evidence.evidence_text.strip().lower()
    claim = finding.claim.strip().lower()

    if not evidence_text or not claim:
        return 0.0

    if evidence_text == claim:
        return 1.0

    claim_tokens = {
        token
        for token in claim.split()
        if token
    }

    evidence_tokens = {
        token
        for token in evidence_text.split()
        if token
    }

    if not claim_tokens:
        return 0.0

    overlap = len(claim_tokens & evidence_tokens)
    ratio = overlap / len(claim_tokens)

    return _clamp(ratio)


def _specificity_score(
    evidence: Evidence,
) -> float:
    """
    Estimate evidence specificity from the evidence text.

    Longer, information-bearing evidence receives a higher score,
    while empty or extremely short evidence receives a lower score.

    This is a structural characteristic, not a truth judgement.
    """
    text = evidence.evidence_text.strip()

    if not text:
        return 0.0

    length = len(text)

    if length < 20:
        return 0.20

    if length < 50:
        return 0.40

    if length < 100:
        return 0.60

    if length < 200:
        return 0.80

    return 1.0


def _finding_linkage_score(
    evidence: Evidence,
    finding: ResearchFinding,
) -> float:
    """
    Confirm that the evidence explicitly belongs to the finding.
    """
    if evidence.finding_id == finding.finding_id:
        return 1.0

    return 0.0


def _source_linkage_score(
    evidence: Evidence,
    source: ResearchSource,
) -> float:
    """
    Confirm that the evidence explicitly belongs to the source.
    """
    if evidence.source_id == source.source_id:
        return 1.0

    return 0.0


def _extraction_confidence_score(
    finding: ResearchFinding,
) -> float:
    """
    Reuse the finding's extraction confidence as an input signal.

    This does not replace evidence strength; it is only one component.
    """
    return _clamp(finding.confidence)


def assess_evidence_strength(
    *,
    evidence: Evidence,
    finding: ResearchFinding,
    source: ResearchSource,
) -> EvidenceStrengthAssessment:
    """
    Calculate the canonical 6G-3 evidence-strength assessment.
    """
    if not isinstance(evidence, Evidence):
        raise TypeError(
            "evidence must be an Evidence"
        )

    if not isinstance(finding, ResearchFinding):
        raise TypeError(
            "finding must be a ResearchFinding"
        )

    if not isinstance(source, ResearchSource):
        raise TypeError(
            "source must be a ResearchSource"
        )

    directness = _directness_score(
        evidence,
        finding,
    )

    specificity = _specificity_score(
        evidence,
    )

    finding_linkage = _finding_linkage_score(
        evidence,
        finding,
    )

    source_linkage = _source_linkage_score(
        evidence,
        source,
    )

    extraction_confidence = _extraction_confidence_score(
        finding,
    )

    strength = (
        directness * DIRECTNESS_WEIGHT
        + specificity * SPECIFICITY_WEIGHT
        + finding_linkage * FINDING_LINKAGE_WEIGHT
        + source_linkage * SOURCE_LINKAGE_WEIGHT
        + extraction_confidence
        * EXTRACTION_CONFIDENCE_WEIGHT
    )

    return EvidenceStrengthAssessment(
        evidence_id=evidence.evidence_id,
        strength_score=round(strength, 4),
        directness_score=round(directness, 4),
        specificity_score=round(specificity, 4),
        finding_linkage_score=round(
            finding_linkage,
            4,
        ),
        source_linkage_score=round(
            source_linkage,
            4,
        ),
        extraction_confidence_score=round(
            extraction_confidence,
            4,
        ),
    )
