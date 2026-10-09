import pytest

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import BrainCapability, BrainStatus, SpecialistBrain
from core.policies.constitution import BrainRole


def test_mother_brain_root_cannot_be_removed_even_without_children():
    registry = BrainRegistry()
    mother = SpecialistBrain(
        name="SAHIBEX Mother",
        description="Constitutional root identity",
        specialization="mother",
        capabilities={BrainCapability.THINK, BrainCapability.VERIFY},
        brain_id="sahibex-master-brain",
        brain_role=BrainRole.MOTHER_BRAIN,
    )
    registry.register(mother)

    with pytest.raises(ValueError, match="constitutional Mother Brain root"):
        registry.remove(mother.brain_id)

    assert registry.get_mother_brain() is mother
    assert registry.count() == 1
