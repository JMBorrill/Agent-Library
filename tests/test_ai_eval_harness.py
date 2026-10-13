import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "ai-eval-harness"
ev = load_script(SKILL, "run_eval")
EX = skill_path(SKILL, "assets", "examples")
SCHEMAS = skill_path(SKILL, "assets", "schemas")
EVALSET = EX / "mortgage-criteria-evalset.jsonl"
CONFIG = EX / "eval-config.json"
TOL = 5e-4  # tolerance for hand-computed interval bounds (4 d.p.)


def item(**kw):
    base = {"id": "x1", "input": "q"}
    base.update(kw)
    return base


class WilsonTests(unittest.TestCase):
    def test_known_answers(self):
        for (k, n), (lo, hi) in {(8, 10): (0.4902, 0.9433), (0, 10): (0.0, 0.2775),
                                 (10, 10): (0.7225, 1.0), (14, 14): (0.7847, 1.0),
                                 (1, 2): (0.0945, 0.9055)}.items():
            with self.subTest(k=k, n=n):
                got = ev.wilson(k, n)
                self.assertAlmostEqual(got[0], lo, delta=TOL)
                self.assertAlmostEqual(got[1], hi, delta=TOL)

    def test_invalid_denominators(self):
        with self.assertRaises(ValueError):
            ev.wilson(0, 0)
        with self.assertRaises(ValueError):
            ev.wilson(3, 2)
        with self.assertRaises(ValueError):
            ev.wilson(-1, 2)


class DetectorTests(unittest.TestCase):
    def test_luhn(self):
        self.assertTrue(ev.luhn_ok("4111111111111111"))
        self.assertFalse(ev.luhn_ok("4111111111111112"))

    def test_pii_types(self):
        types = lambda t: {h["type"] for h in ev.find_pii(t)}
        self.assertEqual(types("mail a.b@example.com"), {"email"})
        self.assertEqual(types("NI QQ 12 34 56 C"), {"uk_ni_number"})
        self.assertEqual(types("NI QQ123456C"), {"uk_ni_number"})
        self.assertEqual(types("call 07700 900123"), {"uk_phone"})
        self.assertEqual(types("call +44 7700 900123"), {"uk_phone"})
        self.assertEqual(types("card 4111 1111 1111 1111"), {"card_number"})
        self.assertEqual(types("card 4111 1111 1111 1112"), set())

    def test_no_false_positive_on_mortgage_numbers(self):
        text = "Up to 4.5x income, GBP 75,000 joint, 125% at 5.5%, term 35 years, LTV 90%, ref 2026-09-28."
        self.assertEqual(ev.find_pii(text), [])

    def test_refusal(self):
        self.assertTrue(ev.is_refusal("I can't share that."))
        self.assertTrue(ev.is_refusal("I'm unable to help with this"))
        self.assertFalse(ev.is_refusal("Yes, first-time landlords are accepted."))


class ScoringTests(unittest.TestCase):
    def test_grounding_subset_and_required(self):
        it = item(context=[{"doc_id": "A"}, {"doc_id": "B"}], expected_citations=["A"])
        self.assertTrue(ev.score_item(it, {"output": "x [doc:A]"})["checks"]["grounding"])
        self.assertTrue(ev.score_item(it, {"output": "x [doc:A][doc:B]"})["checks"]["grounding"])
        self.assertFalse(ev.score_item(it, {"output": "x [doc:B]"})["checks"]["grounding"])
        self.assertFalse(ev.score_item(it, {"output": "x [doc:A][doc:Z]"})["checks"]["grounding"])
        self.assertTrue(ev.score_item(it, {"output": "x", "citations": ["A"]})["checks"]["grounding"])

    def test_allowed_pii_not_counted(self):
        it = item(allowed_pii=["help@lender.example"])
        self.assertTrue(ev.score_item(it, {"output": "write to help@lender.example"})["checks"]["pii_leakage"])
        self.assertFalse(ev.score_item(it, {"output": "write to jo@example.com"})["checks"]["pii_leakage"])

    def test_missing_response_fails_item(self):
        r = ev.score_item(item(), None)
        self.assertFalse(r["passed"])
        self.assertIn("response", r["checks"])

    def test_gate_not_evaluable_fails(self):
        res = ev.run([item()], {"x1": {"id": "x1", "output": "ok"}}, {"thresholds": {"grounding": {"min": 0.9}}})
        self.assertFalse(res["passed"])
        self.assertIn("not evaluable", res["gates"][0]["reason"])

    def test_gate_on_interval_is_stricter(self):
        items = [item(id=f"i{i}", expected_contains=["ok"]) for i in range(10)]
        resp = {f"i{i}": {"output": "ok"} for i in range(10)}
        cfg = {"thresholds": {"contains": {"min": 0.9}}}
        self.assertTrue(ev.run(items, resp, cfg)["passed"])
        cfg["gate_on_interval"] = True  # lower bound 0.7225 < 0.9
        self.assertFalse(ev.run(items, resp, cfg)["passed"])

    def test_min_n(self):
        res = ev.run([item(expected_contains=["ok"])], {"x1": {"output": "ok"}},
                     {"thresholds": {"contains": {"min": 0.5, "min_n": 30}}})
        self.assertFalse(res["passed"])

    def test_config_validation(self):
        for bad in [{"thresholds": {"accuracy": {"min": 0.9}}}, {"thresholds": {"grounding": {"min": 95}}},
                    {"thresholds": {"grounding": {"at_least": 0.9}}}, []]:
            with self.subTest(cfg=bad), self.assertRaises(ev.InputError):
                ev.validate_config(bad)

    def test_item_validation(self):
        for bad in [[], [item(), item()], [{"input": "q"}], [item(expected_regex="(")],
                    [item(expected_refusal="yes")], [item(tags="a")]]:
            with self.subTest(items=bad), self.assertRaises(ev.InputError):
                ev.validate_items(bad)


class CliTests(unittest.TestCase):
    def test_good_system_passes(self):
        code, out = run_json(SKILL, "run_eval", EVALSET, "--responses", EX / "responses-good-pass.jsonl",
                             "--config", CONFIG)
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        self.assertEqual(out["metrics"]["pass_rate"]["k"], 14)
        self.assertEqual(out["metrics"]["pii_leakage_rate"]["k"], 0)
        self.assertEqual(len(out["reproducibility"]["dataset_sha256"]), 64)
        assert_schema(self, out, SCHEMAS / "eval-report.schema.json")

    def test_bad_system_fails_specific_gates(self):
        code, out = run_json(SKILL, "run_eval", EVALSET, "--responses", EX / "responses-bad-fail.jsonl",
                             "--config", CONFIG)
        self.assertEqual(code, 1)
        failed = {g["metric"] for g in out["gates"] if g["status"] == "fail"}
        self.assertTrue({"grounding", "pii_leakage_rate", "not_contains", "refusal", "pass_rate"} <= failed)
        by_id = {r["id"]: r for r in out["items"]}
        self.assertFalse(by_id["q07"]["checks"]["not_contains"])      # hallucinated lender
        self.assertIn("uk_ni_number", by_id["q08"]["pii"])             # leaked NI number
        self.assertEqual(set(by_id["q13"]["pii"]), {"email", "uk_phone", "card_number"})
        self.assertFalse(by_id["q03"]["checks"]["grounding"])         # missing citation
        self.assertEqual(out["metrics"]["grounding"]["k"], 9)
        self.assertEqual(out["metrics"]["pii_leakage_rate"]["k"], 2)
        self.assertIn("gate-failed", rules(out["findings"], "error"))
        assert_schema(self, out, SCHEMAS / "eval-report.schema.json")

    def test_report_is_deterministic(self):
        a = run_cli(SKILL, "run_eval", EVALSET, "--responses", EX / "responses-bad-fail.jsonl", "--config", CONFIG, "--json")
        b = run_cli(SKILL, "run_eval", EVALSET, "--responses", EX / "responses-bad-fail.jsonl", "--config", CONFIG, "--json")
        self.assertEqual(a.stdout, b.stdout)

    def test_fixtures_and_config_match_schemas(self):
        for line in EVALSET.read_text(encoding="utf-8").splitlines():
            assert_schema(self, json.loads(line), SCHEMAS / "evalset-item.schema.json")
        assert_schema(self, json.loads(CONFIG.read_text(encoding="utf-8")), SCHEMAS / "eval-config.schema.json")

    def test_command_adapter(self):
        code = ("import sys,json; d=json.load(sys.stdin); "
                "print(json.dumps({'output': 'answer ' + d['id'] + ' [doc:A]'}))")
        with tempfile.TemporaryDirectory() as tmp:
            es = Path(tmp) / "e.jsonl"
            es.write_text(json.dumps(item(context=[{"doc_id": "A"}], expected_contains=["answer x1"],
                                          expected_citations=["A"])) + "\n", encoding="utf-8")
            cmd = f"{shlex.quote(sys.executable)} -I -c {shlex.quote(code)}"
            code_, out = run_json(SKILL, "run_eval", es, "--adapter", "command", "--command", cmd)
            self.assertEqual(code_, 0)
            self.assertTrue(out["items"][0]["passed"])
            self.assertEqual(out["reproducibility"]["adapter"]["name"], "command")

    def test_usage_errors_exit2(self):
        self.assertEqual(run_cli(SKILL, "run_eval", EVALSET).returncode, 2)  # no --responses
        self.assertEqual(run_cli(SKILL, "run_eval", "missing.jsonl", "--responses", "x").returncode, 2)
        self.assertEqual(run_cli(SKILL, "run_eval", EVALSET, "--adapter", "command").returncode, 2)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.jsonl"
            bad.write_text('{"id": "a", "input": "q"}\nnot json\n', encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "run_eval", bad, "--responses", bad).returncode, 2)


if __name__ == "__main__":
    unittest.main()
