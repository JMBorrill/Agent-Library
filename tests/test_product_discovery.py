import tempfile
import unittest
from pathlib import Path

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "product-discovery"
mod = load_script(SKILL, "evidence_audit")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "evidence-audit.output.schema.json")
EV_COLS = mod.EVIDENCE_COLUMNS
AS_COLS = mod.ASSUMPTION_COLUMNS


def ev(**kw):
    base = dict(id="E-001", claim="7 of 8 walkers plan by hand", type="observation", source_ref="INT-01..08",
                method="interview", date="2026-09-01", participants="8", segment="walkers",
                confidence="high", linked_assumption="")
    base.update(kw)
    return base


def asm(**kw):
    base = dict(id="A-001", assumption="Planning is painful", category="desirability", risk="high",
                evidence_ids="E-001", status="supported")
    base.update(kw)
    return base


class EvidenceAuditTests(unittest.TestCase):
    def run_audit(self, evs, asms=None, target="alpha", as_of=None):
        return mod.audit(EV_COLS, [dict(e) for e in evs], AS_COLS if asms is not None else None,
                         asms, target, as_of)

    def test_pass_example_cli_and_schema(self):
        code, out = run_json(SKILL, "evidence_audit", EX / "evidence-pass.csv",
                             "--assumptions", EX / "assumptions-pass.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        self.assertTrue(out["passed"])
        self.assertEqual(out["summary"]["counted_evidence"], 6)
        self.assertEqual(out["summary"]["by_strength"], {"strong": 4, "moderate": 1, "weak": 1})
        self.assertEqual(out["gate"]["recommendation"], "PROCEED_WITH_CONDITIONS")
        self.assertTrue(out["gate"]["requires_human_decision"])
        assert_schema(self, out, SCHEMA)

    def test_fail_example_detects_seeded_defects(self):
        code, out = run_json(SKILL, "evidence_audit", EX / "evidence-fail.csv",
                             "--assumptions", EX / "assumptions-fail.csv", "--target", "beta")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["observation-no-source", "quote-without-session", "duplicate-id", "bad-date",
                         "observation-no-participants", "observation-no-method", "desk-no-source",
                         "unknown-assumption", "status-without-evidence", "high-risk-untested",
                         "unknown-evidence-id", "invalid-risk"]:
            self.assertIn(expected, errs)
        self.assertIn("non-evidence-cited", rules(out["findings"], "warning"))
        self.assertEqual(out["gate"]["recommendation"], "DO_NOT_PROCEED")
        self.assertEqual(out["summary"]["counted_evidence"], 0)
        assert_schema(self, out, SCHEMA)

    def test_hypothesis_never_counted(self):
        res = self.run_audit([ev(), ev(id="E-002", type="hypothesis", source_ref="", method="none",
                                       date="", participants="", confidence="low")])
        self.assertEqual(res["summary"]["counted_evidence"], 1)
        self.assertEqual(res["summary"]["not_evidence"]["hypothesis"], 1)

    def test_hypothesis_cited_as_evidence_leaves_assumption_uncovered(self):
        res = self.run_audit([ev(id="E-002", type="hypothesis", method="none", participants="")],
                             [asm(evidence_ids="E-002", status="untested")])
        self.assertIn("non-evidence-cited", rules(res["findings"], "warning"))
        self.assertIn("assumption-uncovered", rules(res["findings"], "error"))
        self.assertEqual(res["gate"]["recommendation"], "DO_NOT_PROCEED")

    def test_quote_with_session_reference_is_accepted(self):
        res = self.run_audit([ev(claim='She said "I text every owner on Sunday"', source_ref="INT-03 14:02",
                                 participants="1")])
        self.assertNotIn("quote-without-session", rules(res["findings"]))
        res = self.run_audit([ev(claim='She said "I text every owner on Sunday"', source_ref="team notes",
                                 participants="1")])
        self.assertIn("quote-without-session", rules(res["findings"], "error"))

    def test_gate_rules_alpha_vs_beta_with_planned_experiment(self):
        evs = [ev()]
        asms = [asm(), asm(id="A-002", evidence_ids="", status="experiment_planned")]
        alpha = self.run_audit(evs, asms, "alpha")
        self.assertEqual(alpha["gate"]["recommendation"], "PROCEED_WITH_CONDITIONS")
        self.assertEqual(alpha["summary"]["errors"], 0)
        beta = self.run_audit(evs, asms, "beta")
        self.assertEqual(beta["gate"]["recommendation"], "DO_NOT_PROCEED")
        self.assertIn("high-risk-untested", rules(beta["findings"], "error"))

    def test_all_supported_gives_proceed(self):
        res = self.run_audit([ev()], [asm(), asm(id="A-002", risk="low", evidence_ids="", status="untested")])
        self.assertEqual(res["gate"]["recommendation"], "PROCEED")
        self.assertEqual(res["gate"]["gate_equivalent"], "GO")

    def test_refuted_high_risk_blocks(self):
        res = self.run_audit([ev()], [asm(status="refuted")])
        self.assertIn("high-risk-refuted", rules(res["findings"], "error"))
        self.assertEqual(res["gate"]["recommendation"], "DO_NOT_PROCEED")

    def test_no_register_is_conditional_not_proceed(self):
        res = self.run_audit([ev()])
        self.assertEqual(res["gate"]["recommendation"], "PROCEED_WITH_CONDITIONS")

    def test_future_dated_evidence(self):
        import datetime as dt
        res = self.run_audit([ev(date="2027-01-01")], as_of=dt.date(2026, 10, 13))
        self.assertIn("future-date", rules(res["findings"], "error"))

    def test_strength_thresholds(self):
        res = self.run_audit([ev(id="E-1", participants="4"), ev(id="E-2", participants="5"),
                              ev(id="E-3", participants="1", method="analytics"),
                              ev(id="E-4", type="desk_research", method="desk", participants="")])
        self.assertEqual(res["summary"]["by_strength"], {"strong": 2, "moderate": 1, "weak": 1})

    def test_negative_or_non_numeric_participants(self):
        for bad in ("-3", "many", ""):
            res = self.run_audit([ev(participants=bad)])
            self.assertIn("observation-no-participants", rules(res["findings"], "error"))

    def test_empty_log_and_missing_columns(self):
        res = mod.audit(EV_COLS, [], None, None)
        self.assertIn("empty-log", rules(res["findings"], "error"))
        res = mod.audit(["id", "claim"], [{"id": "x", "claim": "y"}], None, None)
        self.assertIn("missing-columns", rules(res["findings"], "error"))
        self.assertEqual(res["gate"]["recommendation"], "DO_NOT_PROCEED")

    def test_malformed_csv_and_missing_file_exit_2(self):
        self.assertEqual(run_cli(SKILL, "evidence_audit", "no-such-file.csv").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("id,claim\nE-1,a,b,c\n", encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "evidence_audit", p).returncode, 2)
        self.assertEqual(run_cli(SKILL, "evidence_audit", EX / "evidence-pass.csv",
                                 "--as-of", "13/10/2026").returncode, 2)

    def test_human_output_has_scope_note(self):
        proc = run_cli(SKILL, "evidence_audit", EX / "evidence-pass.csv")
        self.assertIn("Scope:", proc.stdout)
        self.assertNotIn("approved", proc.stdout.lower().replace("not an approval", ""))


if __name__ == "__main__":
    unittest.main()
