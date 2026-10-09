from __future__ import annotations

import os

from core.brain.master_brain import MasterBrain


BANNER = """
============================================================
                 SAHIBEX PERSONAL AI
============================================================
 Master Brain Runtime
 Intent + Planning + Authority + Permission + Verification
 Context + Protected Action Control
============================================================
Type 'exit' to stop.
Type 'status' to inspect the brain.
============================================================
"""


def print_result(result) -> None:
    print()
    print("------------------------------------------------------------")
    print("SAHIBEX")
    print("------------------------------------------------------------")
    print(f"Message              : {result.message}")
    print(f"Intent               : {result.intent}")
    print(f"Intent confidence    : {result.intent_confidence:.2f}")
    print(f"Action               : {result.action}")
    print(f"Action confidence    : {result.action_confidence:.2f}")
    print(f"Risk                 : {result.risk}")
    print(f"Authority decision   : {result.authority_decision}")
    print(f"Permission allowed   : {result.permission_allowed}")
    print(f"Confirmation needed  : {result.confirmation_required}")
    print(f"Plan created         : {result.plan_created}")
    print(f"Task count           : {result.task_count}")
    print(f"Verification         : {result.verification_status}")

    if result.goal_id:
        print(f"Goal ID              : {result.goal_id}")

    print("------------------------------------------------------------")
    print()


def print_status(brain: MasterBrain) -> None:
    print()
    print("============================================================")
    print("SAHIBEX BRAIN STATUS")
    print("============================================================")
    print("Master Brain         : ONLINE")
    print("Intent Engine        : ONLINE")
    print("Context Manager      : ONLINE")
    print("Master Planner       : ONLINE")
    print("Constitution         : ACTIVE")
    print("Permission Engine    : ONLINE")
    print("Verification Engine  : ONLINE")
    roles = brain.internal_brain_team.roles()
    executable_roles = sum(1 for role in roles if role.handler_registered)
    print(f"Internal Brain Roles : {len(roles)} defined; {executable_roles} handlers connected")
    print("Independent Child    : NOT BORN (future DNA/spec only)")
    print("Protected Actions    : CONTROLLED")
    print("User Authority       : FINAL")
    print("============================================================")
    print()


def main() -> None:
    # Production runtime uses the self-hosted local cognitive engine by default.
    os.environ.setdefault("SAHIBEX_MODEL_PROVIDER", "local")
    # User-authorized live research backend. Network permission is still
    # enforced by the research acquisition gate for every network action.
    os.environ.setdefault("SAHIBEX_SEARCH_BACKEND", "duckduckgo_html")
    brain = MasterBrain()

    print(BANNER)

    while True:
        try:
            user_input = input("YOU > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSAHIBEX stopped.")
            break

        if not user_input:
            print("SAHIBEX > Please enter a request.")
            continue

        if user_input.lower() in {"exit", "quit", "q"}:
            print("SAHIBEX > Session closed.")
            break

        if user_input.lower() in {"status", "/status"}:
            print_status(brain)
            continue

        result = brain.process(user_input)

        print_result(result)


if __name__ == "__main__":
    main()
