"""Structured assurance cases (claims - arguments - evidence).

    python -m agentlib assurance-case template > case.yaml
    python -m agentlib assurance-case check case.yaml [--strict]
    python -m agentlib assurance-case render case.yaml > case.md

Case format (YAML or JSON)::

    case:
      id: AC-PAY-01
      title: Payments API is acceptably secure for release 2.3
      scope: payments-api commit a1b2c3d, production configuration
      decision_authority: Head of Security Assurance
    claims:
      - id: C1
        text: The payments API is acceptably secure for release.
        criticality: high            # low | medium | high  -> minimum evidence strength E2 / E2 / E3
        argument: Decomposed by ASVS chapter in scope and by the SSDF process that produced it.
        subclaims: [C1.1, C1.2]
      - id: C1.1
        text: Authentication meets ASVS L2 V6.
        criticality: high
        frameworks: ["V6.2.1", "V6.3.1"]   # identifiers are checked against the catalogs
        evidence: [EV-1, EV-2]
      - id: C1.2
        text: Residual risk from third-party components is accepted.
        status: undeveloped
        justification: SCA results pending; tracked as action A-7.
    evidence:
      - id: EV-1
        description: ASVS V6 verification report
        artefact: reports/asvs-v6.md      # path (checked if --base given) or URL
        strength: E3                     # E0-E4, see the evidence-and-citation skill
        method: Test

Checks: unique ids; exactly one root claim; subclaims exist; no cycles; every claim reachable from the root;
every leaf claim is either supported by evidence or explicitly ``undeveloped`` with a justification;
evidence ids exist; evidence strength meets the claim's criticality; framework identifiers exist in the
catalogs (via the evidence checker); optional artefact paths exist. An assurance case structures an
argument for a decision-maker; it does not itself establish that a claim is true.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from agentlib.frameworks import evidence as ev

STRENGTH = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}
MIN_STRENGTH = {"low": 2, "medium": 2, "high": 3}
STATUSES = {"developed", "undeveloped"}


class CaseError(ValueError):
    pass


@dataclass
class Finding:
    level: str
    where: str
    message: str


def load(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text) if str(path).endswith(".json") else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise CaseError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise CaseError("an assurance case needs a 'claims' list")
    if not isinstance(data.get("evidence", []), list):
        raise CaseError("'evidence' must be a list")
    for key in ("claims", "evidence"):
        for entry in data.get(key, []):
            if not isinstance(entry, dict) or "id" not in entry:
                raise CaseError(f"every {key} entry must be a mapping with an 'id'")
    return data


def _as_list(value) -> list:
    if value is None:
        return []
    return [value] if isinstance(value, (str, int)) else list(value)


def check(case: dict, base: Path | None = None, root: Path | None = None) -> list[Finding]:
    out: list[Finding] = []
    claims = case["claims"]
    evidence = case.get("evidence", [])
    cids = [str(c["id"]) for c in claims]
    eids = [str(e["id"]) for e in evidence]
    for kind, ids in (("claim", cids), ("evidence", eids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        for d in dupes:
            out.append(Finding("error", d, f"duplicate {kind} id"))
    by_id = {str(c["id"]): c for c in claims}
    ev_by_id = {str(e["id"]): e for e in evidence}
    meta = case.get("case") or {}
    for key in ("title", "scope", "decision_authority"):
        if not meta.get(key):
            out.append(Finding("warning", "case", f"missing case.{key}"))

    children: dict[str, list[str]] = {}
    referenced: set[str] = set()
    for c in claims:
        cid = str(c["id"])
        if not str(c.get("text", "")).strip():
            out.append(Finding("error", cid, "claim has no text"))
        subs = [str(s) for s in _as_list(c.get("subclaims"))]
        children[cid] = subs
        for s in subs:
            if s not in by_id:
                out.append(Finding("error", cid, f"subclaim '{s}' does not exist"))
            referenced.add(s)
        crit = str(c.get("criticality", "medium")).lower()
        if crit not in MIN_STRENGTH:
            out.append(Finding("error", cid, f"criticality must be one of {sorted(MIN_STRENGTH)}"))
            crit = "medium"
        status = str(c.get("status", "developed")).lower()
        if status not in STATUSES:
            out.append(Finding("error", cid, f"status must be one of {sorted(STATUSES)}"))
        evs = [str(e) for e in _as_list(c.get("evidence"))]
        for e in evs:
            if e not in ev_by_id:
                out.append(Finding("error", cid, f"evidence '{e}' does not exist"))
        if subs and not str(c.get("argument", "")).strip():
            out.append(Finding("warning", cid, "claim is decomposed but states no argument (why the subclaims suffice)"))
        if status == "undeveloped":
            if not str(c.get("justification", "")).strip():
                out.append(Finding("error", cid, "undeveloped claim needs a justification"))
            else:
                out.append(Finding("warning", cid, "undeveloped claim: the case is incomplete here"))
        elif not subs:
            if not evs:
                out.append(Finding("error", cid, "leaf claim has no evidence and is not marked undeveloped"))
            else:
                best = max((STRENGTH.get(str(ev_by_id[e].get("strength", "E0")).upper(), 0) for e in evs if e in ev_by_id), default=0)
                if best < MIN_STRENGTH[crit]:
                    out.append(Finding("error", cid, f"{crit}-criticality claim needs evidence of strength >= E{MIN_STRENGTH[crit]} (best is E{best})"))
        for ident in _as_list(c.get("frameworks")):
            for f in ev.check_document(str(ident), root):
                if f.level == "error":
                    out.append(Finding("error", cid, f.message))
    roots = [cid for cid in cids if cid not in referenced]
    if len(roots) != 1:
        out.append(Finding("error", "case", f"expected exactly one root claim, found {len(roots)}: {roots}"))
    # cycles and reachability
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        state[node] = 1
        for nxt in children.get(node, []):
            if nxt not in by_id:
                continue
            if state.get(nxt) == 1:
                out.append(Finding("error", node, f"cycle: {' -> '.join(stack + [node, nxt])}"))
            elif nxt not in state:
                visit(nxt, stack + [node])
        state[node] = 2

    for r in roots:
        visit(r, [])
    unreachable = [cid for cid in cids if cid not in state]
    for cid in unreachable:
        out.append(Finding("error", cid, "claim is not reachable from the root"))
    for cid in unreachable:  # still detect cycles among claims no root reaches
        if cid not in state:
            visit(cid, [])
    used = {str(e) for c in claims for e in _as_list(c.get("evidence"))}
    for e in evidence:
        eid = str(e["id"])
        s = str(e.get("strength", "")).upper()
        if s not in STRENGTH:
            out.append(Finding("error", eid, "evidence strength must be E0-E4"))
        if not str(e.get("artefact", "")).strip():
            out.append(Finding("error", eid, "evidence names no artefact"))
        elif base is not None and "://" not in str(e["artefact"]) and not (base / str(e["artefact"])).exists():
            out.append(Finding("error", eid, f"artefact not found: {e['artefact']}"))
        if eid not in used:
            out.append(Finding("warning", eid, "evidence is not used by any claim"))
    return out


def summary(case: dict, findings: list[Finding]) -> dict:
    claims = case["claims"]
    undeveloped = [str(c["id"]) for c in claims if str(c.get("status", "")).lower() == "undeveloped"]
    errors = [f for f in findings if f.level == "error"]
    return {"claims": len(claims), "evidence": len(case.get("evidence", [])), "undeveloped": undeveloped,
            "errors": len(errors), "warnings": len(findings) - len(errors),
            "verdict": "invalid" if errors else ("incomplete" if undeveloped else "complete")}


def render(case: dict) -> str:
    by_id = {str(c["id"]): c for c in case["claims"]}
    ev_by_id = {str(e["id"]): e for e in case.get("evidence", [])}
    referenced = {str(s) for c in case["claims"] for s in _as_list(c.get("subclaims"))}
    meta = case.get("case") or {}
    lines = [f"# Assurance case {meta.get('id', '')}: {meta.get('title', '')}".rstrip(": "), ""]
    for key, label in (("scope", "Scope"), ("decision_authority", "Decision authority")):
        if meta.get(key):
            lines.append(f"- **{label}:** {meta[key]}")
    lines += ["", "## Argument", ""]

    def walk(cid: str, depth: int, seen: set[str]) -> None:
        if cid in seen or cid not in by_id:
            return
        seen = seen | {cid}
        c = by_id[cid]
        pad = "  " * depth
        tag = " **[UNDEVELOPED]**" if str(c.get("status", "")).lower() == "undeveloped" else ""
        lines.append(f"{pad}- **{cid}** ({c.get('criticality', 'medium')}): {c.get('text', '')}{tag}")
        if c.get("argument"):
            lines.append(f"{pad}  - *Argument:* {c['argument']}")
        if c.get("justification"):
            lines.append(f"{pad}  - *Justification:* {c['justification']}")
        for e in _as_list(c.get("evidence")):
            item = ev_by_id.get(str(e), {})
            lines.append(f"{pad}  - Evidence {e} [{item.get('strength', '?')}]: {item.get('description', '')} ({item.get('artefact', '')})")
        for s in _as_list(c.get("subclaims")):
            walk(str(s), depth + 1, seen)

    for cid in [str(c["id"]) for c in case["claims"] if str(c["id"]) not in referenced]:
        walk(cid, 0, set())
    lines += ["", "## Evidence register", "", "| ID | Description | Artefact | Method | Strength |", "|---|---|---|---|---|"]
    for e in case.get("evidence", []):
        lines.append(f"| {e['id']} | {e.get('description', '')} | {e.get('artefact', '')} | {e.get('method', '')} | {e.get('strength', '')} |")
    lines += ["", "_This case structures an argument for the decision authority; it does not by itself establish "
              "that the top claim is true._", ""]
    return "\n".join(lines)


TEMPLATE = """case:
  id: AC-001
  title: <system> is acceptable for <decision>
  scope: <artefacts, versions, environment>
  decision_authority: <accountable role>
claims:
  - id: C1
    text: <top claim>
    criticality: high
    argument: <why the subclaims together support the top claim>
    subclaims: [C1.1, C1.2]
  - id: C1.1
    text: <subclaim supported directly by evidence>
    criticality: high
    frameworks: []
    evidence: [EV-1]
  - id: C1.2
    text: <subclaim not yet supported>
    status: undeveloped
    justification: <why, and the action that will close it>
evidence:
  - id: EV-1
    description: <what it is>
    artefact: <path or URL>
    method: Test
    strength: E3
"""


# ------------------------------------------------------------------ grader
def grade_case(output: str, check_spec: dict) -> tuple[bool, str]:
    """Eval grader: the first ```yaml block in the output is a valid case (no errors)."""
    import re

    m = re.search(r"```ya?ml\s*\n(.*?)```", output, re.S)
    if not m:
        return False, "no ```yaml block"
    try:
        data = yaml.safe_load(m.group(1))
        if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
            return False, "yaml block is not an assurance case"
        findings = check(data)
    except (yaml.YAMLError, CaseError, KeyError, TypeError) as exc:
        return False, f"invalid case: {exc}"
    errors = [f for f in findings if f.level == "error"]
    return not errors, f"{len(errors)} error(s): {[f.message for f in errors][:4]}"


# ------------------------------------------------------------------ CLI
def _cmd_template(args) -> int:
    print(TEMPLATE, end="")
    return 0


def _cmd_check(args) -> int:
    try:
        case = load(Path(args.file))
    except (CaseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    base = Path(args.base) if args.base else None
    findings = check(case, base)
    summ = summary(case, findings)
    if args.format == "json":
        print(json.dumps({"summary": summ, "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        print(f"Assurance case: {summ['claims']} claims, {summ['evidence']} evidence items; verdict: {summ['verdict'].upper()}")
        for f in findings:
            print(f"  {f.level.upper():7} {f.where}: {f.message}")
    if summ["errors"] or (args.strict and findings):
        return 1
    return 0


def _cmd_render(args) -> int:
    try:
        print(render(load(Path(args.file))))
    except (CaseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def register(sub) -> None:
    p = sub.add_parser("assurance-case", help="check and render claims-arguments-evidence assurance cases")
    s = p.add_subparsers(dest="ac_cmd", required=True)
    s.add_parser("template", help="print a starter case").set_defaults(func=_cmd_template)
    c = s.add_parser("check", help="validate a case (exit 1 on errors, 2 on unreadable input)")
    c.add_argument("file")
    c.add_argument("--base", help="directory against which artefact paths are checked")
    c.add_argument("--strict", action="store_true", help="warnings (incl. undeveloped claims) also fail")
    c.add_argument("--format", choices=["text", "json"], default="text")
    c.set_defaults(func=_cmd_check)
    r = s.add_parser("render", help="render the case as Markdown")
    r.add_argument("file")
    r.set_defaults(func=_cmd_render)
