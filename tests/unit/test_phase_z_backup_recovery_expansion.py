from core.brain.backup_recovery_expansion import BackupRecoveryManager

def main():
    payload={"state":"ok","count":3}
    m=BackupRecoveryManager.manifest("z-1",payload,"SAHIBEX-1")
    assert BackupRecoveryManager.verify_integrity(payload,m)
    assert not BackupRecoveryManager.verify_integrity({"state":"tampered"},m)
    assert BackupRecoveryManager.sanitize_state({"state":"ok","token":"x"}) == {"state":"ok"}
    assert BackupRecoveryManager.compatibility("1","2")
    try: BackupRecoveryManager.migrate(payload,"1","2")
    except PermissionError: pass
    else: raise AssertionError("unauthorized migration allowed")
    result=BackupRecoveryManager.migrate(payload,"1","2",authorized=True)
    assert result.migrated and result.compatible
    assert not BackupRecoveryManager.grants_permission()
    assert not BackupRecoveryManager.rollback_allowed(authorized=False)
    assert BackupRecoveryManager.rollback_allowed(authorized=True)
    print("SAHIBEX PHASE Z BACKUP/RECOVERY EXPANSION TEST: PASS")

if __name__ == "__main__": main()
