"""Tests for the Green Book 2026 framework: catalog, discounting, tools, CLI and graders."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from agentlib.cli import main
from agentlib.frameworks import greenbook as gb
from agentlib.paths import repo_root

ROOT = repo_root()
EVAL = ROOT / "evals" / "green-book-appraisal"
FLOWS = EVAL / "fixtures" / "appraisal_flows.csv"


# ---------------------------------------------------------------- catalog integrity
@pytest.fixture(scope="module")
def cat():
    return gb.catalog()


def test_catalog_schema_and_identity(cat):
    schema = json.loads((ROOT / "schemas" / "catalog.schema.json").read_text())
    jsonschema.validate(cat, schema)
    assert cat["catalog_id"] == "green-book"
    assert cat["source_id"] == "treasury-green"
    assert "2026" in cat["edition"]


def test_catalog_counts_and_ids(cat):
    ids = [i["id"] for i in cat["items"]]
    assert len(ids) == len(set(ids)) == 121
    assert len(cat["groups"]) == 17
    assert sum(i.startswith("stage.") for i in ids) == 4
    assert sorted(i for i in ids if i.startswith("case.")) == [
        "case.commercial", "case.economic", "case.financial", "case.management", "case.strategic"]
    assert sorted(i for i in ids if i.startswith("bc.")) == ["bc.fbc", "bc.obc", "bc.soc"]
    assert sum(i.startswith("csf.") and i[4].isdigit() for i in ids) == 5
    assert sum(i.startswith("duty.") for i in ids) == 3
    group_ids = {g["id"] for g in cat["groups"]}
    assert all(i["group"] in group_ids for i in cat["items"])


def test_catalog_pages_in_body_and_folios(cat):
    for entry in cat["items"] + cat["groups"]:
        c = entry["citation"]
        assert 7 <= c["pdf_page"] <= 85, entry["id"]
        assert c["printed_page"] == c["pdf_page"] - 6, entry["id"]


@pytest.mark.parametrize("item_id,page", [
    ("discount.stpr", 46), ("discount.health", 46), ("case.strategic", 20), ("bc.soc", 21),
    ("metrics.no-bcr-thresholds", 53), ("risk.optimism-bias", 50), ("metrics.npsv", 52),
    ("metrics.switching-values", 54), ("csf.4-affordability", 30), ("presentation.ast", 75),
    ("me.plan", 79), ("pf.gilt-sensitivity", 85), ("shortlist.time-horizon", 39),
])
def test_key_item_pages(item_id, page):
    assert gb.item(item_id)["citation"]["pdf_page"] == page


def test_five_case_contents(cat):
    strat = gb.item("case.strategic")
    assert "SMART objectives" in strat["contents"] and "Business as usual" in strat["contents"]
    mgmt = gb.item("case.management")
    assert any("evaluation" in c.lower() for c in mgmt["contents"])
    for c in ("strategic", "economic", "commercial", "financial", "management"):
        assert gb.item(f"case.{c}")["demonstrates"]


def test_parameters_2026(cat):
    p = cat["parameters"]
    assert p["stpr"]["bands"] == [
        {"from_year": 1, "to_year": 30, "rate": 0.035},
        {"from_year": 31, "to_year": 75, "rate": 0.03},
        {"from_year": 76, "to_year": None, "rate": 0.025},
    ]
    assert p["health_discount_rate"]["rate"] == 0.015
    assert p["time_horizons_years_after_year0"]["infrastructure"] == 60
    assert p["welfare_weight_elasticity"]["value"] == 1.3
    assert p["bcr_threshold"]["value"] is None
    gaps = {g["parameter"] for g in p["not_in_edition"]}
    assert {"optimism_bias_percentages", "risk_free_real_gilt_rate", "gdp_deflator_series"} <= gaps
    # no optimism-bias percentages hard-coded anywhere in parameters
    assert "optimism_bias" not in json.dumps({k: v for k, v in p.items() if k != "not_in_edition"})


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="pdftotext not installed")
def test_extraction_reproducible():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "extract" / "greenbook.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------- discounting (hand-calculated)
def test_year_zero_and_first_band():
    assert gb.discount_factor(0) == 1.0
    assert gb.discount_factor(1) == pytest.approx(1 / 1.035)
    assert gb.discount_factor(30) == pytest.approx(0.356278, abs=1e-6)  # 1.035^-30


def test_table8_worked_example():
    t8 = gb.parameters()["table8_worked_example"]["discount_factors"]
    assert [round(gb.discount_factor(t), 4) for t in range(6)] == t8
    # Table 8: £1,000 in year 5 is worth £842
    assert round(1000 * gb.discount_factor(5)) == 842


def test_band_boundary_30_31_compounds():
    # hand: DF(31) = 1.035^-30 / 1.03 = 0.356278 / 1.03 = 0.345901
    assert gb.discount_factor(31) == pytest.approx(0.345901, abs=1e-6)
    assert gb.discount_factor(31) / gb.discount_factor(30) == pytest.approx(1 / 1.03)
    # a flat 3.5% would give 0.344230 - the schedule must differ
    assert gb.discount_factor(31) != pytest.approx(1.035 ** -31, abs=1e-4)


def test_band_boundary_75_76_compounds():
    # hand: DF(75) = 1.035^-30 * 1.03^-45 = 0.356278 * 0.264439 = 0.094213
    assert gb.discount_factor(75) == pytest.approx(0.094213, abs=1e-6)
    # DF(76) = DF(75)/1.025 = 0.091916
    assert gb.discount_factor(76) == pytest.approx(0.091916, abs=1e-6)
    # year 100 = DF(75) * 1.025^-25
    assert gb.discount_factor(100) == pytest.approx(0.094213 * 1.025 ** -25, rel=1e-5)


def test_rate_for_year():
    assert gb.rate_for_year(1) == 0.035
    assert gb.rate_for_year(30) == 0.035
    assert gb.rate_for_year(31) == 0.03
    assert gb.rate_for_year(75) == 0.03
    assert gb.rate_for_year(76) == 0.025
    assert gb.rate_for_year(500) == 0.025


def test_pv_of_stream_across_boundary():
    # £100 in each of years 29-32: hand-calculated factors
    # 0.368748 + 0.356278 + 0.345901 (=0.356278/1.03) + 0.335826 (=0.345901/1.03) = 1.406753
    dfs = [1.035 ** -29, 1.035 ** -30, 1.035 ** -30 / 1.03, 1.035 ** -30 / 1.03 ** 2]
    pv = sum(100 * gb.discount_factor(t) for t in range(29, 33))
    assert pv == pytest.approx(100 * sum(dfs))
    assert pv == pytest.approx(140.675, abs=1e-3)


def test_health_and_flat_rates():
    assert gb.health_discount_factor(10) == pytest.approx(1.015 ** -10)
    assert gb.health_discount_factor(80) == pytest.approx(1.015 ** -80)  # constant in every year
    assert gb.discount_factor(10, flat_rate=0.05) == pytest.approx(1.05 ** -10)


def test_discount_errors():
    with pytest.raises(gb.GreenBookError, match="sunk"):
        gb.discount_factor(-1)
    with pytest.raises(gb.GreenBookError):
        gb.discount_factor(1.5)  # type: ignore[arg-type]
    with pytest.raises(gb.GreenBookError):
        gb.discount_factor(3, bands=[{"from_year": 2, "to_year": None, "rate": 0.03}])
    with pytest.raises(gb.GreenBookError):
        gb.discount_factor(3, bands=[{"from_year": 1, "to_year": 10, "rate": 0.03}])
    with pytest.raises(gb.GreenBookError):
        gb.discount_factor(3, flat_rate=-1.0)


def test_custom_bands():
    bands = [{"from_year": 1, "to_year": 2, "rate": 0.10}, {"from_year": 3, "to_year": None, "rate": 0.0}]
    assert gb.discount_factor(5, bands=bands) == pytest.approx(1 / 1.21)


# ---------------------------------------------------------------- inputs and appraisal
def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


SIMPLE_CSV = """option,year,item,type,stream,bearer,value
A,0,Capex,cost,standard,public,100
A,1,Benefit,benefit,standard,,60
A,2,Benefit,benefit,standard,,60
A,1,Disruption,cost,standard,non-public,5
B,0,Capex,cost,standard,public,50
B,1,Health,benefit,health,,30
B,2,Health,benefit,health,,30
"""


def test_appraise_hand_calculated(tmp_path):
    res = gb.appraise(gb.load_flows(_write(tmp_path, "f.csv", SIMPLE_CSV)))
    a = next(r for r in res if r.option == "A")
    pvb = 60 / 1.035 + 60 / 1.035 ** 2
    pvc = 100 + 5 / 1.035
    assert a.pvb == pytest.approx(pvb)
    assert a.pvc == pytest.approx(pvc)
    assert a.npsv == pytest.approx(pvb - pvc)
    assert a.bcr == pytest.approx(pvb / pvc)
    assert a.rpsc == pytest.approx((pvb - 5 / 1.035) / 100)
    b = next(r for r in res if r.option == "B")
    assert b.pvb == pytest.approx(30 / 1.015 + 30 / 1.015 ** 2)  # health stream at 1.5%
    assert [r.rank for r in res] == [1, 2]
    assert res[0].npsv >= res[1].npsv


def test_appraise_settings(tmp_path):
    app = gb.load_flows(_write(tmp_path, "f.csv", SIMPLE_CSV))
    b = next(r for r in gb.appraise(app, gb.Settings(separate_health=False)) if r.option == "B")
    assert b.pvb == pytest.approx(30 / 1.035 + 30 / 1.035 ** 2)
    res = gb.appraise(app, gb.Settings(bau="B", gilt_rate=0.01))
    a = next(r for r in res if r.option == "A")
    bb = next(r for r in res if r.option == "B")
    assert bb.npsv_vs_bau == 0 and a.npsv_vs_bau == pytest.approx(a.npsv - bb.npsv)
    assert a.pvc_gilt == pytest.approx(100 + 5 / 1.01)
    with pytest.raises(gb.GreenBookError):
        gb.appraise(app, gb.Settings(bau="nope"))


def test_rpsc_none_without_bearer_and_bcr_none_without_costs(tmp_path):
    csv_text = "option,year,type,value\nX,0,cost,10\nX,1,benefit,20\nY,1,benefit,5\n"
    res = {r.option: r for r in gb.appraise(gb.load_flows(_write(tmp_path, "f.csv", csv_text)))}
    assert res["X"].rpsc is None and res["X"].bcr is not None
    assert res["Y"].bcr is None and res["Y"].pvc == 0


def test_yaml_and_calendar_years(tmp_path):
    y = """base_year: 2026
options:
  - name: Opt
    flows:
      - {item: Capex, type: cost, bearer: public, values: [100]}
      - {item: Ben, type: benefit, calendar_years: true, values: {2027: 50, 2028: 50}}
"""
    res = gb.appraise(gb.load_flows(_write(tmp_path, "f.yaml", y)))
    assert res[0].pvb == pytest.approx(50 / 1.035 + 50 / 1.035 ** 2)
    c = "option,calendar_year,type,value\nO,2026,cost,10\nO,2027,benefit,20\n"
    res = gb.appraise(gb.load_flows(_write(tmp_path, "c.csv", c), base_year=2026))
    assert res[0].npsv == pytest.approx(20 / 1.035 - 10)
    js = {"options": [{"name": "J", "flows": [{"type": "cost", "values": [1, 1]}]}]}
    assert gb.load_flows(_write(tmp_path, "j.json", json.dumps(js))).options == ["J"]


@pytest.mark.parametrize("name,text,match", [
    ("a.csv", "option,year,value\nA,0,1\n", "columns"),
    ("b.csv", "option,year,type,value\nA,0,profit,1\n", "benefit"),
    ("c.csv", "option,year,type,value\nA,-1,cost,1\n", "year 0"),
    ("d.csv", "option,year,type,value\nA,0,cost,abc\n", "not a number"),
    ("e.csv", "option,calendar_year,type,value\nA,2025,cost,1\n", "base year"),
    ("f.txt", "x", "unsupported"),
    ("g.yaml", "options: []", "options"),
    ("h.csv", "option,year,type,stream,value\nA,0,cost,weird,1\n", "stream"),
    ("i.csv", "option,year,type,bearer,value\nA,0,cost,martian,1\n", "bearer"),
])
def test_load_errors(tmp_path, name, text, match):
    with pytest.raises(gb.GreenBookError, match=match):
        gb.load_flows(_write(tmp_path, name, text))


def test_missing_file():
    with pytest.raises(gb.GreenBookError, match="not found"):
        gb.load_flows("/nonexistent/flows.csv")


def test_fixture_results():
    res = {r.option: r for r in gb.appraise(gb.load_flows(FLOWS))}
    assert res["New build"].npsv == pytest.approx(247.37, abs=0.01)
    assert res["Do minimum"].npsv == pytest.approx(93.09, abs=0.01)
    assert res["Business as usual"].npsv == pytest.approx(-54.86, abs=0.01)
    assert res["New build"].rank == 1


# ---------------------------------------------------------------- switching
def test_switching_hand_calculated(tmp_path):
    csv_text = "option,year,item,type,value\nP,0,c,cost,100\nP,0,b,benefit,150\nQ,0,c,cost,100\nQ,0,b,benefit,120\n"
    sw = gb.switching(gb.appraise(gb.load_flows(_write(tmp_path, "f.csv", csv_text))), [-10, 10])
    p = next(s for s in sw["switching_values"] if s["option"] == "P")
    assert p["benefits_change_pct_to_zero_npsv"] == pytest.approx(-100 / 3)
    assert p["costs_change_pct_to_zero_npsv"] == pytest.approx(50)
    r = sw["ranking_switches"][0]
    assert r["challenger"] == "Q" and r["npsv_gap"] == pytest.approx(30)
    assert r["preferred_benefits_change_pct"] == pytest.approx(-20)
    assert r["preferred_costs_change_pct"] == pytest.approx(30)
    row = next(s for s in sw["sensitivity"] if s["pct"] == -10)
    assert row["benefits_scaled_npsv"]["P"] == pytest.approx(35)
    assert row["top_if_benefits_scaled"] == "P"
    with pytest.raises(gb.GreenBookError):
        gb.switching([])


# ---------------------------------------------------------------- optimism bias
def test_optimism_bias():
    r = gb.optimism_bias(120, 66, 40)
    assert r["capex"]["applied_pct"] == pytest.approx(39.6)
    assert r["capex"]["adjusted"] == pytest.approx(167.52)
    assert r["remaining_cost_adjustment_for_contingency"] == pytest.approx(47.52)
    r = gb.optimism_bias(100, 50, 0, benefits=200, benefits_pct=10, duration=24, duration_upper_pct=25,
                         opex=10, opex_upper_pct=20)
    assert r["benefits"]["adjusted"] == pytest.approx(180)
    assert r["duration"]["adjusted"] == pytest.approx(30)
    assert r["remaining_cost_adjustment_for_contingency"] == pytest.approx(52)
    assert "supplementary guidance" in " ".join(r["notes"]).lower()


@pytest.mark.parametrize("kwargs", [
    {"capex": -1, "upper_pct": 10}, {"capex": 1, "upper_pct": -5}, {"capex": 1, "upper_pct": 5, "mitigation_pct": 120},
    {"capex": 1, "upper_pct": 5, "opex": 3}, {"capex": 1, "upper_pct": 5, "benefits": 3},
    {"capex": float("nan"), "upper_pct": 5},
])
def test_optimism_bias_errors(kwargs):
    with pytest.raises(gb.GreenBookError):
        gb.optimism_bias(**kwargs)


# ---------------------------------------------------------------- real terms
def test_real_reproduces_table7():
    rows = [{"year": str(2026 + t), "cost": str(v)} for t, v in enumerate([1000, 1020, 1040, 1061, 1082, 1104])]
    defl = gb.deflator_index([{"year": str(2026 + t), "growth_pct": "2"} for t in range(6)])
    out, info = gb.nominal_to_real(rows, defl)
    assert info["price_year"] == 2026
    factors = [r["deflator_factor"] for r in out]
    assert [round(f, 4) for f in factors] == gb.parameters()["table7_worked_example"]["deflator_factors"]
    assert all(abs(r["cost"] - 1000) < 1 for r in out)


def test_real_with_index_and_price_year():
    rows = [{"year": 2025, "v": 100}, {"year": 2026, "v": 110}]
    idx = gb.deflator_index([{"year": 2025, "index": 100}, {"year": 2026, "index": 110}])
    out, _ = gb.nominal_to_real(rows, idx, price_year=2026)
    assert out[0]["v"] == pytest.approx(110) and out[1]["v"] == pytest.approx(110)


def test_real_errors():
    idx = gb.deflator_index([{"year": 2025, "index": 100}])
    with pytest.raises(gb.GreenBookError, match="no deflator"):
        gb.nominal_to_real([{"year": 2025, "v": 1}, {"year": 2026, "v": 1}], idx)
    with pytest.raises(gb.GreenBookError):
        gb.deflator_index([{"year": 2025, "foo": 1}])
    with pytest.raises(gb.GreenBookError, match="gap"):
        gb.deflator_index([{"year": 2025, "growth_pct": 2}, {"year": 2027, "growth_pct": 2}])
    with pytest.raises(gb.GreenBookError):
        gb.deflator_index([{"year": 2025, "index": 0}])
    with pytest.raises(gb.GreenBookError):
        gb.nominal_to_real([], idx)


def test_welfare_weight():
    assert gb.welfare_weight(600, 400) == pytest.approx(1.5 ** 1.3)
    with pytest.raises(gb.GreenBookError):
        gb.welfare_weight(0, 400)


# ---------------------------------------------------------------- business case checker
def test_check_case_flags_flawed_case():
    rep = gb.check_case_text((EVAL / "fixtures" / "flawed_business_case.md").read_text())
    status = {f["id"]: f["status"] for f in rep["findings"]}
    for fid in ("options.bau", "options.do-minimum", "options.longlist", "five-case.management",
                "five-case.commercial", "economic.switching", "anti.bcr-threshold", "anti.sunk-costs",
                "anti.nominal-discounting", "management.me-plan", "preferred.justified"):
        assert status[fid] == "fail", fid
    assert status["five-case.strategic"] == "pass"
    assert all("citation" in f and "PDF p." in f["citation"] for f in rep["findings"])


def test_check_case_good_case_passes():
    rep = gb.check_case_text((EVAL / "golden" / "soc-outline.md").read_text())
    assert rep["summary"]["failed"] == 0


def test_check_case_negated_threshold_not_flagged():
    text = "## Economic case\nWe do not apply a BCR threshold; options are never rejected for a BCR below 2."
    status = {f["id"]: f["status"] for f in gb.check_case_text(text)["findings"]}
    assert status["anti.bcr-threshold"] == "pass"


# ---------------------------------------------------------------- CLI
def test_cli_npv_md_and_json(tmp_path, capsys):
    assert main(["greenbook", "npv", str(FLOWS), "--bau", "Business as usual"]) == 0
    out = capsys.readouterr().out
    assert "| 1 | New build |" in out and "247.37" in out and "PDF p.46" in out
    dest = tmp_path / "r.json"
    assert main(["greenbook", "npv", str(FLOWS), "--format", "json", "--out", str(dest), "--gilt-rate", "0.01"]) == 0
    data = json.loads(dest.read_text())
    assert data["preferred_by_npsv"] == "New build"
    assert data["options"][0]["pvc_gilt"] is not None


def test_cli_npv_custom_rate_labelled(capsys):
    assert main(["greenbook", "npv", str(FLOWS), "--rate", "0.05"]) == 0
    assert "CUSTOM flat 5.00%" in capsys.readouterr().out


def test_cli_errors_exit_2(tmp_path, capsys):
    assert main(["greenbook", "npv", str(tmp_path / "missing.csv")]) == 2
    assert "error" in capsys.readouterr().err
    assert main(["greenbook", "npv", str(FLOWS), "--rate", "3.5"]) == 2
    assert main(["greenbook", "optimism-bias", "--capex", "100", "--upper-pct", "50", "--mitigation", "150"]) == 2


def test_cli_switching(capsys):
    assert main(["greenbook", "switching", str(FLOWS), "--pcts", "-10", "10"]) == 0
    out = capsys.readouterr().out
    assert "-53.4%" in out and "+114.4%" in out and "-33.3%" in out


def test_cli_real(tmp_path, capsys):
    nominal = _write(tmp_path, "n.csv", "year,capex,opex\n2026,100,10\n2027,102,10.2\n")
    defl = _write(tmp_path, "d.csv", "year,growth_pct\n2026,\n2027,2\n")
    assert main(["greenbook", "real", str(nominal), "--deflators", str(defl)]) == 0
    out = capsys.readouterr().out
    assert "deflator_factor" in out and "100.0" in out
    assert main(["greenbook", "real", str(nominal), "--deflators", str(defl), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rows"][1]["capex"] == pytest.approx(100)
    assert main(["greenbook", "real", str(nominal), "--deflators", str(defl), "--format", "md"]) == 0


def test_cli_optimism_bias(capsys):
    assert main(["greenbook", "optimism-bias", "--capex", "120", "--upper-pct", "66", "--mitigation", "40",
                 "--source", "test"]) == 0
    out = capsys.readouterr().out
    assert "167.52" in out and "supplementary guidance" in out


def test_cli_check_case(tmp_path, capsys):
    bad = str(EVAL / "fixtures" / "flawed_business_case.md")
    assert main(["greenbook", "check-case", bad]) == 0
    assert "FAIL" in capsys.readouterr().out
    assert main(["greenbook", "check-case", bad, "--strict"]) == 1
    assert main(["greenbook", "check-case", str(EVAL / "golden" / "soc-outline.md"), "--strict",
                 "--format", "json"]) == 0
    assert main(["greenbook", "check-case", str(tmp_path / "nope.md")]) == 2


def test_cli_params_factors_ww(capsys):
    assert main(["greenbook", "params"]) == 0
    out = capsys.readouterr().out
    assert "3.50%" in out and "optimism_bias_percentages" in out
    assert main(["greenbook", "params", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["health_discount_rate"]["rate"] == 0.015
    assert main(["greenbook", "factors", "--years", "31"]) == 0
    assert "| 31 | 3.00% | 0.3459 |" in capsys.readouterr().out
    assert main(["greenbook", "welfare-weight", "--national", "600", "--group", "400", "--income-change", "100"]) == 0
    assert json.loads(capsys.readouterr().out)["weighted_impact"] == pytest.approx(100 * 1.5 ** 1.3)


# ---------------------------------------------------------------- graders
def test_graders_golden_and_negative():
    fx = "evals/green-book-appraisal/fixtures/appraisal_flows.csv"
    good = (EVAL / "golden" / "npsv-ranking.md").read_text()
    bad = (EVAL / "golden" / "npsv-ranking.bad.md").read_text()
    chk = {"fixture": fx, "metrics": ["npsv", "bcr"]}
    assert gb.grade_npsv_matches(good, chk)[0]
    assert not gb.grade_npsv_matches(bad, chk)[0]
    assert gb.grade_ranking(good, {"fixture": fx})[0]
    assert gb.grade_switching_value((EVAL / "golden" / "switching-values.md").read_text(), {"fixture": fx})[0]
    assert not gb.grade_switching_value((EVAL / "golden" / "switching-values.bad.md").read_text(), {"fixture": fx})[0]
    ob = {"capex": 120, "upper_pct": 66, "mitigation_pct": 40}
    assert gb.grade_optimism_bias((EVAL / "golden" / "optimism-bias.md").read_text(), ob)[0]
    assert not gb.grade_optimism_bias((EVAL / "golden" / "optimism-bias.bad.md").read_text(), ob)[0]
    assert not gb.grade_no_hardcoded_optimism_bias((EVAL / "golden" / "optimism-bias.bad.md").read_text(), {})[0]
    ds_good = (EVAL / "golden" / "discount-schedule.md").read_text()
    ds_bad = (EVAL / "golden" / "discount-schedule.bad.md").read_text()
    assert gb.grade_stpr_2026(ds_good, {"health": True})[0]
    assert not gb.grade_stpr_2026(ds_bad, {"health": True})[0]
    dchk = {"years": [30, 31, 76], "health_years": [10]}
    assert gb.grade_discount_factors(ds_good, dchk)[0]
    assert not gb.grade_discount_factors(ds_bad, dchk)[0]
    assert gb.grade_case_structure((EVAL / "golden" / "soc-outline.md").read_text(), {})[0]
    assert not gb.grade_case_structure((EVAL / "golden" / "soc-outline.bad.md").read_text(), {})[0]


def test_grader_scaled_units():
    fx = "evals/green-book-appraisal/fixtures/appraisal_flows.csv"
    # answer expressed in £ (fixture is in £m): scale tells the grader the answer's unit is 1/1e6 of the fixture's
    text = "| New build | £247.37m |\n| Do minimum | £93.09m |\n| Business as usual | -£54.86m |"
    assert gb.grade_npsv_matches(text, {"fixture": fx})[0]
    assert not gb.grade_npsv_matches("| New build | 212.29 |\n| Do minimum | 93.09 |\n| Business as usual | -54.86 |",
                                     {"fixture": fx})[0]
    ok, _ = gb.grade_npsv_matches("| New build | 247.37 |\n| Do minimum | 93.09 |\n| Business as usual | (54.86) |",
                                  {"fixture": fx})
    assert ok


def test_parse_amounts():
    assert -54.86 in gb.parse_amounts("NPSV (54.86)")
    assert 2.5e6 in gb.parse_amounts("£2.5m")
    assert 1234.5 in gb.parse_amounts("£1,234.5")


# ---------------------------------------------------------------------- regressions
def test_check_case_accepts_utf8_bom(tmp_path):
    text = (EVAL / "golden" / "soc-outline.md").read_text(encoding="utf-8")
    plain = _write(tmp_path, "plain.md", text)
    bom = _write(tmp_path, "bom.md", "\ufeff" + text)
    assert main(["greenbook", "check-case", str(bom), "--strict"]) == 0
    assert main(["greenbook", "check-case", str(plain), "--strict"]) == 0


def test_check_case_bom_first_heading_recognised(tmp_path, capsys):
    text = "# Strategic case\n\nText.\n"
    main(["greenbook", "check-case", str(_write(tmp_path, "a.md", text)), "--format", "json"])
    plain = json.loads(capsys.readouterr().out)
    main(["greenbook", "check-case", str(_write(tmp_path, "b.md", "\ufeff" + text)), "--format", "json"])
    assert json.loads(capsys.readouterr().out) == plain


def test_options_as_strings_is_input_error(tmp_path, capsys):
    f = _write(tmp_path, "opt.yaml", "options:\n  - Do minimum\n")
    with pytest.raises(gb.GreenBookError, match="option 0 must be a mapping"):
        gb.load_flows(f)
    assert main(["greenbook", "npv", str(f)]) == 2
    assert "option 0 must be a mapping" in capsys.readouterr().err
    g = _write(tmp_path, "fl.yaml", "options:\n  - name: A\n    flows: [cost]\n")
    with pytest.raises(gb.GreenBookError, match="flow must be a mapping"):
        gb.load_flows(g)


def test_real_financial_year_is_input_error(tmp_path, capsys):
    nom = _write(tmp_path, "nom.csv", "year,capex\n2026,100\n2027/28,110\n")
    defl = _write(tmp_path, "defl.csv", "year,index\n2026,100\n2027,102\n")
    assert main(["greenbook", "real", str(nom), "--deflators", str(defl)]) == 2
    assert "2027/28" in capsys.readouterr().err
    bad_defl = _write(tmp_path, "d2.csv", "year,index\n2026/27,100\n")
    with pytest.raises(gb.GreenBookError, match="year must be an integer"):
        gb.deflator_index(gb.read_table(bad_defl))
