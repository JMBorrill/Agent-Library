import copy
import datetime as dt
import json
import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "ai-risk-assessment"
reg = load_script(SKILL, "ai_risk_register_check")
card_mod = load_script(SKILL, "system_card_check")
EX = skill_path(SKILL, "assets", "examples")
FINDINGS_SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
CARD_SCHEMA_PATH = skill_path(SKILL, "assets", "schemas", "system-card.schema.json")
CARD_SCHEMA = json.loads(CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
STRUCT = reg.load_structure()
AS_OF = dt.date(2026, 10, 13)


def row(**kw):
    base = {c: "" for c in reg.REQUIRED_COLUMNS + reg.OPTIONAL_COLUMNS}
    base.update(risk_id="T-RSK-001", description="d", rmf_refs="AIRMF-1.0-MAP-1", harm_category="people",
                affected_party="applicants", likelihood="3", impact="4", inherent_score="12",
                controls="c", eval_ids="EV-1", owner="Owner A", residual_likelihood="2",
                residual_impact="3", residual_score="6", status="mitigating", review_date="2026-12-01")
    base.update(kw)
    return base


def lint(*rows, as_of=AS_OF, high=15):
    return reg.lint(list(rows[0].keys()) if rows else reg.REQUIRED_COLUMNS, list(rows), STRUCT, as_of, high)


class RiskRegisterTests(unittest.TestCase):
    def test_pass_fixture_exit0_and_schema(self):
        code, out = run_json(SKILL, "ai_risk_register_check", EX / "ai-risk-register-pass.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["errors"], 0)
        self.assertEqual(out["summary"]["warnings"], 0)
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_fail_fixture_detects_seeded_defects(self):
        code, out = run_json(SKILL, "ai_risk_register_check", EX / "ai-risk-register-fail.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ["duplicate-id", "rmf-ref-unknown", "rmf-ref-format", "inherent-score-mismatch", "score-range",
                  "no-owner", "no-eval-evidence", "high-residual-not-accepted", "accepted-by-non-human",
                  "review-overdue", "risk-id-format", "status"]:
            self.assertIn(r, errs)
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_clean_row(self):
        res = lint(row())
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertEqual(res["summary"]["warnings"], 0)

    def test_ref_validation_against_structure(self):
        cases = {"AIRMF-1.0-GOVERN-6": "", "AIRMF-1.0-GOVERN-7": "error", "AIRMF-1.0-MAP-5": "",
                 "AIRMF-1.0-MAP-6": "error", "AIRMF-1.0-MEASURE-4": "", "AIRMF-1.0-MEASURE-5": "error",
                 "AIRMF-1.0-MANAGE-4": "", "AIRMF-1.0-MANAGE-0": "error", "AIRMF-1.0-MEASURE-2.11": "info",
                 "AIRMF-2.0-MAP-1": "error", "AIRMF-1.0-PLAN-1": "error", "airmf-1.0-map-1": "error",
                 "AIRMF-1.0-MAP": "error"}
        for ref, expected in cases.items():
            with self.subTest(ref=ref):
                self.assertEqual(reg.check_ref(ref, STRUCT)[1], expected)

    def test_structure_has_19_categories(self):
        n = sum(len(f["categories"]) for f in STRUCT["functions"].values())
        self.assertEqual(n, 19)  # secondary corroboration: 6+5+4+4

    def test_known_answer_scores(self):
        res = lint(row(likelihood="5", impact="5", inherent_score="25", residual_likelihood="3",
                       residual_impact="5", residual_score="15", accepted_by="Jane Example (CRO)"))
        self.assertEqual(res["summary"]["errors"], 0)
        res = lint(row(inherent_score="13"))
        self.assertIn("inherent-score-mismatch", rules(res["findings"], "error"))
        res = lint(row(residual_score="7"))
        self.assertIn("residual-score-mismatch", rules(res["findings"], "error"))

    def test_high_residual_threshold_boundary(self):
        res = lint(row(likelihood="5", impact="5", inherent_score="25", residual_likelihood="3",
                       residual_impact="5", residual_score="15"))
        self.assertIn("high-residual-not-accepted", rules(res["findings"], "error"))
        res = lint(row(residual_likelihood="2", residual_impact="7", residual_score=""))
        self.assertIn("score-range", rules(res["findings"], "error"))
        res = lint(row(likelihood="5", impact="5", inherent_score="25", residual_likelihood="3",
                       residual_impact="5", residual_score="15"), high=20)
        self.assertNotIn("high-residual-not-accepted", rules(res["findings"]))

    def test_closed_high_residual_not_flagged(self):
        res = lint(row(residual_likelihood="4", residual_impact="4", residual_score="16", status="closed", eval_ids=""))
        self.assertNotIn("high-residual-not-accepted", rules(res["findings"]))
        self.assertNotIn("no-eval-evidence", rules(res["findings"]))

    def test_no_eval_severity_scales_with_inherent(self):
        low = lint(row(eval_ids=""))
        self.assertIn("no-eval-evidence", rules(low["findings"], "warning"))
        high = lint(row(eval_ids="", likelihood="4", impact="4", inherent_score="16"))
        self.assertIn("no-eval-evidence", rules(high["findings"], "error"))

    def test_stale_review_only_with_as_of(self):
        r = row(review_date="2026-01-01")
        self.assertIn("review-overdue", rules(lint(r)["findings"], "error"))
        self.assertIn("stale-check-skipped", rules(lint(r, as_of=None)["findings"], "info"))

    def test_non_integer_and_empty(self):
        self.assertIn("score-not-integer", rules(lint(row(likelihood="3.5"))["findings"], "error"))
        res = reg.lint(reg.REQUIRED_COLUMNS, [], STRUCT, AS_OF)
        self.assertIn("empty-register", rules(res["findings"], "error"))
        res = reg.lint(["risk_id"], [], STRUCT, AS_OF)
        self.assertIn("missing-columns", rules(res["findings"], "error"))

    def test_cli_usage_errors_exit2(self):
        self.assertEqual(run_cli(SKILL, "ai_risk_register_check", "missing.csv").returncode, 2)
        self.assertEqual(run_cli(SKILL, "ai_risk_register_check", EX / "ai-risk-register-pass.csv",
                                 "--as-of", "13/10/2026").returncode, 2)


class SystemCardTests(unittest.TestCase):
    def setUp(self):
        self.card = json.loads((EX / "system-card-pass.json").read_text(encoding="utf-8"))

    def test_pass_card_exit0_schema(self):
        code, out = run_json(SKILL, "system_card_check", EX / "system-card-pass.json", "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        self.assertIn("recommendation-awaiting-sign-off", rules(out["findings"], "info"))
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_pass_card_valid_against_published_schema(self):
        assert_schema(self, self.card, CARD_SCHEMA_PATH)

    def test_fail_card_exit1_rules(self):
        code, out = run_json(SKILL, "system_card_check", EX / "system-card-fail.json", "--as-of", "2026-10-13")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ["eval-result-inconsistent", "go-with-failing-eval", "duplicate-eval-id", "sign-off-non-human",
                  "sign-off-incomplete", "no-human-contact", "schema-required", "schema-format",
                  "schema-min-items", "schema-pattern", "owner-non-human"]:
            self.assertIn(r, errs)
        self.assertIn("eval-stale", rules(out["findings"], "warning"))

    def test_builtin_validator_agrees_with_jsonschema_on_fail_card(self):
        bad = json.loads((EX / "system-card-fail.json").read_text(encoding="utf-8"))
        self.assertTrue(card_mod.validate_schema(bad, CARD_SCHEMA))
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        self.assertTrue(list(jsonschema.Draft202012Validator(CARD_SCHEMA).iter_errors(bad)))

    def test_eval_threshold_comparators(self):
        c = copy.deepcopy(self.card)
        c["evaluations"][1].update(value=0.01, result="pass")  # leakage 0.01 <= 0.0 is false
        res = card_mod.check_card(c, CARD_SCHEMA, AS_OF)
        self.assertIn("eval-result-inconsistent", rules(res["findings"], "error"))
        c["evaluations"][1].update(value=0.0, result="fail")
        res = card_mod.check_card(c, CARD_SCHEMA, AS_OF)
        self.assertIn("eval-result-inconsistent", rules(res["findings"], "error"))

    def test_conditions_required_when_failing(self):
        c = copy.deepcopy(self.card)
        c["evaluations"][0].update(value=0.9, result="fail")
        c.pop("conditions")
        self.assertIn("conditions-missing", rules(card_mod.check_card(c, CARD_SCHEMA, AS_OF)["findings"], "error"))

    def test_assurance_language_warning(self):
        c = copy.deepcopy(self.card)
        c["known_limitations"].append("System is fully compliant with policy")
        self.assertIn("assurance-language", rules(card_mod.check_card(c, CARD_SCHEMA, AS_OF)["findings"], "warning"))

    def test_eval_future_date_and_staleness_boundary(self):
        c = copy.deepcopy(self.card)
        c["evaluations"][0]["date"] = "2026-10-14"
        self.assertIn("eval-date-future", rules(card_mod.check_card(c, CARD_SCHEMA, AS_OF)["findings"], "error"))
        c["evaluations"][0]["date"] = "2026-04-16"  # exactly 180 days before as-of
        self.assertNotIn("eval-stale", rules(card_mod.check_card(c, CARD_SCHEMA, AS_OF, 180)["findings"]))
        c["evaluations"][0]["date"] = "2026-04-15"  # 181 days
        self.assertIn("eval-stale", rules(card_mod.check_card(c, CARD_SCHEMA, AS_OF, 180)["findings"]))

    def test_non_object_card_and_unreadable(self):
        res = card_mod.check_card([], CARD_SCHEMA)
        self.assertIn("schema-type", rules(res["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "system_card_check", "nope.json").returncode, 2)

    def test_output_never_says_approved(self):
        proc = run_cli(SKILL, "system_card_check", EX / "system-card-pass.json")
        self.assertNotRegex(proc.stdout.lower(), r"\bapproved\b|\bcompliant\b")


class LibraryBugRegressionTests(unittest.TestCase):
    """Raised by the mortgage-criteria demo builder."""

    def test_human_role_titles_with_model_are_human(self):
        card_mod = load_script("ai-risk-assessment", "system_card_check")
        self.assertFalse(card_mod.NON_HUMAN.search("Head of Model Risk (synthetic)"))
        self.assertFalse(card_mod.NON_HUMAN.search("AI Governance Lead"))
        self.assertTrue(card_mod.NON_HUMAN.search("the model"))
        self.assertTrue(card_mod.NON_HUMAN.search("GPT-4o"))
        self.assertTrue(card_mod.NON_HUMAN.search("Support chatbot"))

    def test_unknown_eval_id(self):
        reg = load_script("ai-risk-assessment", "ai_risk_register_check")
        ex = skill_path("ai-risk-assessment", "assets", "examples")
        csv_path = next(p for p in ex.iterdir() if p.suffix == ".csv" and "pass" in p.name)
        cols, rows = reg.read_rows(csv_path)
        structure = reg.load_structure(reg.DEFAULT_STRUCTURE)
        ids = {e for r in rows for e in reg.split_list(r["eval_ids"])}
        self.assertTrue(ids, "pass fixture should link evals")
        ok = reg.lint(cols, rows, structure, known_evals=ids)
        self.assertNotIn("unknown-eval", rules(ok["findings"]))
        bad = reg.lint(cols, rows, structure, known_evals=set())
        self.assertIn("unknown-eval", rules(bad["findings"], "error"))


if __name__ == "__main__":
    unittest.main()
