import json
import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-review-gates"
mod = load_script(SKILL, "review_readiness")
EX = skill_path(SKILL, "assets", "examples")
CRIT = json.loads(skill_path(SKILL, "assets", "data", "review-criteria.json").read_text())


def srr(**kw):
    ev = [{"criterion_id": c["id"], "status": "met", "evidence_ref": "ref"} for c in CRIT["reviews"]["SRR"]["criteria"]]
    d = {"review": "SRR", "authors": ["a"], "independent_reviewers": ["b"], "gate_authority": "g", "independent_review_ref": "review/rid-log.md", "evidence": ev,
         "checks": [], "actions": []}
    d.update(kw)
    return d


class ReviewTests(unittest.TestCase):
    def test_all_met_is_go(self):
        res = mod.evaluate(srr(), CRIT)
        self.assertEqual(res["recommendation"], "GO")
        self.assertIn("pending", res["decision"])

    def test_minor_action_conditions(self):
        res = mod.evaluate(srr(actions=[{"id": "A1", "severity": "minor", "owner": "o", "due": "2026-11-01"}]), CRIT)
        self.assertEqual(res["recommendation"], "GO_WITH_CONDITIONS")

    def test_major_action_blocks(self):
        res = mod.evaluate(srr(actions=[{"id": "A1", "severity": "major", "owner": "o", "due": "2026-11-01"}]), CRIT)
        self.assertEqual(res["recommendation"], "NO_GO")

    def test_failed_check_blocks(self):
        res = mod.evaluate(srr(checks=[{"name": "req_lint", "exit_code": 1}]), CRIT)
        self.assertEqual(res["recommendation"], "NO_GO")

    def test_self_review_blocks(self):
        res = mod.evaluate(srr(independent_reviewers=["a"]), CRIT)
        self.assertIn("no-independent-review", rules(res["findings"], "error"))
        self.assertEqual(res["recommendation"], "NO_GO")

    def test_nonblocking_missing_is_condition(self):
        d = srr()
        d["evidence"] = [e for e in d["evidence"] if e["criterion_id"] != "SRR-06"]
        self.assertEqual(mod.evaluate(d, CRIT)["recommendation"], "GO_WITH_CONDITIONS")

    def test_closed_action_needs_evidence(self):
        res = mod.evaluate(srr(actions=[{"id": "A1", "severity": "minor", "status": "closed"}]), CRIT)
        self.assertIn("closed-without-evidence", rules(res["findings"], "error"))

    def test_named_reviewer_without_record_is_condition(self):  # raised by ASTER demo builder
        d = srr()
        del d["independent_review_ref"]
        res = mod.evaluate(d, CRIT)
        self.assertEqual(res["recommendation"], "GO_WITH_CONDITIONS")
        self.assertIn("review-not-evidenced", rules(res["findings"], "warning"))

    def test_unknown_review(self):
        res = mod.evaluate({"review": "XYZ"}, CRIT)
        self.assertEqual(res["recommendation"], "NO_GO")

    def test_fixtures(self):
        code, out = run_json(SKILL, "review_readiness", EX / "review-pass.json")
        self.assertEqual((code, out["recommendation"]), (0, "GO_WITH_CONDITIONS"))
        code, out = run_json(SKILL, "review_readiness", EX / "review-fail.json")
        self.assertEqual((code, out["recommendation"]), (1, "NO_GO"))
        self.assertTrue({"claimed-without-evidence", "na-without-justification", "check-failed",
                         "action-incomplete", "no-independent-review"} <= rules(out["findings"], "error"))
        self.assertIn("TRR-03", out["blocking"])

    def test_criteria_provenance_disclaimer(self):
        self.assertIn("NOT the entrance/success criteria", CRIT["_provenance"])
        self.assertEqual(run_cli(SKILL, "review_readiness", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
