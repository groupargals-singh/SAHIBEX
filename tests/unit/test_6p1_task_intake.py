from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.agent_task_intake import AgentTaskIntake, TaskIntakeResult

def check(v,label):
    if not v: raise AssertionError(label)
    print("[PASS]",label)

def main():
    i=AgentTaskIntake()
    r=i.intake("Research and verify AI security.",intent="research",priority=2,constraints=("Reliable sources",),success_criteria=("Verified findings",),metadata={"channel":"user"})
    check(isinstance(r,TaskIntakeResult),"result contract"); check(r.accepted,"valid request accepted"); check(r.objective is not None,"objective created"); check(bool(r.intake_id),"intake identity exists")
    check(r.objective.objective=="Research and verify AI security.","objective preserved"); check(r.objective.success_criteria==("Verified findings",),"success criteria preserved")
    check(r.grants_permission is False,"intake cannot grant permission"); check(r.executes_protected_actions is False,"intake cannot execute protected actions")
    bad=i.intake("Do something",intent="research")
    check(not bad.accepted,"missing success criteria rejected"); check(bad.objective is None,"rejected request creates no objective"); check(any("success criterion" in e for e in bad.errors),"rejection reason recorded")
    empty=i.intake("",intent="research",success_criteria=("done",))
    check(not empty.accepted,"empty objective rejected")
    for m in ("execute","execute_tool","grant_permission","modify_constitution","run_command","network_access"):
        check(not hasattr(i,m),"no protected method: "+m)
    print("SAHIBEX 6P-1 TASK INTAKE TEST: PASS")
if __name__=="__main__": main()
