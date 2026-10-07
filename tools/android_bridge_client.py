from __future__ import annotations
from dataclasses import dataclass
import json,secrets
from typing import Any
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
from tools.android_bridge_protocol import DEFAULT_HOST,MAX_MESSAGE_BYTES,BridgeSession,PROTOCOL_VERSION,sign_request
@dataclass(frozen=True)
class AndroidBridgeResult:
    success:bool
    action:str
    result:dict[str,Any]|None
    error:str|None
    status_code:int|None
class AndroidBridgeClient:
    def __init__(self,session:BridgeSession,*,host:str=DEFAULT_HOST,timeout_seconds:float=5.0)->None:
        if host not in {"127.0.0.1","localhost"}:raise ValueError("Android bridge client only permits loopback hosts")
        if timeout_seconds<=0:raise ValueError("timeout_seconds must be positive")
        self.session,self.host,self.timeout_seconds=session,host,timeout_seconds
    def call(self,action:str,payload:dict[str,Any]|None=None)->AndroidBridgeResult:
        payload=dict(payload or {});nonce=secrets.token_urlsafe(18)
        body={"protocol_version":PROTOCOL_VERSION,"action":action,"nonce":nonce,"payload":payload,"signature":sign_request(token=self.session.token,action=action,payload=payload,nonce=nonce)}
        raw=json.dumps(body).encode()
        if len(raw)>MAX_MESSAGE_BYTES:raise ValueError("bridge request exceeds message size limit")
        req=Request(f"http://{self.host}:{self.session.port}/v1/action",data=raw,method="POST",headers={"Content-Type":"application/json","Authorization":self.session.authorization_header()})
        try:
            with urlopen(req,timeout=self.timeout_seconds) as response:
                data=response.read(MAX_MESSAGE_BYTES+1)
                if len(data)>MAX_MESSAGE_BYTES:return AndroidBridgeResult(False,action,None,"bridge response exceeds size limit",response.status)
                d=json.loads(data.decode())
                return AndroidBridgeResult(bool(d.get("success")),action,d.get("result"),d.get("error"),response.status)
        except HTTPError as exc:return AndroidBridgeResult(False,action,None,f"bridge HTTP error: {exc.code}",exc.code)
        except (URLError,TimeoutError,OSError) as exc:return AndroidBridgeResult(False,action,None,str(exc),None)
