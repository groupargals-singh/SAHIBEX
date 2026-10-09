from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.master_brain import MasterBrain
from core.policies.constitution import ActionDecision


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        brain = MasterBrain()

        # MasterBrain's ToolBrain is rooted at its process project root,
        # so verify the protected path contract independently at ToolBrain
        # level; MasterBrain must preserve the authorization contract.
        blocked = brain.process("delete file app/main.py")
        assert blocked.success is False
        assert blocked.permission_allowed is False
        assert blocked.confirmation_required is True
        assert blocked.authority_decision == ActionDecision.REQUIRE_CONFIRMATION.value

        protected = brain.process(
            "Change the system configuration.",
            user_confirmation=True,
        )
        assert protected.success is False
        assert protected.permission_allowed is False

        assert (
            brain.constitution.can_sahibex_modify_constitution()
            is False
        )

        print("SAHIBEX MASTER PROTECTED AUTHORITY INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()
