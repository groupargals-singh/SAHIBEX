from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    category: str
    source: str
    severity: str
    description: str
    timestamp: str

class FailureRecoveryEngine:
    CATEGORIES = frozenset({"model","tool","worker","child","memory","network","state","result","security","unknown"})
    SEVERITIES = frozenset({"low","medium","high","critical"})
    def __init__(self): self._failures=[]
    def detect(self, failure_id, category, source, severity, description):
        if category not in self.CATEGORIES or severity not in self.SEVERITIES: raise ValueError("invalid failure classification")
        r=FailureRecord(failure_id,category,source,severity,description,datetime.now(timezone.utc).isoformat())
        self._failures.append(r); return r
    def classify(self, record): return record.category, record.severity
    def contain(self, record): return record.severity in self.SEVERITIES
    def can_retry(self, record, retry_count, max_retries): return record.severity != "critical" and retry_count < max_retries
    def recover(self, record, *, verified=False): return verified and self.contain(record)
    def rollback(self, *, authorized=False, verified=False): return authorized is True and verified is True
    def resume(self, *, checkpoint_available=False, verified=False): return checkpoint_available and verified
    def failures(self): return tuple(self._failures)
    @staticmethod
    def grants_permission(): return False
    @staticmethod
    def executes_protected_actions(): return False
