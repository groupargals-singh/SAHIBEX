from __future__ import annotations
from dataclasses import dataclass
import hashlib, hmac, json, secrets
from typing import Any
PROTOCOL_VERSION=1
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT=38741
MAX_MESSAGE_BYTES=512_000
@dataclass(frozen=True)
class BridgeSession:
    token:str
    port:int=DEFAULT_PORT
    @classmethod
    def create(cls,*,port:int=DEFAULT_PORT)->"BridgeSession":
        if not 1024<=port<=65535: raise ValueError("port must be between 1024 and 65535")
        return cls(secrets.token_urlsafe(32),port)
    def authorization_header(self)->str: return f"Bearer {self.token}"
def canonical_request(*,action:str,payload:dict[str,Any],nonce:str)->bytes:
    if not action.strip(): raise ValueError("action cannot be empty")
    if not nonce.strip(): raise ValueError("nonce cannot be empty")
    body={"protocol_version":PROTOCOL_VERSION,"action":action,"nonce":nonce,"payload":payload}
    return json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sign_request(*,token:str,action:str,payload:dict[str,Any],nonce:str)->str:
    if not token: raise ValueError("token cannot be empty")
    return hmac.new(token.encode(),canonical_request(action=action,payload=payload,nonce=nonce),hashlib.sha256).hexdigest()
def verify_signature(*,token:str,action:str,payload:dict[str,Any],nonce:str,signature:str)->bool:
    if not token or not signature:return False
    return hmac.compare_digest(sign_request(token=token,action=action,payload=payload,nonce=nonce),signature)
