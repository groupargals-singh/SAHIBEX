"""Safe deterministic arithmetic for basic text questions; never uses eval."""
from __future__ import annotations
import ast
import operator
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class MathResponse:
    answer: str
    expression: str

_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def _calculate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        if abs(node.value) > 10**12:
            raise ValueError("number_out_of_range")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left, right = _calculate(node.left), _calculate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("exponent_out_of_range")
        value = _BINOPS[type(node.op)](left, right)
        if abs(value) > 10**15:
            raise ValueError("result_out_of_range")
        return value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_calculate(node.operand))
    raise ValueError("unsupported_expression")

def resolve_math_question(question: str) -> MathResponse | None:
    """Resolve a plainly written arithmetic expression with numeric digits."""
    if not isinstance(question, str) or not question.strip() or len(question) > 300:
        return None
    text = question.replace("×", "*").replace("÷", "/").replace("−", "-").strip()
    # Normalize narrowly recognized spoken arithmetic before the strict parser.
    # Only single arithmetic forms are rewritten; arbitrary prose is not executed.
    text = re.sub(r"\bplus\b", "+", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*(?:reply\s+briefly|briefly\s+answer|please\s+answer)\s*[:,-]?\s*", "", text, flags=re.IGNORECASE)
    hindi_digits = {"शून्य": "0", "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पाँच": "5", "पांच": "5", "छह": "6", "सात": "7", "आठ": "8", "नौ": "9", "दस": "10"}
    spoken_hindi = re.fullmatch(
        r"\s*(?:हिंदी\s+में\s+)?(?:संक्षेप\s+में\s+)?(?:बताओ\s*[:：]?\s*)?(शून्य|एक|दो|तीन|चार|पाँच|पांच|छह|सात|आठ|नौ|दस)\s+और\s+(शून्य|एक|दो|तीन|चार|पाँच|पांच|छह|सात|आठ|नौ|दस)\s*(?:(?:कितना|कितने)\s+)?(?:(?:होता|होते)\s+)?(?:है|हैं)?[?।.!]?\s*",
        text, flags=re.IGNORECASE,
    )
    if spoken_hindi:
        text = f"{hindi_digits[spoken_hindi.group(1)]} + {hindi_digits[spoken_hindi.group(2)]}"
    # Strip only clearly marked response-format instructions. The arithmetic
    # expression still has to pass the strict token allow-list below.
    format_suffixes = (
        r"\s+answer\s+(?:with\s+)?only\s+(?:the\s+)?number\.?$",
        r"\s+give\s+only\s+(?:the\s+)?number\.?$",
        r"\s+केवल\s+संख्या\s+में\s+उत्तर\s+दें[.!।]?$",
        r"\s+सिर्फ\s+संख्या\s+में\s+जवाब\s+दें[.!।]?$",
    )
    for suffix in format_suffixes:
        text = re.sub(suffix, "", text, flags=re.IGNORECASE).strip()
    allowed_words = {
        "कितना", "है", "होता", "होगा", "बताओ", "बताइए", "जोड़", "योग",
        "उत्तर", "निकालो", "गणना", "करो", "का", "क्या", "हैं",
        "what", "is", "the", "sum", "of", "calculate", "please",
        "equals", "answer", "result", "how", "much",
        # Common Roman-script Hindi/Hinglish question words. Keep this list
        # narrow so unrelated prose still fails closed.
        "kitna", "kitne", "kitni", "hai", "hain", "hota", "hote",
        "batao", "bataiye", "jodo", "jod", "yog", "ka", "kya",
    }
    words = re.findall(r"[A-Za-z]+|[\u0900-\u097F]+", text.casefold())
    if any(word not in allowed_words for word in words):
        return None
    for match in re.finditer(r"(?<![\w.])[0-9(][0-9\s().+*/%\-]*", text):
        expression = match.group(0).strip()
        if not expression or not re.search(r"[+*/%\-]", expression) or len(expression) > 100:
            continue
        try:
            value = _calculate(ast.parse(expression, mode="eval").body)
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            continue
        rendered = f"{value:.10g}" if isinstance(value, float) and not value.is_integer() else str(int(value))
        answer = f"उत्तर: {rendered}" if re.search(r"[\u0900-\u097F]", question) else f"Answer: {rendered}"
        return MathResponse(answer=answer, expression=expression)
    return None
