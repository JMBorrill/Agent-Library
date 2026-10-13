"""Minimal YAML front-matter parser for Markdown files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class FrontMatterError(ValueError):
    pass


def split(text: str) -> tuple[dict[str, Any], str]:
    """Split ``text`` into (front-matter dict, body).

    Raises ``FrontMatterError`` when the document has no valid front matter.
    """
    if not text.startswith("---"):
        raise FrontMatterError("missing opening '---' front-matter delimiter")
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        raise FrontMatterError("front-matter delimiter must be on its own line")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            raw = "".join(lines[1:idx])
            body = "".join(lines[idx + 1 :])
            try:
                data = yaml.safe_load(raw) or {}
            except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
                raise FrontMatterError(f"invalid YAML front matter: {exc}") from exc
            if not isinstance(data, dict):
                raise FrontMatterError("front matter must be a mapping")
            return data, body
    raise FrontMatterError("missing closing '---' front-matter delimiter")


def load(path: Path) -> tuple[dict[str, Any], str]:
    return split(path.read_text(encoding="utf-8"))
