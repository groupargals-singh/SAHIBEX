from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UIElement:
    index: int
    class_name: str
    text: str
    content_description: str
    clickable: bool
    editable: bool
    enabled: bool
    bounds: tuple[int, int, int, int]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def flatten_ui_tree(tree: list[dict[str, Any]]) -> list[UIElement]:
    """Convert an Android accessibility tree into searchable UI elements."""
    if not isinstance(tree, list):
        raise TypeError("tree must be a list")
    out: list[UIElement] = []
    stack = list(reversed(tree))
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        raw = node.get("bounds", [0, 0, 0, 0])
        if not isinstance(raw, list) or len(raw) != 4:
            raw = [0, 0, 0, 0]
        try:
            bounds = tuple(int(v) for v in raw)
        except (TypeError, ValueError):
            bounds = (0, 0, 0, 0)
        out.append(UIElement(
            index=len(out),
            class_name=_text(node.get("class")),
            text=_text(node.get("text")),
            content_description=_text(node.get("contentDescription")),
            clickable=bool(node.get("clickable", False)),
            editable=bool(node.get("editable", False)),
            enabled=bool(node.get("enabled", False)),
            bounds=bounds,
        ))
        children = node.get("children", [])
        if isinstance(children, list):
            stack.extend(reversed(children))
    return out


def find_elements(
    tree: list[dict[str, Any]],
    *,
    text: str | None = None,
    content_description: str | None = None,
    clickable: bool | None = None,
    editable: bool | None = None,
) -> list[UIElement]:
    elements = flatten_ui_tree(tree)
    needle_text = text.casefold() if text is not None else None
    needle_desc = content_description.casefold() if content_description is not None else None
    return [e for e in elements
            if (needle_text is None or needle_text in e.text.casefold())
            and (needle_desc is None or needle_desc in e.content_description.casefold())
            and (clickable is None or e.clickable is clickable)
            and (editable is None or e.editable is editable)]
