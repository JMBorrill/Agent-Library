import unittest
from datetime import date

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-risk-analysis"
risk = load_script(SKILL, "risk_check")
fmea = load_script(SKILL, "fmea_calc")
EX = skill_path(SKILL, "assets", "examples")
COLS = ["risk_id", "title", "statement", "category", "likelihood", "consequence", "approach", "mitigation",
        "trigger", "owner", "residual_likelihood", "residual_consequence", "accepted_by", "status",
        "review_date", "related_ids", "evidence"]
STMT = "Given A, there is a possibility of B, resulting in C."


def r(**kw):
    base = {c: "" for c in COLS}
    base.update(risk_id="P-RSK-001", title="t", statement=STMT, category="technical", likelihood="2",
                consequence="2", approach="watch", owner="o", status="open", review_date="2026-10-01")
    base.update(kw)
    return base


class RiskTests(unittest.TestCase):
    def check(self, *rows, **kw):
        return risk.check(COLS, list(rows), dict(risk.DEFAULT_POLICY), **kw)

    def test_levels(self):
        p = risk.DEFAULT_POLICY
        self.assertEqual(risk.level(3, 5, p), "high")   # policy high cell
        self.assertEqual(risk.level(5, 3, p), "high")
        self.assertEqual(risk.level(3, 3, p), "medium")
        self.assertEqual(risk.level(1, 5, p), "low")
        self.assertEqual(risk.level(5, 5, p), "high")

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "risk_check", EX / "risks-pass.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["top_risks"][0], "DEMO-RSK-001")
        self.assertIn("safety-escalation", rules(out["findings"], "warning"))

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "risk_check", EX / "risks-fail.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 1)
        self.assertTrue({"no-owner", "unauthorised-acceptance", "duplicate-id", "score-range"}
                        <= rules(out["findings"], "error"))
        self.assertTrue({"statement-form", "stale-review", "no-review-date"} <= rules(out["findings"], "warning"))

    def test_high_risk_mitigation_requirements(self):
        res = self.check(r(likelihood="4", consequence="4", approach="mitigate"))
        self.assertTrue({"no-mitigation", "no-trigger"} <= rules(res["findings"], "error"))

    def test_accept_high_requires_acceptor(self):
        bad = self.check(r(likelihood="4", consequence="5", approach="accept"))
        self.assertIn("unauthorised-acceptance", rules(bad["findings"], "error"))
        ok = self.check(r(likelihood="4", consequence="5", approach="accept", accepted_by="Programme manager 2026-10-01"))
        self.assertNotIn("unauthorised-acceptance", rules(ok["findings"]))

    def test_residual_exceeding_inherent(self):
        res = self.check(r(approach="mitigate", mitigation="m", trigger="t", residual_likelihood="3", residual_consequence="3"))
        self.assertIn("residual-exceeds-inherent", rules(res["findings"], "error"))

    def test_stale_review_uses_policy_by_level(self):
        res = self.check(r(review_date="2026-01-01"), as_of=date(2026, 10, 13))
        self.assertIn("stale-review", rules(res["findings"], "warning"))
        res = self.check(r(review_date="2026-09-01"), as_of=date(2026, 10, 13))
        self.assertNotIn("stale-review", rules(res["findings"]))

    def test_unknown_related_ids(self):
        res = self.check(r(related_ids="P-SYS-001;P-SYS-404"), known_ids={"P-SYS-001"})
        self.assertIn("unknown-related-id", rules(res["findings"], "error"))

    def test_closed_risk_without_owner_ok(self):
        res = self.check(r(owner="", status="closed"))
        self.assertNotIn("no-owner", rules(res["findings"]))


class FmeaTests(unittest.TestCase):
    COLS = ["fmea_id", "item", "failure_mode", "effect", "cause", "severity", "occurrence", "detection",
            "recommended_action", "owner"]

    def row(self, **kw):
        b = dict(fmea_id="F1", item="i", failure_mode="m", effect="e", cause="c", severity="5",
                 occurrence="5", detection="5", recommended_action="", owner="")
        b.update(kw)
        return b

    def test_rpn_known_answer_and_ranking(self):
        code, out = run_json(SKILL, "fmea_calc", EX / "fmea-example.csv")
        self.assertEqual(code, 0)
        self.assertEqual([x["fmea_id"] for x in out["ranked"]], ["FM-001", "FM-003", "FM-002"])
        self.assertEqual(out["ranked"][0]["rpn"], 9 * 3 * 4)

    def test_severity_overrides_low_rpn(self):
        res = fmea.analyse(self.COLS, [self.row(severity="10", occurrence="1", detection="1")])
        self.assertIn("no-action", rules(res["findings"], "error"))
        self.assertIn("high-severity", rules(res["findings"], "warning"))

    def test_rpn_threshold(self):
        res = fmea.analyse(self.COLS, [self.row()])  # RPN 125
        self.assertIn("no-action", rules(res["findings"], "error"))
        res = fmea.analyse(self.COLS, [self.row(occurrence="2")])  # RPN 50
        self.assertEqual(res["summary"]["errors"], 0)

    def test_range_validation(self):
        res = fmea.analyse(self.COLS, [self.row(severity="11")])
        self.assertIn("range", rules(res["findings"], "error"))
        res = fmea.analyse(self.COLS, [self.row(severity="x")])
        self.assertIn("non-integer", rules(res["findings"], "error"))

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "fmea_calc", "missing.csv").returncode, 2)


if __name__ == "__main__":
    unittest.main()
