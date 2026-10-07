from core.brain.perception import (
    PerceptionParser,
    PerceptionResult,
)


def main() -> None:
    parser = PerceptionParser()

    result = parser.parse(
        input_id="input-001",
        content="Create a new Python program.",
    )

    assert isinstance(result, PerceptionResult)
    assert result.input_id == "input-001"
    assert result.content == "Create a new Python program."
    assert "create" in result.actions
    assert "new" in result.attributes
    assert "python" in result.objects
    assert "program" in result.objects

    event = parser.parse(
        input_id="input-002",
        content="The system failed and stopped.",
    )

    assert "failed" in event.events
    assert "stopped" in event.events

    normalized = parser.parse(
        input_id=" input-003 ",
        content="  Search   the   latest   AI   research. ",
    )

    assert normalized.input_id == "input-003"
    assert normalized.content == (
        "Search the latest AI research."
    )
    assert "search" in normalized.actions
    assert "latest" in normalized.attributes

    # Empty input must fail closed.
    try:
        parser.parse(
            input_id="input-004",
            content="   ",
        )
        raise AssertionError(
            "empty content was accepted"
        )
    except ValueError:
        pass

    # Empty identity must fail closed.
    try:
        parser.parse(
            input_id="   ",
            content="test input",
        )
        raise AssertionError(
            "empty input_id was accepted"
        )
    except ValueError:
        pass

    # Security / authority boundaries.
    assert parser.is_read_only() is True
    assert parser.grants_permission() is False
    assert parser.executes_actions() is False
    assert parser.verifies_truth() is False

    print(
        "SAHIBEX PHASE 1 #27 PERCEPTION PARSING TEST: PASS"
    )


if __name__ == "__main__":
    main()
