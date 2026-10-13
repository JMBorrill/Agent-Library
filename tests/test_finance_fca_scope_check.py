"""Tests for finance-fca-scope-check/reg_triage.py."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "finance-fca-scope-check"
rt = load_script(SKILL, "reg_triage")
EX = skill_path(SKILL, "assets", "examples")
SCH = skill_path(SKILL, "assets", "schemas")
RULES_PATH = skill_path(SKILL, "assets", "rules", "triage-rules.json")
RULES = rt.validate_rules(json.loads(RULES_PATH.read_text()))
PASS = json.loads((EX / "questionnaire-pass.json").read_text())


def areas(out):
    return {c["rule_id"] for c in out["candidates"]}


class Triage(unittest.TestCase):
    def test_second_charge_criteria_search_platform(self):
        out = rt.triage(copy.deepcopy(PASS), RULES)
        self.assertEqual(out["status"], "triage_complete_signoff_required")
        expected = {"TRI-PERG-001", "TRI-PERG-002", "TRI-MCOB-001", "TRI-MCOB-002", "TRI-MCOB-004",
                    "TRI-PRIN-001", "TRI-PRIN-002", "TRI-SYSC-001", "TRI-SYSC-002", "TRI-DISP-001",
                    "TRI-GDPR-001", "TRI-GDPR-002", "TRI-EQA-001"}
        self.assertTrue(expected <= areas(out))
        self.assertNotIn("TRI-CONC-001", areas(out))
        self.assertEqual(set(out["summary"]["out_of_registry"]),
                         {"UK GDPR / Data Protection Act 2018 (ICO)", "UK GDPR automated decision-making (ICO)",
                          "Equality Act 2010"})

    def test_every_candidate_requires_signoff_and_version_check(self):
        out = rt.triage(copy.deepcopy(PASS), RULES)
        for c in out["candidates"]:
            self.assertTrue(c["verify_effective_version"])
            self.assertTrue(c["human_signoff_required"]["required"])
            self.assertTrue(any(role in c["human_signoff_required"]["role"]
                                for role in ("Compliance officer", "Legal counsel")))
            self.assertIn(c["verification"], ("unverified", "partially_corroborated_secondary"))

    def test_non_uk_escalates_with_no_candidates(self):
        for jur in ("Ireland", "US", ""):
            q = dict(PASS, jurisdiction=jur)
            out = rt.triage(q, RULES)
            self.assertEqual(out["status"], "escalate")
            self.assertEqual(out["candidates"], [])
        q = {k: v for k, v in PASS.items() if k != "jurisdiction"}
        self.assertEqual(rt.triage(q, RULES)["status"], "escalate")

    def test_uk_aliases(self):
        for jur in ("United Kingdom", "England", "scotland", "GB"):
            self.assertEqual(rt.triage(dict(PASS, jurisdiction=jur), RULES)["status"],
                             "triage_complete_signoff_required")

    def test_missing_answers_refer(self):
        q = copy.deepcopy(PASS)
        del q["vulnerable_customers"]
        q["activities"]["lends"] = None
        out = rt.triage(q, RULES)
        self.assertEqual(out["status"], "refer")
        ids = {f["id"] for f in out["findings"] if f["rule"] == "missing-answer"}
        self.assertEqual(ids, {"vulnerable_customers", "activities.lends"})

    def test_unrecognised_answers_refer(self):
        q = dict(PASS, products=["crypto_loan"], service_model="robo")
        out = rt.triage(q, RULES)
        self.assertEqual(out["status"], "refer")
        self.assertIn("unrecognised-answer", rules(out["findings"], "error"))

    def test_bnpl_and_unsecured_trigger_conc(self):
        q = dict(PASS, products=["bnpl"])
        ids = areas(rt.triage(q, RULES))
        self.assertTrue({"TRI-CONC-001", "TRI-CONC-002"} <= ids)
        self.assertNotIn("TRI-MCOB-001", ids)

    def test_business_only_customers(self):
        q = dict(PASS, customer_types=["business"], products=["business_lending"])
        ids = areas(rt.triage(q, RULES))
        self.assertIn("TRI-BUS-001", ids)
        self.assertNotIn("TRI-PRIN-001", ids)

    def test_rules_table_provenance_complete(self):
        doc = json.loads(RULES_PATH.read_text())
        for r in doc["rules"]:
            for k in rt.RULE_FIELDS:
                self.assertTrue(r.get(k) not in (None, ""), f"{r['rule_id']} missing {k}")
        bad = copy.deepcopy(doc)
        bad["rules"][0]["provenance"] = ""
        with self.assertRaises(rt.InputError):
            rt.validate_rules(bad)


class Cli(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "reg_triage", EX / "questionnaire-pass.json")
        self.assertEqual(code, 0)
        assert_schema(self, out, SCH / "triage-output.schema.json")
        assert_schema(self, PASS, SCH / "questionnaire.schema.json")

    def test_fail_non_uk(self):
        code, out = run_json(SKILL, "reg_triage", EX / "questionnaire-fail-non-uk.json")
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "escalate")
        self.assertEqual(rules(out["findings"], "error"), {"non-uk-jurisdiction"})
        assert_schema(self, out, SCH / "triage-output.schema.json")

    def test_fail_missing(self):
        code, out = run_json(SKILL, "reg_triage", EX / "questionnaire-fail-missing.json")
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "refer")
        self.assertEqual(rules(out["findings"], "error"), {"missing-answer", "unrecognised-answer"})
        assert_schema(self, out, SCH / "triage-output.schema.json")

    def test_bad_inputs_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text("[1, 2")
            self.assertEqual(run_cli(SKILL, "reg_triage", p).returncode, 2)
            r = Path(td) / "rules.json"
            r.write_text(json.dumps({"rules": [{"rule_id": "X"}]}))
            self.assertEqual(run_cli(SKILL, "reg_triage", EX / "questionnaire-pass.json", "--rules", r).returncode, 2)

    def test_no_compliance_language(self):
        proc = run_cli(SKILL, "reg_triage", EX / "questionnaire-pass.json", "--json")
        low = proc.stdout.lower()
        self.assertNotIn("compliant", low)
        self.assertNotIn("approved", low)


class NullOptionalAnswerRegression(unittest.TestCase):
    def test_null_promotions_answer_refers(self):
        mod = load_script("finance-fca-scope-check", "reg_triage")
        import inspect
        ex = skill_path("finance-fca-scope-check", "assets", "examples")
        q_path = next(p for p in sorted(ex.glob("*.json")) if "pass" in p.name or "platform" in p.name)
        q = json.loads(q_path.read_text())
        q.setdefault("activities", {})["communicates_promotions"] = None
        import tempfile, subprocess, sys
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(q, fh)
        p = subprocess.run([sys.executable, "-I", str(skill_path("finance-fca-scope-check", "scripts", "reg_triage.py")), fh.name],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("communicates_promotions", p.stdout)


if __name__ == "__main__":
    unittest.main()
