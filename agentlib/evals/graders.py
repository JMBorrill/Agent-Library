"""Deterministic graders used by evaluation suites.

Check types
-----------
``contains``       all ``values`` appear (case-insensitive unless ``case_sensitive: true``)
``any_of``         at least ``min`` (default 1) of ``values`` appear
``not_contains``   none of ``values`` appear
``regex``          ``pattern`` matches (``re.M | re.I``); ``count`` sets a minimum number of matches
``sections``       every heading in ``values`` exists as a Markdown heading (any level)
``cites``          each of ``values`` appears; intended for source IDs / clause IDs
``ids``            at least ``min`` distinct identifiers matching ``pattern`` appear
``json_block``     a fenced ```json block parses; optional ``required_keys`` must be present
``table``          at least one Markdown table with all ``columns`` in its header row
``max_words``      response length is at most ``value`` words
``min_words``      response length is at least ``value`` words
``python``         call ``function`` ("pkg.module:func") with (output, check) -> (bool, str)

A grader returns a :class:`CheckResult`. Graders never call a model: they
are cheap, repeatable and suitable for CI. Model-graded rubrics can be layered
on top in live mode, but deterministic checks remain the gate.
"""
from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class CheckResult:
    type: str
    passed: bool
    detail: str


def _norm(text: str, case_sensitive: bool) -> str:
    return text if case_sensitive else text.lower()


class _Check:
    required: tuple[str, ...] = ()

    @classmethod
    def validate(cls, chk: dict) -> None:
        for key in cls.required:
            if key not in chk:
                raise KeyError(f"missing '{key}'")

    @classmethod
    def run(cls, output: str, chk: dict) -> CheckResult:  # pragma: no cover - abstract
        raise NotImplementedError


class Contains(_Check):
    required = ("values",)

    @classmethod
    def run(cls, output, chk):
        cs = chk.get("case_sensitive", False)
        hay = _norm(output, cs)
        missing = [v for v in chk["values"] if _norm(str(v), cs) not in hay]
        return CheckResult("contains", not missing, f"missing: {missing}" if missing else "all present")


class AnyOf(_Check):
    required = ("values",)

    @classmethod
    def run(cls, output, chk):
        hay = output.lower()
        found = [v for v in chk["values"] if str(v).lower() in hay]
        need = int(chk.get("min", 1))
        return CheckResult("any_of", len(found) >= need, f"found {len(found)}/{need}: {found}")


class NotContains(_Check):
    required = ("values",)

    @classmethod
    def run(cls, output, chk):
        hay = output.lower()
        found = [v for v in chk["values"] if str(v).lower() in hay]
        return CheckResult("not_contains", not found, f"forbidden present: {found}" if found else "none present")


class Regex(_Check):
    required = ("pattern",)

    @classmethod
    def validate(cls, chk):
        super().validate(chk)
        re.compile(chk["pattern"])

    @classmethod
    def run(cls, output, chk):
        matches = re.findall(chk["pattern"], output, re.M | re.I)
        need = int(chk.get("count", 1))
        return CheckResult("regex", len(matches) >= need, f"{len(matches)} match(es) of /{chk['pattern']}/ (need {need})")


class Sections(_Check):
    required = ("values",)

    @classmethod
    def run(cls, output, chk):
        heads = [h.strip().lower() for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", output, re.M)]
        missing = [v for v in chk["values"] if not any(str(v).lower() in h for h in heads)]
        return CheckResult("sections", not missing, f"missing headings: {missing}" if missing else "all headings present")


class Cites(Contains):
    @classmethod
    def run(cls, output, chk):
        r = super().run(output, {**chk, "case_sensitive": chk.get("case_sensitive", False)})
        return CheckResult("cites", r.passed, r.detail)


class Ids(_Check):
    required = ("pattern",)

    @classmethod
    def validate(cls, chk):
        super().validate(chk)
        re.compile(chk["pattern"])

    @classmethod
    def run(cls, output, chk):
        found = set(re.findall(chk["pattern"], output))
        need = int(chk.get("min", 1))
        return CheckResult("ids", len(found) >= need, f"{len(found)} distinct ids (need {need})")


class JsonBlock(_Check):
    @classmethod
    def run(cls, output, chk):
        blocks = re.findall(r"```json\s*\n(.*?)```", output, re.S)
        if not blocks:
            return CheckResult("json_block", False, "no ```json block found")
        errors = []
        for block in blocks:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON: {exc}")
                continue
            keys = chk.get("required_keys", [])
            if isinstance(data, dict):
                missing = [k for k in keys if k not in data]
                if not missing:
                    return CheckResult("json_block", True, "valid JSON with required keys")
                errors.append(f"missing keys {missing}")
            elif not keys:
                return CheckResult("json_block", True, "valid JSON")
            else:
                errors.append("JSON is not an object")
        return CheckResult("json_block", False, "; ".join(errors))


class Table(_Check):
    required = ("columns",)

    @classmethod
    def run(cls, output, chk):
        want = [c.lower() for c in chk["columns"]]
        for line in output.splitlines():
            if line.strip().startswith("|"):
                cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
                if all(any(w in c for c in cells) for w in want):
                    return CheckResult("table", True, "table header found")
        return CheckResult("table", False, f"no table with columns {chk['columns']}")


class MaxWords(_Check):
    required = ("value",)

    @classmethod
    def run(cls, output, chk):
        n = len(output.split())
        return CheckResult("max_words", n <= int(chk["value"]), f"{n} words (max {chk['value']})")


class MinWords(_Check):
    required = ("value",)

    @classmethod
    def run(cls, output, chk):
        n = len(output.split())
        return CheckResult("min_words", n >= int(chk["value"]), f"{n} words (min {chk['value']})")


def _resolve(dotted: str) -> Callable:
    mod, _, fn = dotted.partition(":")
    if not fn:
        raise ValueError("function must be 'package.module:function'")
    return getattr(importlib.import_module(mod), fn)


class Python(_Check):
    required = ("function",)

    @classmethod
    def validate(cls, chk):
        super().validate(chk)
        _resolve(chk["function"])

    @classmethod
    def run(cls, output, chk):
        try:
            ok, detail = _resolve(chk["function"])(output, chk)
        except Exception as exc:  # grader bugs must surface as failures, not crashes
            return CheckResult("python", False, f"grader raised {type(exc).__name__}: {exc}")
        return CheckResult("python", bool(ok), str(detail))


CHECK_TYPES: dict[str, type[_Check]] = {
    "contains": Contains,
    "any_of": AnyOf,
    "not_contains": NotContains,
    "regex": Regex,
    "sections": Sections,
    "cites": Cites,
    "ids": Ids,
    "json_block": JsonBlock,
    "table": Table,
    "max_words": MaxWords,
    "min_words": MinWords,
    "python": Python,
}


def grade(output: str, checks: list[dict]) -> list[CheckResult]:
    return [CHECK_TYPES[c["type"]].run(output, c) for c in checks]
