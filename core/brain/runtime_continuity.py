from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ContinuityEnvelope:
    runtime_id: str
    checkpoint_sequence: int
    state: dict[str, Any]
    source: str
    target: str

class RuntimeContinuityBridge:
    """Transfers only serialized runtime state; never transfers authority/credentials."""
    FORBIDDEN_KEYS={'permission','authority','credentials','token','secret','password'}
    def export(self, runtime_id, checkpoint_sequence, state, source='phone', target='pc'):
        safe={k:v for k,v in state.items() if k.lower() not in self.FORBIDDEN_KEYS}
        return ContinuityEnvelope(runtime_id,checkpoint_sequence,safe,source,target)
    def import_state(self, envelope):
        if not envelope.runtime_id.strip(): raise ValueError('runtime_id required')
        return dict(envelope.state)
    @staticmethod
    def transfers_authority(): return False
    @staticmethod
    def transfers_credentials(): return False
