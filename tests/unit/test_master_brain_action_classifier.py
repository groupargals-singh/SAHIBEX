from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.master_brain import MasterBrain
from core.brain.action_classifier import ActionClassifier
from core.policies.approval import ActionType
from core.policies.constitution import ActionClass


def test_protected_action_keywords_have_matching_confidence():
    brain = MasterBrain()
    cases = [
        ("delete the file", ActionType.DELETE_FILE, ActionClass.DELETE),
        ("execute command", ActionType.RUN_COMMAND, ActionClass.EXECUTE),
        ("use this api key", ActionType.CREDENTIAL_USE, ActionClass.CREDENTIAL),
        ("transfer money", ActionType.FINANCIAL_ACTION, ActionClass.FINANCIAL),
        ("change system configuration", ActionType.SYSTEM_CHANGE, ActionClass.SYSTEM_CHANGE),
        ("download the report", ActionType.NETWORK_ACCESS, ActionClass.NETWORK),
        ("write file", ActionType.WRITE_FILE, ActionClass.WRITE),
        ("इस फाइल को डिलीट करो", ActionType.DELETE_FILE, ActionClass.DELETE),
        ("file delete karo", ActionType.DELETE_FILE, ActionClass.DELETE),
        ("सिस्टम की सेटिंग बदलो", ActionType.SYSTEM_CHANGE, ActionClass.SYSTEM_CHANGE),
        ("system settings badal do", ActionType.SYSTEM_CHANGE, ActionClass.SYSTEM_CHANGE),
        ("कमांड चलाओ", ActionType.RUN_COMMAND, ActionClass.EXECUTE),
        ("command chalao", ActionType.RUN_COMMAND, ActionClass.EXECUTE),
        ("नेटवर्क से कनेक्ट करो", ActionType.NETWORK_ACCESS, ActionClass.NETWORK),
        ("network se connect karo", ActionType.NETWORK_ACCESS, ActionClass.NETWORK),
        ("फाइल में बदलाव करो", ActionType.WRITE_FILE, ActionClass.WRITE),
        ("file likh do", ActionType.WRITE_FILE, ActionClass.WRITE),
        ("पासवर्ड दिखाओ", ActionType.CREDENTIAL_USE, ActionClass.CREDENTIAL),
        ("पैसे भेजो", ActionType.FINANCIAL_ACTION, ActionClass.FINANCIAL),
    ]
    for text, expected_action, expected_class in cases:
        action, action_class = brain._classify_action(text, "general_request")
        assert action is expected_action
        assert action_class is expected_class
        assert brain._action_confidence(text, action) >= 0.85


def test_master_brain_blocks_hindi_protected_actions_without_confirmation():
    cases = (
        "इस फाइल को डिलीट करो",
        "सिस्टम की सेटिंग बदलो",
        "कमांड चलाओ",
        "नेटवर्क से कनेक्ट करो",
        "फाइल में बदलाव करो",
        "पासवर्ड दिखाओ",
        "पैसे भेजो",
    )
    protected_actions = {
        "delete_file",
        "system_change",
        "run_command",
        "network_access",
        "write_file",
        "credential_use",
        "financial_action",
    }
    for text in cases:
        result = MasterBrain().process(text, user_confirmation=False)
        assert result.action in protected_actions, (text, result)
        assert result.success is False, (text, result)
        assert result.permission_allowed is False, (text, result)
        assert result.confirmation_required is True, (text, result)
        assert result.verification_status == "NOT_EXECUTED", (text, result)


def test_secondary_action_classifier_recognizes_hindi_protected_actions():
    classifier = ActionClassifier()
    cases = {
        "इस फाइल को डिलीट करो": ActionType.DELETE_FILE,
        "फाइल में बदलाव करो": ActionType.WRITE_FILE,
        "कमांड चलाओ": ActionType.RUN_COMMAND,
        "सिस्टम की सेटिंग बदलो": ActionType.SYSTEM_CHANGE,
        "नेटवर्क से कनेक्ट करो": ActionType.NETWORK_ACCESS,
        "पासवर्ड दिखाओ": ActionType.CREDENTIAL_USE,
        "पैसे भेजो": ActionType.FINANCIAL_ACTION,
    }
    for text, expected_action in cases.items():
        result = classifier.classify(text)
        assert result.action is expected_action, (text, result)


def test_self_update_keywords_get_high_confidence_and_protected_class():
    brain = MasterBrain()
    for text in ("self update", "self-update", "update yourself", "modify yourself", "rewrite yourself"):
        action, action_class = brain._classify_action(text, "general_request")
        assert action is ActionType.SYSTEM_CHANGE
        assert action_class is ActionClass.SELF_UPDATE
        assert brain._action_confidence(text, action) >= 0.85


def test_protected_keyword_registry_is_shared_and_nonempty():
    brain = MasterBrain()
    assert set(brain.PROTECTED_ACTION_KEYWORDS) == {
        ActionType.DELETE_FILE,
        ActionType.RUN_COMMAND,
        ActionType.CREDENTIAL_USE,
        ActionType.FINANCIAL_ACTION,
        ActionType.SYSTEM_CHANGE,
        ActionType.NETWORK_ACCESS,
        ActionType.WRITE_FILE,
    }
    assert all(keywords for keywords in brain.PROTECTED_ACTION_KEYWORDS.values())
