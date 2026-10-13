# Examples

## Tool walkthrough

Each command below runs on the sample inputs under `evals/*/fixtures/` (fictional projects). Several inputs are
deliberately defective, so a non-zero exit code shows the tool catching the defects. The steps are executed by
`tests/test_examples.py` from [`walkthrough.yaml`](walkthrough.yaml), so they stay in sync with the code.

```sh
pip install -r requirements-dev.txt
```

1. **Route a problem to skills** (expected exit 0)

   ```sh
   python -m agentlib route 'security review of a payments API and its CI/CD pipeline with SBOM'
   ```

2. **Lint weak requirements (NASA SE Appendix C)** (expected exit 1)

   ```sh
   python -m agentlib nasa-se lint-requirements evals/requirements-engineering/fixtures/weak-reqs.csv
   ```

3. **Check bidirectional traceability and verification methods** (expected exit 1)

   ```sh
   python -m agentlib nasa-se trace evals/requirements-engineering/fixtures/trace-set.csv
   ```

4. **Generate a PDR readiness checklist** (expected exit 0)

   ```sh
   python -m agentlib nasa-se review-checklist PDR
   ```

5. **Propose a NASA software class (candidate only)** (expected exit 0)

   ```sh
   python -m agentlib nasa-swe classify --answers evals/nasa-software-engineering/fixtures/cubesat-answers.yaml
   ```

6. **Validate an NPR 7150.2D compliance matrix** (expected exit 1)

   ```sh
   python -m agentlib nasa-swe check-matrix evals/nasa-software-engineering/fixtures/rmm-class-c.csv
   ```

7. **Validate an AI risk register (NIST AI RMF)** (expected exit 1)

   ```sh
   python -m agentlib ai-rmf check-register evals/nist-ai-rmf/fixtures/hiring-risk-register.csv
   ```

8. **AI RMF GOVERN profile gap analysis** (expected exit 1)

   ```sh
   python -m agentlib ai-rmf check-profile evals/nist-ai-rmf/fixtures/govern-profile.yaml
   ```

9. **Map a CI/CD pipeline to SSDF tasks (support, not compliance)** (expected exit 0)

   ```sh
   python -m agentlib ssdf map-pipeline evals/nist-ssdf/fixtures/acme-pipeline.yaml
   ```

10. **Score an SSDF gap assessment** (expected exit 1)

   ```sh
   python -m agentlib ssdf check-assessment evals/nist-ssdf/fixtures/acme-assessment.yaml
   ```

11. **Generate an ASVS Level 2 checklist for authentication** (expected exit 0)

   ```sh
   python -m agentlib asvs checklist --level 2 --chapters V6 --format md
   ```

12. **Validate an ASVS Level 1 assessment** (expected exit 1)

   ```sh
   python -m agentlib asvs check-assessment evals/owasp-asvs/fixtures/assessment-l1.yaml --level 1
   ```

13. **Suggest ASVS requirements for pentest findings** (expected exit 0)

   ```sh
   python -m agentlib asvs map-findings evals/owasp-asvs/fixtures/pentest-findings.json
   ```

14. **Green Book NPSV and BCR with the 2026 discount schedule** (expected exit 0)

   ```sh
   python -m agentlib greenbook npv evals/green-book-appraisal/fixtures/appraisal_flows.csv
   ```

15. **Switching values and sensitivity** (expected exit 0)

   ```sh
   python -m agentlib greenbook switching evals/green-book-appraisal/fixtures/appraisal_flows.csv
   ```

16. **Structural check of a flawed business case (strict mode fails)** (expected exit 1)

   ```sh
   python -m agentlib greenbook check-case evals/green-book-appraisal/fixtures/flawed_business_case.md --strict
   ```

17. **Audit citations and identifiers in a report** (expected exit 1)

   ```sh
   python -m agentlib evidence check evals/evidence-and-citation/fixtures/flawed-report.md
   ```

18. **Show a workflow plan (stages, agents, skills, gates)** (expected exit 0)

   ```sh
   python -m agentlib workflow show secure-software-delivery
   ```

To run a workflow as a tracked review folder: `python -m agentlib workflow init <id> --dir reviews/x`,
fill the artefact stubs, check progress with `workflow status reviews/x`, and record each gate decision with
`workflow gate reviews/x <stage> --result pass --by "<decision-maker>"`.

## A completed review (fictional)

[`sample-review/`](sample-review/) is a finished `secure-software-delivery` review of a fictional payments API,
produced with the workflow runner and the real tools: ASVS plan and verification report, SSDF assessment and
pipeline map, evidence audit, an assurance case (deliberately *incomplete*: one undeveloped claim) and the
board decision record. Start at [`sample-review/PLAN.md`](sample-review/PLAN.md) and
[`sample-review/release-recommendation.md`](sample-review/release-recommendation.md). Regenerate with
`python examples/build_sample_review.py`; `tests/test_sample_review.py` keeps it complete and valid.

## Claude Agent SDK

[`agent_sdk_review.py`](agent_sdk_review.py) loads this library as a local plugin and runs a skill or
command through the Claude Agent SDK (`pip install claude-agent-sdk`, needs `ANTHROPIC_API_KEY`).

## Full workflows in Claude Code

```text
/professional-agent-library:secure-delivery-review docs/system.md ci/pipeline.yaml
/professional-agent-library:business-case proposal.md costs.csv
/professional-agent-library:technical-review PDR reqs.csv docs/design/
```
