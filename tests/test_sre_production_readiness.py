import copy
import json
import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "sre-production-readiness"
mod = load_script(SKILL, "readiness_check")
EX = skill_path(SKILL, "assets", "examples")
SCHEMAS = skill_path(SKILL, "assets", "schemas")
PASS = json.loads((EX / "readiness-pass.json").read_text())


def with_item(doc, key, **changes):
    d = copy.deepcopy(doc)
    for it in d["items"]:
        if it.get("key") == key:
            it.update(changes)
    return d


class ReadinessTests(unittest.TestCase):
    def test_pass_fixture_go(self):
        code, out = run_json(SKILL, "readiness_check", EX / "readiness-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["recommendation"], "GO")
        self.assertTrue(out["summary"]["requires_human_signoff"])
        assert_schema(self, out, SCHEMAS / "readiness.output.schema.json")
        assert_schema(self, PASS, SCHEMAS / "readiness-checklist.schema.json")

    def test_conditions_fixture(self):
        code, out = run_json(SKILL, "readiness_check", EX / "readiness-conditions-pass.json")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["recommendation"], "GO_WITH_CONDITIONS")
        self.assertEqual(rules(out["findings"], "warning"), {"open-item", "na-without-justification"})

    def test_fail_fixture_no_go(self):
        code, out = run_json(SKILL, "readiness_check", EX / "readiness-fail.json")
        self.assertEqual(code, 1)
        s = out["summary"]
        self.assertEqual(s["recommendation"], "NO_GO")
        self.assertEqual(s["blocking_failures"], ["oncall_staffed", "restore_tested", "rollback_tested", "slo_defined"])
        self.assertEqual(rules(out["findings"], "error"),
                         {"blocking-item-not-done", "blocking-no-evidence", "blocking-item-missing"})
        assert_schema(self, out, SCHEMAS / "readiness.output.schema.json")

    def test_each_blocking_item_alone_forces_no_go(self):
        for key in mod.BLOCKING:
            res = mod.evaluate(with_item(PASS, key, status="partial"))
            self.assertEqual(res["summary"]["recommendation"], "NO_GO", key)

    def test_restore_na_only_with_justification(self):
        ok = mod.evaluate(with_item(PASS, "restore_tested", status="na", evidence_ref="",
                                    justification="Stateless service: no persistent data"))
        self.assertEqual(ok["summary"]["recommendation"], "GO")
        bad = mod.evaluate(with_item(PASS, "rollback_tested", status="na", justification="Not needed for this launch"))
        self.assertEqual(bad["summary"]["recommendation"], "NO_GO")

    def test_invalid_checklist_is_no_go(self):
        d = copy.deepcopy(PASS)
        d["items"][1]["status"] = "maybe"
        d["items"][2]["area"] = "vibes"
        res = mod.evaluate(d)
        self.assertEqual(res["summary"]["recommendation"], "NO_GO")
        self.assertTrue({"status-value", "unknown-area"} <= rules(res["findings"], "error"))
        self.assertEqual(mod.evaluate({})["summary"]["recommendation"], "NO_GO")

    def test_never_outputs_approval_language(self):
        proc = run_cli(SKILL, "readiness_check", EX / "readiness-pass.json")
        self.assertNotRegex(proc.stdout.lower(), r"\bapproved\b|\bcompliant\b")
        self.assertIn("requires human sign-off", proc.stdout)

    def test_unreadable_exit_2(self):
        self.assertEqual(run_cli(SKILL, "readiness_check", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
