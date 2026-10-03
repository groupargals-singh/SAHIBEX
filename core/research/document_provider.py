from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from core.research.acquisition import (
    AcquiredSource,
    AcquisitionRequest,
    AcquisitionResult,
    ResearchAcquisitionProvider,
)


@dataclass(frozen=True)
class DocumentProviderConfig:
    """Configuration for safe local document acquisition."""

    project_root: Path
    max_file_size: int = 2_000_000
    max_sources: int = 10
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve()

        if self.max_file_size <= 0:
            raise ValueError(
                "max_file_size must be greater than zero"
            )

        if self.max_sources <= 0:
            raise ValueError(
                "max_sources must be greater than zero"
            )

        if not isinstance(self.encoding, str):
            raise ValueError(
                "encoding must be a string"
            )

        if not self.encoding.strip():
            raise ValueError(
                "encoding must be a non-empty string"
            )

        object.__setattr__(
            self,
            "project_root",
            root,
        )


class LocalDocumentResearchProvider(
    ResearchAcquisitionProvider
):
    """Safe local document acquisition provider."""

    provider_name = "document"
    requires_network = False

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".log",
    }

    def __init__(
        self,
        config: DocumentProviderConfig,
    ) -> None:
        if not isinstance(
            config,
            DocumentProviderConfig,
        ):
            raise TypeError(
                "config must be a DocumentProviderConfig"
            )

        self.config = config

    def _safe_path(
        self,
        requested: str,
    ) -> Path:
        """Resolve a requested path inside project boundary."""

        if not isinstance(
            requested,
            str,
        ):
            raise ValueError(
                "document path must be a string"
            )

        raw_path = requested.strip()

        if not raw_path:
            raise ValueError(
                "document path must be a non-empty string"
            )

        path_parts = Path(raw_path).parts

        if ".." in path_parts:
            raise PermissionError(
                "document path traversal is not allowed"
            )

        candidate = (
            self.config.project_root / raw_path
        ).resolve()

        try:
            candidate.relative_to(
                self.config.project_root
            )
        except ValueError as exc:
            raise PermissionError(
                "document path is outside the "
                "SAHIBEX project boundary"
            ) from exc

        return candidate

    def _validate_file(
        self,
        path: Path,
    ) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"document not found: {path}"
            )

        if not path.is_file():
            raise IsADirectoryError(
                f"document path is not a file: {path}"
            )

        if (
            path.suffix.lower()
            not in self.SUPPORTED_EXTENSIONS
        ):
            raise ValueError(
                "unsupported document format: "
                f"{path.suffix or '<none>'}"
            )

        size = path.stat().st_size

        if size > self.config.max_file_size:
            raise ValueError(
                "document exceeds maximum allowed size"
            )

    def _read_document(
        self,
        path: Path,
    ) -> str:
        try:
            content = path.read_text(
                encoding=self.config.encoding,
                errors="replace",
            )
        except OSError as exc:
            raise RuntimeError(
                f"failed to read document: {exc}"
            ) from exc

        if not content.strip():
            raise ValueError(
                "document content is empty"
            )

        return content

    @staticmethod
    def _source_id(
        relative_path: str,
        content: str,
    ) -> str:
        digest = hashlib.sha256(
            (
                relative_path
                + "\n"
                + content
            ).encode("utf-8")
        ).hexdigest()

        return f"document_{digest}"

    @staticmethod
    def _title(
        path: Path,
    ) -> str:
        return path.stem

    def _build_source(
        self,
        path: Path,
        content: str,
        request: AcquisitionRequest,
    ) -> AcquiredSource:
        relative_path = str(
            path.relative_to(
                self.config.project_root
            )
        )

        acquired_at = datetime.now(
            timezone.utc
        ).isoformat()

        source_id = self._source_id(
            relative_path,
            content,
        )

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        metadata = dict(
            request.metadata
        )

        metadata.update(
            {
                "provider": self.__class__.__name__,
                "provider_name": self.provider_name,
                "acquired_at": acquired_at,
                "document_path": relative_path,
                "file_extension": path.suffix.lower(),
                "content_bytes": path.stat().st_size,
                "content_hash": content_hash,
                "discovery_only": False,
                "content_is_full_document": True,
                "reliability": 1.0,
            }
        )

        return AcquiredSource(
            source_id=source_id,
            title=self._title(path),
            source_type="document",
            locator=relative_path,
            content=content,
            metadata=metadata,
        )

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        if request.source_type is not None:
            requested_type = (
                request.source_type.strip().lower()
            )

            if requested_type != "document":
                raise ValueError(
                    "document provider requires "
                    "source_type='document'"
                )

        raw_paths = request.metadata.get(
            "paths",
            request.metadata.get("path"),
        )

        if raw_paths is None:
            raise ValueError(
                "document acquisition requires "
                "metadata path or paths"
            )

        if isinstance(
            raw_paths,
            str,
        ):
            paths = [raw_paths]
        elif isinstance(
            raw_paths,
            (list, tuple),
        ):
            paths = list(raw_paths)
        else:
            raise TypeError(
                "metadata path/paths must be "
                "a string or list of strings"
            )

        if not paths:
            raise ValueError(
                "document paths cannot be empty"
            )

        max_sources = min(
            request.max_sources,
            self.config.max_sources,
        )

        sources: List[AcquiredSource] = []
        seen_ids: set[str] = set()
        errors: List[str] = []

        for requested_path in paths:
            if len(sources) >= max_sources:
                break

            try:
                path = self._safe_path(
                    requested_path
                )

                self._validate_file(
                    path
                )

                content = self._read_document(
                    path
                )

                source = self._build_source(
                    path,
                    content,
                    request,
                )

                if source.source_id in seen_ids:
                    continue

                seen_ids.add(
                    source.source_id
                )

                sources.append(
                    source
                )

            except Exception as exc:
                errors.append(
                    f"{requested_path}: "
                    f"{type(exc).__name__}: {exc}"
                )

        if sources and not errors:
            status = "completed"
            completed = True
        elif sources and errors:
            status = "partial"
            completed = False
        else:
            status = "failed"
            completed = False

        return AcquisitionResult(
            query=request.query,
            sources=sources,
            completed=completed,
            status=status,
            metadata={
                "provider": self.__class__.__name__,
                "provider_name": self.provider_name,
                "requested_paths": list(paths),
                "source_count": len(sources),
                "errors": errors,
                "max_sources": max_sources,
            },
        )
