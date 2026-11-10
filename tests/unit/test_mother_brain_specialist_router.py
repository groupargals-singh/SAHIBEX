from core.brain.mother_brain_specialist_router import MotherBrainSpecialistRouter
from core.brain.master_brain import MasterBrain


def test_router_selects_math_for_hinglish_arithmetic():
    route = MotherBrainSpecialistRouter().select("2 + 2 kitna hota hai?", "general_request")
    assert route is not None
    assert route.role_id == "math"
    assert route.context["expression"] == "2 + 2 kitna hota hai?"


def test_router_selects_teaching_for_explicit_learning_intent():
    route = MotherBrainSpecialistRouter().select("Mujhe Python sikhao", "learn")
    assert route is not None
    assert route.role_id == "teaching"
    assert route.context["topic"] == "Mujhe Python sikhao"


def test_router_selects_language_only_for_explicit_language_detection_request():
    route = MotherBrainSpecialistRouter().select("Detect language of hello", "general_request")
    assert route is not None
    assert route.role_id == "language"
    assert route.context["text"] == "Detect language of hello"


def test_router_does_not_claim_translation_capability():
    assert MotherBrainSpecialistRouter().select("Translate hello to Hindi", "general_request") is None


def test_router_does_not_misroute_numeric_dates_as_arithmetic():
    assert MotherBrainSpecialistRouter().select("My appointment is on 12/11/2026", "general_request") is None


def test_router_does_not_fan_out_or_guess_on_generic_chat():
    router = MotherBrainSpecialistRouter()
    assert router.select("Namaste Sahibex", "general_request") is None
    assert router.select("Please help me", "general_request") is None


def test_router_rejects_empty_or_invalid_input():
    router = MotherBrainSpecialistRouter()
    assert router.select("", "general_request") is None
    assert router.select("hello", None) is None


def test_selected_language_role_dispatches_through_mother_brain():
    brain = MasterBrain()
    route = brain.specialist_router.select("Detect language of hello", "general_request")
    assert route is not None and route.role_id == "language"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "Detect language of hello", route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["success"] is True
    assert dispatched.result["translation_performed"] is False


def test_selected_teaching_role_dispatches_through_mother_brain():
    brain = MasterBrain()
    route = brain.specialist_router.select("Mujhe Python sikhao", "learn")
    assert route is not None and route.role_id == "teaching"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "Mujhe Python sikhao", route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["success"] is True
    assert dispatched.result["external_research_performed"] is False
