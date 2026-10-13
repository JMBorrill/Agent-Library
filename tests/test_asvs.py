"""Tests for the OWASP ASVS 5.0.0 catalog, tools, graders and CLI."""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

import pytest
import yaml

from agentlib.cli import main
from agentlib.frameworks import asvs
from agentlib.paths import repo_root

ROOT = repo_root()


# ------------------------------------------------------------------ catalog integrity
def test_catalog_counts_match_document():
    cat = asvs.catalog()
    assert cat["catalog_id"] == "owasp-asvs-5" and cat["source_id"] == "owasp-asvs"
    items = cat["items"]
    assert len(items) == 345  # PDF p. 23: "70 L1 requirements out of a total of 345"
    assert sum(r["level"] == 1 for r in items) == 70
    assert len(asvs.chapters()) == 17
    assert [c["id"] for c in asvs.chapters()] == [f"V{i}" for i in range(1, 18)]
    assert len(asvs.sections()) == 80
    counts = cat["parameters"]["requirement_counts"]
    assert counts["L1"] + counts["L2"] + counts["L3"] == 345
    assert counts["cumulative"]["2"] == counts["L1"] + counts["L2"]


def test_ids_unique_well_formed_and_contiguous():
    ids = [r["id"] for r in asvs.requirements()]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"\d+\.\d+\.\d+", i) for i in ids)
    for s in asvs.sections():
        nums = [int(r["id"].split(".")[2]) for r in asvs.requirements() if r["group"] == s["id"]]
        assert nums == list(range(1, len(nums) + 1)), s["id"]
        assert s["requirement_count"] == len(nums)


def test_items_have_text_level_and_page_ranges():
    for r in asvs.requirements():
        assert r["text"].startswith("Verify"), r["id"]
        assert r["level"] in (1, 2, 3)
        assert r["group"].startswith(r["chapter"] + ".")
        assert r["group"] == "V" + ".".join(r["id"].split(".")[:2])
        # requirement chapters span PDF pages 24-96 (printed 23-95)
        assert 24 <= r["citation"]["pdf_page"] <= 96
        assert r["citation"]["printed_page"] == r["citation"]["pdf_page"] - 1
        assert r["canonical_ref"] == f"v5.0.0-{r['id']}"
        assert "May 2025" not in r["text"] and "  " not in r["text"]


def test_known_requirement_text_and_pages():
    r = asvs.get("1.2.5")  # quoted in the document's referencing guidance, PDF p. 16
    assert r["text"].startswith("Verify that the application protects against OS command injection")
    assert r["level"] == 1 and r["citation"]["pdf_page"] == 26
    assert asvs.get("6.2.9")["text"] == "Verify that passwords of at least 64 characters are permitted."
    assert asvs.get("6.2.9")["level"] == 2
    assert asvs.get("17.3.2")["chapter"] == "V17"


def test_groups_pages_monotonic_and_titles():
    groups = asvs.catalog()["groups"]
    pages = [g["citation"]["pdf_page"] for g in groups]
    assert pages == sorted(pages)
    titles = {g["id"]: g["title"] for g in groups}
    assert titles["V9"] == "Self-contained Tokens"
    assert titles["V10.4"] == "OAuth Authorization Server"


def test_levels_documented_with_citations():
    lv = asvs.catalog()["levels"]
    assert lv["cumulative"] is True
    for k in ("1", "2", "3"):
        assert lv[k]["citation"]["pdf_page"] in (14, 15)
    assert any(c["pdf_page"] == 14 for c in lv["statement_citations"])


def test_catalog_validator_clean():
    from agentlib.validate import check_catalogs

    issues = [i for i in check_catalogs(ROOT) if "owasp-asvs-5" in i.path]
    assert not issues, issues


# ------------------------------------------------------------------ ids and selection
@pytest.mark.parametrize("raw", ["1.2.5", "V1.2.5", "v1.2.5", "v5.0.0-1.2.5", "ASVS 1.2.5", " 1.2.5 "])
def test_normalize_id_accepts_forms(raw):
    assert asvs.normalize_id(raw) == "1.2.5"


@pytest.mark.parametrize("raw", ["v4.0.3-1.2.5", "1.2", "abc", "V1", ""])
def test_normalize_id_rejects(raw):
    with pytest.raises(asvs.AsvsError):
        asvs.normalize_id(raw)


def test_get_unknown_raises():
    with pytest.raises(asvs.AsvsError):
        asvs.get("6.9.9")
    assert not asvs.exists("99.1.1") and asvs.exists("V2.1.1")


def test_levels_are_cumulative():
    l1, l2, l3 = (asvs.select(n) for n in (1, 2, 3))
    assert len(l1) == 70 and len(l3) == 345
    assert {r["id"] for r in l1} <= {r["id"] for r in l2} <= {r["id"] for r in l3}
    assert all(r["level"] <= 2 for r in l2)


def test_scope_filters():
    v6 = asvs.select(3, ["V6"])
    assert v6 and all(r["chapter"] == "V6" for r in v6)
    sec = asvs.select(3, ["6.2"])
    assert {r["group"] for r in sec} == {"V6.2"}
    assert len(asvs.select(3, ["V1, V2"])) == len(asvs.select(3, ["V1"])) + len(asvs.select(3, ["V2"]))
    with pytest.raises(asvs.AsvsError):
        asvs.select(2, ["V18"])
    with pytest.raises(asvs.AsvsError):
        asvs.select(4)


def test_search():
    hits = asvs.search("samesite")
    assert [h["id"] for h in hits] == ["3.3.2"]
    assert all(h["level"] == 1 for h in asvs.search("password", level=1))
    with pytest.raises(asvs.AsvsError):
        asvs.search("   ")


# ------------------------------------------------------------------ checklist
@pytest.mark.parametrize("fmt", ["md", "csv", "yaml", "json"])
def test_checklist_formats(fmt):
    out = asvs.render_checklist(2, ["V1", "V6"], fmt)
    expected = len(asvs.select(2, ["V1", "V6"]))
    if fmt == "json":
        data = json.loads(out)
        assert data["requirement_count"] == expected and len(data["results"]) == expected
        assert {r["status"] for r in data["results"]} == {"not-verified"}
    elif fmt == "yaml":
        assert len(yaml.safe_load(out)["results"]) == expected
    elif fmt == "csv":
        rows = list(csv.DictReader(io.StringIO(out)))
        assert len(rows) == expected and "finding_ref" in rows[0]
    else:
        assert out.count("\n| ") - out.count("\n| ID") == expected
        assert "## V1 Encoding and Sanitization" in out and "## V6 Authentication" in out


def test_checklist_roundtrip_through_check_assessment():
    data = json.loads(asvs.render_checklist(1, None, "json"))
    rep = asvs.check_assessment(data)
    assert rep["valid"] and not rep["complete"] and len(rep["not_verified"]) == 70
    for r in data["results"]:
        r["status"] = "pass"
    rep = asvs.check_assessment(data)
    assert rep["compliant"] and rep["totals"]["compliance_pct"] == 100.0


# ------------------------------------------------------------------ assessment validation
def _results(level=1, scope=("V6",), status="pass"):
    return [{"id": r["id"], "status": status, "evidence": "test"} for r in asvs.select(level, list(scope))]


def test_assessment_all_errors_detected():
    res = _results()
    res[0]["status"] = "fail"                       # fail without finding
    res[1].update(status="fail", finding_ref="F-1")  # ok
    res[2]["status"] = "not-applicable"             # N/A without justification
    res[3].update(status="N/A", justification="no passwords; SSO only")  # alias accepted
    res[4]["status"] = "maybe"                      # invalid status
    missing_id = res.pop(5)["id"]                   # missing
    res.append({"id": "6.9.9", "status": "pass"})   # unknown
    res.append({"id": res[1]["id"], "status": "pass"})  # duplicate
    res.append({"id": "6.2.9", "status": "pass"})   # L2: out of scope warning
    rep = asvs.check_assessment({"level": 1, "chapters": ["V6"], "results": res})
    problems = " | ".join(f"{e['id']}:{e['problem']}" for e in rep["errors"])
    assert "fail' without a finding" in problems
    assert "not-applicable' without a justification" in problems
    assert "invalid status" in problems
    assert f"{missing_id}:in-scope requirement has no result" in problems
    assert "6.9.9:unknown id" in problems
    assert "duplicate entry" in problems
    assert any(w["id"] == "6.2.9" and "above target level" in w["problem"] for w in rep["warnings"])
    assert not rep["valid"] and not rep["complete"] and not rep["compliant"]
    assert [f["id"] for f in rep["failures"]] == sorted([res[0]["id"], res[1]["id"]], key=asvs.sort_key)


def test_assessment_compliance_percentage():
    res = _results(level=2, scope=("V3",))
    n = len(res)
    res[0].update(status="fail", finding_ref="F-9")
    res[1].update(status="not-applicable", justification="no cookies")
    rep = asvs.check_assessment(res, level=2, scope=["V3"])
    assert rep["valid"] and rep["complete"] and not rep["compliant"]
    assert rep["totals"]["compliance_pct"] == round(100 * (n - 2) / (n - 1), 1)
    assert rep["chapters"][0]["chapter"] == "V3"


def test_assessment_mapping_and_level_from_file_and_errors():
    data = {r["id"]: "pass" for r in asvs.select(1, ["V2"])}
    rep = asvs.check_assessment(data, level=1, scope=["V2"])
    assert rep["compliant"]
    with pytest.raises(asvs.AsvsError):
        asvs.check_assessment([{"id": "1.1.1", "status": "pass"}])  # no level
    with pytest.raises(asvs.AsvsError):
        asvs.check_assessment("nonsense", level=1)


def test_all_na_chapter_has_no_percentage():
    res = [{"id": r["id"], "status": "not-applicable", "justification": "no WebRTC"} for r in asvs.select(2, ["V17"])]
    rep = asvs.check_assessment(res, level=2, scope=["V17"])
    assert rep["compliant"] and rep["totals"]["compliance_pct"] is None
    assert "n/a" in asvs.render_assessment(rep)


# ------------------------------------------------------------------ mapping
def test_map_findings_deterministic_and_relevant():
    findings = [
        {"id": "F-1", "title": "SQL injection in report filter", "cwe": "CWE-89"},
        {"id": "F-2", "title": "IDOR on invoice endpoint", "description": "any user can read other users' invoices by changing the id"},
        {"id": "F-3", "title": "JWT accepted with alg none"},
        {"id": "F-4", "title": "Session cookie missing HttpOnly"},
    ]
    a = asvs.map_findings(findings, top=3)
    b = asvs.map_findings({"findings": findings}, top=3)
    assert a == b
    top = {r["finding"]: [c["id"] for c in r["candidates"]] for r in a}
    assert top["F-1"][0] == "1.2.4"
    assert top["F-2"][0] == "8.2.2"
    assert set(top["F-3"]) & {"9.1.1", "9.1.2"}
    assert "3.3.4" in top["F-4"]
    assert a[0]["candidates"][0]["cwe_hint"] is True
    scores = [c["score"] for c in a[0]["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_map_findings_level_cap_and_bad_input():
    res = asvs.map_findings([{"title": "SQL injection"}], level=1)
    assert all(c["level"] == 1 for c in res[0]["candidates"])
    with pytest.raises(asvs.AsvsError):
        asvs.map_findings([{"cwe": "CWE-79"}])
    with pytest.raises(asvs.AsvsError):
        asvs.map_findings("x")
    assert asvs.map_findings([{"title": "zzzz qqqq"}])[0]["candidates"] == []


def test_cwe_hints_point_to_real_sections():
    groups = {g["id"] for g in asvs.catalog()["groups"]}
    for sections in asvs.CWE_SECTION_HINTS.values():
        assert set(sections) <= groups


# ------------------------------------------------------------------ graders
def test_ids_in_ignores_versions():
    text = "ASVS 5.0.0 / v4.0.3; see v5.0.0-1.2.5, V6.2.9 and 13.4.1. IP 10.1.2.3 is not an id."
    assert asvs.ids_in(text) == ["1.2.5", "6.2.9", "13.4.1"]


def test_grade_ids_exist():
    ok, _ = asvs.grade_ids_exist("Fails 1.2.4 and 8.2.2", {"min": 2, "require": ["V8.2.2"]})
    assert ok
    ok, detail = asvs.grade_ids_exist("Fails 1.2.4 and 6.9.9", {})
    assert not ok and "6.9.9" in detail
    assert not asvs.grade_ids_exist("no ids", {})[0]


def test_grade_level_appropriate_and_claimed():
    assert asvs.grade_level_appropriate("1.2.4 and 1.2.5", {"level": 1})[0]
    assert not asvs.grade_level_appropriate("1.2.4 and 6.2.9", {"level": 1})[0]
    good = "| ID | Level | Requirement |\n|---|---|---|\n| 1.2.4 | 1 | x |\n| 6.2.9 | 2 | y |\n\nAlso 3.4.7 (L3)."
    assert asvs.grade_levels_claimed(good, {"min": 3})[0]
    bad = good.replace("| 6.2.9 | 2 |", "| 6.2.9 | 1 |")
    ok, detail = asvs.grade_levels_claimed(bad, {})
    assert not ok and "6.2.9" in detail


def test_grade_chapters_exist_and_json_assessment():
    assert asvs.grade_chapters_exist("See V3 and V10.4", {})[0]
    assert not asvs.grade_chapters_exist("See V18 and V3.9", {})[0]
    block = json.dumps({"level": 1, "chapters": ["V2"], "results": _results(1, ("V2",))})
    assert asvs.grade_json_assessment(f"```json\n{block}\n```", {"require_complete": True})[0]
    bad = json.dumps({"level": 1, "chapters": ["V2"], "results": _results(1, ("V2",), status="fail")})
    assert not asvs.grade_json_assessment(f"```json\n{bad}\n```", {})[0]
    assert not asvs.grade_json_assessment("no block", {})[0]


# ------------------------------------------------------------------ CLI
def test_cli_chapters_show_search(capsys):
    assert main(["asvs", "chapters", "--sections"]) == 0
    out = capsys.readouterr().out
    assert "V17" in out and "345 requirements" in out and "V10.4 OAuth Authorization Server" in out
    assert main(["asvs", "show", "V1.2.5", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "1.2.5"
    assert main(["asvs", "show", "9.9.9"]) == 2
    assert "unknown" in capsys.readouterr().err
    assert main(["asvs", "search", "prototype", "pollution"]) == 0
    assert "15.3.6" in capsys.readouterr().out


def test_cli_checklist_to_file(tmp_path, capsys):
    out = tmp_path / "plan.csv"
    assert main(["asvs", "checklist", "--level", "2", "--chapters", "V1", "V6", "--format", "csv", "-o", str(out)]) == 0
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == len(asvs.select(2, ["V1", "V6"]))
    assert main(["asvs", "checklist", "--level", "1", "--chapters", "V99"]) == 2


def test_cli_check_assessment_exit_codes(tmp_path, capsys):
    good = tmp_path / "a.yaml"
    res = _results(1, ("V2",))
    good.write_text(yaml.safe_dump({"level": 1, "chapters": ["V2"], "results": res}), encoding="utf-8")
    assert main(["asvs", "check-assessment", str(good)]) == 0
    assert "COMPLIANT" in capsys.readouterr().out
    res[0].update(status="fail", finding_ref="F-1")
    good.write_text(yaml.safe_dump({"level": 1, "chapters": ["V2"], "results": res}), encoding="utf-8")
    assert main(["asvs", "check-assessment", str(good)]) == 0
    assert main(["asvs", "check-assessment", str(good), "--strict"]) == 1
    capsys.readouterr()
    incomplete = tmp_path / "b.csv"
    incomplete.write_text("id,status,finding_ref,justification\n1.1.1,pass,,\n", encoding="utf-8")
    assert main(["asvs", "check-assessment", str(incomplete), "--level", "1", "--format", "json"]) == 1
    rep = json.loads(capsys.readouterr().out)
    assert not rep["complete"] and len(rep["missing"]) == 70
    assert main(["asvs", "check-assessment", str(tmp_path / "nope.json"), "--level", "1"]) == 2


def test_cli_map_findings(tmp_path, capsys):
    f = tmp_path / "findings.json"
    f.write_text(json.dumps([{"id": "F-1", "title": "Stack trace in error page"}]), encoding="utf-8")
    assert main(["asvs", "map-findings", str(f), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "Suggestions only" in data["note"]
    assert data["results"][0]["candidates"][0]["id"] == "16.5.1"
    assert main(["asvs", "map-findings", str(f)]) == 0
    assert "SUGGESTIONS ONLY" in capsys.readouterr().out


def test_extraction_script_is_reproducible():
    import shutil
    import subprocess
    import sys

    if not shutil.which("pdftotext") or not (ROOT / "sources/pdfs/owasp-asvs-5-0-0-en.pdf").is_file():
        pytest.skip("pdftotext or pinned PDF unavailable")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/extract/asvs.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_grade_covers_scope():
    text = " ".join(r["id"] for r in asvs.select(1, ["V2"]))
    assert asvs.grade_covers_scope(text, {"level": 1, "chapters": ["V2"]})[0]
    ok, detail = asvs.grade_covers_scope(text, {"level": 2, "chapters": ["V2"]})
    assert not ok and "missing" in detail


def test_claimed_levels_ignores_version_strings():
    assert asvs.claimed_levels("OWASP ASVS 5.0.0 Level 1 checklist; 1.2.4 (L1)") == [("1.2.4", 1)]


def test_check_assessment_scalar_scope():
    res = _results()
    rep = asvs.check_assessment({"target_level": 1, "scope": "V6", "results": res})
    assert rep["scope"] == ["V6"] and rep["compliant"]
    assert rep["totals"]["in_scope"] == len(res)
    assert asvs.normalize_scope("V6") == ["V6"]
    assert asvs.check_assessment({"target_level": 1, "scope": "all chapters", "results": res})["scope"] == \
        ["V1-V17 (all)"]
