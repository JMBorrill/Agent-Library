"""The committed sample review must stay complete, valid and properly cited."""
from pathlib import Path

from agentlib.frameworks import assurance_case as ac
from agentlib.frameworks import evidence
from agentlib.frameworks import workflow as wf

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample-review"


def test_workflow_complete():
    st = wf.status(SAMPLE)
    assert st["complete"], st


def test_documents_pass_evidence_check():
    for md in sorted(SAMPLE.glob("*.md")):
        errors = [f for f in evidence.check_document(md.read_text(encoding="utf-8"), ROOT) if f.level == "error"]
        assert not errors, (md.name, errors)


def test_assurance_case_valid_and_incomplete_by_design():
    case = ac.load(SAMPLE / "data" / "assurance-case.yaml")
    findings = ac.check(case, base=SAMPLE)
    assert ac.summary(case, findings)["verdict"] == "incomplete"


def test_assessments_validate():
    from agentlib.cli import main

    assert main(["ssdf", "check-assessment", str(SAMPLE / "data" / "ssdf-assessment.yaml")]) == 0
    # ASVS has two documented failures (with findings): valid and complete, so exit 0 unless --strict
    assert main(["asvs", "check-assessment", str(SAMPLE / "data" / "asvs-v6-l1.yaml"), "--level", "1"]) == 0
