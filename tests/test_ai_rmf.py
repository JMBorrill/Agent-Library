"""Tests for the NIST AI RMF catalogs, tools, CLI and graders."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from agentlib.cli import main
from agentlib.frameworks import ai_rmf as rmf
from agentlib.paths import repo_root

ROOT = repo_root()


# ------------------------------------------------------------------ catalog integrity
def test_core_counts():
    cat = rmf.core()
    assert cat["source_id"] == "nist-ai"
    assert len(cat["items"]) == 72
    cats = [g for g in cat["groups"] if g.get("kind") == "category"]
    fns = [g for g in cat["groups"] if g.get("kind") == "function"]
    assert len(cats) == 19 and [f["id"] for f in fns] == list(rmf.FUNCTIONS)
    counts = {fn: len(rmf.subcategories([fn])) for fn in rmf.FUNCTIONS}
    assert counts == {"GOVERN": 19, "MAP": 18, "MEASURE": 22, "MANAGE": 13}
    assert cat["parameters"]["subcategory_counts"] == counts


def test_core_ids_pages_and_groups():
    cat = rmf.core()
    groups = {g["id"] for g in cat["groups"]}
    ids = [i["id"] for i in cat["items"]]
    assert len(ids) == len(set(ids))
    for item in cat["items"]:
        assert rmf.normalise_id(item["id"]) == item["id"]
        assert item["group"] in groups
        assert 27 <= item["citation"]["pdf_page"] <= 38
        assert item["citation"]["printed_page"] == item["citation"]["pdf_page"] - 5
        assert item["text"].endswith((".", ")"))


def test_core_verbatim_spot_checks():
    idx = rmf.subcategory_index()
    assert idx["GOVERN 1.1"]["text"] == ("Legal and regulatory requirements involving AI are understood, "
                                         "managed, and documented.")
    assert idx["GOVERN 1.7"]["text"].startswith("Processes and procedures are in place for decommissioning")
    assert "mitigating, transferring, avoiding, or accepting" in idx["MANAGE 1.3"]["text"]
    assert idx["MEASURE 2.11"]["citation"]["pdf_page"] == 35
    assert idx["MANAGE 4.3"]["citation"]["pdf_page"] == 38
    assert "GOVERN 7.1" not in idx and "MAP 6.1" not in idx and "MEASURE 2.14" not in idx


def test_trustworthy_characteristics():
    tcs = rmf.trustworthy_characteristics()
    assert [t["id"] for t in tcs] == ["valid-reliable", "safe", "secure-resilient", "accountable-transparent",
                                     "explainable-interpretable", "privacy-enhanced", "fair-bias-managed"]
    assert [t["section"] for t in tcs] == [f"3.{n}" for n in range(1, 8)]
    for t in tcs:
        assert 17 <= t["citation"]["pdf_page"] <= 23


def test_playbook_catalog():
    pb = rmf.playbook()
    assert pb["source_id"] == "nist-ai-playbook"
    subs = {i["subcategory"] for i in pb["items"]}
    assert subs == set(rmf.subcategory_index())
    ids = [i["id"] for i in pb["items"]]
    assert len(ids) == len(set(ids))
    for i in pb["items"]:
        assert 5 <= i["citation"]["pdf_page"] <= 147
        assert i["id"].startswith(i["subcategory"] + "/")
    for sid in rmf.subcategory_index():
        e = rmf.playbook_entries(sid)
        assert e["actions"], sid
        assert e["actions"][0]["id"] == f"{sid}/action-1"
    gv23 = rmf.playbook_entries("GOVERN 2.3")["actions"]
    assert gv23[0]["text"] == "Organizational management can:" and len(gv23[0]["sub_actions"]) == 5
    assert pb["parameters"]["gaps"] == []


def test_catalogs_validate_and_reproduce():
    from agentlib.validate import check_catalogs

    issues = [i for i in check_catalogs(ROOT) if "nist-ai-rmf" in i.path]
    assert not issues, issues


@pytest.mark.skipif(not __import__("shutil").which("pdftotext"), reason="pdftotext not installed")
def test_extraction_reproducible():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/extract/ai_rmf.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ------------------------------------------------------------------ ids
@pytest.mark.parametrize("raw,canon", [("GOVERN 1.1", "GOVERN 1.1"), ("gv-1.1", "GOVERN 1.1"),
                                       ("Map 5.1", "MAP 5.1"), ("MS-2.11", "MEASURE 2.11"), ("MANAGE4.3", "MANAGE 4.3")])
def test_normalise_id(raw, canon):
    assert rmf.normalise_id(raw) == canon


def test_normalise_id_rejects():
    assert rmf.normalise_id("GOVERN 1") is None
    assert rmf.normalise_id("foo") is None
    assert not rmf.is_valid_id(rmf.normalise_id("MAP 9.9"))


def test_scan_text():
    rep = rmf.scan_text("We use GOVERN 1.1, MAP 1.5 and MS-2.11; also MAP 6.2 and Privacy-enhanced and fairness with harmful bias managed.")
    assert rep["valid"] == ["GOVERN 1.1", "MAP 1.5", "MEASURE 2.11"]
    assert rep["invalid"] == ["MAP 6.2"]
    assert rep["functions_covered"] == ["GOVERN", "MAP", "MEASURE"]
    assert set(rep["characteristics"]) == {"privacy-enhanced", "fair-bias-managed"}


@pytest.mark.parametrize("raw,cid", [("Fairness", "fair-bias-managed"), ("privacy", "privacy-enhanced"),
                                     ("Valid & Reliable", "valid-reliable"), ("Fair (harmful bias managed)", "fair-bias-managed"),
                                     ("security", "secure-resilient"), ("transparency", "accountable-transparent")])
def test_normalise_characteristic(raw, cid):
    assert rmf.normalise_characteristic(raw) == cid


def test_normalise_characteristic_unknown():
    assert rmf.normalise_characteristic("profitability") is None


# ------------------------------------------------------------------ profiles
def _profile_rows(fill="implemented", evidence="policy v2"):
    return [{"subcategory": s["id"], "current_status": fill, "target_status": "implemented", "priority": "medium",
             "owner": "CRO", "evidence": evidence} for s in rmf.subcategories()]


def test_profile_template_formats():
    md = rmf.profile_template(["MAP"], "md")
    assert md.count("| MAP ") == 18 and "## MAP" in md and "GOVERN 1.1" not in md
    rows = list(csv.DictReader(rmf.profile_template(None, "csv").splitlines()))
    assert len(rows) == 72 and rows[0]["subcategory"] == "GOVERN 1.1"
    doc = yaml.safe_load(rmf.profile_template(["GOVERN", "MANAGE"], "yaml"))
    assert doc["profile"]["functions"] == ["GOVERN", "MANAGE"]
    assert len(doc["subcategories"]) == 32
    with pytest.raises(rmf.AIRMFError):
        rmf.profile_template(None, "xlsx")


def test_check_profile_clean():
    rep = rmf.check_profile(_profile_rows())
    assert rep["ok"] and not rep["gaps"] and rep["assessed"] == 72


def test_check_profile_errors_and_gaps():
    rows = _profile_rows(fill="partial", evidence="")
    rows[0]["current_status"] = "implemented"            # no evidence -> error
    rows[1]["current_status"] = "sort of"               # invalid status
    rows[2]["owner"] = ""                               # gap without owner -> warning
    rows[2]["priority"] = "high"
    rows.pop(5)                                         # missing GOVERN 1.6
    rows.append({"subcategory": "GOVERN 7.1", "current_status": "implemented", "target_status": "implemented"})
    rep = rmf.check_profile(rows)
    joined = "\n".join(rep["errors"])
    assert not rep["ok"]
    assert "GOVERN 1.1: current status 'implemented' but no evidence" in joined
    assert "invalid current status 'sort of'" in joined
    assert "GOVERN 1.6: missing from profile" in joined
    assert "unknown subcategory id 'GOVERN 7.1'" in joined
    assert any("GOVERN 1.3: gap" in w and "no owner" in w for w in rep["warnings"])
    assert rep["gaps"][0]["id"] == "GOVERN 1.3"          # high priority first
    assert rep["summary"]["by_function"]["GOVERN"]["high_priority_gaps"] == 1
    assert rep["summary"]["by_category"]["MAP 1"]["gaps"] == 6


def test_check_profile_scope_and_na():
    rows = [{"id": s["id"], "current": "n/a", "target": "n/a"} for s in rmf.subcategories(["MANAGE"])]
    rep = rmf.check_profile(rows, ["MANAGE"])
    assert rep["ok"]
    assert len([w for w in rep["warnings"] if "not-applicable without a justification" in w]) == 13
    assert rep["summary"]["by_function"]["MANAGE"]["not_applicable"] == 13


def test_check_profile_duplicate_and_missing_status():
    rows = [{"subcategory": "MAP 1.1", "current_status": "", "target_status": "implemented"},
            {"subcategory": "MAP 1.1", "current_status": "implemented", "target_status": "implemented"}]
    rep = rmf.check_profile(rows, ["MAP"])
    assert any("MAP 1.1: current status missing" in e for e in rep["errors"])
    assert any("duplicate" in e for e in rep["errors"])


# ------------------------------------------------------------------ register
GOOD_RISK = {
    "id": "R-1", "description": "Model under-predicts creditworthiness for thin-file applicants",
    "affected_stakeholders": "applicants; lending officers",
    "trustworthiness_characteristics": "fair-bias-managed; valid-reliable",
    "likelihood": 4, "impact": 4, "inherent_rating": "high", "treatment": "mitigate",
    "controls": "reweighting; disparity monitoring", "residual_likelihood": 2, "residual_impact": 4,
    "residual_rating": "medium", "owner": "Head of Credit Risk",
    "linked_subcategories": "MAP 5.1; MEASURE 2.11; MANAGE 1.3", "review_date": "2026-12-01",
}


def test_register_clean():
    rep = rmf.check_register([dict(GOOD_RISK)])
    assert rep["ok"], rep["errors"]
    assert rep["summary"]["by_residual"] == {"medium": 1}
    assert "safe" in rep["summary"]["characteristics_not_covered"]


def test_register_missing_fields_and_invalid_values():
    bad = dict(GOOD_RISK, owner="", treatment="ignore", linked_subcategories="MAP 7.1; GOVERN 1.1",
               trustworthiness_characteristics="profitability", likelihood=9)
    del bad["affected_stakeholders"]
    errs = "\n".join(rmf.check_register([bad])["errors"])
    assert "missing required field 'owner'" in errs
    assert "missing required field 'stakeholders'" in errs
    assert "invalid treatment 'ignore'" in errs
    assert "invalid AI RMF subcategory id 'MAP 7.1'" in errs
    assert "unknown trustworthiness characteristic 'profitability'" in errs
    assert "likelihood '9' not on the 1-5 scale" in errs


def test_register_residual_exceeds_inherent():
    r = dict(GOOD_RISK, inherent_rating="medium", residual_rating="high", escalated_to="AI risk committee")
    errs = rmf.check_register([r])["errors"]
    assert any("exceeds inherent" in e for e in errs)
    r["residual_justification"] = "new deployment context increases exposure"
    assert rmf.check_register([r])["ok"]


def test_register_high_residual_needs_signoff():
    r = dict(GOOD_RISK, residual_rating="high")
    errs = rmf.check_register([r])["errors"]
    assert any("requires escalation" in e for e in errs)
    assert rmf.check_register([dict(r, accepted_by="CRO, 2026-10-01")])["ok"]


def test_register_accept_needs_signoff_and_matrix_warning():
    r = dict(GOOD_RISK, treatment="accept", controls="", inherent_rating="low")
    rep = rmf.check_register([r])
    assert any("requires an acceptance sign-off" in e for e in rep["errors"])
    assert any("differs from likelihood x impact" in w for w in rep["warnings"])


def test_register_duplicates_and_empty():
    assert not rmf.check_register([])["ok"]
    rep = rmf.check_register([dict(GOOD_RISK), dict(GOOD_RISK)])
    assert any("duplicate risk id" in e for e in rep["errors"])


def test_rating_parsing():
    assert rmf._rating("High (16)") == "high"
    assert rmf._rating("20") == "critical"
    assert rmf._rating("amber") == "medium"
    assert rmf._rating("bad").startswith("INVALID")
    assert rmf.score_band(9) == "medium" and rmf.score_band(10) == "high"


# ------------------------------------------------------------------ file loading
def test_load_rows_formats(tmp_path):
    y = tmp_path / "r.yaml"
    y.write_text(yaml.safe_dump({"register": {"system": "x"}, "risks": [GOOD_RISK]}), encoding="utf-8")
    rows, meta = rmf.load_rows(y, "risks")
    assert rows[0]["id"] == "R-1" and meta["register"]["system"] == "x"
    c = tmp_path / "r.csv"
    with c.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(GOOD_RISK))
        w.writeheader()
        w.writerow(GOOD_RISK)
    rows, _ = rmf.load_rows(c, "risks")
    assert rmf.check_register(rows)["ok"]
    with pytest.raises(rmf.AIRMFError):
        rmf.load_rows(tmp_path / "missing.yaml", "risks")
    bad = tmp_path / "bad.txt"
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(rmf.AIRMFError):
        rmf.load_rows(bad, "risks")
    notlist = tmp_path / "n.yaml"
    notlist.write_text("risks: 3\n", encoding="utf-8")
    with pytest.raises(rmf.AIRMFError):
        rmf.load_rows(notlist, "risks")


def test_parse_md_tables():
    md = "x\n\n| Subcategory | Current status |\n|---|---|\n| MAP 1.1 | implemented |\n| MAP 1.2 | partial |\n"
    t = rmf.parse_md_tables(md)
    assert t == [[{"subcategory": "MAP 1.1", "current_status": "implemented"},
                  {"subcategory": "MAP 1.2", "current_status": "partial"}]]


# ------------------------------------------------------------------ CLI
def test_cli_list_and_show(capsys):
    assert main(["ai-rmf", "list", "--function", "MANAGE"]) == 0
    out = capsys.readouterr().out
    assert "MANAGE 4.3" in out and "13 subcategories" in out and "GOVERN" not in out
    assert main(["ai-rmf", "show", "GOVERN 1.1"]) == 0
    out = capsys.readouterr().out
    assert "Legal and regulatory requirements" in out and "GOVERN 1.1/action-1" in out and "question-1" in out
    assert main(["ai-rmf", "show", "MAP 9.1"]) == 2
    assert main(["ai-rmf", "show", "mp-2.3", "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["subcategory"]["id"] == "MAP 2.3" and data["playbook"]["actions"]


def test_cli_characteristics(capsys):
    assert main(["ai-rmf", "characteristics"]) == 0
    assert capsys.readouterr().out.count("PDF p.") == 7


def test_cli_profile_roundtrip(tmp_path, capsys):
    out = tmp_path / "p.yaml"
    assert main(["ai-rmf", "profile-template", "--functions", "MAP", "--format", "yaml", "-o", str(out)]) == 0
    doc = yaml.safe_load(out.read_text(encoding="utf-8"))
    # unfilled template fails
    assert main(["ai-rmf", "check-profile", str(out)]) == 1
    for row in doc["subcategories"]:
        row.update(current_status="partial", target_status="implemented", priority="high", owner="AI lead")
    out.write_text(yaml.safe_dump(doc), encoding="utf-8")
    capsys.readouterr()
    assert main(["ai-rmf", "check-profile", str(out)]) == 0      # scope from profile.functions
    text = capsys.readouterr().out
    assert "| MAP | 18 | 0 | 18 | 18 | 0 |" in text and "Result: PASS" in text
    assert main(["ai-rmf", "check-profile", str(out), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["scope"] == ["MAP"]
    # with all four functions in scope the MAP-only profile is incomplete
    assert main(["ai-rmf", "check-profile", str(out), "--functions", "GOVERN", "MAP"]) == 1


def test_cli_profile_csv_md(tmp_path):
    c = tmp_path / "p.csv"
    assert main(["ai-rmf", "profile-template", "--format", "csv", "-o", str(c)]) == 0
    rows = list(csv.DictReader(c.read_text(encoding="utf-8").splitlines()))
    for r in rows:
        r.update(current_status="implemented", target_status="implemented", evidence="doc")
    with c.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    assert main(["ai-rmf", "check-profile", str(c)]) == 0
    m = tmp_path / "p.md"
    assert main(["ai-rmf", "profile-template", "--functions", "GOVERN", "-o", str(m)]) == 0
    assert main(["ai-rmf", "check-profile", str(m), "--functions", "GOVERN"]) == 1  # blank statuses


def test_cli_register(tmp_path, capsys):
    y = tmp_path / "reg.yaml"
    assert main(["ai-rmf", "register-template", "--format", "yaml", "-o", str(y)]) == 0
    assert main(["ai-rmf", "check-register", str(y)]) == 1      # placeholders are invalid
    y.write_text(yaml.safe_dump({"risks": [GOOD_RISK]}), encoding="utf-8")
    capsys.readouterr()
    assert main(["ai-rmf", "check-register", str(y)]) == 0
    assert "Result: PASS" in capsys.readouterr().out
    assert main(["ai-rmf", "check-register", str(tmp_path / "nope.yaml")]) == 2
    assert main(["ai-rmf", "register-template", "--format", "csv", "-o", str(tmp_path / "r.csv")]) == 0
    assert main(["ai-rmf", "register-template"]) == 0


def test_cli_scan(tmp_path, capsys):
    f = tmp_path / "doc.md"
    f.write_text("GOVERN 1.1 MAP 1.1 MEASURE 2.11 MANAGE 1.3", encoding="utf-8")
    assert main(["ai-rmf", "scan", str(f)]) == 0
    f.write_text("GOVERN 1.1 and GOVERN 8.2", encoding="utf-8")
    assert main(["ai-rmf", "scan", str(f), "--json"]) == 1
    assert "GOVERN 8.2" in capsys.readouterr().out


def test_fixture_files_check():
    fx = ROOT / "evals" / "nist-ai-rmf" / "fixtures"
    rows, _ = rmf.load_rows(fx / "hiring-risk-register.csv", "risks")
    rep = rmf.check_register(rows)
    assert not rep["ok"]  # the fixture deliberately contains defects for the review eval case
    errs = "\n".join(rep["errors"])
    assert "R-03" in errs and "MAP 6.1" in errs


# ------------------------------------------------------------------ graders
FULL = ("GOVERN 1.1, GOVERN 2.1, MAP 1.1, MAP 5.1, MEASURE 2.11, MEASURE 2.6, MANAGE 1.3, MANAGE 4.1. "
        "Characteristics: valid and reliable, safe, secure and resilient, accountable and transparent, "
        "explainable and interpretable, privacy-enhanced, fair with harmful bias managed.")


def test_grade_valid_ids():
    assert rmf.grade_valid_subcategory_ids(FULL, {"min": 8})[0]
    ok, msg = rmf.grade_valid_subcategory_ids(FULL + " GOVERN 7.2", {})
    assert not ok and "GOVERN 7.2" in msg
    assert not rmf.grade_valid_subcategory_ids("nothing here", {})[0]


def test_grade_function_coverage():
    assert rmf.grade_function_coverage(FULL, {"min_per_function": 2})[0]
    assert not rmf.grade_function_coverage("GOVERN 1.1 MAP 1.1 MEASURE 1.1", {})[0]
    assert rmf.grade_function_coverage("GOVERN 1.1 MAP 1.1", {"functions": ["GOVERN", "MAP"]})[0]


def test_grade_characteristics():
    assert rmf.grade_trustworthy_characteristics(FULL, {})[0]
    assert not rmf.grade_trustworthy_characteristics("safety and privacy-enhanced", {})[0]
    assert rmf.grade_trustworthy_characteristics("safety and privacy-enhanced", {"min": 2, "required": ["safe"]})[0]
    assert not rmf.grade_trustworthy_characteristics("safety", {"min": 1, "required": ["privacy"]})[0]


def test_grade_register_table():
    good = ("| ID | Description | Affected stakeholders | Trustworthiness characteristics | Likelihood | Impact | "
            "Inherent rating | Treatment | Controls | Residual rating | Owner | Accepted by | Linked subcategories | Review date |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| R-1 | Bias | applicants | fairness | 4 | 4 | high | mitigate | audit | medium | HR lead | | MEASURE 2.11; MANAGE 1.3 | 2026-12-01 |\n")
    assert rmf.grade_register_table(good, {})[0]
    bad = good.replace("| medium | HR lead | |", "| high | HR lead | |")
    ok, msg = rmf.grade_register_table(bad, {})
    assert not ok and "requires escalation" in msg
    assert not rmf.grade_register_table("no table", {})[0]
    assert not rmf.grade_register_table(good, {"min_risks": 2})[0]


def test_grade_profile_table():
    good = ("| Subcategory | Current status | Target status | Priority | Owner | Evidence |\n|---|---|---|---|---|---|\n"
            "| GOVERN 1.1 | partial | implemented | high | GC | legal register draft |\n"
            "| MAP 1.1 | implemented | implemented | low | PM | context record v1 |\n")
    ok, msg = rmf.grade_profile_table(good, {"min_gaps": 1})
    assert ok, msg
    assert not rmf.grade_profile_table(good.replace("context record v1", ""), {})[0]
    assert not rmf.grade_profile_table(good, {"require_complete": True})[0]
    assert not rmf.grade_profile_table("nothing", {})[0]
