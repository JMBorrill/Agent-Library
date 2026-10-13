"""Strict parser for the YAML frontmatter subset used by SKILL.md and agent files.

Supported (deliberately small, so files stay portable across YAML parsers):
  key: scalar                 plain, 'single' or "double" quoted
  key:                        followed by an indented block of either
    sub: scalar               -> mapping of string scalars
    - item                    -> list of string scalars
  key: [a, b]                 -> flow list of plain scalars
Comments (# ...) on their own line and blank lines are ignored.

Block scalars (| or >), anchors, nested structures and multi-document streams are rejected
with a FrontmatterError so authors get a precise message instead of a silent misparse.
"""
from __future__ import annotations

import re

_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")


class FrontmatterError(ValueError):
    pass


def split(text: str) -> tuple[str, str]:
    """Return (frontmatter_text, body). The opening '---' must be the first line."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise FrontmatterError("file must start with '---' on the first line")
    lines = text.splitlines(keepends=True)
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            return "".join(lines[1:i]), "".join(lines[i + 1:])
    raise FrontmatterError("closing '---' not found")


def _scalar(raw: str, lineno: int) -> str:
    raw = raw.strip()
    if raw[:1] in ("|", ">"):
        raise FrontmatterError(f"line {lineno}: block scalars (| or >) are not supported; use one line")
    if raw[:1] in ("&", "*", "!"):
        raise FrontmatterError(f"line {lineno}: anchors/aliases/tags are not supported")
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if raw[:1] in ('"', "'"):
        raise FrontmatterError(f"line {lineno}: unterminated quoted string")
    # strip trailing comment ' #...'
    m = re.search(r"\s#", raw)
    if m:
        raw = raw[: m.start()].rstrip()
    if raw.startswith("{"):
        raise FrontmatterError(f"line {lineno}: flow mappings are not supported")
    if ": " in raw:
        raise FrontmatterError(f"line {lineno}: unquoted value contains ': ' — quote the value")
    return raw


def parse(fm: str) -> dict:
    data: dict = {}
    current_key = None
    lines = fm.splitlines()
    for idx, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise FrontmatterError(f"line {idx}: tabs are not allowed for indentation")
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            m = _KEY.match(stripped)
            if not m:
                raise FrontmatterError(f"line {idx}: expected 'key: value', got {stripped!r}")
            key, value = m.group(1), m.group(2)
            if key in data:
                raise FrontmatterError(f"line {idx}: duplicate key {key!r}")
            if value is None or value.strip() == "":
                data[key] = None  # block follows
                current_key = key
            elif value.strip().startswith("["):
                v = value.strip()
                if not v.endswith("]"):
                    raise FrontmatterError(f"line {idx}: unterminated flow list")
                inner = v[1:-1].strip()
                data[key] = [_scalar(x, idx) for x in inner.split(",")] if inner else []
                current_key = None
            else:
                data[key] = _scalar(value, idx)
                current_key = None
            continue
        if current_key is None:
            raise FrontmatterError(f"line {idx}: unexpected indentation")
        block = data[current_key]
        if stripped.startswith("- ") or stripped == "-":
            if isinstance(block, dict):
                raise FrontmatterError(f"line {idx}: cannot mix list and mapping under {current_key!r}")
            if block is None:
                block = data[current_key] = []
            item = stripped[1:].strip()
            if not item:
                raise FrontmatterError(f"line {idx}: empty list item")
            block.append(_scalar(item, idx))
        else:
            m = _KEY.match(stripped)
            if not m or m.group(2) is None:
                raise FrontmatterError(f"line {idx}: expected 'sub: value' under {current_key!r}")
            if isinstance(block, list):
                raise FrontmatterError(f"line {idx}: cannot mix list and mapping under {current_key!r}")
            if block is None:
                block = data[current_key] = {}
            if m.group(1) in block:
                raise FrontmatterError(f"line {idx}: duplicate key {m.group(1)!r}")
            block[m.group(1)] = _scalar(m.group(2), idx)
    for k, v in data.items():
        if v is None:
            raise FrontmatterError(f"key {k!r} has no value")
    return data


def load(text: str) -> tuple[dict, str]:
    fm, body = split(text)
    return parse(fm), body
