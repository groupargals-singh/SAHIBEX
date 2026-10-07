from core.agent.agent_objective_contract import AgentObjective

def test_contract():
    g=AgentObjective("Research AI security","research",5,("verified sources",),("evidence-backed findings",),{"brain_role":"root"},{"source":"user"})
    assert (g.objective,g.intent,g.priority)==("Research AI security","research",5)
    assert g.constraints==("verified sources",) and g.success_criteria==("evidence-backed findings",)
    assert g.authority_context["brain_role"]=="root" and g.goal_id and g.created_at

def test_immutable_and_no_authority():
    g=AgentObjective("Read a file","read")
    try: g.objective="delete a file"; assert False
    except AttributeError: pass
    assert not g.grants_permission and not g.executes_protected_actions

def test_identity_preserved():
    g=AgentObjective("Inspect logs","read"); u=g.with_update_timestamp("2026-10-07T00:00:00+00:00")
    assert u.goal_id==g.goal_id and u.created_at==g.created_at and u.updated_at.endswith("00:00")
