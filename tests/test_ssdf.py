"""Tests for the NIST SP 800-218 (SSDF 1.1) catalog and tools."""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

from agentlib.cli import main
from agentlib.frameworks import ssdf

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "evals" / "nist-ssdf" / "fixtures"


# ----------------------------------------------------------------- catalog integrity
def test_catalog_counts_match_document():
    cat = ssdf.catalog()
    assert cat["catalog_id"] == "nist-ssdf" and cat["source_id"] == "nist-ssdf"
    assert [g["id"] for g in cat["groups"]] == ["PO", "PS", "PW", "RV"]
    per_group = {g: len([p for p in ssdf.practices() if p["group"] == g]) for g in ("PO", "PS", "PW", "RV")}
    assert per_group == {"PO": 5, "PS": 3, "PW": 8, "RV": 3}
    assert len(ssdf.practices()) == 19
    assert len(ssdf.tasks()) == 42
    assert {g: len(ssdf.tasks(group=g)) for g in ("PO", "PS", "PW", "RV")} == {"PO": 13, "PS": 4, "PW": 16, "RV": 9}
    retired = {i["id"] for i in cat["items"] if i["status"] == "retired"}
    # SSDF 1.1 Change Log (PDF p.36) retired these identifiers
    assert retired == {"PW.3", "PW.3.1", "PW.3.2", "PW.4.3", "PW.4.5", "PW.5.2"}


def test_catalog_ids_pages_and_structure():
    cat = ssdf.catalog()
    ids = [i["id"] for i in cat["items"]]
    assert len(ids) == len(set(ids))
    practice_ids = {p["id"] for p in ssdf.practices(active_only=False)}
    for it in cat["items"]:
        assert re.fullmatch(r"(PO|PS|PW|RV)\.\d+(\.\d+)?", it["id"])
        assert 14 <= it["citation"]["pdf_page"] <= 28  # Table 1
        assert it["citation"]["printed_page"] == it["citation"]["pdf_page"] - 9
        if it["kind"] == "task":
            assert it["practice"] in practice_ids
            assert it["id"].startswith(it["practice"] + ".")
            if it["status"] == "active":
                assert it["examples"] and it["references"]
                assert all(r["ref"] and r["text"] for r in it["references"])
    for g in cat["groups"]:
        assert g["citation"]["pdf_page"] == 13


@pytest.mark.parametrize("tid,page,start,n_examples", [
    ("PO.1.1", 14, "Identify and document all security requirements for the organization’s software development", 4),
    ("PO.1.2", 14, "Identify and document all security requirements for organization-developed software", 7),
    ("PO.5.1", 17, "Separate and protect each environment involved in software development.", 10),
    ("PS.2.1", 19, "Make software integrity verification information available to software acquirers.", 3),
    ("PW.4.4", 22, "Verify that acquired commercial, open-source, and all other third-party software components", 7),
    ("PW.9.1", 25, "Define a secure baseline", 1),
    ("RV.1.3", 26, "Have a policy that addresses vulnerability disclosure and remediation", 4),
    ("RV.3.4", 27, "Review the SDLC process", 2),
])
def test_spot_check_tasks_against_pdf(tid, page, start, n_examples):
    t = ssdf.items_by_id()[tid]
    assert t["citation"]["pdf_page"] == page
    assert t["text"].startswith(start)
    assert len(t["examples"]) == n_examples


def test_references_and_moves():
    by = ssdf.items_by_id()
    refs = {r["ref"]: r["text"] for r in by["PO.1.1"]["references"]}
    assert refs["SP80053"] == "SA-1, SA-8, SA-15, SR-3"
    assert refs["BSAFSS"] == "SM.3, DE.1, IA.1, IA.2"
    assert by["PO.1.3"]["formerly"] == "PW.3.1"
    assert by["PW.1.3"]["formerly"] == "PW.4.3"
    assert by["PW.4.3"]["moved_to"] == ["PW.1.3"]
    assert by["PW.3"]["kind"] == "practice" and by["PW.3"]["status"] == "retired"
    # footnote superscripts must not leak into text
    assert not re.search(r"[a-z]\d\b", by["PS.3.2"]["text"].replace("SBOM", ""))
    assert "zero trust architecture." in by["PO.5.1"]["examples"][-1]


def test_eo14028_mapping():
    m = ssdf.eo_mapping()
    assert len(m) == 15
    assert m["4e(vii)"] == ["PS.3.2"]
    assert isinstance(m["4e(ix)"], str)
    assert ssdf.eo_subsections("PS.3.2") == ["4e(vi)", "4e(vii)", "4e(x)"]
    for ids in m.values():
        if isinstance(ids, list):
            assert all(i in ssdf.active_task_ids() for i in ids)


def test_catalog_reproducible_from_pdf():
    pytest.importorskip("pdfplumber")
    import importlib.util

    spec = importlib.util.spec_from_file_location("ssdf_extract", ROOT / "scripts" / "extract" / "ssdf.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.extract() == json.loads((ROOT / "catalog" / "nist-ssdf.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------- lookup
def test_get_and_render():
    assert ssdf.get("pw.4.1")["id"] == "PW.4.1"
    assert ssdf.get("RV")["kind"] == "group"
    text = ssdf.render_item(ssdf.get("PS.3.2"))
    assert "PDF p.19" in text and "4e(vii)" in text and "Informative references" in text
    assert "RETIRED" in ssdf.render_item(ssdf.get("PW.5.2"))
    assert "PO.1.1" in ssdf.render_item(ssdf.get("PO.1"))
    with pytest.raises(ssdf.SSDFError):
        ssdf.get("PW.10.1")


def test_list_items_filters():
    pw = ssdf.list_items("PW")
    assert {i["group"] for i in pw} == {"PW"}
    assert not any(i["status"] == "retired" for i in pw)
    assert any(i["status"] == "retired" for i in ssdf.list_items("PW", include_retired=True))
    with pytest.raises(ssdf.SSDFError):
        ssdf.list_items("XX")


# ----------------------------------------------------------------- template
@pytest.mark.parametrize("fmt", ["md", "csv", "yaml"])
def test_template_round_trips_as_unassessed(tmp_path, fmt):
    text = ssdf.assessment_template(fmt)
    path = tmp_path / f"t.{fmt}"
    path.write_text(text, encoding="utf-8")
    meta, rows = ssdf.load_assessment(path)
    assert len(rows) == 42
    res = ssdf.check_assessment(meta, rows)
    assert len(res.errors) == 42  # every status empty
    assert res.scores["overall"]["coverage_pct"] == 0.0


def test_template_csv_columns():
    rows = list(csv.DictReader(io.StringIO(ssdf.assessment_template("csv"))))
    assert list(rows[0]) == ssdf.TEMPLATE_COLUMNS
    assert rows[-1]["id"] == "RV.3.4"
    with pytest.raises(ssdf.SSDFError):
        ssdf.assessment_template("docx")


# ----------------------------------------------------------------- check-assessment
def _full(status="implemented", **extra):
    return [{"id": t, "status": status, "evidence": ["doc"], **extra} for t in ssdf.active_task_ids()]


def test_check_all_implemented_scores_100():
    res = ssdf.check_assessment({}, _full())
    assert not res.findings
    assert res.scores["overall"]["coverage_pct"] == 100.0
    assert res.gaps == []


def test_check_detects_each_problem():
    rows = _full()
    rows[0] = {"id": "PO.1.1", "status": "implemented", "evidence": ""}           # no evidence
    rows[1] = {"id": "PO.1.2", "status": "not-applicable"}                         # no justification
    rows[2] = {"id": "PO.1.3", "status": "done-ish", "evidence": "x"}              # invalid status
    rows.append({"id": "PW.10.1", "status": "implemented", "evidence": "x"})       # unknown
    rows.append({"id": "PW.4.5", "status": "implemented", "evidence": "x"})        # retired
    rows.append({"id": "PO.2.1", "status": "implemented", "evidence": "x"})        # duplicate
    rows.append({"status": "implemented"})                                        # no id
    rows = [r for r in rows if r.get("id") != "RV.3.4"]                            # missing
    rows[5] = {"id": rows[5]["id"], "status": "planned"}                           # planned w/o owner/date
    res = ssdf.check_assessment({}, rows, today=date(2026, 10, 13))
    msgs = {(f.id, f.message.split(" (")[0]) for f in res.findings}
    assert ("PO.1.1", "status 'implemented' without evidence") in msgs
    assert ("PO.1.2", "status 'not-applicable' without justification") in msgs
    assert any(f.id == "PO.1.3" and "invalid status" in f.message for f in res.findings)
    assert ("PW.10.1", "unknown SSDF v1.1 task id") in msgs
    assert any(f.id == "PW.4.5" and "retired" in f.message and "PW.4.1" in f.message for f in res.findings)
    assert ("PO.2.1", "duplicate row for this task") in msgs
    assert any(f.id == "row 46" or f.message == "row has no task id" for f in res.findings)
    assert ("RV.3.4", "task missing from assessment") in msgs
    assert any(f.level == "warning" and "planned without an owner" in f.message for f in res.findings)
    # conservative scoring: unevidenced and unjustified rows earn nothing and appear as gaps
    gap_ids = {g["id"]: g for g in res.gaps}
    assert gap_ids["PO.1.1"]["status"] == "unevidenced"
    assert gap_ids["PO.1.2"]["status"] == "unassessed"
    assert gap_ids["RV.3.4"]["tier"] == "Medium"  # no EO 14028 specific subsection


def test_scoring_and_prioritisation():
    rows = _full()
    by = {r["id"]: r for r in rows}
    by["PS.3.2"].update(status="not-implemented", evidence=[])      # EO-mapped -> High
    by["RV.3.2"].update(status="not-implemented", evidence=[])      # not EO-mapped -> Medium
    by["PW.6.1"].update(status="not-applicable", justification="interpreted language only")
    by["PW.6.2"].update(status="partial")
    by["PW.9.1"].update(status="planned", evidence=[], owner="A", target_date="2027-01-01")
    res = ssdf.check_assessment({}, list(by.values()), today=date(2026, 10, 13))
    assert not res.errors
    o = res.scores["overall"]
    assert o["applicable"] == 41
    assert o["coverage_pct"] == round(100 * (37 + 0.5) / 41, 1)
    assert res.scores["practices"]["PW.6"]["coverage_pct"] == 50.0
    assert [g["id"] for g in res.gaps] == ["PS.3.2", "RV.3.2", "PW.9.1", "PW.6.2"]
    assert [g["tier"] for g in res.gaps] == ["High", "Medium", "Low", "Low"]


def test_past_target_date_and_bad_date_warn():
    rows = _full()
    rows[0].update(status="planned", owner="x", target_date="2020-01-01")
    rows[1].update(status="planned", owner="x", target_date="next week")
    res = ssdf.check_assessment({}, rows, today=date(2026, 10, 13))
    warns = [f.message for f in res.findings if f.level == "warning"]
    assert any("in the past" in w for w in warns)
    assert any("not YYYY-MM-DD" in w for w in warns)


def test_status_aliases_and_md_parsing(tmp_path):
    md = "| id | status | evidence | justification |\n|---|---|---|---|\n| PO.1.1 | N/A | | not developing |\n| PO.1.2 | Not Implemented | | |\n"
    p = tmp_path / "a.md"
    p.write_text(md, encoding="utf-8")
    _, rows = ssdf.load_assessment(p)
    res = ssdf.check_assessment({}, rows)
    assert res.rows["PO.1.1"]["status"] == "not-applicable"
    assert res.rows["PO.1.2"]["status"] == "not-implemented"


@pytest.mark.parametrize("content,suffix", [("tasks: 5", ".yaml"), ("[1, 2]", ".json"), ("no table", ".md"), (": :", ".yaml")])
def test_load_assessment_errors(tmp_path, content, suffix):
    p = tmp_path / f"bad{suffix}"
    p.write_text(content, encoding="utf-8")
    with pytest.raises(ssdf.SSDFError):
        ssdf.load_assessment(p)
    with pytest.raises(ssdf.SSDFError):
        ssdf.load_assessment(tmp_path / "missing.yaml")
    (tmp_path / "x.txt").write_text("x")
    with pytest.raises(ssdf.SSDFError):
        ssdf.load_assessment(tmp_path / "x.txt")


def test_fixture_assessment():
    meta, rows = ssdf.load_assessment(FIX / "acme-assessment.yaml")
    res = ssdf.check_assessment(meta, rows, today=date(2026, 10, 13))
    assert {f.id for f in res.errors} == {"PO.3.3", "PW.4.2", "RV.3.4"}
    assert res.scores["overall"]["coverage_pct"] == 50.0
    assert [g["id"] for g in res.gaps if g["tier"] == "High"] == ["PO.4.2", "PS.2.1", "PW.8.2", "RV.3.3", "PO.1.3", "RV.1.3"]


def test_evidence_matrix_content():
    meta, rows = ssdf.load_assessment(FIX / "acme-assessment.yaml")
    res = ssdf.check_assessment(meta, rows)
    md = ssdf.evidence_matrix(res)
    assert "Acme Payments Ltd" in md and "not an attestation form" in md
    assert md.count("| PO.") == 13 and "## RV - Respond to Vulnerabilities" in md
    assert "**none**" in md  # PO.3.3 implemented without evidence is visible
    assert "Open validation issues" in md
    ok, _ = ssdf.grade_no_overclaim(md, {})
    assert ok


# ----------------------------------------------------------------- pipeline mapping
def test_map_pipeline_fixture():
    res = ssdf.map_pipeline(ssdf.load_pipeline(FIX / "acme-pipeline.yaml"))
    sup = {t["id"]: t for t in res["tasks"]}
    assert sup["PW.7.2"]["support"] == "supported"
    assert sup["PW.4.4"]["support"] == "supported"
    assert sup["RV.1.2"]["support"] == "supported"        # scheduled SAST
    assert sup["PO.4.2"]["support"] == "supported"        # blocking gate
    assert sup["RV.1.1"]["support"] == "no-supporting-control"  # SCA not scheduled
    assert sup["PS.2.1"]["support"] == "no-supporting-control"  # signing step disabled
    assert sup["PW.8.2"]["support"] == "no-supporting-control"
    assert res["disabled_steps"] == ["Cosign image signing"]
    assert res["unmapped_steps"][0]["step"].startswith("Checkov")
    assert sum(res["counts"].values()) == 42


def test_map_pipeline_shapes_and_interpretive():
    res = ssdf.map_pipeline({"controls": ["secret-scanning", "Dependency Pinning"]})
    by = {t["id"]: t["support"] for t in res["tasks"]}
    assert by["PW.7.2"] == "interpretive-support"
    assert by["PW.4.1"] == "interpretive-support"
    res = ssdf.map_pipeline({"pipeline": {"steps": [{"tool": "cosign"}, {"type": "sbom"}]}})
    by = {t["id"]: t["support"] for t in res["tasks"]}
    assert by["PS.2.1"] == by["PS.3.2"] == "supported"
    for bad in ({}, {"pipeline": {"steps": []}}, {"pipeline": "x"}, {"steps": [5]}):
        with pytest.raises(ssdf.SSDFError):
            ssdf.map_pipeline(bad)


def test_rules_reference_real_active_tasks():
    active = set(ssdf.active_task_ids())
    seen_aliases = set()
    for r in ssdf.PIPELINE_RULES:
        for d in (r.tasks, r.scheduled_tasks, r.blocking_tasks):
            for tid, (basis, note) in d.items():
                assert tid in active, (r.control, tid)
                assert basis in ("example", "interpretive")
                assert note
        for a in (r.control,) + r.aliases:
            key = ssdf._norm_control(a)
            assert key not in seen_aliases, a
            seen_aliases.add(key)
    assert ssdf.ORGANISATIONAL_TASKS <= active


# ----------------------------------------------------------------- graders
def test_grade_ids_valid():
    assert ssdf.grade_ids_valid("Fix PW.7.2 and PS.3.2.", {"min": 2})[0]
    assert not ssdf.grade_ids_valid("Implement PW.10.1", {})[0]
    assert not ssdf.grade_ids_valid("Do PW.4.5 now; and PW.4.1", {})[0]
    assert ssdf.grade_ids_valid("PW.4.5 was retired (moved to PW.4.1)", {"allow_retired": True})[0]
    assert ssdf.grade_practice_ids_valid("PO.1 and PW.9", {"min": 2})[0]
    assert not ssdf.grade_practice_ids_valid("PW.12 practice", {})[0]


def test_grade_overclaim():
    assert not ssdf.grade_no_overclaim("The pipeline is SSDF compliant.", {})[0]
    assert not ssdf.grade_no_overclaim("We are fully compliant with SP 800-218.", {})[0]
    assert ssdf.grade_no_overclaim("This does not make the pipeline SSDF compliant.", {})[0]
    assert ssdf.grade_no_overclaim("Coverage is 50%.", {})[0]


def test_grade_page_citations():
    assert ssdf.grade_page_citations("PS.3.2 (p.19) and PO.5.1 (PDF p.18)", {"min": 2})[0]
    assert not ssdf.grade_page_citations("PS.3.2 (p.12)", {})[0]


def test_grade_assessment_numbers_and_pipeline_gaps():
    chk = {"fixture": "evals/nist-ssdf/fixtures/acme-assessment.yaml"}
    good = "Coverage 50.0%. Errors: PO.3.3, PW.4.2, RV.3.4. High: PO.4.2 PS.2.1 PW.8.2 RV.3.3 PO.1.3 RV.1.3"
    assert ssdf.grade_assessment_numbers(good, chk)[0]
    assert not ssdf.grade_assessment_numbers(good.replace("50.0", "53.8"), chk)[0]
    pchk = {"fixture": "evals/nist-ssdf/fixtures/acme-pipeline.yaml"}
    res = ssdf.map_pipeline(ssdf.load_pipeline(FIX / "acme-pipeline.yaml"))
    gaps = [t["id"] for t in res["tasks"] if t["support"] == "no-supporting-control" and not t["organisational"]]
    assert ssdf.grade_pipeline_gaps("No supporting control: " + ", ".join(gaps), pchk)[0]
    assert not ssdf.grade_pipeline_gaps("Gaps: PW.8.2", pchk)[0]
    assert not ssdf.grade_pipeline_gaps("No control: " + ", ".join(gaps) + "\nPS.2.1 is covered by signing", pchk)[0]


# ----------------------------------------------------------------- CLI
def test_cli_list_show(capsys):
    assert main(["ssdf", "list", "--group", "RV"]) == 0
    out = capsys.readouterr().out
    assert "RV.3.4" in out and "PW." not in out
    assert main(["ssdf", "show", "PW.4.4"]) == 0
    assert "Notional implementation examples" in capsys.readouterr().out
    assert main(["ssdf", "show", "PW.4.4", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "PW.4.4"
    assert main(["ssdf", "show", "ZZ.9"]) == 2
    assert main(["ssdf", "list", "--format", "json", "--all"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 19 + 42 + 6


def test_cli_template_check_matrix(tmp_path, capsys):
    out = tmp_path / "t.yaml"
    assert main(["ssdf", "assessment-template", "--format", "yaml", "--out", str(out)]) == 0
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    for row in data["tasks"]:
        row.update(status="implemented", evidence=["evidence"])
    out.write_text(yaml.safe_dump(data), encoding="utf-8")
    capsys.readouterr()
    assert main(["ssdf", "check-assessment", str(out)]) == 0
    assert "Coverage: 100.0%" in capsys.readouterr().out
    fx = str(FIX / "acme-assessment.yaml")
    assert main(["ssdf", "check-assessment", fx, "--format", "json", "--today", "2026-10-13"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["valid"] is False and data["scores"]["overall"]["coverage_pct"] == 50.0
    em = tmp_path / "m.md"
    assert main(["ssdf", "evidence-matrix", fx, "--out", str(em)]) == 0
    assert "SSDF v1.1 evidence matrix" in em.read_text(encoding="utf-8")
    assert main(["ssdf", "check-assessment", str(tmp_path / "nope.yaml")]) == 2


def test_cli_pipeline(tmp_path, capsys):
    assert main(["ssdf", "map-pipeline", str(FIX / "acme-pipeline.yaml")]) == 0
    out = capsys.readouterr().out
    assert "Support != compliance" in out and "Tasks with no supporting control" in out
    assert main(["ssdf", "map-pipeline", str(FIX / "acme-pipeline.yaml"), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["supported"] == 8
    assert main(["ssdf", "pipeline-controls"]) == 0
    assert "secret-scanning" in capsys.readouterr().out
    bad = tmp_path / "p.yaml"
    bad.write_text("pipeline: {steps: []}", encoding="utf-8")
    assert main(["ssdf", "map-pipeline", str(bad)]) == 2


def test_skill_rule_reference_in_sync():
    ref = (ROOT / "skills" / "nist-ssdf" / "references" / "pipeline-mapping-rules.md").read_text(encoding="utf-8")
    table = ssdf.render_rules().split("Support != compliance.\n\n", 1)[1]
    assert table.strip() in ref, "regenerate the Rules table in references/pipeline-mapping-rules.md"


def test_grade_page_citation_formats():
    assert ssdf.grade_page_citations("PW.7.2, PDF p.23 and PO.5.1 [PDF p. 18]", {"min": 2})[0]
    # a different page mentioned later in the sentence is not attributed to the task
    assert ssdf.grade_page_citations("PS.3.2 (p.19) maps to 4e(vii) (PDF p.33)", {"min": 1})[0]
