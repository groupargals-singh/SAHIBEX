from core.research.research_plan import (
    ResearchPlan,
    ResearchStep,
)


def main() -> None:
    print("SAHIBEX RESEARCH PLAN TEST")

    # ---------------------------------------------------------
    # 1. Step creation
    # ---------------------------------------------------------
    step_one = ResearchStep(
        step_id="step-001",
        description="Collect primary research sources",
        source_types=["web", "document"],
    )

    assert step_one.step_id == "step-001"
    assert step_one.description == (
        "Collect primary research sources"
    )
    assert step_one.source_types == [
        "web",
        "document",
    ]
    assert step_one.required is True

    print("[PASS] research step creation")

    # ---------------------------------------------------------
    # 2. Optional step
    # ---------------------------------------------------------
    step_two = ResearchStep(
        step_id="step-002",
        description="Collect supplementary sources",
        source_types=["rss"],
        required=False,
    )

    assert step_two.required is False

    print("[PASS] optional step")

    # ---------------------------------------------------------
    # 3. Plan creation
    # ---------------------------------------------------------
    plan = ResearchPlan(
        plan_id="plan-test-001",
        job_id="job-test-001",
        objective="Research SAHIBEX architecture",
        steps=[
            step_one,
            step_two,
        ],
        metadata={
            "test": True,
        },
    )

    assert plan.plan_id == "plan-test-001"
    assert plan.job_id == "job-test-001"
    assert plan.objective == (
        "Research SAHIBEX architecture"
    )
    assert plan.step_count == 2

    print("[PASS] research plan creation")

    # ---------------------------------------------------------
    # 4. Required / optional separation
    # ---------------------------------------------------------
    assert len(plan.required_steps) == 1
    assert plan.required_steps[0].step_id == "step-001"

    assert len(plan.optional_steps) == 1
    assert plan.optional_steps[0].step_id == "step-002"

    print("[PASS] required/optional steps")

    # ---------------------------------------------------------
    # 5. Step lookup
    # ---------------------------------------------------------
    found_step = plan.get_step("step-002")

    assert found_step.step_id == "step-002"
    assert found_step.required is False

    print("[PASS] step lookup")

    # ---------------------------------------------------------
    # 6. Unknown step protection
    # ---------------------------------------------------------
    try:
        plan.get_step("unknown-step")
    except KeyError:
        pass
    else:
        raise AssertionError(
            "unknown step must raise KeyError"
        )

    print("[PASS] unknown step protection")

    # ---------------------------------------------------------
    # 7. Duplicate step IDs
    # ---------------------------------------------------------
    try:
        ResearchPlan(
            plan_id="plan-test-002",
            job_id="job-test-001",
            objective="Duplicate step test",
            steps=[
                ResearchStep(
                    step_id="duplicate",
                    description="First step",
                ),
                ResearchStep(
                    step_id="duplicate",
                    description="Second step",
                ),
            ],
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "duplicate step IDs must be rejected"
        )

    print("[PASS] duplicate step protection")

    # ---------------------------------------------------------
    # 8. Empty plan protection
    # ---------------------------------------------------------
    try:
        ResearchPlan(
            plan_id="plan-test-003",
            job_id="job-test-001",
            objective="Empty plan test",
            steps=[],
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty research plan must be rejected"
        )

    print("[PASS] empty plan protection")

    # ---------------------------------------------------------
    # 9. Invalid step object protection
    # ---------------------------------------------------------
    try:
        ResearchPlan(
            plan_id="plan-test-004",
            job_id="job-test-001",
            objective="Invalid step test",
            steps=["not-a-research-step"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "invalid step objects must be rejected"
        )

    print("[PASS] invalid step protection")

    # ---------------------------------------------------------
    # 10. Input validation
    # ---------------------------------------------------------
    try:
        ResearchStep(
            step_id="",
            description="Valid description",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank step_id must be rejected"
        )

    try:
        ResearchStep(
            step_id="valid",
            description="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank description must be rejected"
        )

    try:
        ResearchPlan(
            plan_id="",
            job_id="job-test-001",
            objective="Valid objective",
            steps=[step_one],
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank plan_id must be rejected"
        )

    try:
        ResearchPlan(
            plan_id="plan-test-005",
            job_id="",
            objective="Valid objective",
            steps=[step_one],
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank job_id must be rejected"
        )

    print("[PASS] input validation")

    # ---------------------------------------------------------
    # 11. Frozen contract
    # ---------------------------------------------------------
    try:
        step_one.step_id = "changed"
    except Exception:
        pass
    else:
        raise AssertionError(
            "ResearchStep must be immutable"
        )

    try:
        plan.plan_id = "changed"
    except Exception:
        pass
    else:
        raise AssertionError(
            "ResearchPlan must be immutable"
        )

    print("[PASS] immutable contract")

    # ---------------------------------------------------------
    # 12. Snapshot
    # ---------------------------------------------------------
    snapshot = plan.snapshot()

    assert snapshot["plan_id"] == "plan-test-001"
    assert snapshot["job_id"] == "job-test-001"
    assert snapshot["objective"] == (
        "Research SAHIBEX architecture"
    )
    assert snapshot["step_count"] == 2
    assert len(snapshot["steps"]) == 2
    assert snapshot["steps"][0]["step_id"] == "step-001"
    assert snapshot["steps"][1]["step_id"] == "step-002"
    assert snapshot["steps"][1]["required"] is False
    assert snapshot["metadata"]["test"] is True

    print("[PASS] plan snapshot")

    print("SAHIBEX RESEARCH PLAN TEST: PASS")


if __name__ == "__main__":
    main()
