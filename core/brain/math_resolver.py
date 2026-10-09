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
        return MathResponse(answer=f"उत्तर: {rendered}", expression=expression)
    return None
