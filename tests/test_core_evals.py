import pytest

from agentlib.evals import graders
from agentlib.evals.runner import discover_suites, run_offline
from agentlib.evals.spec import SpecError, load_suite

SAMPLE = """# Report
## Findings
| ID | Severity | Requirement |
|----|----------|-------------|
| F1 | High | V6.2.1 |

Cites nist-ssdf PW.7.1 and PO.1.1.

```json
{"verdict": "fail", "score": 2}
```
"""


@pytest.mark.parametrize("check,expected", [
    ({"type": "contains", "values": ["findings", "V6.2.1"]}, True),
    ({"type": "contains", "values": ["absent"]}, False),
    ({"type": "any_of", "values": ["x", "y", "High"]}, True),
    ({"type": "not_contains", "values": ["guarantee"]}, True),
    ({"type": "not_contains", "values": ["report"]}, False),
    ({"type": "regex", "pattern": r"PW\.\d+\.\d+"}, True),
    ({"type": "regex", "pattern": r"[A-Z]{2}\.\d\.\d", "count": 3}, False),
    ({"type": "sections", "values": ["Findings"]}, True),
    ({"type": "sections", "values": ["Recommendations"]}, False),
    ({"type": "ids", "pattern": r"\b(?:PO|PW|PS|RV)\.\d+\.\d+\b", "min": 2}, True),
    ({"type": "json_block", "required_keys": ["verdict"]}, True),
    ({"type": "json_block", "required_keys": ["nope"]}, False),
    ({"type": "table", "columns": ["ID", "Severity"]}, True),
    ({"type": "table", "columns": ["Owner"]}, False),
    ({"type": "max_words", "value": 5}, False),
    ({"type": "min_words", "value": 5}, True),
])
def test_graders(check, expected):
    assert graders.CHECK_TYPES[check["type"]].run(SAMPLE, check).passed is expected


def test_python_grader_errors_become_failures():
    r = graders.Python.run("x", {"function": "json:loads"})
    assert r.passed is False and "raised" in r.detail


def test_spec_rejects_bad_suites(tmp_path):
    d = tmp_path / "demo"
    d.mkdir()
    (d / "cases.yaml").write_text("skill: other\ndescription: d\ncases: []\n")
    with pytest.raises(SpecError):
        load_suite(d / "cases.yaml")
    (d / "cases.yaml").write_text("skill: demo\ndescription: d\ncases:\n  - id: a\n    prompt: p\n    checks: [{type: bogus}]\n")
    with pytest.raises(SpecError, match="unknown check type"):
        load_suite(d / "cases.yaml")
    (d / "cases.yaml").write_text("skill: demo\ndescription: d\ncases:\n  - id: a\n    prompt: p\n    checks: [{type: contains, values: [x]}]\n")
    with pytest.raises(SpecError, match="golden"):
        load_suite(d / "cases.yaml")


def test_offline_golden_and_negative(tmp_path):
    d = tmp_path / "demo"
    (d / "golden").mkdir(parents=True)
    (d / "golden" / "a.md").write_text("## Findings\nall good V1.1.1")
    (d / "golden" / "a.bad.md").write_text("nothing here")
    (d / "cases.yaml").write_text(
        "skill: demo\ndescription: d\ncases:\n  - id: a\n    prompt: p\n    golden: golden/a.md\n"
        "    negative: golden/a.bad.md\n    checks: [{type: sections, values: [Findings]}, {type: contains, values: [V1.1.1]}]\n")
    results = run_offline(load_suite(d / "cases.yaml"))
    assert [r.mode for r in results] == ["golden", "negative"]
    assert all(r.passed for r in results)


def test_all_repository_suites_pass_offline(root):
    failures = [r for s in discover_suites(root) for r in run_offline(s) if not r.passed]
    assert not failures, failures
