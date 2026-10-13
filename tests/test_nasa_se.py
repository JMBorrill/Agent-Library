"""Tests for the NASA SE Handbook framework: catalogs, tools, graders and CLI."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agentlib.cli import main
from agentlib.frameworks import nasa_se as n
from agentlib.paths import load_catalog, repo_root
from agentlib.validate import check_catalogs

ROOT = repo_root()
PAGES = 356
OFFSET = 13


# ----------------------------------------------------------------------------- catalogs
@pytest.fixture(scope="module")
def procs():
    return load_catalog("nasa-se-processes")


@pytest.fixture(scope="module")
def life():
    return load_catalog("nasa-se-lifecycle")


@pytest.fixture(scope="module")
def chk():
    return load_catalog("nasa-requirements-checklist")


def _entries(cat):
    return cat.get("groups", []) + cat["items"]


@pytest.mark.parametrize("cid", ["nasa-se-processes", "nasa-se-lifecycle", "nasa-requirements-checklist"])
def test_catalog_schema_ids_and_pages(cid):
    cat = load_catalog(cid)
    assert cat["source_id"] == "nasa-se"
    assert cat["catalog_id"] == cid
    issues = [i for i in check_catalogs(ROOT) if cid in i.path]
    assert not issues, issues
    ids = [i["id"] for i in cat["items"]]
    assert len(ids) == len(set(ids))
    for e in _entries(cat):
        c = e["citation"]
        assert 1 <= c["pdf_page"] <= PAGES
        if "printed_page" in c:
            assert c["printed_page"] == c["pdf_page"] - OFFSET


def test_processes_structure(procs):
    items = procs["items"]
    assert [i["number"] for i in items] == list(range(1, 18))
    groups = {g["id"]: g for g in procs["groups"]}
    assert set(groups) == {"system-design", "product-realization", "technical-management"}
    by_group = {g: [i["number"] for i in items if i["group"] == g] for g in groups}
    assert by_group == {"system-design": [1, 2, 3, 4], "product-realization": [5, 6, 7, 8, 9],
                        "technical-management": list(range(10, 18))}
    for i in items:
        assert i["inputs"] and i["outputs"] and i["activities"] and len(i["text"]) > 40
        for a in i["activities"]:
            assert a["pdf_page"] >= i["citation"]["pdf_page"]


def test_process_known_pages(procs):
    pages = {i["id"]: i["citation"]["pdf_page"] for i in procs["items"]}
    assert pages["stakeholder-expectations-definition"] == 66   # printed 53
    assert pages["technical-requirements-definition"] == 76
    assert pages["requirements-management"] == 163
    assert pages["decision-analysis"] == 206
    acts = {i["id"]: [a["title"] for a in i["activities"]] for i in procs["items"]}
    assert "Validate Technical Requirements" in acts["technical-requirements-definition"]
    assert "Conduct Configuration Audits" in acts["configuration-management"]
    assert len(acts["design-solution-definition"]) == 10
    assert procs["parameters"]["engine"]["citation"]["pdf_page"] == 19


def test_lifecycle_structure(life):
    kinds = {}
    for i in life["items"]:
        kinds.setdefault(i["kind"], []).append(i["id"])
    assert kinds["phase"] == ["pre-phase-a", "phase-a", "phase-b", "phase-c", "phase-d", "phase-e", "phase-f"]
    assert kinds["kdp"] == [f"KDP-{x}" for x in "ABCDEF"]
    assert len(kinds["review"]) == 16
    assert {"MCR", "SRR", "MDR-SDR", "PDR", "CDR", "PRR", "SIR", "TRR", "SAR", "ORR", "FRR", "DR", "DRR"} <= set(
        kinds["review"])
    assert kinds["trl"] == [f"TRL-{k}" for k in range(1, 10)]
    rv = {i["id"]: i for i in life["items"] if i["kind"] == "review"}
    assert rv["PDR"]["phases"] == ["phase-b"] and rv["PDR"]["criteria_reference"] == "NPR 7123.1 Table G-6"
    assert rv["CDR"]["phases"] == ["phase-c"] and rv["SIR"]["phases"] == ["phase-c"]
    assert rv["MCR"]["citation"]["pdf_page"] == 200 and rv["PDR"]["citation"]["pdf_page"] == 201
    assert "design-to baseline" in rv["PDR"]["results"]
    assert "build-to baseline" in rv["CDR"]["results"]
    trl = {i["level"]: i["text"] for i in life["items"] if i["kind"] == "trl"}
    assert trl[6].startswith("System/subsystem model or prototype demonstration in a relevant environment")
    assert all(i["citation"]["pdf_page"] == 264 for i in life["items"] if i["kind"] == "trl")


def test_product_maturity_table(life):
    pm = life["parameters"]["se_product_maturity"]
    assert pm["citation"]["pdf_page"] == 35 and len(pm["columns"]) == 10
    rows = {r["product"]: r["cells"] for r in pm["rows"]}
    assert rows["SEMP"][1] == "**Baseline"            # SRR
    assert rows["Requirements"][1] == "**Baseline"
    assert rows["Design solution definition"][4] == "**Baseline"  # CDR
    assert rows["Verification and Validation results"][7] == "**Baseline"  # FRR
    srr = next(i for i in life["items"] if i["id"] == "SRR")
    required = {p["product"] for p in srr["product_maturity"] if p["required"]}
    assert required == {"SEMP", "Requirements"}


def test_checklist_structure(chk):
    groups = {}
    for i in chk["items"]:
        groups.setdefault(i["group"], []).append(i)
    appc = [i for i in chk["items"] if i["group"].startswith("c")]
    assert len(appc) == 55
    assert len(groups["c1-terms"]) == 3 and len(groups["c3-general-goodness"]) == 7
    assert len(groups["c4-reliability"]) == 5
    assert len(groups["metadata"]) == 7 and len(groups["verification-methods"]) == 4
    assert len(groups["validation-steps"]) == 6
    assert all(249 <= i["citation"]["pdf_page"] <= 252 for i in appc)
    p = chk["parameters"]
    assert "user-friendly" in p["unverifiable_terms"] and "and/or" in p["ambiguous_terms"]
    assert p["verification_methods"] == ["Test", "Analysis", "Inspection", "Demonstration"]
    assert p["unverifiable_terms_citation"]["pdf_page"] == 252
    unver = next(i for i in appc if i["id"] == "c4-verifiability-unverifiable-terms")
    assert "user-friendly" in unver["text"]


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext not installed")
def test_extraction_is_reproducible():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "extract" / "nasa_se.py"), "--check"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr + proc.stdout


# ----------------------------------------------------------------------------- linter
def R(text, rid="R-1", **kw):
    kw.setdefault("rationale", "because")
    kw.setdefault("verification", "Test")
    return n.Requirement(id=rid, text=text, **kw)


def rules(text, **kw):
    return {f.rule for f in n.lint_requirement(R(text, **kw))}


def test_clean_requirement_has_no_findings():
    assert rules("The spacecraft shall provide a downlink rate of at least 2 Mbps.") == set()


@pytest.mark.parametrize("text,rule", [
    ("The system will survive launch.", "no-shall"),
    ("The system should survive launch.", "no-shall"),
    ("The pump shall start and the valve shall open.", "multiple-shall"),
    ("The software shall log errors, etc.", "ambiguous-term"),
    ("The system shall support Ka and/or X band.", "ambiguous-term"),
    ("The GUI shall be user-friendly.", "unverifiable-term"),
    ("The system shall respond quickly to commands.", "unverifiable-term"),
    ("The rover shall be robust to dust.", "unverifiable-term"),
    ("The system shall automatically restart.", "ly-ize-word"),
    ("The software shall optimize power usage.", "ly-ize-word"),
    ("The bus shall store TBD GB of data.", "tbd"),
    ("The bus shall store 8 GB (TBR) of data.", "tbr"),
    ("The heater shall not exceed 40 C.", "negative-statement"),
    ("The data shall be transmitted to the ground station.", "passive-voice"),
    ("The operator shall verify the configuration.", "operational-statement"),
    ("The radio shall transmit telemetry and receive commands.", "compound-statement"),
    ("The radio shall transmit telemetry. This is needed for ops.", "multiple-sentences"),
    ("The battery shall supply 28 V.", "missing-tolerance"),
    ("These shall be logged by the computer.", "indefinite-pronoun"),
])
def test_rules_trigger(text, rule):
    assert rule in rules(text)


def test_appropriate_not_double_reported():
    fs = n.lint_requirement(R("The system shall restart as appropriate."))
    assert [f.rule for f in fs].count("ambiguous-term") == 1
    assert not any(f.rule == "unverifiable-term" for f in fs)


def test_bounded_quantity_not_flagged():
    assert "missing-tolerance" not in rules("The battery shall supply 28 V plus or minus 0.5 V.")
    assert "missing-tolerance" not in rules("The software shall comply with NPR 7150.2 class B.")


def test_missing_metadata_and_methods():
    r = n.Requirement(id=None, text="The system shall operate.", verification="Simulation")
    fs = {f.rule: f for f in n.lint_requirement(r)}
    assert {"missing-id", "missing-rationale", "invalid-verification-method"} <= set(fs)
    assert "Analysis" in fs["invalid-verification-method"].message
    assert fs["missing-id"].severity == "error"
    assert "p. 251" in fs["missing-id"].source
    r2 = n.Requirement(id="X-1", text="The system shall operate.", rationale="r")
    assert "missing-verification-method" in {f.rule for f in n.lint_requirement(r2)}
    assert not n.lint_requirement(r2, require_rationale=False, require_verification=False)


def test_empty_text_and_duplicates():
    fs = n.lint_requirements([R("", "A-1"), R("The x shall y.", "A-2"), R("The x shall z.", "A-2")])
    rs = [f.rule for f in fs]
    assert "empty-text" in rs and rs.count("duplicate-id") == 1


@pytest.mark.parametrize("value,valid,invalid", [
    ("Test", ["Test"], []), ("T/A", ["Test", "Analysis"], []), ("TAID", ["Test", "Analysis", "Inspection",
                                                                         "Demonstration"], []),
    ("analysis and inspection", ["Analysis", "Inspection"], []), ("Demo", ["Demonstration"], []),
    ("Review", [], ["Review"]), ("Simulation; Test", ["Test"], ["Simulation"]), ("", [], []),
])
def test_parse_methods(value, valid, invalid):
    assert n.parse_methods(value) == (valid, invalid)


def test_summary_and_render():
    fs = n.lint_requirements([R("The GUI shall be easy to use.")])
    s = n.summarise(fs, 1)
    assert s["errors"] == 1 and s["requirements_with_errors"] == 1
    assert "unverifiable-term" in n.render_findings(fs, s, "table")
    assert json.loads(n.render_findings(fs, s, "json"))["summary"]["errors"] == 1
    assert "| R-1 | error |" in n.render_findings(fs, s, "markdown")


# ----------------------------------------------------------------------------- parsing
def test_parse_formats(tmp_path):
    (tmp_path / "r.csv").write_text("Req ID,Shall Statement,Verification Method,Traced From\n"
                                    "S-1,The x shall y.,T,P-1\n", encoding="utf-8")
    (tmp_path / "r.yaml").write_text("requirements:\n  - id: S-1\n    text: The x shall y.\n    parent: [P-1, P-2]\n",
                                     encoding="utf-8")
    (tmp_path / "m.yml").write_text("S-1: The x shall y.\nS-2: {text: The x shall z., verification: A}\n",
                                    encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps([{"id": "S-1", "requirement": "The x shall y."}]), encoding="utf-8")
    (tmp_path / "t.md").write_text("| ID | Requirement | Parent |\n|---|---|---|\n| S-1 | The x shall y. | P-1 |\n",
                                   encoding="utf-8")
    (tmp_path / "r.tsv").write_text("id\ttext\nS-1\tThe x shall y.\n", encoding="utf-8")
    assert n.load_requirements(tmp_path / "r.csv")[0].parents == ["P-1"]
    assert n.load_requirements(tmp_path / "r.yaml")[0].parents == ["P-1", "P-2"]
    m = n.load_requirements(tmp_path / "m.yml")
    assert [r.id for r in m] == ["S-1", "S-2"] and m[1].verification == "A"
    assert n.load_requirements(tmp_path / "r.json")[0].text == "The x shall y."
    assert n.load_requirements(tmp_path / "t.md")[0].parents == ["P-1"]
    assert n.load_requirements(tmp_path / "r.tsv")[0].id == "S-1"


def test_parse_markdown_list_with_subfields():
    md = ("# Spec\n\n- **SYS-001**: The craft shall weigh no more than 12 kg.\n  - Rationale: launcher\n"
          "  - Verification: Inspection\n  - Parent: MRD-1, MRD-2\n- SYS-002: The craft shall fit the dispenser.\n"
          "\nThe battery shall hold 40 Wh minimum.\n")
    reqs = n.parse_markdown(md)
    assert [r.id for r in reqs] == ["SYS-001", "SYS-002", None]
    assert reqs[0].parents == ["MRD-1", "MRD-2"] and reqs[0].rationale == "launcher"
    assert reqs[0].verification == "Inspection"


@pytest.mark.parametrize("name,content", [
    ("x.docx", "irrelevant"), ("bad.csv", "foo,bar\n1,2\n"), ("empty.md", "# nothing here\n"),
    ("bad.yaml", "a: [unclosed\n"), ("bad.json", "{"), ("scalar.yaml", "42\n"),
])
def test_parse_errors(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    with pytest.raises(n.InputError):
        n.load_requirements(p)


def test_missing_file():
    with pytest.raises(n.InputError):
        n.load_requirements("/nonexistent/reqs.csv")


# ----------------------------------------------------------------------------- traceability
def T(rid, parents=(), level="", verification="T", children=(), status=""):
    return n.Requirement(id=rid, text=f"{rid} shall x.", parents=list(parents), level=level,
                         verification=verification, children=list(children), status=status)


def checks(rep):
    return {(f["req_id"], f["check"]) for f in rep["findings"]}


def test_trace_clean_hierarchy():
    reqs = [T("S-1", level="system"), T("S-2", level="system"), T("U-1", ["S-1"], "sub", status="pass"),
            T("U-2", ["S-2"], "sub", "A")]
    rep = n.trace(reqs)
    assert rep["summary"]["error"] == 0 and rep["summary"]["warning"] == 0
    st = rep["stats"]
    assert st["roots"] == ["S-1", "S-2"] and st["orphans"] == []
    assert st["verification_methods"]["Test"] == 3 and st["verification_methods"]["Analysis"] == 1
    assert st["verification_method_pct"] == 100.0 and st["verified_pct"] == 25.0
    mx = {r["id"]: r for r in rep["matrix"]}
    assert mx["S-1"]["children"] == ["U-1"]


def test_trace_problems():
    reqs = [T("S-1", level="system"), T("U-1", ["S-9"], "sub"), T("U-2", [], "sub"), T("U-3", ["self-derived"], "sub"),
            T("U-4", ["S-1"], "sub", verification=""), T("U-5", ["S-1"], "sub", verification="Review"),
            T("U-6", ["MRD-3"], "sub"), T("U-7", ["U-8"], "sub"), T("U-8", ["U-7"], "sub"), T("U-6", [], "sub")]
    rep = n.trace(reqs, external_prefixes=["MRD-"])
    c = checks(rep)
    assert ("U-1", "dangling-parent") in c and ("U-2", "orphan") in c
    assert ("U-3", "self-derived") in c and ("U-3", "orphan") not in c
    assert ("U-4", "no-verification-method") in c and ("U-5", "invalid-verification-method") in c
    assert ("U-6", "duplicate-id") in c and ("U-6", "dangling-parent") not in c
    assert ("U-7", "cycle") in c and ("U-8", "cycle") in c
    assert rep["stats"]["external_parent_links"] == 1


def test_trace_bidirectional_and_unallocated():
    reqs = [T("S-1", level="sys", children=["U-1", "U-2"]), T("S-2", level="sys"), T("U-1", ["S-1"], "sub"),
            T("U-2", [], "sub"), T("U-3", ["S-1"], "sub")]
    c = checks(n.trace(reqs))
    assert ("S-1", "one-way-link") in c          # U-2 does not trace back; U-3 not listed as child
    assert ("S-2", "not-allocated") in c
    assert ("S-1", "self-reference") not in c


def test_trace_no_levels_and_top_level_option():
    rep = n.trace([T("A-1"), T("A-2", ["A-1"]), T("A-3")])
    assert rep["stats"]["roots"] == ["A-1"] and rep["stats"]["orphans"] == ["A-3"]
    rep2 = n.trace([T("A-1", level="L1"), T("B-1", level="L2")], top_levels=["L2"])
    assert rep2["stats"]["orphans"] == ["A-1"]
    rep3 = n.trace([n.Requirement(id=None, text="x shall y")])
    assert ("(line 0)", "missing-id") in checks(rep3)


def test_render_trace_formats():
    rep = n.trace([T("S-1", level="sys"), T("U-1", ["S-1"], "sub")])
    assert "TRACEABILITY MATRIX" in n.render_trace(rep, "table", matrix=True)
    assert "## Traceability matrix" in n.render_trace(rep, "markdown", matrix=True)
    assert json.loads(n.render_trace(rep, "json"))["stats"]["requirements"] == 2


# ----------------------------------------------------------------------------- reviews
@pytest.mark.parametrize("rid", ["MCR", "SRR", "MDR", "SDR", "mdr/sdr", "PDR", "cdr", "PRR", "SIR", "TRR", "SAR",
                                 "ORR", "FRR", "MRR", "PLAR", "CERR", "PFAR", "DR", "DRR"])
def test_review_checklist_renders(rid):
    md = n.render_review_checklist(n.review_checklist(rid, "Demo"))
    assert md.startswith("# ") and "## Limitations" in md and "nasa-se" in md
    assert "- [ ]" in md


def test_review_checklist_content():
    pdr = n.render_review_checklist(n.review_checklist("PDR"))
    assert "NPR 7123.1 Table G-6" in pdr and "**Design solution definition** - maturity: **Preliminary**" in pdr
    assert "Phase B" in pdr and "Requirements validation" in pdr
    srr = n.render_review_checklist(n.review_checklist("SRR"))
    assert "**SEMP** - maturity: **Baseline**" in srr and "SEMP is baselined at SRR" in srr
    trr = n.render_review_checklist(n.review_checklist("TRR"))
    assert "## Test readiness" in trr and "does not list product maturity" in trr
    with pytest.raises(KeyError):
        n.find_review("XYZ")


# ----------------------------------------------------------------------------- trade study
SPEC = {"criteria": [{"name": "Cost", "weight": 40}, {"name": "Mass", "weight": 60},
                     {"name": "Fits", "mandatory": True}],
        "alternatives": [{"name": "A", "scores": {"Cost": 5, "Mass": 5, "Fits": "yes"}},
                         {"name": "B", "scores": {"Cost": 9, "Mass": 7, "Fits": True}},
                         {"name": "C", "scores": {"Cost": 10, "Mass": 10, "Fits": "no"}}]}


def test_trade_study_ranking_and_mandatory():
    res = n.trade_study(SPEC)
    assert [e["name"] for e in res["ranking"]] == ["B", "A"]
    assert res["ranking"][0]["weighted_total"] == pytest.approx(0.4 * 9 + 0.6 * 7)
    assert res["disregarded"][0]["name"] == "C" and res["recommended"] == "B"
    assert res["weights"] == {"Cost": 0.4, "Mass": 0.6}
    md = n.render_trade(res, "markdown")
    assert n.grade_decision_matrix(md, {})[0]


def test_trade_study_close_and_errors():
    spec = {"criteria": [{"name": "X", "weight": 3}],
            "alternatives": [{"name": "A", "scores": {"X": 10}}, {"name": "B", "scores": {"X": 9.8}}]}
    res = n.trade_study(spec)
    assert res["closely_ranked"] and res["recommended"] is None
    assert any("normalised" in s for s in res["notes"])
    with pytest.raises(n.InputError):
        n.trade_study({"criteria": [{"name": "X", "weight": 1}], "alternatives": [{"name": "A", "scores": {}}]})
    with pytest.raises(n.InputError):
        n.trade_study({"criteria": [{"name": "X", "weight": "heavy"}], "alternatives": [{"name": "A",
                                                                                         "scores": {"X": 1}}]})
    with pytest.raises(n.InputError):
        n.trade_study({"criteria": [], "alternatives": []})


def test_trade_from_csv_rows():
    spec = n._trade_from_rows([["alternative", "Cost", "Fits"], ["weight", "1", ""], ["mandatory", "no", "yes"],
                               ["A", "3", "yes"], ["B", "4", "no"]])
    res = n.trade_study(spec)
    assert res["recommended"] == "A" and res["disregarded"][0]["name"] == "B"


# ----------------------------------------------------------------------------- listings
def test_listings():
    assert n.render_processes("table").count("\n") == 17
    assert "| 17 | Decision Analysis |" in n.render_processes("markdown")
    assert len(json.loads(n.render_processes("json", group="product-realization"))) == 5
    assert "Requirements Management" in n.render_processes("table", ident="11")
    with pytest.raises(KeyError):
        n.render_processes("table", ident="99")
    assert len(json.loads(n.render_lifecycle("json", "trl"))) == 9
    assert "| PDR | review |" in n.render_lifecycle("markdown", "review")
    ck = n.render_req_checklist()
    assert ck.count("- [ ]") == 55 and "## C.4 Validation: Clarity" in ck


# ----------------------------------------------------------------------------- graders
GOOD_REQS = """| ID | Requirement | Rationale | Verification |
|---|---|---|---|
| SYS-1 | The spacecraft shall provide a downlink rate of at least 2 Mbps. | data volume | Test |
| SYS-2 | The spacecraft shall have a mass of no more than 12 kg. | launcher | Inspection |
"""
BAD_REQS = GOOD_REQS + "| SYS-3 | The GUI shall be user-friendly and/or fast. | | Review |\n"


def test_grade_requirements_quality():
    assert n.grade_requirements_quality(GOOD_REQS, {"min_requirements": 2, "require_rationale": True})[0]
    ok, detail = n.grade_requirements_quality(BAD_REQS, {"min_requirements": 2})
    assert not ok and "SYS-3" in detail
    assert not n.grade_requirements_quality("no requirements here", {})[0]
    assert not n.grade_requirements_quality(GOOD_REQS, {"min_requirements": 5})[0]


def test_grade_verification_methods():
    assert n.grade_verification_methods(GOOD_REQS.replace("Verification", "Verification Method"), {"min_rows": 2})[0]
    assert not n.grade_verification_methods(BAD_REQS.replace("Verification", "Method"), {})[0]
    assert not n.grade_verification_methods("no table", {})[0]


def test_grade_trace():
    good = ("| ID | Level | Parent | Verification method |\n|---|---|---|---|\n| S-1 | system | MRD-1 | Test |\n"
            "| U-1 | subsystem | S-1 | Analysis |\n")
    assert n.grade_trace(good, {"external_prefixes": ["MRD-"], "min_requirements": 2})[0]
    bad = good + "| U-2 | subsystem | S-9 | Test |\n| U-3 | subsystem | | Test |\n"
    ok, detail = n.grade_trace(bad, {"external_prefixes": ["MRD-"]})
    assert not ok and "dangling-parent" in detail and "orphan" in detail


def test_grade_review_phase_consistency():
    good = "| Review | Phase |\n|---|---|\n| PDR | Phase B |\n| CDR | Phase C |\n| MCR | Pre-Phase A |\n| SRR | Phase A |\n"
    assert n.grade_review_phase_consistency(good, {"min_reviews": 4})[0]
    bad = good.replace("| CDR | Phase C |", "| CDR | Phase B |")
    ok, detail = n.grade_review_phase_consistency(bad, {})
    assert not ok and "CDR" in detail
    assert not n.grade_review_phase_consistency("PDR is important.", {"min_reviews": 1})[0]


def test_grade_process_coverage(procs):
    names = "\n".join(f"- {p['title']}" for p in procs["items"])
    assert n.grade_process_coverage(names, {})[0]
    assert not n.grade_process_coverage(names + "\nThe engine has 16 processes.", {})[0]
    partial = "\n".join(f"- {p['title']}" for p in procs["items"][:10])
    assert not n.grade_process_coverage(partial, {})[0]
    assert n.grade_process_coverage(partial, {"min": 10})[0]


def test_grade_decision_matrix():
    good = ("| Criterion | Weight | A | B |\n|---|---|---|---|\n| Cost | 0.4 | 5 | 9 |\n| Mass | 0.6 | 5 | 7 |\n"
            "| **Weighted total** | 1.0 | 5.0 | 7.8 |\n")
    assert n.grade_decision_matrix(good, {})[0]
    pct = good.replace("0.4", "40").replace("0.6", "60").replace("| 1.0 |", "| 100 |")
    assert n.grade_decision_matrix(pct, {})[0]
    assert not n.grade_decision_matrix(good.replace("7.8", "8.4"), {})[0]
    assert not n.grade_decision_matrix(good.replace("0.6", "0.9"), {})[0]
    assert not n.grade_decision_matrix("| a | b |\n|---|---|\n| 1 | 2 |\n", {})[0]


# ----------------------------------------------------------------------------- CLI
def test_cli_lint(tmp_path, capsys):
    good = tmp_path / "good.csv"
    good.write_text("id,text,rationale,verification\nS-1,The craft shall weigh no more than 12 kg.,launcher,"
                    "Inspection\n", encoding="utf-8")
    bad = tmp_path / "bad.csv"
    bad.write_text("id,text,rationale,verification\nS-1,The craft shall be easy to integrate.,x,T\n", encoding="utf-8")
    assert main(["nasa-se", "lint-requirements", str(good)]) == 0
    assert main(["nasa-se", "lint-requirements", str(bad)]) == 1
    assert main(["nasa-se", "lint-requirements", str(bad), "--fail-on", "never"]) == 0
    out = tmp_path / "lint.json"
    assert main(["nasa-se", "lint-requirements", str(bad), "--format", "json", "-o", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["summary"]["errors"] == 1 and data["findings"][0]["rule"] == "unverifiable-term"
    warn = tmp_path / "warn.csv"
    warn.write_text("id,text,verification\nS-1,The craft shall weigh no more than 12 kg.,I\n", encoding="utf-8")
    assert main(["nasa-se", "lint-requirements", str(warn)]) == 0
    assert main(["nasa-se", "lint-requirements", str(warn), "--fail-on", "warning"]) == 1
    assert main(["nasa-se", "lint-requirements", str(warn), "--fail-on", "warning", "--no-rationale"]) == 0
    assert main(["nasa-se", "lint-requirements", str(tmp_path / "missing.csv")]) == 2
    capsys.readouterr()


def test_cli_trace(tmp_path, capsys):
    f = tmp_path / "t.yaml"
    f.write_text("- {id: S-1, text: The x shall y., level: system, parent: NGO-1, verification: T}\n"
                 "- {id: U-1, text: The x shall z., level: sub, parent: S-1, verification: A}\n", encoding="utf-8")
    assert main(["nasa-se", "trace", str(f), "--external", "NGO-"]) == 0
    assert main(["nasa-se", "trace", str(f), "--format", "markdown", "--matrix", "--external", "NGO-"]) == 0
    out = capsys.readouterr().out
    assert "## Traceability matrix" in out
    f.write_text("- {id: S-1, text: The x shall y., level: system}\n- {id: U-1, text: x, level: sub}\n",
                 encoding="utf-8")
    assert main(["nasa-se", "trace", str(f), "--format", "json"]) == 1
    rep = json.loads(capsys.readouterr().out)
    assert rep["stats"]["orphans"] == ["U-1"]
    assert main(["nasa-se", "trace", str(f), "--no-verification", "--top-level", "system", "--top-level", "sub"]) == 0


def test_cli_review_trade_listings(tmp_path, capsys):
    out = tmp_path / "pdr.md"
    assert main(["nasa-se", "review-checklist", "PDR", "--project", "X", "-o", str(out)]) == 0
    assert "Preliminary Design Review (PDR) readiness checklist: X" in out.read_text(encoding="utf-8")
    assert main(["nasa-se", "review-checklist", "CDR", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["review"]["id"] == "CDR"
    assert main(["nasa-se", "review-checklist", "NOPE"]) == 2
    spec = tmp_path / "trade.json"
    spec.write_text(json.dumps(SPEC), encoding="utf-8")
    assert main(["nasa-se", "trade-study", str(spec), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["recommended"] == "B"
    csvf = tmp_path / "trade.csv"
    csvf.write_text("alternative,Cost\nweight,1\nA,3\nB,4\n", encoding="utf-8")
    assert main(["nasa-se", "trade-study", str(csvf)]) == 0
    bad = tmp_path / "trade.yaml"
    bad.write_text("criteria: []\n", encoding="utf-8")
    assert main(["nasa-se", "trade-study", str(bad)]) == 2
    assert main(["nasa-se", "trade-study", str(tmp_path / "none.yaml")]) == 2
    capsys.readouterr()
    assert main(["nasa-se", "processes"]) == 0
    assert main(["nasa-se", "processes", "--id", "decision-analysis"]) == 0
    assert main(["nasa-se", "processes", "--id", "nope"]) == 2
    assert main(["nasa-se", "lifecycle", "--kind", "review", "--format", "markdown"]) == 0
    assert main(["nasa-se", "req-checklist", "-o", str(tmp_path / "c.md")]) == 0
    assert (tmp_path / "c.md").read_text(encoding="utf-8").count("- [ ]") == 55
