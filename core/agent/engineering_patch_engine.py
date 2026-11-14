from __future__ import annotations

"""Fail-closed patch application with clean-file backups and guarded rollback."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time


class PatchPolicyError(PermissionError):
    pass


@dataclass(frozen=True)
class PatchResult:
    success: bool
    applied: bool
    dry_run: bool
    backup_id: str | None
    files: tuple[str, ...]
    message: str
    diff_check: str = ""


class EngineeringPatchEngine:
    MAX_PATCH_BYTES = 256 * 1024
    MAX_FILES = 20
    MAX_FILE_BYTES = 2 * 1024 * 1024
    HEADER = re.compile(r"^diff --git a/([^\s]+) b/([^\s]+)$", re.MULTILINE)

    def __init__(self, project_root: str | Path, backup_root: str | Path | None = None):
        self.root = Path(project_root).expanduser().resolve(strict=True)
        if not (self.root / ".git").exists() or not (self.root / "app").is_dir() or not (self.root / "core").is_dir():
            raise ValueError("project_root must be the SAHIBEX Git repository")
        self.backup_root = Path(backup_root or (Path.home() / ".cache/sahibex/engineering-backups")).expanduser().resolve()
        if self.backup_root == self.root or self.root in self.backup_root.parents:
            raise ValueError("Backups must be stored outside the repository")

    def _git(self, args: list[str], patch: str | None = None):
        return subprocess.run(
            ["git", *args], cwd=self.root, input=patch, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL if patch is None else None,
            timeout=30, check=False, shell=False,
            env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "LANG": "C.UTF-8"},
        )

    @staticmethod
    def _sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _validate(self, patch: str) -> tuple[str, ...]:
        if not patch or len(patch.encode("utf-8")) > self.MAX_PATCH_BYTES or "\x00" in patch:
            raise PatchPolicyError("Patch is empty, invalid or exceeds 256 KiB.")
        banned = ("GIT binary patch", "Binary files ", "new file mode ", "deleted file mode ",
                  "old mode ", "new mode ", "rename from ", "rename to ", "copy from ",
                  "copy to ", "\n--- /dev/null", "\n+++ /dev/null")
        if any(x in patch for x in banned):
            raise PatchPolicyError("Binary/add/delete/rename/copy/mode changes are forbidden.")
        headers = list(self.HEADER.finditer(patch))
        if not headers or len(headers) > self.MAX_FILES:
            raise PatchPolicyError("Patch must touch 1-20 existing files.")
        paths = []
        for i, match in enumerate(headers):
            old, new = match.groups()
            pure = PurePosixPath(old)
            if old != new or pure.is_absolute() or "\\" in old or old.startswith("-") or any(p in ("", ".", "..") for p in pure.parts):
                raise PatchPolicyError("Unsafe or renamed target path.")
            if old in paths:
                raise PatchPolicyError("Duplicate target path.")
            end = headers[i + 1].start() if i + 1 < len(headers) else len(patch)
            section = patch[match.start():end]
            if f"--- a/{old}\n+++ b/{old}\n" not in section or "@@" not in section:
                raise PatchPolicyError("Malformed unified diff section.")
            target = self.root.joinpath(*pure.parts)
            cursor = self.root
            for part in pure.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise PatchPolicyError("Symlink targets are forbidden.")
            resolved = target.resolve(strict=True)
            if self.root not in resolved.parents or not resolved.is_file() or resolved.stat().st_size > self.MAX_FILE_BYTES:
                raise PatchPolicyError("Target must be an existing regular file under 2 MiB.")
            if self._git(["ls-files", "--error-unmatch", "--", old]).returncode:
                raise PatchPolicyError("Only tracked files may be modified.")
            if self._git(["diff", "--quiet", "HEAD", "--", old]).returncode:
                raise PatchPolicyError("Target has existing changes; refusing to overwrite user work.")
            paths.append(old)
        return tuple(paths)

    def apply(self, patch: str, *, dry_run: bool = True) -> PatchResult:
        paths = self._validate(patch)
        checked = self._git(["apply", "--check"], patch)
        if checked.returncode:
            return PatchResult(False, False, dry_run, None, paths, "Git patch preflight failed.", checked.stdout[:8000])
        if dry_run:
            return PatchResult(True, False, True, None, paths, "Preflight PASS; no files changed.", checked.stdout[:8000])

        originals = {p: (self.root / p).read_bytes() for p in paths}
        backup_id = hashlib.sha256((str(time.time_ns()) + patch).encode()).hexdigest()[:20]
        directory = self.backup_root / backup_id
        directory.mkdir(parents=True, exist_ok=False)
        manifest = {"backup_id": backup_id, "created_at": time.time(), "files": {}}
        try:
            for path, data in originals.items():
                name = hashlib.sha256(path.encode()).hexdigest() + ".bin"
                (directory / name).write_bytes(data)
                manifest["files"][path] = {"backup": name, "before_sha256": self._sha(data)}
            (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            result = self._git(["apply"], patch)
            if result.returncode:
                for path, data in originals.items():
                    (self.root / path).write_bytes(data)
                return PatchResult(False, False, False, backup_id, paths, "Apply failed; original files restored.", result.stdout[:8000])
            for path in paths:
                manifest["files"][path]["after_sha256"] = self._sha((self.root / path).read_bytes())
            (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return PatchResult(True, True, False, backup_id, paths, "Applied after preflight and verified backups.", result.stdout[:8000])
        except Exception:
            for path, data in originals.items():
                (self.root / path).write_bytes(data)
            raise

    def rollback(self, backup_id: str):
        if not re.fullmatch(r"[0-9a-f]{20}", backup_id):
            raise PatchPolicyError("Invalid backup identifier.")
        directory = self.backup_root / backup_id
        manifest_file = directory / "manifest.json"
        if not manifest_file.is_file() or manifest_file.is_symlink():
            raise PatchPolicyError("Backup manifest missing or unsafe.")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        entries = manifest.get("files")
        if not isinstance(entries, dict) or not entries or len(entries) > self.MAX_FILES:
            raise PatchPolicyError("Invalid backup manifest.")
        restore = {}
        for path, meta in entries.items():
            pure = PurePosixPath(path)
            if pure.is_absolute() or any(p in ("", ".", "..") for p in pure.parts):
                raise PatchPolicyError("Unsafe manifest path.")
            target = self.root.joinpath(*pure.parts)
            cursor = self.root
            for part in pure.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise PatchPolicyError("Symlink detected during rollback.")
            if not target.is_file() or self._sha(target.read_bytes()) != meta.get("after_sha256"):
                raise PatchPolicyError("Rollback refused: target changed since patch.")
            backup = directory / str(meta.get("backup", ""))
            if backup.parent != directory or not backup.is_file() or backup.is_symlink():
                raise PatchPolicyError("Backup file missing or unsafe.")
            data = backup.read_bytes()
            if self._sha(data) != meta.get("before_sha256"):
                raise PatchPolicyError("Backup integrity check failed.")
            restore[path] = data
        for path, data in restore.items():
            target = self.root / path
            fd, temp = tempfile.mkstemp(prefix=".sahibex-rollback-", dir=str(target.parent))
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        return {"success": True, "backup_id": backup_id, "restored_files": tuple(restore)}
