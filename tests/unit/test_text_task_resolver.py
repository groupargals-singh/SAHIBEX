import ast
import re

from core.brain.master_brain import MasterBrain
from core.brain.text_task_resolver import resolve_text_task


def test_known_text_tasks_are_resolved_without_model():
    brain = MasterBrain()
    water = brain.process("पानी क्यों जरूरी है?")
    code = brain.process("एक साधारण Python प्रोग्राम लिखो जो दो संख्याएँ जोड़ता है")
    assert water.success
    assert water.metadata["response_source"] == "deterministic_text_task"
    assert "तापमान नियंत्रित" in water.message
    assert code.success
    assert code.metadata["response_source"] == "deterministic_text_task"
    assert "a + b" in code.message


def test_generated_python_snippet_is_syntactically_valid():
    result = resolve_text_task("write a simple python program to add two numbers")
    assert result is not None
    match = re.search(r"```python\n(.*?)\n```", result.answer, flags=re.S)
    assert match is not None
    ast.parse(match.group(1))


def test_compound_requests_are_not_answered_partially():
    assert resolve_text_task("पानी क्यों जरूरी है और कितनी मात्रा पीनी चाहिए?") is None
