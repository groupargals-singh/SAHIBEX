from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from core.research.memory_association import MemoryAssociation
from core.research.memory_association_storage import (
    MemoryAssociationStorage,
)
from core.research.memory_backup import MemoryBackupEngine
from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        source_db = root / "source.db"
        restored_db = root / "restored.db"
        backup_file = root / "memory_backup.json"

        source = ResearchStorage(source_db)

        memory = MemoryCandidate(
            memory_id="memory-001",
            content="SAHIBEX memory backup test",
            memory_type="semantic",
            source="unit-test",
            importance=0.9,
            confidence=0.95,
        )

        source.save_memory(memory)

        source.record_memory_verification(
            memory_id="memory-001",
            status="VERIFIED",
            evidence_id="evidence-001",
            reason="unit test verification",
        )

        association_storage = MemoryAssociationStorage(
            source_db
        )

        association = MemoryAssociation(
            association_id="association-001",
            source_memory_id="memory-001",
            target_id="concept-001",
            target_type="concept",
            association_type="memory_to_concept",
            strength=0.9,
            confidence=0.95,
            metadata={"test": True},
        )

        association_storage.save_association(association)

        result = MemoryBackupEngine.create_backup(
            source_db,
            backup_file,
        )

        assert result.memory_count == 1
        assert result.verification_count == 1
        assert result.association_count == 1
        assert backup_file.exists()
        print("[PASS] memory backup created")

        validated = MemoryBackupEngine.validate_backup(
            backup_file
        )

        assert (
            validated["payload"]["backup_id"]
            == result.backup_id
        )
        assert (
            validated["payload"]["memories"][0]["memory_id"]
            == "memory-001"
        )
        assert (
            validated["payload"]
            ["memory_verification_records"][0]["status"]
            == "VERIFIED"
        )
        assert (
            validated["payload"]
            ["memory_associations"][0]["association_id"]
            == "association-001"
        )
        print("[PASS] backup integrity and content validated")

        restored = ResearchStorage(restored_db)

        try:
            restored.save_memory(
                MemoryCandidate(
                    memory_id="old-memory",
                    content="old state",
                    memory_type="test",
                    source="test",
                )
            )

            try:
                MemoryBackupEngine.restore_backup(
                    backup_file,
                    restored_db,
                )
                raise AssertionError(
                    "restore without authorization was allowed"
                )
            except PermissionError:
                pass

            print("[PASS] unauthorized restore blocked")

            restore_result = (
                MemoryBackupEngine.restore_backup(
                    backup_file,
                    restored_db,
                    authorized=True,
                )
            )

            assert restore_result["restored"] is True
            assert restore_result["memory_count"] == 1
            assert restore_result["verification_count"] == 1
            assert restore_result["association_count"] == 1
            print("[PASS] authorized restore completed")

            restored_memory = restored.get_memory(
                "memory-001"
            )

            assert restored_memory is not None
            assert (
                restored_memory.content
                == "SAHIBEX memory backup test"
            )
            print("[PASS] memory content restored")

            verification = (
                restored.get_memory_verification(
                    "memory-001"
                )
            )

            assert verification is not None
            assert verification["status"] == "VERIFIED"
            assert (
                verification["evidence_id"]
                == "evidence-001"
            )
            print("[PASS] verification state restored")

            restored_associations = (
                MemoryAssociationStorage(
                    restored_db
                )
            )

            links = (
                restored_associations.associations_for_memory(
                    "memory-001"
                )
            )

            assert len(links) == 1
            assert (
                links[0].association_id
                == "association-001"
            )
            print("[PASS] memory associations restored")

        finally:
            restored.close()
            source.close()

        corrupted = root / "corrupted_backup.json"

        package = json.loads(
            backup_file.read_text(encoding="utf-8")
        )

        package["payload"]["memories"][0]["source"] = (
            "tampered"
        )

        corrupted.write_text(
            json.dumps(package),
            encoding="utf-8",
        )

        try:
            MemoryBackupEngine.validate_backup(
                corrupted
            )
            raise AssertionError(
                "corrupted backup was accepted"
            )
        except ValueError:
            pass

        print("[PASS] corrupted backup rejected")

    print(
        "SAHIBEX PHASE 2 #63 MEMORY BACKUP & RECOVERY TEST: PASS"
    )


if __name__ == "__main__":
    main()
