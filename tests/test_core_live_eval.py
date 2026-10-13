"""Live-mode evaluation with the model call mocked (no network, no API key)."""
import json

from agentlib.cli import main
from agentlib.evals import runner
from agentlib.evals.spec import load_suite


def test_skill_system_prompt_includes_skill_and_references(root):
    prompt = runner.skill_system_prompt(root, "owasp-asvs")
    assert "name: owasp-asvs" in prompt
    assert '<reference path="references/' in prompt
    assert len(prompt) < runner.MAX_REFERENCE_CHARS + 50_000


def test_run_live_grades_golden_responses(tmp_path, root, monkeypatch):
    suite = load_suite(root / "evals" / "nist-ssdf" / "cases.yaml")
    goldens = {c.full_prompt(): (c.base / c.golden).read_text() for c in suite.cases}
    calls = []

    def fake_call(system, prompt, model, max_tokens=8000):
        calls.append((system[:40], model))
        return goldens[prompt]

    monkeypatch.setattr(runner, "call_claude", fake_call)
    results = runner.run_live(suite, root, "test-model", tmp_path)
    assert len(results) == len(suite.cases) and all(r.passed for r in results)
    assert all(m == "test-model" for _, m in calls)
    assert len(list(tmp_path.glob("nist-ssdf__*.md"))) == len(suite.cases)


def test_run_live_reports_api_errors_without_crashing(tmp_path, root, monkeypatch):
    suite = load_suite(root / "evals" / "framework-selector" / "cases.yaml")

    def boom(*a, **k):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(runner, "call_claude", boom)
    results = runner.run_live(suite, root, "m", tmp_path)
    assert results and not any(r.passed for r in results)
    assert "rate limited" in results[0].note


def test_call_claude_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        runner.call_claude("s", "p", "m")
    except RuntimeError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError")


def test_cli_grade_mode(tmp_path, root, capsys):
    golden = root / "evals" / "evidence-and-citation" / "golden" / "grade-policy-only.md"
    bad = root / "evals" / "evidence-and-citation" / "golden" / "grade-policy-only.bad.md"
    out = tmp_path / "r.json"
    assert main(["eval", "--mode", "grade", "--skill", "evidence-and-citation", "--case", "grade-policy-only",
                 "--output", str(golden), "--json", str(out)]) == 0
    assert json.loads(out.read_text())[0]["passed"] is True
    assert main(["eval", "--mode", "grade", "--skill", "evidence-and-citation", "--case", "grade-policy-only",
                 "--output", str(bad)]) == 1
    assert main(["eval", "--mode", "grade", "--skill", "evidence-and-citation"]) == 2
