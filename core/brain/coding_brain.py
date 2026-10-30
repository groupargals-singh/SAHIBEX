"""Bounded Coding Brain for repository-aware code review.

This internal specialist analyzes supplied Python source without executing it,
installing packages, writing files, or changing SAHIBEX permissions.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class CodeFinding:
    severity: str
    code: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class CodeReview:
    success: bool
    language: str
    status: str
    lines: int
    imports: tuple[str, ...]
    functions: int
    classes: int
    findings: tuple[CodeFinding, ...]
    executes_code: bool = False
    writes_files: bool = False
    installs_packages: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["findings"] = [asdict(item) for item in self.findings]
        return result


class CodingBrain:
    """A deterministic first-pass coding specialist; not a substitute for tests."""

    MAX_SOURCE_CHARS = 200_000
    RISKY_CALLS = {
        "eval": "Dynamic eval can execute untrusted expressions.",
        "exec": "Dynamic exec can execute arbitrary code.",
        "os.system": "Shell execution needs explicit review and authorization.",
        "subprocess.Popen": "Process execution needs explicit review and authorization.",
        "subprocess.run": "Process execution needs explicit review and authorization.",
    }

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        parts: list[str] = []
        current = node
        while isinstance(current, (ast.Name, ast.Attribute)):
            if isinstance(current, ast.Name):
                parts.append(current.id)
                break
            parts.append(current.attr)
            current = current.value
        return ".".join(reversed(parts))

    def review_python(self, source: str) -> CodeReview:
        if not isinstance(source, str) or not source.strip():
            return CodeReview(False, "python", "SOURCE_REQUIRED", 0, (), 0, 0,
                              (CodeFinding("error", "SOURCE_REQUIRED", "Provide Python source text."),))
        if len(source) > self.MAX_SOURCE_CHARS:
            return CodeReview(False, "python", "SOURCE_TOO_LARGE", source.count("\n") + 1,
                              (), 0, 0, (CodeFinding("error", "SOURCE_TOO_LARGE",
                              f"Source exceeds the {self.MAX_SOURCE_CHARS}-character review limit."),))
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            finding = CodeFinding("error", "SYNTAX_ERROR", exc.msg, exc.lineno)
            return CodeReview(False, "python", "SYNTAX_ERROR", source.count("\n") + 1,
                              (), 0, 0, (finding,))

        imports: list[str] = []
        findings: list[CodeFinding] = []
        functions = classes = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append("." * node.level + (node.module or ""))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions += 1
            elif isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, ast.Call):
                name = self._call_name(node.func)
                if name in self.RISKY_CALLS:
                    findings.append(CodeFinding("warning", "REVIEW_REQUIRED",
                                                self.RISKY_CALLS[name], getattr(node, "lineno", None)))
                if name in {"pickle.load", "pickle.loads"}:
                    findings.append(CodeFinding("warning", "UNSAFE_DESERIALIZATION",
                                                "Untrusted pickle data can execute code.", getattr(node, "lineno", None)))
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(CodeFinding("warning", "BARE_EXCEPT",
                                            "Bare except can hide unexpected failures.", getattr(node, "lineno", None)))

        status = "REVIEW_REQUIRED" if findings else "STATIC_CHECK_PASSED"
        return CodeReview(True, "python", status, source.count("\n") + 1,
                          tuple(sorted(set(imports))), functions, classes, tuple(findings))

    def review_context(self, context: dict[str, Any]) -> dict[str, Any]:
        source = context.get("source_code")
        language = context.get("language", "python")
        if language != "python":
            return {
                "success": False, "status": "LANGUAGE_NOT_SUPPORTED_YET",
                "language": str(language), "supported_languages": ["python"],
                "executes_code": False, "writes_files": False, "installs_packages": False,
            }
        return self.review_python(source).to_dict()
