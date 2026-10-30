from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass(frozen=True)
class CognitiveNeuralAssessment:
    """Advisory cognitive-control trace; never an authority grant."""

    version: str
    route: str
    complexity: float
    attention: float
    inhibition_required: bool
    stages: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["stages"] = list(self.stages)
        result["rationale"] = list(self.rationale)
        return result


class CognitiveNeuralArchitecture:
    """Small, deterministic executive layer over SAHIBEX's existing brains.

    This is software inspired by cognitive/neural organization, not a claim
    of biological neurons or general superintelligence. It observes completed
    decisions, suggests a cognitive route, and records the control stages.
    Constitution and permission systems remain the only authority boundaries.
    """

    VERSION = "1.0.0"
    STAGES = (
        "perception",
        "attention_and_context",
        "intent_and_action_understanding",
        "executive_routing",
        "safety_inhibition",
        "verification_review",
        "response_and_learning_signal",
    )
    # Markers are deliberately phrase-oriented and advisory. They affect routing
    # complexity only; they never authorize tools or protected actions.
    _MULTI_STEP_MARKERS = (
        " then ", " after that ", " and also ", " step by step ", " stepwise ",
        "compare", "analyze", "analyse", "plan", "debug", "fix",
        "verify", "research", "design", "implement",
        " uske baad ", " iske baad ", " ek-ek karke ", " step by step ",
        " tulna ", " vishleshan ", " yojana ", " jaanch ", " janch ",
        " sudhar ", " shodh ", " samjhao ", " banao ", " karke batao ",
        " उसके बाद ", " इसके बाद ", " एक-एक करके ", " क्रम से ",
        " तुलना ", " विश्लेषण ", " योजना ", " जाँच ", " जांच ",
        " सुधार ", " शोध ", " समझाओ ", " बनाओ ", " करके बताओ ",
    )
    _PROTECTED_ACTIONS = {
        "delete_file", "run_command", "credential_use", "financial_action",
        "system_change", "network_access", "write_file",
    }

    def assess(
        self,
        *,
        request: str,
        intent: str,
        action: str,
        risk: str,
        verification_status: str,
        confirmation_required: bool,
    ) -> CognitiveNeuralAssessment:
        if not isinstance(request, str):
            raise TypeError("request must be a string")
        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("intent must be a non-empty string")
        if not isinstance(action, str) or not action.strip():
            raise ValueError("action must be a non-empty string")
        if not isinstance(risk, str) or not risk.strip():
            raise ValueError("risk must be a non-empty string")
        if not isinstance(verification_status, str) or not verification_status.strip():
            raise ValueError("verification_status must be a non-empty string")
        if not isinstance(confirmation_required, bool):
            raise TypeError("confirmation_required must be bool")

        # Normalize punctuation as boundaries so bilingual phrases still match
        # when users type natural commas/full stops between clauses.
        # Strip common punctuation explicitly. Avoid a Unicode word-character
        # whitelist here: it can drop Devanagari combining vowel marks (matras).
        normalized_text = re.sub(r"[.,!?;:()\[\]{}]+", " ", request.lower())
        normalized = " " + re.sub(r"\s+", " ", normalized_text).strip() + " "
        words = re.findall(r"\b[\w'-]+\b", normalized)
        marker_count = sum(1 for marker in self._MULTI_STEP_MARKERS if marker in normalized)
        complexity = min(1.0, round(min(len(words), 80) / 80 * 0.65 + min(marker_count, 4) * 0.0875, 4))
        attention = min(1.0, round(0.45 + min(len(words), 60) / 120 + min(marker_count, 3) * 0.08, 4))

        intent_key = intent.strip().lower()
        action_key = action.strip().lower()
        rationale: list[str] = []
        if confirmation_required or action_key in self._PROTECTED_ACTIONS or risk.lower() in {"high", "critical"}:
            route = "protected_action_review"
            rationale.append("Safety inhibition flags the request for existing authority/permission checks.")
        elif intent_key in {"search", "research", "learn"}:
            route = "research_and_evidence"
            rationale.append("Research/learning intent should use source evidence and verification gates.")
        elif intent_key in {"code", "create", "file_operation"} or action_key in {"create", "write_file"}:
            route = "specialist_and_plan"
            rationale.append("Creation or tool-oriented work benefits from planning and specialist review.")
        elif marker_count >= 2 or complexity >= 0.48 or any(x in normalized for x in ("why", "compare", "analyze", "analyse", "debug", "step by step")):
            route = "deliberative_reasoning"
            rationale.append("Request complexity suggests multi-step reasoning before response.")
        else:
            route = "direct_reasoning"
            rationale.append("A bounded request can use the direct reasoning path.")

        if verification_status.upper() not in {"VERIFIED", "STRUCTURALLY_VALID", "DETERMINISTIC_ARITHMETIC"}:
            rationale.append("Result is not marked fully verified; downstream trust must remain conservative.")
        else:
            rationale.append("Record the existing verification outcome without upgrading its authority.")
        rationale.append("This assessment is advisory and cannot grant, widen, or bypass permission.")
        return CognitiveNeuralAssessment(
            version=self.VERSION,
            route=route,
            complexity=complexity,
            attention=attention,
            inhibition_required=(route == "protected_action_review"),
            stages=self.STAGES,
            rationale=tuple(rationale),
        )
