"""Tests for the NPR 7150.2D / NASA-STD-8739.8B catalogs and the ``nasa-swe`` tools."""
from __future__ import annotations

import csv
import io
import json
import re

import pytest
import yaml

from agentlib.cli import main
from agentlib.frameworks import nasa_swe as ns
from agentlib.paths import load_catalog

NPR_PAGES = 89
STD_PAGES = 65


# ------------------------------------------------------------------ catalog integrity
@pytest.fixture(scope="module")
def npr():
    return load_catalog("npr-7150-2d")


@pytest.fixture(scope="module")
def std():
    return load_catalog("nasa-std-8739-8b")


def test_npr_counts_and_ids(npr):
    items = npr["items"]
    ids = [i["id"] for i in items]
    assert len(ids) == 130 == len(set(ids))
    assert all(re.fullmatch(r"SWE-\d{3}", i) for i in ids)
    ch2 = [i for i in items if i["chapter"] == 2]
    assert len(ch2) == 30
    assert sum(1 for i in items if i["applicability"]) == 100
    assert all(i["applicability"] is None for i in ch2)


def test_npr_pages_in_range(npr):
    for it in npr["items"]:
        assert 11 <= it["citation"]["pdf_page"] <= 43, it["id"]
        assert all(1 <= p <= NPR_PAGES for p in it["pages"])
        if it["applicability"]:
            assert 56 <= it["applicability"]["citation"]["pdf_page"] <= 78


@pytest.mark.parametrize("swe,page,section,start", [
    ("SWE-033", 20, "3.1.2", "The project manager shall assess options for software acquisition versus development"),
    ("SWE-134", 26, "3.7.3", "If a project has safety-critical software or mission-critical software"),
    ("SWE-219", 26, "3.7.4", "If a project has safety-critical software, the project manager shall ensure that there is 100 percent"),
    ("SWE-220", 27, "3.7.5", "If a project has safety-critical software, the project manager shall ensure all identified"),
    ("SWE-086", 40, "5.2", "The project manager shall record, analyze, plan, track, control, and communicate"),
    ("SWE-150", 19, "2.2.7", "The engineering, CIO, and SMA authorities shall review and agree"),
    ("SWE-002", 11, "2.1.1.1", "The NASA OCE shall lead and maintain"),
])
def test_known_requirements(npr, swe, page, section, start):
    it = next(i for i in npr["items"] if i["id"] == swe)
    assert it["citation"]["pdf_page"] == page
    assert it["section"] == section
    assert it["text"].startswith(start)
    assert "[SWE-" not in it["text"]


def test_list_items_and_notes(npr):
    idx = {i["id"]: i for i in npr["items"]}
    assert "l. The software can place the system into a safe state." in idx["SWE-134"]["text"]
    assert "f. Release notes." in idx["SWE-148"]["text"]  # list item resumes after a note
    assert "b. Indicate the Technical Authority" in idx["SWE-126"]["text"]
    assert idx["SWE-219"]["notes"].startswith("Note: In MC/DC coverage")
    assert "cyclomatic complexity value of 15 or lower" in idx["SWE-220"]["text"]
    assert "Table 1." not in idx["SWE-052"].get("notes", "")


def test_appendix_c_applicability(npr):
    idx = {i["id"]: i for i in npr["items"]}

    def classes(swe):
        app = idx[swe]["applicability"]
        return "".join(c for c in "ABCDEF" if app[c] == "X")

    assert classes("SWE-033") == "ABCDEF"
    assert classes("SWE-141") == "AB"
    assert idx["SWE-141"]["applicability"]["authority"] == "HQ OSMA"
    assert idx["SWE-032"]["applicability"]["authority"] == "HQ OCE and HQ OSMA"
    assert classes("SWE-174") == "ABCD"
    assert classes("SWE-086") == "ABCF"
    assert classes("SWE-052") == "ABCDF"
    counts = npr["levels"]["applicable_counts"]
    assert counts == {"A": 100, "B": 100, "C": 92, "D": 64, "E": 12, "F": 65}
    # every applicability value is X or blank (NPR 7150.2D has no P(Center) notation)
    for it in npr["items"]:
        if it["applicability"]:
            assert {it["applicability"][c] for c in "ABCDEF"} <= {"X", ""}


def test_classes_and_traceability(npr):
    classes = npr["parameters"]["classes"]
    assert list(classes) == list("ABCDEF")
    for cls, d in classes.items():
        assert d["criteria"], cls
        assert 79 <= d["citation"]["pdf_page"] <= 86
    table = next(i for i in npr["items"] if i["id"] == "SWE-052")["traceability_table"]
    rows = {r["trace"]: r["classes"] for r in table["rows"]}
    assert rows["Software requirements to the system hazards"] == ["A", "B", "C", "D"]
    assert "E" not in sum(rows.values(), [])


def test_std_catalog(std):
    kinds = {}
    for it in std["items"]:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
        assert 1 <= it["citation"]["pdf_page"] <= STD_PAGES
    assert kinds == {"requirement": 1, "safety-critical-criterion": 5, "sa-task-set": 103,
                     "ivv-requirement": 49, "tailoring-requirement": 2, "hazard-cause-area": 12}
    sa = [i for i in std["items"] if i["kind"] == "sa-task-set"]
    assert {i["swe"] for i in sa} == {i["id"] for i in load_catalog("npr-7150-2d")["items"] if i["applicability"]}
    assert sum(len(i["tasks"]) for i in sa) == 198
    for i in sa:
        assert [t["n"] for t in i["tasks"]] == list(range(1, len(i["tasks"]) + 1))
        for t in i["tasks"]:
            assert "Software Assurance and Software Safety Tasks" not in t["text"]
    swe039 = next(i for i in sa if i["id"] == "SA-SWE-039")
    assert "at least once every two years" in swe039["tasks"][4]["text"]
    ivv3 = next(i for i in std["items"] if i["id"] == "4.4.2.3")
    assert ivv3["actor"] == "NASA SMA Technical Authority" and ivv3["citation"]["pdf_page"] == 50


def test_extraction_is_reproducible():
    pytest.importorskip("pdfplumber")
    import shutil
    import subprocess
    import sys

    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext not installed")
    from agentlib.paths import repo_root

    res = subprocess.run([sys.executable, str(repo_root() / "scripts/extract/nasa_swe.py"), "--check"],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr


# ------------------------------------------------------------------ helpers
def test_normalise_swe_and_class():
    assert ns.normalise_swe("swe-33") == "SWE-033"
    assert ns.normalise_swe("SWE 134") == "SWE-134"
    assert ns.normalise_swe("65b") == "SWE-065"
    with pytest.raises(ns.NasaSweError):
        ns.normalise_swe("PW.1.1")
    with pytest.raises(ns.NasaSweError):
        ns.get_requirement("SWE-999")
    assert ns.normalise_class("class b") == "B"
    with pytest.raises(ns.NasaSweError):
        ns.normalise_class("G")


def test_status_normalisation():
    assert ns.normalise_status("n/a") == "Not Applicable"
    assert ns.normalise_status(" COMPLIANT ") == "Compliant"
    assert ns.normalise_status("waived") == "Tailored"
    assert ns.normalise_status("") is None
    assert ns.normalise_status("Done-ish") == "INVALID"


# ------------------------------------------------------------------ classification
@pytest.mark.parametrize("answers,expected", [
    ({"A-scope": True, "A-1a": True}, "A"),
    ({"B-scope": True, "B-1a": True}, "B"),
    ({"B-scope": True, "B-1b": True, "B-x3": True, "C-5": True}, "C"),  # NASA Class D payload
    ({"C-1f": True}, "C"),
    ({"D-1b": True}, "D"),
    ({"E-1": True}, "E"),
    ({"F-1": True}, "F"),
    ({"E-1": True, "D-1b": True}, "D"),  # higher class wins
    ({"E-2": True, "safety_critical": True}, "D"),  # safety-critical cannot be Class E
    ({"B-2a": True}, None),  # aeronautics criterion without the large-scale scope
    ({"B-scope-2": True, "B-2a": True}, "B"),
])
def test_classify(answers, expected):
    res = ns.classify(answers)
    assert res["candidate_class"] == expected
    assert "Chief Engineer" in res["disclaimer"]


def test_classify_rationale_and_errors():
    res = ns.classify({"E-1": True, "D-1b": True, "F-1": True})
    assert res["candidate_class"] == "D"
    joined = " ".join(res["rationale"])
    assert "higher class" in joined and "Class F" in joined
    res = ns.classify({"D-1a": True, "D-x4": True})
    assert res["candidate_class"] is None
    with pytest.raises(ns.NasaSweError):
        ns.classify({"Z-9": True})
    with pytest.raises(ns.NasaSweError):
        ns.classify({"A-1a": "maybe"})
    md = ns.render_classification(ns.classify({"C-1b": "yes"}))
    assert "Candidate class: **Class C**" in md
    assert "[nasa-software-requirements Appendix D Class C, p. 82]" in md


# ------------------------------------------------------------------ safety-critical
def test_sc_assess():
    res = ns.sc_assess(["b"])
    assert res["safety_critical"] is True
    ids = {f["id"] for f in res["follow_on_requirements"]}
    assert {"SWE-023", "SWE-134", "SWE-219", "SWE-220", "SWE-205"} <= ids
    assert ns.sc_assess({"a": "no", "e": False})["safety_critical"] is False
    with pytest.raises(ns.NasaSweError):
        ns.sc_assess(["z"])
    md = ns.render_sc(res)
    assert "Safety-critical determination: **Yes**" in md


# ------------------------------------------------------------------ matrix
def test_build_matrix_counts():
    assert len(ns.build_matrix("B")) == 100
    assert len(ns.build_matrix("E")) == 12
    rows = ns.build_matrix("D", safety_critical=True)
    swe134 = next(r for r in rows if r["swe_id"] == "SWE-134")
    assert swe134["condition"].startswith("applies")
    rows_f = ns.build_matrix("F")
    assert next(r for r in rows_f if r["swe_id"] == "SWE-033")["authority"] == "CIO"
    assert all(r["sa_tasks"] >= 1 for r in rows)


def test_check_matrix_complete_and_errors():
    rows = [{"swe_id": r["swe_id"], "status": "Compliant", "evidence": "SDP v1.2", "tailoring_rationale": "",
             "approval": ""} for r in ns.build_matrix("E")]
    rep = ns.check_matrix(rows, "E")
    assert rep["summary"]["errors"] == 0
    assert rep["summary"]["compliant_pct_of_applicable"] == 100.0
    bad = rows[1:-1] + [  # drop SWE-033 (missing) and SWE-156 (re-added below as Tailored)
        {"swe_id": "SWE-999", "status": "Compliant", "evidence": "x"},
        {"swe_id": rows[1]["swe_id"], "status": "Compliant", "evidence": "x"},
        {"swe_id": "SWE-134", "status": "Done", "evidence": ""},
        {"swe_id": "SWE-024", "status": "Tailored", "evidence": "", "tailoring_rationale": ""},
        {"swe_id": "SWE-002", "status": "Compliant", "evidence": "x"},
        {"swe_id": "SWE-156", "status": "Tailored", "tailoring_rationale": "legacy", "approval": "Center ETA"},
        {"swe_id": "not-an-id", "status": "Compliant"},
    ]
    rep = ns.check_matrix(bad, "E")
    msgs = " ".join(f"{f['level']}:{f['swe']}:{f['message']}" for f in rep["findings"])
    assert "unknown requirement id SWE-999" in msgs
    assert "appears more than once" in msgs
    assert "invalid status 'Done'" in msgs
    assert "needs a tailoring/waiver rationale" in msgs
    assert "Chapter 2 institutional" in msgs
    assert "SAISO" in msgs
    assert f"error:{rows[0]['swe_id']}" in msgs and "missing from the matrix" in msgs
    assert "not-an-id" in msgs
    assert rep["summary"]["missing_applicable"] == 1


def test_check_matrix_without_class_warns():
    rep = ns.check_matrix([{"swe_id": "SWE-033", "status": "Planned"}], None)
    assert rep["summary"]["applicable_requirements"] is None
    assert any("class unknown" in f["message"] for f in rep["findings"])


def test_parse_matrix_formats(tmp_path):
    md = ns.render_matrix(ns.build_matrix("E"), "E", "md")
    cls, rows = ns.parse_matrix_text(md, "md")
    assert cls == "E" and len(rows) == 12 and rows[0]["swe_id"] == "SWE-033"
    csv_text = "# class: C\nSWE,Status,Evidence\nSWE-033,compliant,trade study\n"
    cls, rows = ns.parse_matrix_text(csv_text, "csv")
    assert cls == "C" and rows[0]["status"] == "compliant"
    cls, rows = ns.parse_matrix_text(json.dumps({"class": "D", "rows": [{"id": "SWE-033", "status": "Planned"}]}), "json")
    assert cls == "D" and rows[0]["swe_id"] == "SWE-033"
    with pytest.raises(ns.NasaSweError):
        ns.parse_matrix_text("no table here", "md")
    with pytest.raises(ns.NasaSweError):
        ns.parse_matrix_text("{bad", "json")
    with pytest.raises(ns.NasaSweError):
        ns.load_matrix(tmp_path / "missing.csv")
    with pytest.raises(ns.NasaSweError):
        ns.parse_matrix_text("a,b\n1,2\n", "csv")


# ------------------------------------------------------------------ CLI
def test_cli_matrix_formats(tmp_path, capsys):
    out = tmp_path / "m.csv"
    assert main(["nasa-swe", "matrix", "--class", "C", "--format", "csv", "-o", str(out)]) == 0
    rows = list(csv.DictReader(io.StringIO(out.read_text())))
    assert len(rows) == 92 and rows[0]["swe_id"] == "SWE-033"
    assert main(["nasa-swe", "matrix", "--class", "B", "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["class"] == "B" and len(data["rows"]) == 100
    assert main(["nasa-swe", "matrix", "--class", "Q"]) == 2


def test_cli_check_matrix_roundtrip(tmp_path, capsys):
    out = tmp_path / "m.csv"
    main(["nasa-swe", "matrix", "--class", "E", "--format", "csv", "-o", str(out)])
    rows = list(csv.DictReader(io.StringIO(out.read_text())))
    for r in rows:
        r["status"], r["evidence"] = "Compliant", "doc"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    out.write_text("# class: E\n" + buf.getvalue())
    capsys.readouterr()
    assert main(["nasa-swe", "check-matrix", str(out)]) == 0
    assert "Errors: 0" in capsys.readouterr().out
    # blank skeleton fails: statuses missing
    blank = tmp_path / "blank.json"
    main(["nasa-swe", "matrix", "--class", "E", "--format", "json", "-o", str(blank)])
    capsys.readouterr()
    assert main(["nasa-swe", "check-matrix", str(blank), "--format", "json"]) == 1
    rep = json.loads(capsys.readouterr().out)
    assert rep["summary"]["errors"] == 12  # every row lacks a status


def test_cli_check_matrix_json_output(tmp_path, capsys):
    f = tmp_path / "m.yaml"
    f.write_text(yaml.safe_dump({"class": "E", "rows": [{"swe": "SWE-033", "status": "bogus"}]}))
    assert main(["nasa-swe", "check-matrix", str(f), "--format", "json"]) == 1
    rep = json.loads(capsys.readouterr().out)
    assert rep["summary"]["missing_applicable"] == 11
    assert any("invalid status" in x["message"] for x in rep["findings"])
    assert main(["nasa-swe", "check-matrix", str(tmp_path / "nope.csv")]) == 2


def test_cli_classify(tmp_path, capsys):
    ans = tmp_path / "a.yaml"
    ans.write_text("answers:\n  B-scope: yes\n  B-1a: yes\nsafety_critical: true\n")
    assert main(["nasa-swe", "classify", "--answers", str(ans)]) == 0
    out = capsys.readouterr().out
    assert "Candidate class: **Class B**" in out
    assert main(["nasa-swe", "classify", "--yes", "D-1b", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["candidate_class"] == "D"
    assert main(["nasa-swe", "classify", "--list-questions"]) == 0
    assert "A-scope" in capsys.readouterr().out
    assert main(["nasa-swe", "classify"]) == 2
    assert main(["nasa-swe", "classify", "--yes", "nonsense"]) == 2


def test_cli_sa_tasks_show_sc_hazards(capsys):
    assert main(["nasa-swe", "sa-tasks", "--swe", "SWE-065"]) == 0
    out = capsys.readouterr().out
    assert "SWE-065a" in out and "SWE-065d" in out
    assert main(["nasa-swe", "sa-tasks", "--class", "E", "--format", "json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 12
    assert main(["nasa-swe", "sa-tasks", "--ivv"]) == 0
    assert "4.4.2.49" in capsys.readouterr().out
    assert main(["nasa-swe", "sa-tasks", "--swe", "SWE-002"]) == 2
    assert main(["nasa-swe", "show", "swe-219"]) == 0
    out = capsys.readouterr().out
    assert "MC/DC" in out and "[nasa-software-requirements SWE-219, p. 26]" in out
    assert main(["nasa-swe", "show", "4.4.2.3"]) == 0
    assert "SMA Technical Authority" in capsys.readouterr().out
    assert main(["nasa-swe", "show", "SWE-999"]) == 2
    assert main(["nasa-swe", "sc-assess", "--criteria", "a,c"]) == 0
    assert "**Yes**" in capsys.readouterr().out
    assert main(["nasa-swe", "sc-assess", "--criteria", ""]) == 0
    assert "**No**" in capsys.readouterr().out
    assert main(["nasa-swe", "hazard-causes", "--area", "command"]) == 0
    assert "Commanding errors" in capsys.readouterr().out
    assert main(["nasa-swe", "hazard-causes", "--area", "zzz"]) == 2


# ------------------------------------------------------------------ graders
def test_grade_swe_ids_valid():
    assert ns.grade_swe_ids_valid("SWE-033 and SWE-134", {"min": 2})[0]
    assert not ns.grade_swe_ids_valid("SWE-033 and SWE-999", {})[0]
    assert not ns.grade_swe_ids_valid("SWE-033", {"required": ["SWE-134"]})[0]


def test_grade_candidate_class():
    assert ns.grade_candidate_class("Candidate class: **Class C** - mission support", {"expected": "C"})[0]
    assert not ns.grade_candidate_class("Candidate class: B", {"expected": "C"})[0]
    assert not ns.grade_candidate_class("It is probably class C", {"expected": "C"})[0]


def test_grade_matrix_coverage():
    good = ns.render_matrix(ns.build_matrix("E"), "E")
    assert ns.grade_matrix_coverage(good, {"class": "E"})[0]
    assert not ns.grade_matrix_coverage(good, {"class": "D"})[0]
    assert ns.grade_matrix_coverage(good, {"ids": ["SWE-033"], "forbid": ["SWE-134"]})[0]
    bad = good.replace("| SWE-033 | 3.1.2 |", "| SWE-999 | 3.1.2 |")
    assert not ns.grade_matrix_coverage(bad, {"class": "E", "min_fraction": 0.5})[0]


def test_grade_sc_and_ivv_and_pages():
    out = "Safety-critical determination: **Yes** (criteria 4.2 b and 4.2 c)"
    assert ns.grade_safety_critical_determination(out, {"expected": "yes", "criteria": ["b"]})[0]
    assert not ns.grade_safety_critical_determination(out, {"expected": "no"})[0]
    assert not ns.grade_safety_critical_determination(out, {"expected": "yes", "criteria": ["e"]})[0]
    assert ns.grade_ivv_refs_valid("see 4.4.2.3 and 4.4.2.49", {"min": 2})[0]
    assert not ns.grade_ivv_refs_valid("see 4.4.2.50", {})[0]
    ok = "[nasa-software-requirements SWE-219, p. 27] [nasa-software-assurance 4.4.2.3, p. 50] [nasa-software-assurance Table 1 SWE-039, p. 19]"
    assert ns.grade_page_citations(ok, {"min": 3})[0]
    assert not ns.grade_page_citations("[nasa-software-requirements SWE-219, p. 40]", {})[0]


def test_grade_check_matrix_fixture():
    chk = {"fixture": "evals/nasa-software-engineering/fixtures/rmm-class-c.csv"}
    named = "SWE-999 SWE-191 SWE-202 SWE-219 SWE-087 SWE-071"
    assert ns.grade_check_matrix_fixture(named, chk)[0]
    assert not ns.grade_check_matrix_fixture("SWE-999 only", chk)[0]


def test_skill_reference_indexes_cover_catalogs(root):
    req_index = (root / "skills/nasa-software-engineering/references/requirements-index.md").read_text()
    for it in load_catalog("npr-7150-2d")["items"]:
        assert f"| {it['id']} | {it['section']} | {it['citation']['pdf_page']} |" in req_index, it["id"]
    sa_index = (root / "skills/nasa-software-assurance/references/sa-task-index.md").read_text()
    for it in load_catalog("nasa-std-8739-8b")["items"]:
        if it["kind"] == "sa-task-set":
            assert f"| {it['swe']}{it['swe_part'] or ''} | {it['npr_section']} |" in sa_index, it["id"]
        if it["kind"] == "ivv-requirement":
            assert f"| {it['id']} | {it['citation']['pdf_page']} |" in sa_index, it["id"]


def test_check_matrix_compliance_counts_only_applicable_first_rows(tmp_path, capsys):
    rows = [{"swe_id": r["swe_id"], "status": "Compliant", "evidence": "doc"} for r in ns.build_matrix("A")]
    rep = ns.check_matrix(rows, "E")
    assert rep["summary"]["compliant_pct_of_applicable"] == 100.0
    dup = ns.check_matrix([{"swe_id": "SWE-033", "status": "Compliant", "evidence": "doc"}] * 3, "E")
    assert dup["summary"]["status_counts"]["Compliant"] == 1
    assert dup["summary"]["compliant_pct_of_applicable"] == round(100 / 12, 1)
    assert sum("appears more than once" in f["message"] for f in dup["findings"]) == 1
    f = tmp_path / "a.json"
    f.write_text(json.dumps({"class": "A", "rows": rows}), encoding="utf-8")
    main(["nasa-swe", "check-matrix", str(f), "--class", "E", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["summary"]["compliant_pct_of_applicable"] == 100.0


def test_load_matrix_accepts_utf8_bom(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text("\ufeff# class: C\nSWE,Status,Evidence\nSWE-033,compliant,trade study\n", encoding="utf-8")
    cls, rows = ns.load_matrix(f)
    assert cls == "C" and rows[0]["swe_id"] == "SWE-033"
