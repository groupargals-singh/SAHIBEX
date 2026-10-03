from __future__ import annotations

from core.brain.specialist_brain import SpecialistBrain
from core.policies.constitution import BrainRole


class BrainRegistry:
    """
    Registry for SAHIBEX brains.

    Responsibilities:
    - register brains
    - retrieve brains by stable identity
    - list registered brains
    - find brains by specialization
    - remove registered brains
    - maintain brain parent/child identity relationships
    - protect hierarchy integrity

    This registry does NOT:
    - execute brains
    - select models
    - route user requests
    - grant permissions
    - override the Constitution
    - modify brain capabilities
    """

    def __init__(self) -> None:
        self._brains: dict[str, SpecialistBrain] = {}

    def register(
        self,
        brain: SpecialistBrain,
    ) -> SpecialistBrain:
        if not isinstance(brain, SpecialistBrain):
            raise TypeError(
                "brain must be a SpecialistBrain."
            )

        if brain.brain_id in self._brains:
            raise ValueError(
                f"Brain already registered: {brain.brain_id}"
            )

        self._validate_hierarchy_registration(brain)

        self._brains[brain.brain_id] = brain

        return brain

    def _validate_hierarchy_registration(
        self,
        brain: SpecialistBrain,
    ) -> None:
        if not isinstance(brain.brain_role, BrainRole):
            raise TypeError(
                "brain.brain_role must be a BrainRole."
            )

        # Mother Brain is the single root.
        if brain.brain_role == BrainRole.MOTHER_BRAIN:
            if brain.parent_brain_id is not None:
                raise ValueError(
                    "Mother Brain cannot have a parent."
                )

            existing_mother = self.get_mother_brain()

            if existing_mother is not None:
                raise ValueError(
                    "Only one Mother Brain can be registered."
                )

            return

        # A hierarchy-aware brain with a parent must point to
        # an already registered brain.
        if brain.parent_brain_id is not None:
            parent = self._brains.get(
                brain.parent_brain_id
            )

            if parent is None:
                raise ValueError(
                    "Parent brain is not registered: "
                    f"{brain.parent_brain_id}"
                )

            if parent.brain_id == brain.brain_id:
                raise ValueError(
                    "A brain cannot be its own parent."
                )

            # No brain may become the parent of the Mother Brain.
            if parent.brain_role == BrainRole.CHILD_BRAIN:
                # A Child Brain may contain its own Internal Army,
                # but another Child Brain cannot become its child
                # in this architecture.
                if brain.brain_role == BrainRole.CHILD_BRAIN:
                    raise ValueError(
                        "A Child Brain cannot directly contain "
                        "another Child Brain."
                    )

            if parent.brain_role == BrainRole.INTERNAL_ARMY:
                raise ValueError(
                    "An Internal Army Brain cannot be a parent."
                )

        # A Child Brain must have a parent.
        #
        # The parent may be Mother Brain or another permitted
        # hierarchy root according to the architecture.
        if (
            brain.brain_role == BrainRole.CHILD_BRAIN
            and brain.parent_brain_id is None
        ):
            raise ValueError(
                "Child Brain must have a parent_brain_id."
            )

    def get(
        self,
        brain_id: str,
    ) -> SpecialistBrain | None:
        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        return self._brains.get(brain_id)

    def list_all(self) -> list[SpecialistBrain]:
        return list(self._brains.values())

    def find_by_specialization(
        self,
        specialization: str,
    ) -> list[SpecialistBrain]:
        if not isinstance(specialization, str):
            raise TypeError(
                "specialization must be a string."
            )

        normalized = specialization.strip().lower()

        if not normalized:
            raise ValueError(
                "specialization cannot be empty."
            )

        return [
            brain
            for brain in self._brains.values()
            if brain.specialization.strip().lower()
            == normalized
        ]

    def get_mother_brain(
        self,
    ) -> SpecialistBrain | None:
        for brain in self._brains.values():
            if brain.brain_role == BrainRole.MOTHER_BRAIN:
                return brain

        return None

    def get_children(
        self,
        parent_brain_id: str,
    ) -> list[SpecialistBrain]:
        if not isinstance(parent_brain_id, str):
            raise TypeError(
                "parent_brain_id must be a string."
            )

        return [
            brain
            for brain in self._brains.values()
            if brain.parent_brain_id == parent_brain_id
        ]

    def get_children_by_role(
        self,
        parent_brain_id: str,
        role: BrainRole,
    ) -> list[SpecialistBrain]:
        if not isinstance(role, BrainRole):
            raise TypeError(
                "role must be a BrainRole."
            )

        return [
            brain
            for brain in self.get_children(parent_brain_id)
            if brain.brain_role == role
        ]

    def get_parent(
        self,
        brain_id: str,
    ) -> SpecialistBrain | None:
        brain = self.get(brain_id)

        if brain is None:
            return None

        if brain.parent_brain_id is None:
            return None

        return self.get(brain.parent_brain_id)

    def is_descendant(
        self,
        brain_id: str,
        ancestor_brain_id: str,
    ) -> bool:
        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        if not isinstance(ancestor_brain_id, str):
            raise TypeError(
                "ancestor_brain_id must be a string."
            )

        current = self.get(brain_id)

        visited: set[str] = set()

        while current is not None:
            if current.brain_id in visited:
                return False

            visited.add(current.brain_id)

            if current.parent_brain_id is None:
                return False

            if current.parent_brain_id == ancestor_brain_id:
                return True

            current = self.get(current.parent_brain_id)

        return False

    def remove(
        self,
        brain_id: str,
    ) -> SpecialistBrain | None:
        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        # Prevent removing a brain while descendants still
        # depend on its hierarchy identity.
        children = self.get_children(brain_id)

        if children:
            raise ValueError(
                "Cannot remove a brain that still has "
                "registered children."
            )

        return self._brains.pop(
            brain_id,
            None,
        )

    def count(self) -> int:
        return len(self._brains)
