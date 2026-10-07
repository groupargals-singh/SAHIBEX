"""Phase N additive sleep/consolidation coverage layer.

Read-only assessment only: no execution, permission grant, deletion, or authority override.
"""
from dataclasses import dataclass

PHASE_N_VERSION = "PHASE-N-SLEEP-CONSOLIDATION-1"


@dataclass(frozen=True)
class SleepConsolidationAssessment:
    scores: dict
    ready: bool


class SleepConsolidationExpansion:
    ITEM_IDS = tuple(f"N-{i:02d}" for i in range(1, 13))
    ITEM_NAMES = (
        "Sleep Foundation", "Wake/Sleep State", "Idle Consolidation",
        "Memory Consolidation", "Memory Reinforcement", "Memory Cleanup",
        "Learning Consolidation", "Knowledge Consolidation", "Pattern Stabilization",
        "Recovery During Low Activity", "Consolidation Safety Boundary",
        "Post-Sleep Readiness",
    )

    def assess(self, *, sleep_state="sleeping", memory_ready=True,
               learning_ready=True, knowledge_ready=True, recovery_ready=True,
               safety_ok=True, post_sleep_ready=True, consolidation_score=1.0):
        score = max(0.0, min(1.0, float(consolidation_score)))
        state_ok = sleep_state in {"sleeping", "awaking", "awake"}
        scores = {
            "N-01": 1.0 if state_ok else 0.0,
            "N-02": 1.0 if state_ok else 0.0,
            "N-03": score,
            "N-04": score if memory_ready else 0.0,
            "N-05": score if memory_ready else 0.0,
            "N-06": score if memory_ready else 0.0,
            "N-07": score if learning_ready else 0.0,
            "N-08": score if knowledge_ready else 0.0,
            "N-09": score,
            "N-10": score if recovery_ready else 0.0,
            "N-11": 1.0 if safety_ok else 0.0,
            "N-12": 1.0 if post_sleep_ready else 0.0,
        }
        return SleepConsolidationAssessment(scores=scores, ready=all(v >= 0.8 for v in scores.values()))

    @staticmethod
    def security_summary():
        return {
            "read_only": True,
            "executes_actions": False,
            "grants_permission": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }
