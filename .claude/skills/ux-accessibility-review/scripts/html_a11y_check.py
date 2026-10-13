#!/usr/bin/env python3
"""Static accessibility and form-pattern checks for an HTML page (stdlib html.parser).

Checks are derived from the library's GOV.UK Design System extract (rules flagged
testable_in_static_html), plus a few library-baseline checks (LOCAL-*) such as html lang and img
alt. Every finding carries `source_rule` (GDS-* from sources/extracts/gov-design-rules.json, or
LOCAL-*) and `wcag` where the extract cites a success criterion (LOCAL rules give a WCAG pointer
marked "(unverified)").

Usage:
  html_a11y_check.py page.html [--strict] [--json]
Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors, 2 unreadable input.

Scope: static markup checks only. They cannot judge focus management, keyboard operability,
screen-reader announcements, colour contrast, zoom/reflow, timing or whether content makes sense;
they never replace testing with assistive technologies and with disabled users.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

# rule slug -> (source_rule, wcag reference or None, severity)
RULES: dict[str, tuple[str, str | None, str]] = {
    "input-unlabelled": ("GDS-INP-01", None, "error"),
    "label-trailing-colon": ("GDS-INP-01", None, "warning"),
    "label-asterisk": ("GDS-QP-03", None, "warning"),
    "placeholder-as-label": ("GDS-INP-02", "WCAG 2.2 SC 1.4.3", "error"),
    "placeholder-present": ("GDS-INP-02", "WCAG 2.2 SC 1.4.3", "warning"),
    "options-not-in-fieldset": ("GDS-OPT-01", None, "error"),
    "fieldset-legend-not-first": ("GDS-OPT-01", None, "error"),
    "option-preselected": ("GDS-OPT-02", None, "warning"),
    "error-not-associated": ("GDS-ERR-09", None, "error"),
    "error-prefix-missing": ("GDS-ERR-09", None, "warning"),
    "error-summary-missing": ("GDS-ERR-01", None, "error"),
    "error-summary-heading": ("GDS-ERR-02", None, "warning"),
    "error-summary-position": ("GDS-ERR-04", None, "error"),
    "summary-link-broken": ("GDS-ERR-03", None, "error"),
    "summary-link-missing": ("GDS-ERR-03", None, "error"),
    "summary-text-mismatch": ("GDS-ERR-06", None, "warning"),
    "title-error-prefix": ("GDS-ERR-07", None, "error"),
    "error-wording-banned": ("GDS-ERR-11", None, "warning"),
    "error-wording-generic": ("GDS-ERR-12", None, "warning"),
    "autocomplete-missing": ("GDS-AC-01", "WCAG 2.2 SC 1.3.5", "error"),
    "autocomplete-unexpected": ("GDS-AC-01", "WCAG 2.2 SC 1.3.5", "warning"),
    "email-input-type": ("GDS-AC-03", None, "warning"),
    "spellcheck-not-disabled": ("GDS-INP-06", None, "warning"),
    "button-disabled": ("GDS-BTN-02", None, "warning"),
    "continue-button-next": ("GDS-QP-05", None, "warning"),
    "date-not-in-fieldset": ("GDS-DATE-01", None, "error"),
    "date-native-input": ("GDS-DATE-01", None, "warning"),
    "date-incomplete": ("GDS-DATE-01", None, "warning"),
    "form-novalidate-missing": ("GDS-VAL-01", None, "warning"),
    "required-attribute": ("GDS-VAL-01", None, "warning"),
    "maxlength-used": ("GDS-INP-05", None, "warning"),
    "number-input-type": ("GDS-INP-03", None, "warning"),
    "paste-blocked": ("GDS-INP-04", None, "error"),
    "range-slider": ("GDS-QP-08", "WCAG 2.2 SC 2.5.1", "warning"),
    "html-lang-missing": ("LOCAL-LANG-01", "WCAG 2.2 SC 3.1.1 (unverified)", "error"),
    "title-missing": ("LOCAL-TITLE-01", "WCAG 2.2 SC 2.4.2 (unverified)", "error"),
    "img-alt-missing": ("LOCAL-IMG-01", "WCAG 2.2 SC 1.1.1 (unverified)", "error"),
    "aria-ref-broken": ("LOCAL-ARIA-01", None, "error"),
    "duplicate-id": ("LOCAL-ID-01", None, "error"),
    "empty-document": ("LOCAL-DOC-01", None, "error"),
}
# Autocomplete purposes: purpose -> (specific GDS rule, accepted tokens)
PURPOSES = {
    "name": ("GDS-AC-02", {"name"}),
    "given-name": ("GDS-AC-02", {"given-name"}),
    "family-name": ("GDS-AC-02", {"family-name"}),
    "additional-name": ("GDS-NAME-01", {"additional-name"}),
    "email": ("GDS-AC-03", {"email"}),
    "tel": ("GDS-AC-04", {"tel", "tel-national", "tel-local", "mobile tel", "home tel", "work tel"}),
    "bday-day": ("GDS-AC-05", {"bday-day"}),
    "bday-month": ("GDS-AC-05", {"bday-month"}),
    "bday-year": ("GDS-AC-05", {"bday-year"}),
    "address": ("GDS-AC-06", {"street-address", "address-line1", "address-line2", "address-line3",
                              "address-level1", "address-level2", "address-level3", "postal-code",
                              "country", "country-name"}),
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CONTROLS = {"input", "select", "textarea"}
NON_LABELLED_INPUTS = {"hidden", "submit", "button", "image", "reset"}
TEXTLIKE = {"", "text", "email", "tel", "search", "url"}
BANNED = ["please", "sorry", "invalid", "valid", "oops", "forbidden", "illegal", "you forgot", "prohibited"]
GENERIC = ["an error occurred", "this field is required", "field is required", "error occurred"]
NOT_PERSON = {"dog", "pet", "user", "username", "business", "company", "file", "account"}


class Node:
    __slots__ = ("tag", "attrs", "parent", "children", "content", "line", "order")

    def __init__(self, tag: str, attrs: dict, parent: "Node | None", line: int, order: int):
        self.tag, self.attrs, self.parent, self.line, self.order = tag, attrs, parent, line, order
        self.children: list[Node] = []
        self.content: list = []  # text strings and child nodes in document order

    def text(self) -> str:
        parts = [c if isinstance(c, str) else c.text() for c in self.content]
        return " ".join(" ".join(parts).split())

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent

    def descendants(self):
        for c in self.children:
            yield c
            yield from c.descendants()

    def label(self) -> str:
        i = self.attrs.get("id")
        return f"{self.tag}#{i}" if i else f"{self.tag}@line{self.line}"


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None, 0, 0)
        self.stack = [self.root]
        self.nodes: list[Node] = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1],
                    self.getpos()[0], len(self.nodes) + 1)
        self.stack[-1].children.append(node)
        self.stack[-1].content.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].content.append(data)


def _tokens(*values: str) -> list[str]:
    return [t for v in values for t in re.split(r"[^a-z0-9]+", (v or "").lower()) if t]


def field_purpose(node: Node) -> str | None:
    """Infer the input purpose from type, then name, then id."""
    for key in ("name", "id"):
        purpose = _purpose(node.attrs.get("type", "").lower(), _tokens(node.attrs.get(key, "")))
        if purpose:
            return purpose
    return None


def _purpose(typ: str, toks: list[str]) -> str | None:
    tset = set(toks)
    if typ == "email" or "email" in tset:
        return "email"
    if typ == "tel" or tset & {"phone", "tel", "telephone", "mobile"}:
        return "tel"
    if tset & {"dob", "birth", "bday"}:
        for part in ("day", "month", "year"):
            if part in tset:
                return f"bday-{part}"
    if tset & NOT_PERSON:
        return None
    if tset & {"given", "first", "forename", "forenames"}:
        return "given-name"
    if tset & {"family", "last", "surname"}:
        return "family-name"
    if "middle" in tset:
        return "additional-name"
    if toks in (["name"], ["full", "name"], ["fullname"]):
        return "name"
    if tset & {"address", "postcode", "town", "city", "county", "street"}:
        return "address"
    return None


def check_html(text: str) -> list[dict]:
    findings: list[dict] = []

    def add(rule: str, where: str, message: str, **extra):
        src, wcag, sev = RULES[rule]
        f = {"id": where, "severity": sev, "rule": rule, "message": message, "source_rule": src, "wcag": wcag}
        f.update(extra)
        findings.append(f)

    if not text.strip():
        add("empty-document", "document", "document is empty")
        return findings
    tb = TreeBuilder()
    tb.feed(text)
    tb.close()
    nodes = tb.nodes
    ids = Counter(n.attrs["id"] for n in nodes if n.attrs.get("id"))
    by_id = {n.attrs["id"]: n for n in nodes if n.attrs.get("id")}
    for i, c in ids.items():
        if c > 1:
            add("duplicate-id", f"#{i}", f"id '{i}' used {c} times; labels and links become ambiguous")

    html = next((n for n in nodes if n.tag == "html"), None)
    if html is None or not html.attrs.get("lang", "").strip():
        add("html-lang-missing", "html", "<html> has no lang attribute")
    title_node = next((n for n in nodes if n.tag == "title"), None)
    title = title_node.text() if title_node else ""
    if not title:
        add("title-missing", "title", "page has no <title>")
    for n in nodes:
        if n.tag == "img" and "alt" not in n.attrs:
            add("img-alt-missing", n.label(), "img has no alt attribute (use alt=\"\" if decorative)")
        for attr in ("aria-describedby", "aria-labelledby"):
            for ref in n.attrs.get(attr, "").split():
                if ref not in by_id:
                    add("aria-ref-broken", n.label(), f"{attr} references missing id '{ref}'")

    labels_for = {n.attrs.get("for"): n for n in nodes if n.tag == "label" and n.attrs.get("for")}
    controls = [n for n in nodes if n.tag in CONTROLS
                and n.attrs.get("type", "").lower() not in NON_LABELLED_INPUTS]

    def label_of(n: Node) -> Node | None:
        if n.attrs.get("id") in labels_for:
            return labels_for[n.attrs["id"]]
        return next((a for a in n.ancestors() if a.tag == "label"), None)

    for n in controls:
        typ = n.attrs.get("type", "").lower()
        lab = label_of(n)
        has_aria = bool(n.attrs.get("aria-label", "").strip()) or any(
            r in by_id for r in n.attrs.get("aria-labelledby", "").split())
        labelled = (lab is not None and lab.text()) or has_aria
        if "placeholder" in n.attrs:
            if not labelled:
                add("placeholder-as-label", n.label(), "placeholder used instead of a label")
            else:
                add("placeholder-present", n.label(), "avoid placeholder text; use a label and hint")
        elif not labelled:
            add("input-unlabelled", n.label(), "form control has no associated label (label for=, wrapping label, aria-label or aria-labelledby)")
        if lab is not None and lab.text():
            lt = lab.text()
            if "*" in lt:
                add("label-asterisk", n.label(), "do not mark mandatory fields with asterisks; mark optional ones '(optional)'")
            if lt.rstrip().endswith(":"):
                add("label-trailing-colon", n.label(), "label ends with a colon")
        if "required" in n.attrs:
            add("required-attribute", n.label(), "remove the required attribute; validate server side and show GOV.UK-style errors")
        if "maxlength" in n.attrs:
            add("maxlength-used", n.label(), "avoid maxlength; state limits in hint text and validate after entry")
        if typ == "number":
            add("number-input-type", n.label(), "avoid type=number; use inputmode=numeric")
        if typ == "range":
            add("range-slider", n.label(), "range sliders need a non-drag alternative")
        if re.search(r"return\s+false|preventDefault", n.attrs.get("onpaste", "")):
            add("paste-blocked", n.label(), "pasting is blocked")
        if typ == "date":
            add("date-native-input", n.label(), "use three text fields (day, month, year) in a fieldset rather than type=date")
        if n.tag in ("input", "textarea") and typ in TEXTLIKE:
            purpose = field_purpose(n)
            if purpose:
                rule_id, accepted = PURPOSES[purpose]
                ac = " ".join(n.attrs.get("autocomplete", "").lower().split())
                if not ac or ac in ("off", "on"):
                    add("autocomplete-missing", n.label(),
                        f"{purpose} field needs autocomplete (expected one of {sorted(accepted)})", related_rule=rule_id)
                elif ac not in accepted and ac.split()[-1] not in accepted:
                    add("autocomplete-unexpected", n.label(),
                        f"autocomplete '{ac}' unexpected for a {purpose} field (expected {sorted(accepted)})", related_rule=rule_id)
                if purpose == "email" and typ != "email":
                    add("email-input-type", n.label(), "email fields should use type=email")
                if purpose in ("email", "name", "given-name", "family-name", "additional-name") \
                        and n.attrs.get("spellcheck", "").lower() != "false":
                    add("spellcheck-not-disabled", n.label(), "set spellcheck=false on name and email fields")

    # radios / checkboxes grouped in a fieldset with a first-child legend
    groups: dict[tuple[str, str], list[Node]] = {}
    for n in controls:
        typ = n.attrs.get("type", "").lower()
        if typ in ("radio", "checkbox"):
            groups.setdefault((typ, n.attrs.get("name", "")), []).append(n)
    for (typ, name), members in groups.items():
        if typ == "checkbox" and len(members) < 2:
            continue
        fs = next((a for a in members[0].ancestors() if a.tag == "fieldset"), None)
        legend_ok = fs is not None and any(c.tag == "legend" and c.text() for c in fs.children)
        if not legend_ok:
            add("options-not-in-fieldset", f"{typ}[name={name}]", f"{typ} group is not in a fieldset with a legend")
    for fs in (n for n in nodes if n.tag == "fieldset"):
        if fs.children and fs.children[0].tag != "legend":
            add("fieldset-legend-not-first", fs.label(), "legend must be the first element inside the fieldset")
        elif not fs.children:
            add("fieldset-legend-not-first", fs.label(), "fieldset has no legend")

    # date input pattern
    date_parts: dict[str, dict[str, Node]] = {}
    for n in controls:
        key = n.attrs.get("name") or n.attrs.get("id") or ""
        m = re.match(r"^(.*?)[-_\[](day|month|year)\]?$", key, re.I)
        if m and m.group(1) and n.attrs.get("type", "text").lower() in TEXTLIKE:
            date_parts.setdefault(m.group(1).rstrip("-_["), {})[m.group(2).lower()] = n
    for base, parts in date_parts.items():
        first = next(iter(parts.values()))
        if not any(a.tag == "fieldset" for a in first.ancestors()):
            add("date-not-in-fieldset", base, "date parts must be grouped in a fieldset with a legend")
        if set(parts) != {"day", "month", "year"}:
            add("date-incomplete", base, f"date input has parts {sorted(parts)}; use day, month and year")

    # buttons
    for n in nodes:
        is_button = n.tag == "button" or (n.tag == "input" and n.attrs.get("type", "").lower() in ("submit", "button"))
        if not is_button:
            continue
        label = n.text() if n.tag == "button" else n.attrs.get("value", "")
        if "disabled" in n.attrs:
            add("button-disabled", n.label(), "avoid disabled buttons unless research supports them")
        if label.strip().lower() == "next":
            add("continue-button-next", n.label(), "use 'Continue' rather than 'Next'")
    for form in (n for n in nodes if n.tag == "form"):
        if "novalidate" not in form.attrs:
            add("form-novalidate-missing", form.label(), "add novalidate to turn off browser validation")

    # errors
    err_msgs = [n for n in nodes if n.classes() & {"govuk-error-message", "error-message"}]
    invalid = [n for n in controls if n.attrs.get("aria-invalid", "").lower() == "true"]
    error_state = bool(err_msgs or invalid)
    if not error_state:
        for n in controls:
            if n.attrs.get("type", "").lower() in ("radio", "checkbox") and "checked" in n.attrs:
                add("option-preselected", n.label(), "do not pre-select options on a fresh page")
        return findings

    describedby: dict[str, list[Node]] = {}
    for n in nodes:
        for ref in n.attrs.get("aria-describedby", "").split():
            describedby.setdefault(ref, []).append(n)

    def strip_prefix(s: str) -> str:
        return re.sub(r"^\s*error\s*:\s*", "", s, flags=re.I).strip()

    expected_targets: list[tuple[Node, set[str]]] = []
    for m in err_msgs:
        mid = m.attrs.get("id")
        txt = m.text()
        if not re.match(r"^\s*error\s*:", txt, re.I):
            add("error-prefix-missing", m.label(), "inline error should start with a visually hidden 'Error:' prefix")
        refs = describedby.get(mid, []) if mid else []
        if not refs:
            add("error-not-associated", m.label(), "error message is not referenced by aria-describedby on its field or fieldset")
        targets: set[str] = set()
        for r in refs:
            if r.tag == "fieldset":
                targets |= {d.attrs["id"] for d in r.descendants() if d.tag in CONTROLS and d.attrs.get("id")}
            elif r.attrs.get("id"):
                targets.add(r.attrs["id"])
        expected_targets.append((m, targets))
        low = strip_prefix(txt).lower()
        banned = [w for w in BANNED if re.search(rf"\b{re.escape(w)}\b", low)]
        if banned:
            add("error-wording-banned", m.label(), f"error wording uses {banned}")
        if any(g in low for g in GENERIC):
            add("error-wording-generic", m.label(), "generic error; say what is wrong and how to fix it")

    summary = next((n for n in nodes if "govuk-error-summary" in n.classes() or n.attrs.get("role") == "alert"), None)
    if not title.startswith("Error: "):
        add("title-error-prefix", "title", "page with errors: <title> must start with 'Error: '")
    if summary is None:
        add("error-summary-missing", "document", "errors present but no error summary (class govuk-error-summary or role=alert)")
        return findings
    heading = next((d for d in summary.descendants() if re.fullmatch(r"h[1-6]", d.tag)), None)
    if heading is None or heading.text() != "There is a problem":
        add("error-summary-heading", summary.label(), "error summary heading should read 'There is a problem'")
    h1 = next((n for n in nodes if n.tag == "h1"), None)
    if h1 is not None and h1.order < summary.order:
        add("error-summary-position", summary.label(), "error summary must come before the h1 (top of main)")
    links = [d for d in summary.descendants() if d.tag == "a"]
    linked: dict[str, str] = {}
    for a in links:
        href = a.attrs.get("href", "")
        if href.startswith("#"):
            target = href[1:]
            if target not in by_id:
                add("summary-link-broken", f"a[href={href}]", f"summary link targets missing id '{target}'")
            linked[target] = a.text()
    for m, targets in expected_targets:
        if not targets:
            continue
        hit = targets & set(linked)
        if not hit:
            add("summary-link-missing", m.label(), f"no error-summary link to the field in error (expected #{sorted(targets)[0]})")
        else:
            if strip_prefix(m.text()) != linked[sorted(hit)[0]].strip():
                add("summary-text-mismatch", m.label(), "summary link text differs from the inline error message")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Static accessibility/form-pattern checks for HTML.")
    ap.add_argument("html", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        text = args.html.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read {args.html}: {exc}", file=sys.stderr)
        return 2
    findings = check_html(text)
    sev = Counter(f["severity"] for f in findings)
    summary = {"errors": sev.get("error", 0), "warnings": sev.get("warning", 0),
               "source_rules": sorted({f["source_rule"] for f in findings}),
               "manual_checks_required": True}
    failed = summary["errors"] > 0 or (args.strict and summary["warnings"] > 0)
    out = {"findings": findings, "summary": summary, "passed": not failed}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for f in findings:
            w = f" [{f['wcag']}]" if f["wcag"] else ""
            print(f"{f['severity'].upper():8} {f['id']:<24} {f['rule']:<26} {f['source_rule']:<14} {f['message']}{w}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {summary['errors']} errors, {summary['warnings']} warnings")
        print("Scope: static markup checks only; does not replace keyboard, screen-reader, zoom, contrast "
              "and real-user testing (see references/manual-checks.md).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
