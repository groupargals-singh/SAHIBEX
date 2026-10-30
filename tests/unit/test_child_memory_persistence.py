from core.brain.child_memory_runtime import ChildMemoryRuntime


def test_persistent_child_memory_survives_runtime_restart_and_is_namespace_isolated(tmp_path):
    db = tmp_path / "child-memory.sqlite3"
    first = ChildMemoryRuntime("child-a", "brain:child-a", database_path=db)
    assert first.write("topic", {"verified": True, "count": 2}).allowed
    first.close()

    restored = ChildMemoryRuntime("child-a", "brain:child-a", database_path=db)
    assert restored.read("topic") == {"verified": True, "count": 2}

    other_child = ChildMemoryRuntime("child-b", "brain:child-b", database_path=db)
    assert other_child.read("topic") is None
    same_child_other_namespace = ChildMemoryRuntime("child-a", "brain:other-namespace", database_path=db)
    assert same_child_other_namespace.read("topic") is None

    # Credential values are intentionally not written to the durable memory table.
    assert restored.write_credential("token", "secret", authority_approved=True).allowed
    restored.close()
    reopened = ChildMemoryRuntime("child-a", "brain:child-a", database_path=db)
    assert reopened.read_credential("token", authority_approved=True) is None
    reopened.close()
    other_child.close()
    same_child_other_namespace.close()


def test_manager_restores_child_identity_memory_but_not_execution_trust(tmp_path):
    from core.brain.specialist_child_manager import SpecialistChildBrainManager

    registry_path = str(tmp_path / "child-registry.sqlite3")
    first = SpecialistChildBrainManager(identity_database_path=registry_path)
    child = first.create_child(
        name="Persistent research child",
        description="restart acceptance",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    child_id = child.brain.brain_id
    assert child.memory.write("fact", {"claim": "retained"}).allowed
    first.close()

    second = SpecialistChildBrainManager(identity_database_path=registry_path)
    restored = second.get(child_id)
    assert restored is not None
    assert restored.memory.read("fact") == {"claim": "retained"}
    assert restored.runtime_state.value == "paused"
    assert restored.brain.trust_status.value == "unverified"
    assert second.dispatch(child_id, "must not run after restart").success is False
    assert second.instance_registry.verify_integrity()
    second.close()


def test_manager_fails_closed_when_persisted_child_registry_is_tampered(tmp_path):
    import sqlite3
    from core.brain.specialist_child_manager import SpecialistChildBrainManager

    path = str(tmp_path / "tampered-registry.sqlite3")
    manager = SpecialistChildBrainManager(identity_database_path=path)
    manager.create_child(
        name="Integrity child",
        description="tamper detection",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    manager.close()
    connection = sqlite3.connect(path)
    connection.execute("UPDATE child_instances SET data='{}'")
    connection.commit()
    connection.close()

    try:
        SpecialistChildBrainManager(identity_database_path=path)
    except RuntimeError as exc:
        assert "integrity_failure" in str(exc)
    else:
        raise AssertionError("tampered child registry was restored")
