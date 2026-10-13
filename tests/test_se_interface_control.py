import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-interface-control"
mod = load_script(SKILL, "icd_check")
EX = skill_path(SKILL, "assets", "examples")
COLS = ["interface_id", "from_component", "to_component", "type", "parameter", "value", "units_from",
        "units_to", "tolerance", "range_or_protocol", "owner_from", "owner_to", "version", "status",
        "failure_behavior", "requirement_ids", "verification_id"]


def row(**kw):
    b = {c: "" for c in COLS}
    b.update(interface_id="P-IF-001", from_component="A", to_component="B", type="electrical",
             parameter="voltage", value="5", units_from="V", units_to="V", owner_from="a", owner_to="b",
             version="1.0", status="baselined", failure_behavior="safe", requirement_ids="P-SYS-001",
             verification_id="P-VER-001")
    b.update(kw)
    return b


class IcdTests(unittest.TestCase):
    def test_unit_relation(self):
        self.assertEqual(mod.unit_relation("V", "v"), "same")
        self.assertEqual(mod.unit_relation("V", "mV"), "convertible")
        self.assertEqual(mod.unit_relation("A", "V"), "incompatible")
        self.assertEqual(mod.unit_relation("furlong", "V"), "unknown")
        self.assertEqual(mod.unit_relation("N", "lbf"), "convertible")

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "icd_check", EX / "icd-pass.csv", "--components", EX / "components.csv")
        self.assertEqual(code, 0)
        self.assertEqual(out["n2"]["cells"]["PWR"]["CTRL"], ["DEMO-IF-001"])

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "icd_check", EX / "icd-fail.csv", "--components", EX / "components.csv")
        self.assertEqual(code, 1)
        self.assertTrue({"unit-conversion", "unit-incompatible", "duplicate-parameter", "missing-owner-to",
                         "no-failure-behaviour", "no-verification", "self-interface", "status",
                         "unknown-component"} <= rules(out["findings"], "error"))

    def test_conversion_is_warning_in_draft(self):
        res = mod.check(COLS, [row(units_to="mV", status="draft")])
        self.assertIn("unit-conversion", rules(res["findings"], "warning"))
        self.assertEqual(res["summary"]["errors"], 0)

    def test_clean_row(self):
        res = mod.check(COLS, [row()])
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertEqual(res["summary"]["warnings"], 0)

    def test_unknown_requirement_link(self):  # raised by ASTER demo builder
        res = mod.check(COLS, [row(requirement_ids="P-SYS-001;P-SYS-404")], None, {"P-SYS-001"})
        self.assertIn("unknown-requirement", rules(res["findings"], "error"))

    def test_n2_markdown_diagonal(self):
        md = mod.n2_markdown(mod.n2([row()]))
        self.assertIn("**A**", md)
        self.assertIn("P-IF-001", md)

    def test_missing_columns_and_unreadable(self):
        self.assertIn("missing-columns", rules(mod.check(["interface_id"], [])["findings"]))
        self.assertEqual(run_cli(SKILL, "icd_check", "nope.csv").returncode, 2)


if __name__ == "__main__":
    unittest.main()
