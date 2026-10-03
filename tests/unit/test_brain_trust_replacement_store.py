from pathlib import Path
from tempfile import TemporaryDirectory

from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def make_record(
    previous_provenance: str = "old-proof",
    replacement_provenance: str = "new-proof",
) -> dict[str, str]:
    return {
        "brain_id": "brain-001",
        "previous_provenance": previous_provenance,
        "replacement_provenance": replacement_provenance,
        "reason": "Evidence replacement after review.",
        "provenance": "replacement-auth-proof",
    }


def test_append_and_read_replacement_record() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        record = make_record()

        store.append(record)

        records = store.read_recent()

        assert records == [record]


def test_history_is_append_only() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        first = make_record(
            previous_provenance="proof-001",
            replacement_provenance="proof-002",
        )

        second = make_record(
            previous_provenance="proof-002",
            replacement_provenance="proof-003",
        )

        store.append(first)
        store.append(second)

        records = store.read_recent()

        assert records == [first, second]
        assert len(records) == 2


def test_missing_required_field_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        record = make_record()
        record.pop("reason")

        try:
            store.append(record)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Missing required field was accepted."
            )


def test_same_previous_and_replacement_are_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        record = make_record(
            previous_provenance="same-proof",
            replacement_provenance="same-proof",
        )

        try:
            store.append(record)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Identical replacement evidence was accepted."
            )


def test_empty_history_returns_empty_list() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        assert store.read_recent() == []


def test_invalid_limit_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustReplacementStore(
            Path(temp_dir)
        )

        try:
            store.read_recent(0)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Invalid limit was accepted."
            )


def run_all_tests() -> None:
    test_append_and_read_replacement_record()
    test_history_is_append_only()
    test_missing_required_field_is_rejected()
    test_same_previous_and_replacement_are_rejected()
    test_empty_history_returns_empty_list()
    test_invalid_limit_is_rejected()

    print(
        "SAHIBEX 6P-27 REPLACEMENT STORE "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
