"""Regenerate examples/sample-review: a completed secure-software-delivery review for a FICTIONAL system.

    python examples/build_sample_review.py

Assessments are produced from the tools' own templates with deterministic, illustrative statuses; tool
outputs (checks, matrices, pipeline map) are produced by running the real CLI. Narrative artefacts are
written here. tests/test_sample_review.py checks the result stays complete and valid.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agentlib.cli import main  # noqa: E402
from agentlib.frameworks import workflow as wf  # noqa: E402

OUT = ROOT / "examples" / "sample-review"
SYSTEM = "Acme Checkout API (fictional), commit a1b2c3d"
PIPELINE = ROOT / "evals" / "nist-ssdf" / "fixtures" / "acme-pipeline.yaml"

# Illustrative SSDF statuses (everything else: implemented with evidence)
SSDF_PARTIAL = {"PO.4.1", "PO.4.2", "PW.8.2", "RV.1.2", "RV.3.3"}
SSDF_PLANNED = {"PS.2.1", "RV.3.4"}
SSDF_NA = {"PW.6.1": "Interpreted Python services; no compiler toolchain in scope",
           "PW.6.2": "No compilation step; interpreter hardening covered by base image policy"}
ASVS_FAIL = {"6.3.1": "F-01", "6.4.1": "F-02"}
ASVS_NA = {}


def run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, buf.getvalue()


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def ssdf_assessment() -> Path:
    _, tpl = run(["ssdf", "assessment-template", "--format", "yaml"])
    data = yaml.safe_load(tpl)
    data["assessment"].update(organisation="Acme Payments Ltd (fictional)", scope=SYSTEM,
                              assessor="secure-development-reviewer (AI-assisted)", date="2026-10-13")
    for t in data["tasks"]:
        tid = t["id"]
        if tid in SSDF_NA:
            t.update(status="not-applicable", justification=SSDF_NA[tid])
        elif tid in SSDF_PLANNED:
            t.update(status="planned", owner="Platform security lead", target_date="2026-12-15")
        elif tid in SSDF_PARTIAL:
            t.update(status="partial", evidence=[f"docs/ssdf/{tid}.md (illustrative)"], owner="AppSec team")
        else:
            t.update(status="implemented", evidence=[f"docs/ssdf/{tid}.md (illustrative)"])
    path = OUT / "data" / "ssdf-assessment.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def asvs_assessment() -> Path:
    _, tpl = run(["asvs", "checklist", "--level", "1", "--chapters", "V6", "--format", "yaml"])
    data = yaml.safe_load(tpl)
    data["application"] = SYSTEM
    for r in data["results"]:
        if r["id"] in ASVS_FAIL:
            r.update(status="fail", finding_ref=ASVS_FAIL[r["id"]], evidence="see finding")
        else:
            r.update(status="pass", evidence=f"Test record T-{r['id']} (illustrative)")
    path = OUT / "data" / "asvs-v6-l1.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def main_build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    wf.init("secure-software-delivery", OUT, {"system-description": "system.md",
                                              "pipeline-description": "data/pipeline.yaml",
                                              "codebase": "acme-checkout@a1b2c3d"})
    (OUT / "data").mkdir()
    shutil.copy(PIPELINE, OUT / "data" / "pipeline.yaml")
    write("system.md", f"# System description\n\n{SYSTEM}: REST API taking card-not-present payments for a "
          "fictional retailer. Internet-facing; processes personal and payment data; 6 services.")
    ssdf = ssdf_assessment()
    asvs = asvs_assessment()
    _, ssdf_check = run(["ssdf", "check-assessment", str(ssdf)])
    _, ssdf_map = run(["ssdf", "map-pipeline", str(OUT / "data" / "pipeline.yaml")])
    _, asvs_check = run(["asvs", "check-assessment", str(asvs), "--level", "1"])

    write("asvs-verification-plan.md", """# ASVS verification plan (fictional example)

- **Application:** Acme Checkout API (fictional), commit a1b2c3d.
- **Target level:** L1 for this illustrative sample, scoped to V6 Authentication. A real payments API would
  normally justify L2 or above: ASVS leaves level choice to the organisation's risk assessment
  [owasp-asvs, p. 15], and higher levels are recommendations rather than mandatory [owasp-asvs, p. 13].
- **Method:** configuration review, code review and test of each requirement; evidence recorded per row.
- **Checklist:** `python -m agentlib asvs checklist --level 1 --chapters V6` (13 requirements).""")
    write("ssdf-assessment.md", "# SSDF assessment (fictional example)\n\nSource data: `data/ssdf-assessment.yaml`.\n\n"
          "```text\n" + ssdf_check.strip() + "\n```")
    write("ssdf-pipeline-map.md", ssdf_map)
    write("asvs-assessment.md", "# ASVS assessment data\n\nSource data: `data/asvs-v6-l1.yaml` "
          "(checked with `python -m agentlib asvs check-assessment data/asvs-v6-l1.yaml --level 1`).")
    write("asvs-verification-report.md", "# ASVS verification report (fictional example)\n\n"
          "Two failures, each with a finding: F-01 (6.3.1) and F-02 (6.4.1). Results below are tool output.\n\n"
          "```text\n" + asvs_check.strip() + "\n```")
    write("evidence-audit-report.md", """# Evidence audit (fictional example)

- `python -m agentlib evidence check *.md --require-citations`: no errors (see `tests/test_sample_review.py`).
- Spot-checks: ASVS level-selection guidance [owasp-asvs, p. 15] and the statement that higher levels are
  recommendations [owasp-asvs, p. 13] confirmed against the pinned PDF.
- Evidence strengths: assessment rows cite illustrative records only; in a real review each would be an
  evidence record per the evidence-and-citation skill.
- **Verdict:** Pass with corrections (illustrative evidence must be replaced by real records).""")
    case = {
        "case": {"id": "AC-ACME-1", "title": "Acme Checkout API is acceptable for release (fictional)",
                 "scope": SYSTEM, "decision_authority": "Head of Security Assurance (fictional)"},
        "claims": [
            {"id": "C1", "text": "The checkout API is acceptably secure for release.", "criticality": "high",
             "argument": "Product security (ASVS V6 at L1) and secure development process (SSDF) both hold, "
                         "with open findings treated as release conditions.",
             "subclaims": ["C1.1", "C1.2", "C1.3"]},
            {"id": "C1.1", "text": "Authentication requirements at ASVS L1 (V6) are met except F-01, F-02.",
             "criticality": "high", "frameworks": ["V6.3.1"], "evidence": ["EV-1"]},
            {"id": "C1.2", "text": "Code is reviewed before merge.", "criticality": "medium",
             "frameworks": ["PW.7.1"], "evidence": ["EV-2"]},
            {"id": "C1.3", "text": "Release integrity can be verified by consumers.", "status": "undeveloped",
             "justification": "PS.2.1 is planned (target 2026-12-15); release signing not yet in place."},
        ],
        "evidence": [
            {"id": "EV-1", "description": "ASVS V6 L1 verification results", "artefact": "data/asvs-v6-l1.yaml",
             "method": "Test", "strength": "E3"},
            {"id": "EV-2", "description": "SSDF assessment row PW.7.1 and branch protection settings",
             "artefact": "data/ssdf-assessment.yaml", "method": "Inspection", "strength": "E2"},
        ],
    }
    (OUT / "data" / "assurance-case.yaml").write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
    _, rendered = run(["assurance-case", "render", str(OUT / "data" / "assurance-case.yaml")])
    write("assurance-case.md", rendered)
    write("release-recommendation.md", """# Review board decision record (fictional example)

| Field | Value |
|---|---|
| Review | secure-software-delivery v1.0.0 |
| Subject | Acme Checkout API (fictional), commit a1b2c3d |
| Accountable decision-maker | Head of Security Assurance (fictional) |

## Recommendation

**Proceed with conditions.** ASVS V6 (L1) verification found two failures (F-01, F-02); the SSDF assessment
shows release integrity verification (PS.2.1) is planned, not implemented. The assurance case
(`assurance-case.md`) is *incomplete* by design: claim C1.3 is undeveloped.

## Conditions and actions

| ID | Action | Owner | Due | Closes |
|---|---|---|---|---|
| A-1 | Fix F-01 and F-02 and re-verify 6.3.1 and 6.4.1 | Auth team | before release | F-01, F-02 |
| A-2 | Implement release signing and publish verification instructions | Platform security lead | 2026-12-15 | PS.2.1, C1.3 |

## Residual risks

| Risk | Proposed treatment | Acceptance authority |
|---|---|---|
| Consumers cannot verify release integrity until A-2 | Accept temporarily with A-2 tracked | Head of Security Assurance |

## Limitations

Fictional, illustrative example produced with AI assistance. It does not constitute approval; the decision
rests with the accountable decision-maker named above.""")
    for stage, by in (("scope", "Head of Security Assurance (fictional)"), ("process", "automated check"),
                      ("verify", "automated check"), ("evidence-audit", "evidence-auditor"),
                      ("decision", "Head of Security Assurance (fictional)")):
        wf.record_gate(OUT, stage, "pass", by, "illustrative sample")
    state = json.loads((OUT / "state.json").read_text())
    for g in state["gates"].values():  # stable output for diffs
        g["date"] = "2026-10-13T00:00:00+00:00"
    state["created"] = "2026-10-13"
    (OUT / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main_build()
    print(f"wrote {OUT}")
