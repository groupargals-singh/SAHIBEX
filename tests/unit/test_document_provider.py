from __future__ import annotations

import tempfile
from pathlib import Path

from core.research.acquisition import AcquisitionRequest
from core.research.acquisition_validator import (
    AcquisitionSafetyValidator,
)
from core.research.document_provider import (
    DocumentProviderConfig,
    LocalDocumentResearchProvider,
)


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir).resolve()

        (root / "notes").mkdir()

        (root / "notes" / "sample.txt").write_text(
            "SAHIBEX local document test.",
            encoding="utf-8",
        )

        (root / "notes" / "second.md").write_text(
            "# Second Document\n\nResearch content.",
            encoding="utf-8",
        )

        (root / "empty.txt").write_text(
            "",
            encoding="utf-8",
        )

        (root / "sample.pdf").write_bytes(
            b"%PDF-FAKE"
        )

        provider = LocalDocumentResearchProvider(
            DocumentProviderConfig(
                project_root=root,
            )
        )

        # ---------------------------------------------------------
        # Provider identity / capability
        # ---------------------------------------------------------

        check(
            provider.provider_name == "document",
            "provider name mismatch",
        )

        check(
            provider.requires_network is False,
            "document provider must not require network",
        )

        print("[PASS] provider identity and network capability")

        # ---------------------------------------------------------
        # Single document acquisition
        # ---------------------------------------------------------

        request = AcquisitionRequest(
            query="SAHIBEX local document",
            source_type="document",
            metadata={
                "path": "notes/sample.txt",
            },
        )

        result = provider.acquire(request)

        check(
            result.completed is True,
            "single document acquisition failed",
        )

        check(
            result.status == "completed",
            "single document status mismatch",
        )

        check(
            len(result.sources) == 1,
            "expected exactly one source",
        )

        source = result.sources[0]

        check(
            source.source_type == "document",
            "source type mismatch",
        )

        check(
            source.locator == "notes/sample.txt",
            "locator mismatch",
        )

        check(
            source.content
            == "SAHIBEX local document test.",
            "document content mismatch",
        )

        check(
            source.title == "sample",
            "document title mismatch",
        )

        print("[PASS] local document acquisition")

        # ---------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------

        check(
            source.metadata["provider"]
            == "LocalDocumentResearchProvider",
            "provider metadata mismatch",
        )

        check(
            source.metadata["provider_name"]
            == "document",
            "provider_name metadata mismatch",
        )

        check(
            source.metadata["document_path"]
            == "notes/sample.txt",
            "document path metadata mismatch",
        )

        check(
            source.metadata["file_extension"]
            == ".txt",
            "file extension metadata mismatch",
        )

        check(
            source.metadata["content_is_full_document"]
            is True,
            "full document metadata missing",
        )

        check(
            source.metadata["discovery_only"]
            is False,
            "discovery_only metadata mismatch",
        )

        check(
            source.metadata["reliability"]
            == 1.0,
            "reliability metadata mismatch",
        )

        print("[PASS] document metadata")

        # ---------------------------------------------------------
        # Acquisition validator compatibility
        # ---------------------------------------------------------

        validator = AcquisitionSafetyValidator()

        validation = validator.validate(
            source
        )

        check(
            validation.valid is True,
            "acquired document failed safety validation",
        )

        check(
            validation.source_id == source.source_id,
            "validator source ID mismatch",
        )

        print(
            "[PASS] acquisition validator compatibility"
        )

        # ---------------------------------------------------------
        # Multiple documents
        # ---------------------------------------------------------

        multi_request = AcquisitionRequest(
            query="multiple documents",
            source_type="document",
            metadata={
                "paths": [
                    "notes/sample.txt",
                    "notes/second.md",
                ],
            },
        )

        multi_result = provider.acquire(
            multi_request
        )

        check(
            multi_result.completed is True,
            "multiple document acquisition failed",
        )

        check(
            multi_result.status == "completed",
            "multiple document status mismatch",
        )

        check(
            len(multi_result.sources) == 2,
            "expected two document sources",
        )

        print(
            "[PASS] multiple document acquisition"
        )

        # ---------------------------------------------------------
        # Duplicate source handling
        # ---------------------------------------------------------

        duplicate_request = AcquisitionRequest(
            query="duplicate document",
            source_type="document",
            metadata={
                "paths": [
                    "notes/sample.txt",
                    "notes/sample.txt",
                ],
            },
        )

        duplicate_result = provider.acquire(
            duplicate_request
        )

        check(
            duplicate_result.completed is True,
            "duplicate request should complete",
        )

        check(
            len(duplicate_result.sources) == 1,
            "duplicate source was not removed",
        )

        print(
            "[PASS] duplicate source handling"
        )

        # ---------------------------------------------------------
        # Stable source identity
        # ---------------------------------------------------------

        first_result = provider.acquire(
            request
        )

        second_result = provider.acquire(
            request
        )

        first = first_result.sources[0]
        second = second_result.sources[0]

        check(
            first.source_id == second.source_id,
            "source_id is not stable",
        )

        print(
            "[PASS] stable source identity"
        )

        # ---------------------------------------------------------
        # Path traversal
        #
        # Provider intentionally records per-source failures inside
        # AcquisitionResult instead of raising them to the caller.
        # ---------------------------------------------------------

        traversal_result = provider.acquire(
            AcquisitionRequest(
                query="path traversal",
                source_type="document",
                metadata={
                    "path": "../outside.txt",
                },
            )
        )

        check(
            traversal_result.completed is False,
            "path traversal unexpectedly completed",
        )

        check(
            traversal_result.status == "failed",
            "path traversal should produce failed acquisition",
        )

        check(
            len(traversal_result.sources) == 0,
            "path traversal produced a source",
        )

        check(
            any(
                "path traversal is not allowed"
                in error
                for error in traversal_result.metadata[
                    "errors"
                ]
            ),
            "path traversal error was not recorded",
        )

        print(
            "[PASS] path traversal blocked"
        )

        # ---------------------------------------------------------
        # Unsupported document format
        # ---------------------------------------------------------

        unsupported_result = provider.acquire(
            AcquisitionRequest(
                query="unsupported format",
                source_type="document",
                metadata={
                    "path": "sample.pdf",
                },
            )
        )

        check(
            unsupported_result.completed is False,
            "unsupported format unexpectedly completed",
        )

        check(
            unsupported_result.status == "failed",
            "unsupported format should produce failed acquisition",
        )

        check(
            len(unsupported_result.sources) == 0,
            "unsupported format produced a source",
        )

        check(
            any(
                "unsupported document format"
                in error
                for error in unsupported_result.metadata[
                    "errors"
                ]
            ),
            "unsupported format error was not recorded",
        )

        print(
            "[PASS] unsupported document format blocked"
        )

        # ---------------------------------------------------------
        # Empty document
        # ---------------------------------------------------------

        empty_result = provider.acquire(
            AcquisitionRequest(
                query="empty document",
                source_type="document",
                metadata={
                    "path": "empty.txt",
                },
            )
        )

        check(
            empty_result.completed is False,
            "empty document unexpectedly completed",
        )

        check(
            empty_result.status == "failed",
            "empty document should produce failed acquisition",
        )

        check(
            len(empty_result.sources) == 0,
            "empty document produced a source",
        )

        check(
            any(
                "document content is empty"
                in error
                for error in empty_result.metadata[
                    "errors"
                ]
            ),
            "empty document error was not recorded",
        )

        print(
            "[PASS] empty document blocked"
        )

        # ---------------------------------------------------------
        # Wrong source type
        # ---------------------------------------------------------

        wrong_type_result = None

        try:
            wrong_type_result = provider.acquire(
                AcquisitionRequest(
                    query="wrong source type",
                    source_type="web",
                    metadata={
                        "path": "notes/sample.txt",
                    },
                )
            )
        except ValueError as exc:
            check(
                "source_type='document'"
                in str(exc),
                "unexpected source-type error",
            )

            print(
                "[PASS] wrong source type blocked"
            )
        else:
            raise AssertionError(
                "wrong source type was not blocked"
            )

        check(
            wrong_type_result is None,
            "wrong source type unexpectedly returned a result",
        )

        # ---------------------------------------------------------
        # Missing path
        # ---------------------------------------------------------

        try:
            provider.acquire(
                AcquisitionRequest(
                    query="missing path",
                    source_type="document",
                )
            )
        except ValueError as exc:
            check(
                "requires metadata path or paths"
                in str(exc),
                "unexpected missing-path error",
            )

            print(
                "[PASS] missing document path blocked"
            )
        else:
            raise AssertionError(
                "missing document path was not blocked"
            )

        # ---------------------------------------------------------
        # Missing document
        # ---------------------------------------------------------

        missing_result = provider.acquire(
            AcquisitionRequest(
                query="missing document",
                source_type="document",
                metadata={
                    "path": "notes/not-found.txt",
                },
            )
        )

        check(
            missing_result.completed is False,
            "missing document unexpectedly completed",
        )

        check(
            missing_result.status == "failed",
            "missing document should produce failed acquisition",
        )

        check(
            any(
                "document not found"
                in error
                for error in missing_result.metadata[
                    "errors"
                ]
            ),
            "missing document error was not recorded",
        )

        print(
            "[PASS] missing document blocked"
        )

        # ---------------------------------------------------------
        # Source limit
        # ---------------------------------------------------------

        limited_provider = LocalDocumentResearchProvider(
            DocumentProviderConfig(
                project_root=root,
                max_sources=1,
            )
        )

        limited_result = limited_provider.acquire(
            AcquisitionRequest(
                query="source limit",
                source_type="document",
                max_sources=10,
                metadata={
                    "paths": [
                        "notes/sample.txt",
                        "notes/second.md",
                    ],
                },
            )
        )

        check(
            limited_result.completed is True,
            "source limit acquisition failed",
        )

        check(
            len(limited_result.sources) == 1,
            "provider source limit was not enforced",
        )

        print(
            "[PASS] source limit enforced"
        )

        # ---------------------------------------------------------
        # File size limit
        # ---------------------------------------------------------

        (root / "large.txt").write_text(
            "0123456789",
            encoding="utf-8",
        )

        small_provider = LocalDocumentResearchProvider(
            DocumentProviderConfig(
                project_root=root,
                max_file_size=5,
            )
        )

        large_result = small_provider.acquire(
            AcquisitionRequest(
                query="large document",
                source_type="document",
                metadata={
                    "path": "large.txt",
                },
            )
        )

        check(
            large_result.completed is False,
            "oversized document unexpectedly completed",
        )

        check(
            large_result.status == "failed",
            "oversized document should produce failed acquisition",
        )

        check(
            any(
                "document exceeds maximum allowed size"
                in error
                for error in large_result.metadata[
                    "errors"
                ]
            ),
            "file size error was not recorded",
        )

        print(
            "[PASS] file size limit enforced"
        )

        # ---------------------------------------------------------
        # Final result
        # ---------------------------------------------------------

        print()
        print(
            "SAHIBEX DOCUMENT PROVIDER TEST: PASS"
        )


if __name__ == "__main__":
    main()
