import json

import pytest

from agentlib.cli import main
from agentlib.frameworks import workflow as wfm


def _fill(directory, names):
    for n in names:
        (directory / f"{n}.md").write_text(f"# {n}\nreal content\n")


@pytest.mark.parametrize("wid", ["technical-review-gate", "secure-software-delivery", "ai-system-assurance",
                                 "public-investment-business-case", "software-assurance-audit"])
def test_every_workflow_initialises(tmp_path, wid):
    created = wfm.init(wid, tmp_path / wid)
    assert "PLAN.md" in created and "state.json" in created
    st = wfm.status(tmp_path / wid)
    assert st["next_stage"] == wfm.load_workflow(wid)["stages"][0]["id"]
    assert not st["complete"]


def test_full_lifecycle(tmp_path):
    d = tmp_path / "r"
    wfm.init("secure-software-delivery", d, {"system-description": "sys.md"})
    st = wfm.status(d)
    assert set(st["missing_required_inputs"]) == {"pipeline-description", "codebase"}
    # cannot pass with stubs
    with pytest.raises(wfm.WorkflowError, match="stubs"):
        wfm.record_gate(d, "scope", "pass", "AppSec lead")
    # cannot skip ahead
    with pytest.raises(wfm.WorkflowError, match="earlier stage"):
        wfm.record_gate(d, "process", "pass", "x")
    wf = wfm.load_workflow("secure-software-delivery")
    for stage in wf["stages"]:
        _fill(d, stage["produces"])
        wfm.record_gate(d, stage["id"], "pass", "Board")
    assert wfm.status(d)["complete"]
    # output started from the decision template
    state = json.loads((d / "state.json").read_text())
    assert state["gates"]["decision"]["by"] == "Board"


def test_failed_gate_blocks_and_waiver_needs_note(tmp_path):
    d = tmp_path / "r"
    wfm.init("technical-review-gate", d)
    _fill(d, ["readiness-checklist", "package-gap-list"])
    wfm.record_gate(d, "readiness", "fail", "Chief engineer", "gaps")
    st = wfm.status(d)
    assert st["next_stage"] == "readiness" and st["blocked_by_failed_gate"]
    with pytest.raises(wfm.WorkflowError, match="note"):
        wfm.record_gate(d, "readiness", "waived", "Chief engineer")
    wfm.record_gate(d, "readiness", "waived", "Chief engineer", "accepted at board")
    assert wfm.status(d)["next_stage"] == "requirements-audit"


def test_template_output_is_stubbed(tmp_path):
    d = tmp_path / "r"
    wfm.init("technical-review-gate", d)
    text = (d / "board-decision.md").read_text()
    assert wfm.STUB_MARK in text and "Review board decision record" in text


def test_errors(tmp_path):
    with pytest.raises(wfm.WorkflowError, match="unknown workflow"):
        wfm.init("nope", tmp_path / "x")
    with pytest.raises(wfm.WorkflowError, match="unknown input"):
        wfm.init("technical-review-gate", tmp_path / "y", {"bogus": "x"})
    wfm.init("technical-review-gate", tmp_path / "z")
    with pytest.raises(wfm.WorkflowError, match="already"):
        wfm.init("technical-review-gate", tmp_path / "z")
    with pytest.raises(wfm.WorkflowError, match="not a workflow folder"):
        wfm.status(tmp_path)


def test_cli(tmp_path, capsys):
    d = tmp_path / "rev"
    assert main(["workflow", "list"]) == 0
    assert main(["workflow", "show", "ai-system-assurance"]) == 0
    assert "GOVERN" in capsys.readouterr().out
    assert main(["workflow", "init", "ai-system-assurance", "--dir", str(d), "--input", "ai-system-description=a.md"]) == 0
    assert main(["workflow", "status", str(d)]) == 3
    assert main(["workflow", "gate", str(d), "map", "--result", "pass", "--by", "x"]) == 2  # stubs
    assert main(["workflow", "init", "nope", "--dir", str(tmp_path / "n")]) == 2
