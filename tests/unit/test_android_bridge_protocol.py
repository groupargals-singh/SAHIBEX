from tools.android_bridge_protocol import BridgeSession,canonical_request,sign_request,verify_signature
from tools.android_bridge_client import AndroidBridgeClient
def test_session_token_is_random_and_loopback_only():
    a,b=BridgeSession.create(),BridgeSession.create()
    assert a.token!=b.token and a.port==38741
    AndroidBridgeClient(a)
    try:AndroidBridgeClient(a,host="192.168.1.2")
    except ValueError:pass
    else:raise AssertionError("non-loopback bridge host must be rejected")
def test_signature_is_deterministic_and_verifiable():
    p={"x":10,"y":20};s=sign_request(token="secret",action="click",payload=p,nonce="nonce-1")
    assert verify_signature(token="secret",action="click",payload=p,nonce="nonce-1",signature=s)
    assert not verify_signature(token="wrong",action="click",payload=p,nonce="nonce-1",signature=s)
def test_canonical_request_is_stable():
    assert canonical_request(action="tap",payload={"b":2,"a":1},nonce="n")==canonical_request(action="tap",payload={"a":1,"b":2},nonce="n")
