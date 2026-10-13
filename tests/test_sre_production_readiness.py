import copy
import json
import tempfile
import unittest
from pathlib import Path

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

    # ---- SR-15 project-defined blocking items and security evidence -----------------------
    def security_partial(self):
        d = copy.deepcopy(PASS)
        for it in d["items"]:
            if it["area"] == "security":
                it.update(status="partial", owner="security owner", due="2026-11-30")
        return d

    def test_project_blocking_items_field_forces_no_go(self):
        d = self.security_partial()
        self.assertEqual(mod.evaluate(d)["summary"]["recommendation"], "GO_WITH_CONDITIONS")  # library default
        d["blocking_items"] = ["security_isolation_tested", "tool_enforcement_tested", "dpia_complete"]
        d["items"].append({"id": "RR-90", "area": "security", "key": "dpia_complete",
                           "title": "DPIA completed", "status": "done", "evidence_ref": "DPIA-v1"})
        res = mod.evaluate(d)
        s = res["summary"]
        self.assertEqual(s["recommendation"], "NO_GO")
        self.assertEqual(s["blocking_failures"], ["security_isolation_tested", "tool_enforcement_tested"])
        self.assertEqual(s["project_blocking_items"], ["security_isolation_tested", "tool_enforcement_tested", "dpia_complete"])
        self.assertIn("blocking-item-missing", rules(res["findings"], "error"))

    def test_project_blocking_item_matches_id_and_needs_done_with_evidence(self):
        d = copy.deepcopy(PASS)
        sec = next(it for it in d["items"] if it["area"] == "security")
        d["blocking_items"] = [sec["id"]]
        self.assertEqual(mod.evaluate(d)["summary"]["recommendation"], "GO")
        sec["evidence_ref"] = ""
        res = mod.evaluate(d)
        self.assertEqual(res["summary"]["recommendation"], "NO_GO")
        self.assertIn("blocking-no-evidence", rules(res["findings"], "error"))
        sec.update(status="na", justification="Not applicable for this launch, reviewed")
        self.assertEqual(mod.evaluate(d)["summary"]["recommendation"], "NO_GO")  # N/A never satisfies a project blocker

    def test_cli_blocking_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            path.write_text(json.dumps(self.security_partial()), encoding="utf-8")
            self.assertEqual(run_cli(SKILL, "readiness_check", path).returncode, 0)
            sec_ids = [it["id"] for it in PASS["items"] if it["area"] == "security"]
            code, out = run_json(SKILL, "readiness_check", path, "--blocking", ",".join(sec_ids) + ",dpia_complete")
            self.assertEqual(code, 1)
            self.assertEqual(out["summary"]["recommendation"], "NO_GO")
            self.assertIn("dpia_complete", out["summary"]["blocking_failures"])
            assert_schema(self, out, SCHEMAS / "readiness.output.schema.json")
            self.assertEqual(run_cli(SKILL, "readiness_check", path, "--blocking", " , ").returncode, 2)

    def test_no_security_evidence_warning(self):
        res = mod.evaluate(self.security_partial())
        self.assertIn("no-security-evidence", rules(res["findings"], "warning"))
        self.assertNotIn("no-security-evidence", rules(mod.evaluate(PASS)["findings"]))
        d = copy.deepcopy(PASS)
        d["items"] = [it for it in d["items"] if it["area"] != "security"]
        self.assertIn("no-security-evidence", rules(mod.evaluate(d)["findings"], "warning"))

    def test_blocking_items_field_validated(self):
        d = copy.deepcopy(PASS)
        d["blocking_items"] = "dpia_complete"
        res = mod.evaluate(d)
        self.assertEqual(res["summary"]["recommendation"], "NO_GO")
        self.assertIn("bad-blocking-items", rules(res["findings"], "error"))

    def test_unreadable_exit_2(self):
        self.assertEqual(run_cli(SKILL, "readiness_check", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
