from pathlib import Path
from types import SimpleNamespace
import os
import pytest
from tools.android_computer_control import AndroidComputerControlProvider, AndroidControlConfig
from tools.computer_control import ComputerAction, ComputerControlRequest

class FakeClient:
    def __init__(self, response): self.response=response; self.calls=[]
    def call(self, action, payload): self.calls.append((action,payload)); return self.response

def req(action, params=None): return ComputerControlRequest(action, params or {})
def setup(tmp_path, response):
    token=tmp_path/'token'; token.write_text('private-test-token'); token.chmod(0o600)
    client=FakeClient(response)
    provider=AndroidComputerControlProvider(config=AndroidControlConfig(token_path=str(token)),client_factory=lambda session: client)
    return provider,client

def test_denies_without_permission(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={},error=None))
    assert not p.execute(req(ComputerAction.CLICK,{'x':1,'y':2})).success
    assert not c.calls

def test_click_routes_to_companion_and_requires_completion(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={'completed':True},error=None))
    r=p.execute(req(ComputerAction.CLICK,{'x':12,'y':34}),authorized=True)
    assert r.success and c.calls==[('tap',{'x':12,'y':34})]

def test_does_not_claim_success_without_completion(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={'accepted':True},error=None))
    assert not p.execute(req(ComputerAction.CLICK,{'x':1,'y':2}),authorized=True).success

def test_ui_tree_requires_tree_evidence(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={'tree':[]},error=None))
    r=p.execute(req(ComputerAction.UI_TREE,{}),authorized=True)
    assert c.calls[0][0]=='ui_tree' and r.success

def test_ui_tree_missing_evidence_is_not_success(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={},error=None))
    r=p.execute(req(ComputerAction.UI_TREE,{}),authorized=True)
    assert not r.success

def test_missing_token_fails_closed(tmp_path):
    p=AndroidComputerControlProvider(config=AndroidControlConfig(token_path=str(tmp_path/'missing')))
    r=p.execute(req(ComputerAction.CLICK,{'x':1,'y':2}),authorized=True)
    assert not r.success and 'token not configured' in r.error

def test_bad_token_permissions_fail_closed(tmp_path):
    if os.name=='nt': pytest.skip('POSIX file mode test')
    token=tmp_path/'token'; token.write_text('x'); token.chmod(0o644)
    p=AndroidComputerControlProvider(config=AndroidControlConfig(token_path=str(token)))
    r=p.execute(req(ComputerAction.CLICK,{'x':1,'y':2}),authorized=True)
    assert not r.success and 'mode 0600' in r.error

def test_rejects_bad_coordinates_and_password_unsafe_keys(tmp_path):
    p,c=setup(tmp_path,SimpleNamespace(success=True,result={'completed':True},error=None))
    assert not p.execute(req(ComputerAction.CLICK,{'x':True,'y':2}),authorized=True).success
    assert not p.execute(req(ComputerAction.PRESS_KEY,{'key':'POWER'}),authorized=True).success
    assert not c.calls


def test_provider_rejects_unsupported_global_key_events(tmp_path):
    token = tmp_path / "token"
    token.write_text("test-token", encoding="utf-8")
    token.chmod(0o600)
    provider = AndroidComputerControlProvider(config=AndroidControlConfig(token_path=str(token)))
    request = ComputerControlRequest(action=ComputerAction.PRESS_KEY, parameters={"key": "ENTER"})
    result = provider.execute(request, authorized=True)
    assert result.success is False
    assert "only BACK, HOME, and APP_SWITCH" in result.error
