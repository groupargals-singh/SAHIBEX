from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import re
from typing import Any

@dataclass(frozen=True)
class BrainPerspective:
    brain: str
    role: str
    finding: str
    recommendation: str
    confidence: float
    needs_external_evidence: bool
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ThreeBrainResult:
    version: str
    mode: str
    perspectives: tuple[BrainPerspective, ...]
    consensus: str
    disagreement: bool
    suggestions: tuple[str, ...]
    limitations: tuple[str, ...]
    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "mode": self.mode, "perspectives": [p.to_dict() for p in self.perspectives], "consensus": self.consensus, "disagreement": self.disagreement, "suggestions": list(self.suggestions), "limitations": list(self.limitations)}

class ThreeBrainCouncil:
    """Three parallel advisory perspectives; no tool or permission authority."""
    VERSION = "1.0.0"
    MAX_REQUEST_CHARS = 12000

    def deliberate(self, *, request: str, answer: str, intent: str, risk: str, verification_status: str) -> ThreeBrainResult:
        for name, value in (("request", request), ("answer", answer), ("intent", intent), ("risk", risk), ("verification_status", verification_status)):
            if not isinstance(value, str): raise TypeError(f"{name} must be a string")
        if not request.strip(): raise ValueError("request must not be empty")
        if not intent.strip() or not risk.strip() or not verification_status.strip(): raise ValueError("intent, risk, and verification_status must not be empty")
        request = request[:self.MAX_REQUEST_CHARS]
        answer = answer[:self.MAX_REQUEST_CHARS]
        normalized = " ".join(request.casefold().split())
        answer_tokens = set(re.findall(r"[\w]+", answer.casefold()))
        question_tokens = set(re.findall(r"[\w]+", normalized))
        overlap = len(question_tokens & answer_tokens) / max(1, len(question_tokens))
        evidence_needed = intent.casefold() in {"search", "research", "learn"} or any(w in normalized for w in ("latest", "current", "today", "price", "news", "source", "evidence", "आज", "ताज़ा", "स्रोत", "प्रमाण"))
        protected = risk.casefold() in {"high", "critical"} or any(w in normalized for w in ("delete", "transfer money", "make payment", "password", "api key", "self-update", "modify yourself", "हटा दो", "पैसे भेज", "भुगतान"))

        def solver():
            if not answer.strip(): return BrainPerspective("brain_1_solver", "direct solution", "No answer text was supplied.", "Generate a grounded answer before presenting a conclusion.", 0.95, evidence_needed)
            if overlap > 0.92 and len(answer_tokens) < 12: return BrainPerspective("brain_1_solver", "direct solution", "The answer may repeat the request without enough new information.", "Add the direct answer, the reason, and one concrete example.", 0.72, evidence_needed)
            return BrainPerspective("brain_1_solver", "direct solution", "A candidate response is available for review.", "Keep the answer focused on the user's stated goal.", 0.55, evidence_needed)
        def challenger():
            if protected: return BrainPerspective("brain_2_challenger", "critical review", "Potentially sensitive or high-risk intent requires conservative handling.", "Check Constitution, explicit permission, scope, and reversibility before any protected action.", 0.96, evidence_needed)
            if evidence_needed and verification_status.upper() not in {"VERIFIED", "MULTI_SOURCE_SUPPORTED", "DETERMINISTIC_ARITHMETIC"}: return BrainPerspective("brain_2_challenger", "critical review", "Fresh or source-dependent claims are not clearly verified.", "Fetch primary sources, compare dates, and label unresolved conflicts instead of storing them as trusted facts.", 0.91, True)
            if not answer.strip() or overlap > 0.92: return BrainPerspective("brain_2_challenger", "critical review", "The response may be empty or insufficiently informative.", "Check whether every part of the request is answered and mark unknowns explicitly.", 0.78, evidence_needed)
            return BrainPerspective("brain_2_challenger", "critical review", "No obvious high-risk marker found; factual correctness is not proven.", "Run the domain-specific verifier for consequential or factual claims.", 0.52, evidence_needed)
        def strategist():
            if intent.casefold() in {"search", "research", "learn"}: return BrainPerspective("brain_3_strategist", "alternatives and planning", "The request benefits from evidence-backed synthesis.", "Compare credible sources where practical, separate facts from inference, and give a concise recommendation plus alternatives.", 0.78, True)
            if any(w in normalized for w in ("idea", "suggest", "better", "improve", "विचार", "सुझाव", "बेहतर", "सुधार")): return BrainPerspective("brain_3_strategist", "alternatives and planning", "The user explicitly seeks improvement ideas or alternatives.", "Offer a best default, one lower-cost alternative, and trade-offs with the next practical step.", 0.83, evidence_needed)
            return BrainPerspective("brain_3_strategist", "alternatives and planning", "A next-step option may make the answer more actionable.", "When useful, include one practical next step and one alternative without irrelevant detail.", 0.58, evidence_needed)

        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="sahibex-council") as pool:
            perspectives = tuple(f.result() for f in (pool.submit(solver), pool.submit(challenger), pool.submit(strategist)))
        suggestions = tuple(dict.fromkeys(p.recommendation for p in perspectives))
        disagreement = len({p.needs_external_evidence for p in perspectives}) > 1
        if protected: consensus = "SAFETY_REVIEW_REQUIRED"
        elif evidence_needed and verification_status.upper() not in {"VERIFIED", "MULTI_SOURCE_SUPPORTED", "DETERMINISTIC_ARITHMETIC"}: consensus = "EVIDENCE_REQUIRED"
        elif not answer.strip(): consensus = "NO_CANDIDATE_ANSWER"
        else: consensus = "ADVISORY_REVIEW_COMPLETE"
        limitations = ("These are complementary heuristics, not three independent language models.", "Consensus does not prove factual truth; source-based verification is required for factual claims.", "The council cannot grant permissions, execute tools, or override the Constitution.")
        return ThreeBrainResult(self.VERSION, "parallel_advisory", perspectives, consensus, disagreement, suggestions, limitations)
