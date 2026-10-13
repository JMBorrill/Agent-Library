import copy

import pytest
import yaml

from agentlib.cli import main
from agentlib.frameworks import assurance_case as ac

GOOD = {
    "case": {"id": "AC-1", "title": "API secure for release", "scope": "commit abc", "decision_authority": "CISO"},
    "claims": [
        {"id": "C1", "text": "API acceptably secure", "criticality": "high",
         "argument": "Split by product and process", "subclaims": ["C1.1", "C1.2"]},
        {"id": "C1.1", "text": "Code review enforced", "criticality": "high", "frameworks": ["PW.7.1"], "evidence": ["EV-1"]},
        {"id": "C1.2", "text": "Third-party risk accepted", "status": "undeveloped", "justification": "SCA pending"},
    ],
    "evidence": [{"id": "EV-1", "description": "branch protection + PR sample", "artefact": "ev/ev1.md",
                  "method": "Inspection", "strength": "E3"}],
}


def msgs(case, **kw):
    return [(f.level, f.where, f.message) for f in ac.check(case, **kw)]


def test_good_case_has_no_errors_and_is_incomplete():
    findings = ac.check(GOOD)
    assert not [f for f in findings if f.level == "error"]
    assert ac.summary(GOOD, findings)["verdict"] == "incomplete"


def test_complete_case():
    case = copy.deepcopy(GOOD)
    case["claims"][0]["subclaims"] = ["C1.1"]
    case["claims"].pop()
    assert ac.summary(case, ac.check(case))["verdict"] == "complete"


@pytest.mark.parametrize("mutate,expected", [
    (lambda c: c["claims"][1].update(evidence=[]), "no evidence"),
    (lambda c: c["evidence"][0].update(strength="E2"), "strength >= E3"),
    (lambda c: c["claims"][2].pop("justification"), "needs a justification"),
    (lambda c: c["claims"][0]["subclaims"].append("C9"), "does not exist"),
    (lambda c: c["claims"][1].update(evidence=["EV-9"]), "evidence 'EV-9' does not exist"),
    (lambda c: c["claims"].append({"id": "C2", "text": "orphan", "evidence": ["EV-1"]}), "exactly one root"),
    (lambda c: c["claims"][1].update(subclaims=["C1"]), "cycle"),
    (lambda c: c["claims"].append(copy.deepcopy(c["claims"][1])), "duplicate claim id"),
    (lambda c: c["claims"][1].update(frameworks=["PW.9.9"]), "PW.9.9"),
    (lambda c: c["evidence"][0].update(artefact=""), "names no artefact"),
    (lambda c: c["claims"][1].update(criticality="extreme"), "criticality must be"),
])
def test_defects_are_errors(mutate, expected):
    case = copy.deepcopy(GOOD)
    mutate(case)
    errs = [m for lvl, _, m in msgs(case) if lvl == "error"]
    assert any(expected in m for m in errs), errs


def test_medium_claim_accepts_e2():
    case = copy.deepcopy(GOOD)
    case["claims"][1]["criticality"] = "medium"
    case["evidence"][0]["strength"] = "E2"
    assert not [m for lvl, _, m in msgs(case) if lvl == "error"]


def test_artefact_paths_checked_with_base(tmp_path):
    errs = [m for lvl, _, m in msgs(GOOD, base=tmp_path) if lvl == "error"]
    assert any("artefact not found" in m for m in errs)
    (tmp_path / "ev").mkdir()
    (tmp_path / "ev" / "ev1.md").write_text("x")
    assert not [m for lvl, _, m in msgs(GOOD, base=tmp_path) if lvl == "error"]


def test_render():
    md = ac.render(GOOD)
    assert "**C1.2**" in md and "[UNDEVELOPED]" in md and "| EV-1 |" in md
    assert md.index("**C1**") < md.index("**C1.1**")


def test_grader():
    good = "```yaml\n" + yaml.safe_dump(GOOD) + "```"
    assert ac.grade_case(good, {})[0]
    bad = copy.deepcopy(GOOD)
    bad["claims"][1]["evidence"] = []
    assert not ac.grade_case("```yaml\n" + yaml.safe_dump(bad) + "```", {})[0]
    assert not ac.grade_case("no yaml here", {})[0]


def test_cli(tmp_path, capsys):
    f = tmp_path / "case.yaml"
    f.write_text(yaml.safe_dump(GOOD))
    assert main(["assurance-case", "check", str(f)]) == 0
    assert main(["assurance-case", "check", str(f), "--strict"]) == 1  # undeveloped claim warning
    assert main(["assurance-case", "render", str(f)]) == 0
    assert main(["assurance-case", "template"]) == 0
    (tmp_path / "bad.yaml").write_text("claims: 3\n")
    assert main(["assurance-case", "check", str(tmp_path / "bad.yaml")]) == 2
    capsys.readouterr()
    assert main(["assurance-case", "template"]) == 0
    tpl = tmp_path / "tpl.yaml"
    tpl.write_text(capsys.readouterr().out)
    assert main(["assurance-case", "check", str(tpl)]) == 0  # the starter template is itself valid
