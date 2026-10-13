import copy
import json
import unittest

from tests.helpers import ROOT, assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "security-threat-model"
mod = load_script(SKILL, "threat_model_check")
EX = skill_path(SKILL, "assets", "examples")
INDEX_PATH = skill_path(SKILL, "assets", "data", "asvs-5.0.0-index.json")
INDEX = mod.load_index(INDEX_PATH)
OUT_SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
IN_SCHEMA = skill_path(SKILL, "assets", "schemas", "threat-model.schema.json")
PASS = json.loads((EX / "threat-model-pass.json").read_text())


class ThreatModelTests(unittest.TestCase):
    def test_bundled_index_matches_extract_and_keeps_licence(self):
        bundled = json.loads(INDEX_PATH.read_text())
        extract = json.loads((ROOT / "sources" / "extracts" / "owasp-asvs-5.0.0-index.json").read_text())
        self.assertEqual(bundled["requirements"], extract["requirements"])
        self.assertIn("CC BY-SA 4.0", bundled["licence_notice"])
        self.assertIn("OWASP", bundled["attribution"])
        self.assertEqual(len(INDEX), 345)

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "threat_model_check", EX / "threat-model-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["warnings"], 0)
        self.assertTrue(all(v["missing"] == "" for v in out["summary"]["coverage"].values()))
        assert_schema(self, out, OUT_SCHEMA)
        assert_schema(self, PASS, IN_SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "threat_model_check", EX / "threat-model-fail.json")
        self.assertEqual(code, 1)
        expected = {"no-tenant-isolation-threat", "missing-stride-coverage", "unmitigated-high",
                    "asvs-unversioned", "asvs-version-mismatch", "asvs-unknown-id", "unknown-boundary",
                    "stride-category", "acceptance-incomplete", "mitigated-without-implementation",
                    "na-without-justification"}
        self.assertTrue(expected <= rules(out["findings"], "error"), expected - rules(out["findings"], "error"))
        assert_schema(self, out, OUT_SCHEMA)

    def test_risk_rating_table(self):
        self.assertEqual(mod.risk_rating("high", "medium"), "high")
        self.assertEqual(mod.risk_rating("medium", "medium"), "medium")
        self.assertEqual(mod.risk_rating("low", "high"), "medium")
        self.assertEqual(mod.risk_rating("low", "medium"), "low")
        self.assertIsNone(mod.risk_rating("extreme", "low"))

    def test_asvs_id_forms(self):
        self.assertEqual(mod.check_asvs_id("v5.0.0-1.2.5", INDEX), ("v5.0.0-1.2.5", None))
        self.assertEqual(mod.check_asvs_id("ASVS-v5.0.0-8.2.2", INDEX)[0], "v5.0.0-8.2.2")
        self.assertEqual(mod.check_asvs_id("V5.0.0-1.2.5", INDEX)[1], "asvs-bad-format")  # 'v' must be lowercase
        self.assertEqual(mod.check_asvs_id("1.2.5", INDEX)[1], "asvs-unversioned")
        self.assertEqual(mod.check_asvs_id("v5.0.0-17.3.3", INDEX)[1], "asvs-unknown-id")

    def test_categories_option_raises_bar(self):
        res = mod.check(PASS, INDEX, "STRIDE")
        self.assertIn("missing-stride-coverage", rules(res["findings"], "error"))

    def test_cleartext_crossing(self):
        m = copy.deepcopy(PASS)
        m["data_flows"][0]["protocol"] = "HTTP"
        self.assertIn("cleartext-crossing", rules(mod.check(m, INDEX)["findings"], "error"))

    def test_high_risk_planned_only_and_accepted(self):
        m = copy.deepcopy(PASS)
        m["threats"][0]["mitigations"][0]["status"] = "planned"
        self.assertIn("high-mitigation-planned-only", rules(mod.check(m, INDEX)["findings"], "warning"))
        m["threats"][0].update(status="accepted", accepted_by="ciso (synthetic)", acceptance_rationale="pilot only")
        self.assertIn("high-risk-accepted", rules(mod.check(m, INDEX)["findings"], "info"))

    def test_empty_model(self):
        res = mod.check({}, INDEX)
        self.assertIn("missing-field", rules(res["findings"], "error"))

    def test_unreadable_and_bad_args_exit_2(self):
        self.assertEqual(run_cli(SKILL, "threat_model_check", "missing.json").returncode, 2)
        self.assertEqual(run_cli(SKILL, "threat_model_check", EX / "threat-model-pass.json",
                                 "--categories", "XYZ").returncode, 2)


if __name__ == "__main__":
    unittest.main()
