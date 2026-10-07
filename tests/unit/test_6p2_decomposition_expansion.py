from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.agent_goal import AgentGoal
from core.agent_decomposition_expansion import GoalDecompositionExpansion

def check(v,label):
    if not v: raise AssertionError(label)
    print("[PASS]",label)

def main():
    goal=AgentGoal(objective="Research and verify AI security.",intent="research",priority="high",constraints=("Reliable sources",),success_criteria=("Verified findings",))
    e=GoalDecompositionExpansion(); r=e.decompose(goal)
    check(r.success,"decomposition succeeds"); check(len(r.tasks)==3,"three structured tasks created")
    for x in r.tasks:
        check(x.objective==goal.objective,"objective preserved"); check(x.constraints==goal.constraints,"constraints preserved"); check(x.success_criteria==goal.success_criteria,"success criteria preserved"); check(x.verification_required,"verification required")
    check(r.tasks[1].dependencies==(r.tasks[0].task_id,),"dependency preserved"); check(r.tasks[2].dependencies==(r.tasks[1].task_id,),"verification dependency preserved")
    check(not r.tasks[1].protected_action,"research task is not protected")
    protected=AgentGoal(objective="Execute approved action",intent="execute",success_criteria=("Action verified",))
    pr=e.decompose(protected); check(pr.tasks[1].protected_action,"protected intent identified")
    check(e.validate(r.tasks)==(),"valid decomposition passes validation")
    bad=list(r.tasks); bad[2]=type(bad[2])(bad[2].title,bad[2].objective,bad[2].intent,bad[2].success_criteria,bad[2].constraints,("missing",),False,bad[2].task_id)
    check(e.validate(tuple(bad)),"invalid dependency detected")
    check(r.grants_permission is False,"decomposition cannot grant permission"); check(r.executes_protected_actions is False,"decomposition cannot execute protected actions")
    for m in ("execute","execute_tool","grant_permission","modify_constitution","run_command","network_access"):
        check(not hasattr(e,m),"no protected method: "+m)
    print("SAHIBEX 6P-2 DECOMPOSITION EXPANSION TEST: PASS")
if __name__=="__main__": main()
