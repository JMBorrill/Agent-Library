#!/usr/bin/env python3
"""Select frameworks, packs, skills and agents for a project profile — with reasons and exclusions.

Input profile JSON (see assets/templates/project-profile.json):
  name, description, objectives[], stage (concept|mvp|beta|production), risk_class (low|moderate|high),
  jurisdiction, flags{hardware, software, ai, finance, lending, personal_data, multi_tenant, ui,
  external_users, physical_tests, safety_critical, regulated, decisions_about_individuals,
  online_service, payments, novel_technology, agentic_tools}
Matching uses explicit flags first, then whole-word keywords in name/description/objectives.

Output: selected packs (reason + matched triggers), excluded packs (reason), skills, agents (authors
and reviewers covering the skills), frameworks with access status, oversight level, required human
sign-offs, phased workflow, and a dry-run install command.

Usage: select_frameworks.py profile.json [--catalog catalog.json] [--rules routing-rules.json] [--markdown] [--json]
Exit: 0 selection produced, 1 profile errors (e.g. missing description or invalid enums), 2 unreadable.
Scope: a proposal for the project owner; it does not determine legal or regulatory applicability.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "assets" / "data"
RISK = {"low": 0, "moderate": 1, "high": 2}
STAGES = {"concept", "mvp", "beta", "production"}


def _f(rid, sev, rule, msg):
    return {"id": rid, "severity": sev, "rule": rule, "message": msg}


def _text(p: dict) -> str:
    return " ".join([p.get("name", ""), p.get("description", ""), " ".join(p.get("objectives", []))]).lower()


def _kw_hits(text: str, kws: list[str]) -> list[str]:
    return [k for k in kws if re.search(rf"(?<![a-z0-9]){re.escape(k.lower())}(?![a-z0-9])", text)]


def _cond(cond: dict, p: dict, text: str) -> tuple[bool, list[str]]:
    """Return (matched, triggers). Keys inside one condition are OR-ed except flags_all/jurisdiction_in (AND)."""
    flags = p.get("flags", {})
    triggers, any_hit = [], False
    if "flags_all" in cond:
        if not all(flags.get(x) for x in cond["flags_all"]):
            return False, []
        triggers += [f"flag:{x}" for x in cond["flags_all"]]
        any_hit = True
    if "jurisdiction_in" in cond:
        if p.get("jurisdiction", "").upper() not in {j.upper() for j in cond["jurisdiction_in"]}:
            return False, []
        triggers.append(f"jurisdiction:{p.get('jurisdiction')}")
        any_hit = True
    ors = []
    for x in cond.get("flags_any", []):
        if flags.get(x):
            ors.append(f"flag:{x}")
    if "risk_at_least" in cond and RISK.get(p.get("risk_class"), -1) >= RISK[cond["risk_at_least"]]:
        ors.append(f"risk:{p.get('risk_class')}")
    if "stage_in" in cond and p.get("stage") in cond["stage_in"]:
        ors.append(f"stage:{p.get('stage')}")
    ors += [f"keyword:{k}" for k in _kw_hits(text, cond.get("keywords", []))]
    has_or = any(k in cond for k in ("flags_any", "risk_at_least", "stage_in", "keywords"))
    if has_or and not ors:
        return False, []
    return (any_hit or bool(ors)), triggers + ors


def select(p: dict, catalog: dict, rules: dict) -> dict:
    f = []
    if not p.get("description"):
        f.append(_f("description", "error", "no-description", "describe the project objectives and technical scope"))
    if p.get("risk_class") not in RISK:
        f.append(_f("risk_class", "error", "risk-class", f"risk_class must be one of {sorted(RISK)}"))
    if p.get("stage") and p["stage"] not in STAGES:
        f.append(_f("stage", "error", "stage", f"stage must be one of {sorted(STAGES)}"))
    if any(x["severity"] == "error" for x in f):
        return {"findings": f}
    flags = p.setdefault("flags", {})
    text = _text(p)
    if flags.get("safety_critical"):
        flags.setdefault("physical_tests", flags.get("hardware", False))
    selected, excluded, skills = {}, {}, []
    for pack, rule in rules["packs"].items():
        if pack not in catalog["packs"]:
            continue
        if rule.get("always"):
            ok, trig = True, ["always"]
        else:
            ok, trig = _cond({k: rule[k] for k in ("flags_any", "risk_at_least", "keywords") if k in rule}, p, text)
        if not ok:
            excluded[pack] = rule.get("exclude_reason", "no trigger matched")
            continue
        chosen = [s for s in rule.get("skills_always", []) if s in catalog["skills"]]
        for s, cond in rule.get("skills_if", {}).items():
            if s in catalog["skills"] and _cond(cond, p, text)[0]:
                chosen.append(s)
        if not chosen:
            excluded[pack] = f"pack triggered ({', '.join(trig[:3])}) but no skill conditions matched"
            continue
        selected[pack] = {"reason": rule["reason"], "triggers": trig[:6], "skills": chosen}
        skills += [s for s in chosen if s not in skills]
    for pack, info in list(selected.items()):
        for req in catalog["packs"][pack].get("requires", []):
            if req not in selected:
                f.append(_f(pack, "warning", "pack-dependency", f"'{pack}' supplements '{req}', which was not selected — consider adding its core skills"))
    # agents: choose agents whose skill lists cover selected skills; prefer pack agents
    agents = {}
    for s in skills:
        cands = [a for a, info in catalog["agents"].items() if s in info["skills"]]
        authors = [a for a in cands if not catalog["agents"][a]["reviewer"]]
        reviewers = [a for a in cands if catalog["agents"][a]["reviewer"]]
        for a in (authors[:1] + reviewers[:1]):
            agents.setdefault(a, []).append(s)
    agents.setdefault("independent-reviewer", [])
    frameworks = sorted({src for s in skills for src in catalog["skills"][s]["sources"]})
    fw = [{"source_id": x, **{k: catalog["sources"][x][k] for k in ("title", "access_status", "normative_status")}}
          for x in frameworks if x in catalog["sources"]]
    # oversight
    high = flags.get("safety_critical") or flags.get("regulated") or p.get("risk_class") == "high" or \
        (flags.get("ai") and flags.get("decisions_about_individuals"))
    medium = p.get("risk_class") == "moderate" or flags.get("personal_data") or flags.get("multi_tenant") or flags.get("ai")
    oversight = "high" if high else "medium" if medium else "low"
    signoffs = ["Decision owner approves tailoring, baselines and gate decisions"]
    if flags.get("safety_critical") or flags.get("physical_tests"):
        signoffs.append("Qualified safety authority approves hazard analysis and authorises every physical test")
    if flags.get("regulated"):
        signoffs.append("Compliance officer / legal counsel confirms regulatory applicability and obligations")
    if flags.get("lending"):
        signoffs.append("Authorised lender staff make all credit decisions; the system only supports them")
    if flags.get("ai"):
        signoffs.append("Accountable owner approves AI deployment after independent evaluation review")
    if flags.get("personal_data"):
        signoffs.append("Data-protection lead approves personal-data processing and lawful basis")
    if any(x["severity"] == "warning" for x in f if x["rule"] == "pack-dependency"):
        pass
    workflow = []
    for step in rules["workflow"]:
        ss = [s for s in step["skills"] if s in skills]
        if ss:
            workflow.append({"phase": step["phase"], "skills": ss})
    unverified = [x["source_id"] for x in fw if x["access_status"] != "VERIFIED"]
    if unverified:
        f.append(_f("frameworks", "info", "unverified-sources",
                    f"{len(unverified)} selected framework sources were not verified at primary level in this library: {', '.join(unverified)}"))
    install = ("python3 scripts/install_packs.py --target <PROJECT_DIR> --skills " + ",".join(skills) +
               " --agents " + ",".join(sorted(agents)) + "   # dry-run by default; add --apply to write")
    return {"project": p.get("name", ""), "findings": f, "selected_packs": selected, "excluded_packs": excluded,
            "skills": skills, "agents": {k: sorted(set(v)) for k, v in sorted(agents.items())}, "frameworks": fw,
            "oversight_level": oversight, "human_signoffs": signoffs, "workflow": workflow, "install_command": install,
            "provenance": rules.get("_provenance", "")}


def markdown(r: dict) -> str:
    out = [f"# Framework selection — {r['project']}", "", f"**Oversight level:** {r['oversight_level']}", "",
           "## Selected packs", "| Pack | Why | Triggers | Skills |", "|---|---|---|---|"]
    for k, v in r["selected_packs"].items():
        out.append(f"| {k} | {v['reason']} | {', '.join(v['triggers'])} | {', '.join('`'+s+'`' for s in v['skills'])} |")
    out += ["", "## Excluded packs", "| Pack | Why not |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in r["excluded_packs"].items()]
    out += ["", "## Agents", "| Agent | Skills it covers here |", "|---|---|"]
    out += [f"| `{k}` | {', '.join(v) or 'cross-pack challenge review'} |" for k, v in r["agents"].items()]
    out += ["", "## Frameworks (source access status in this library)", "| Source | Title | Access | Normative status |", "|---|---|---|---|"]
    out += [f"| `{x['source_id']}` | {x['title']} | {x['access_status']} | {x['normative_status']} |" for x in r["frameworks"]]
    out += ["", "## Recommended workflow"]
    for w in r["workflow"]:
        out.append(f"- **{w['phase']}**: " + ", ".join(f"`{s}`" for s in w["skills"]))
    out += ["", "## Human sign-offs required"] + [f"- {s}" for s in r["human_signoffs"]]
    out += ["", "## Install (dry-run first)", "```", r["install_command"], "```", "",
            "_Proposal generated by select_frameworks.py; the project owner decides which frameworks apply._"]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Select frameworks, skills and agents for a project.")
    ap.add_argument("profile", type=Path)
    ap.add_argument("--catalog", type=Path, default=DATA / "catalog.json")
    ap.add_argument("--rules", type=Path, default=DATA / "routing-rules.json")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        p = json.loads(a.profile.read_text(encoding="utf-8"))
        catalog = json.loads(a.catalog.read_text(encoding="utf-8"))
        rules = json.loads(a.rules.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    r = select(p, catalog, rules)
    r["passed"] = not any(x["severity"] == "error" for x in r["findings"])
    if a.json:
        print(json.dumps(r, indent=2))
    elif r["passed"]:
        print(markdown(r))
        for x in r["findings"]:
            print(f"\n{x['severity'].upper()}: {x['message']}")
    else:
        for x in r["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<12} {x['rule']:<16} {x['message']}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
