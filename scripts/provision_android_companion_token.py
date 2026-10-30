#!/usr/bin/env python3
"""Store the Companion pairing token locally without echoing or logging it."""
from getpass import getpass
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "android_companion_control_token"

def main() -> int:
    print("SAHIBEX Companion token setup")
    print("Enter the token shown inside the Companion app. Input is hidden; token is never printed.")
    token = getpass("Pairing token: ").strip()
    if not token:
        print("ERROR: empty token; nothing saved.")
        return 2
    if len(token) > 512 or not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", token):
        print("ERROR: token format looks invalid; nothing saved.")
        return 2
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    temp = TARGET.with_name(TARGET.name + ".tmp")
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(token + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, 0o600)
        os.replace(temp, TARGET)
        os.chmod(TARGET, 0o600)
    except Exception:
        try: temp.unlink(missing_ok=True)
        except Exception: pass
        print("ERROR: could not securely save token.")
        return 1
    finally:
        token = ""  # reduce accidental retention in this script's scope
    print("Saved locally: data/android_companion_control_token (permissions 0600). Token value was not displayed.")
    print("Next: run the P8 UI-tree handshake test; do not paste the token into chat.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
