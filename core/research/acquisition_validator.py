from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse

from core.research.acquisition import AcquiredSource


@dataclass(frozen=True)
class AcquisitionValidationResult:
    valid: bool
    source_id: Optional[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AcquisitionSafetyValidator:
    """
    Structural safety gate for acquired research sources.

    This validator does NOT decide whether research is true.
    It only validates whether acquired material is acceptable
    for entry into the research ingestion pipeline.
    """

    DEFAULT_MAX_CONTENT_LENGTH = 2_000_000
    DEFAULT_MAX_TITLE_LENGTH = 1_000
    DEFAULT_MAX_SOURCE_TYPE_LENGTH = 100
    DEFAULT_MAX_LOCATOR_LENGTH = 8_000

    ALLOWED_SOURCE_TYPES = {
        "web",
        "api",
        "rss",
        "document",
        "database",
        "mock",
        "unknown",
    }

    def __init__(
        self,
        *,
        max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH,
        max_title_length: int = DEFAULT_MAX_TITLE_LENGTH,
        max_source_type_length: int = DEFAULT_MAX_SOURCE_TYPE_LENGTH,
        max_locator_length: int = DEFAULT_MAX_LOCATOR_LENGTH,
    ) -> None:
        if max_content_length <= 0:
            raise ValueError(
                "max_content_length must be greater than zero"
            )

        if max_title_length <= 0:
            raise ValueError(
                "max_title_length must be greater than zero"
            )

        if max_source_type_length <= 0:
            raise ValueError(
                "max_source_type_length must be greater than zero"
            )

        if max_locator_length <= 0:
            raise ValueError(
                "max_locator_length must be greater than zero"
            )

        self.max_content_length = max_content_length
        self.max_title_length = max_title_length
        self.max_source_type_length = max_source_type_length
        self.max_locator_length = max_locator_length

    @staticmethod
    def _check_required_text(
        value: object,
        field_name: str,
        errors: List[str],
    ) -> None:
        if not isinstance(value, str):
            errors.append(
                f"{field_name} must be a string"
            )
            return

        if not value.strip():
            errors.append(
                f"{field_name} cannot be empty"
            )

    def validate(
        self,
        source: AcquiredSource,
    ) -> AcquisitionValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(source, AcquiredSource):
            return AcquisitionValidationResult(
                valid=False,
                source_id=None,
                errors=[
                    "source must be an AcquiredSource"
                ],
            )

        self._check_required_text(
            source.source_id,
            "source_id",
            errors,
        )

        self._check_required_text(
            source.title,
            "title",
            errors,
        )

        self._check_required_text(
            source.source_type,
            "source_type",
            errors,
        )

        self._check_required_text(
            source.locator,
            "locator",
            errors,
        )

        self._check_required_text(
            source.content,
            "content",
            errors,
        )

        if len(source.title) > self.max_title_length:
            errors.append(
                "title exceeds maximum length"
            )

        if len(source.source_type) > self.max_source_type_length:
            errors.append(
                "source_type exceeds maximum length"
            )

        if len(source.locator) > self.max_locator_length:
            errors.append(
                "locator exceeds maximum length"
            )

        if len(source.content) > self.max_content_length:
            errors.append(
                "content exceeds maximum length"
            )

        if (
            isinstance(source.source_type, str)
            and source.source_type.strip()
            and source.source_type.strip().lower()
            not in self.ALLOWED_SOURCE_TYPES
        ):
            warnings.append(
                "source_type is not in the known source type registry"
            )

        if (
            isinstance(source.locator, str)
            and source.locator.strip()
        ):
            parsed = urlparse(source.locator)

            if source.source_type.strip().lower() in {
                "web",
                "api",
                "rss",
            }:
                if parsed.scheme not in {
                    "http",
                    "https",
                }:
                    errors.append(
                        "network source locator must use "
                        "http or https"
                    )

        if not isinstance(source.metadata, dict):
            errors.append(
                "metadata must be a dictionary"
            )

        source_id = (
            source.source_id
            if isinstance(source.source_id, str)
            else None
        )

        return AcquisitionValidationResult(
            valid=not errors,
            source_id=source_id,
            errors=errors,
            warnings=warnings,
        )

    def require_valid(
        self,
        source: AcquiredSource,
    ) -> AcquisitionValidationResult:
        result = self.validate(source)

        if not result.valid:
            raise ValueError(
                "acquisition validation failed: "
                + "; ".join(result.errors)
            )

        return result
