from core.research.acquisition import AcquiredSource
from core.research.acquisition_validator import AcquisitionSafetyValidator


def valid_source(**overrides):
    data = {
        "source_id": "src_001",
        "title": "Test Source",
        "source_type": "web",
        "locator": "https://example.com",
        "content": "This is valid test content.",
        "publisher": "Test Publisher",
        "author": "Test Author",
        "metadata": {},
    }
    data.update(overrides)
    return AcquiredSource(**data)


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main():
    validator = AcquisitionSafetyValidator()

    print("SAHIBEX ACQUISITION VALIDATOR TEST")

    # 1. Valid acquisition
    source = valid_source()
    result = validator.validate(source)

    check(
        result.valid,
        "valid acquisition accepted",
    )

    # 2. require_valid()
    validator.require_valid(source)

    print("[PASS] valid acquisition passes require_valid")

    # 3. Empty content
    source = valid_source(content="")
    result = validator.validate(source)

    check(
        not result.valid,
        "empty content rejected",
    )

    # 4. Oversized content
    validator_small = AcquisitionSafetyValidator(
        max_content_length=10,
    )

    source = valid_source(
        content="This content is definitely longer than ten characters."
    )

    result = validator_small.validate(source)

    check(
        not result.valid,
        "oversized content rejected",
    )

    # 5. Empty title
    # AcquiredSource itself rejects empty title.
    try:
        AcquiredSource(
            source_id="src_empty_title",
            title="",
            source_type="web",
            locator="https://example.com",
            content="valid content",
        )
        raise AssertionError("empty title should be rejected")
    except ValueError:
        print("[PASS] empty title rejected")

    # 6. Oversized title
    validator_title = AcquisitionSafetyValidator(
        max_title_length=10,
    )

    source = valid_source(
        title="This title is much longer than ten characters."
    )

    result = validator_title.validate(source)

    check(
        not result.valid,
        "oversized title rejected",
    )

    # 7. Invalid web locator
    source = valid_source(
        locator="ftp://example.com",
    )

    result = validator.validate(source)

    check(
        not result.valid,
        "invalid web locator rejected",
    )

    # 8. Invalid API locator
    source = valid_source(
        source_type="api",
        locator="example.com/api",
    )

    result = validator.validate(source)

    check(
        not result.valid,
        "invalid API locator rejected",
    )

    # 9. Invalid RSS locator
    source = valid_source(
        source_type="rss",
        locator="example.com/feed.xml",
    )

    result = validator.validate(source)

    check(
        not result.valid,
        "invalid RSS locator rejected",
    )

    # 10. HTTP accepted
    source = valid_source(
        locator="http://example.com",
    )

    result = validator.validate(source)

    check(
        result.valid,
        "HTTP locator accepted",
    )

    # 11. HTTPS accepted
    source = valid_source(
        locator="https://example.com",
    )

    result = validator.validate(source)

    check(
        result.valid,
        "HTTPS locator accepted",
    )

    # 12. Unknown source type produces warning
    source = valid_source(
        source_type="custom_source",
        locator="custom://example",
    )

    result = validator.validate(source)

    check(
        result.valid,
        "unknown source type accepted with warning",
    )

    check(
        len(result.warnings) > 0,
        "unknown source type warning generated",
    )

    # 13. Metadata dict accepted
    source = valid_source(
        metadata={
            "test": True,
            "provider": "unit-test",
        },
    )

    result = validator.validate(source)

    check(
        result.valid,
        "metadata dictionary accepted",
    )

    # 14. Invalid object rejected
    result = validator.validate("not-an-acquired-source")

    check(
        not result.valid,
        "invalid object rejected",
    )

    # 15. require_valid() blocks invalid source
    invalid_source = valid_source(
        content="",
    )

    try:
        validator.require_valid(invalid_source)
        raise AssertionError(
            "require_valid should reject invalid source"
        )
    except ValueError:
        print("[PASS] require_valid blocks invalid source")

    # 16. Invalid constructor limit
    try:
        AcquisitionSafetyValidator(
            max_content_length=0,
        )
        raise AssertionError(
            "invalid validator limit should be rejected"
        )
    except ValueError:
        print("[PASS] invalid content limit rejected")

    # 17. Invalid title limit
    try:
        AcquisitionSafetyValidator(
            max_title_length=0,
        )
        raise AssertionError(
            "invalid title limit should be rejected"
        )
    except ValueError:
        print("[PASS] invalid title limit rejected")

    print()
    print("SAHIBEX ACQUISITION VALIDATOR TEST [PASS]")


if __name__ == "__main__":
    main()
