import json
import subprocess
import sys
import unittest

from tests.helpers import ROOT, load_script, rules, run_cli, run_json, skill_path

SKILL = "select-frameworks"
mod = load_script(SKILL, "select_frameworks")
EX = skill_path(SKILL, "assets", "examples")
CAT = json.loads(skill_path(SKILL, "assets", "data", "catalog.json").read_text())
RULES = json.loads(skill_path(SKILL, "assets", "data", "routing-rules.json").read_text())


def sel(name):
    code, out = run_json(SKILL, "select_frameworks", EX / f"profile-{name}.json")
    assert code == 0, out
    return out


class SelectFrameworksTests(unittest.TestCase):
    def test_catalog_in_sync_with_library(self):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_catalog.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_rules_reference_existing_skills(self):
        for pack, r in RULES["packs"].items():
            for s in r.get("skills_always", []) + list(r.get("skills_if", {})):
                # skills may be planned but not yet built; every rule skill must at least be in the pack catalogue
                self.assertIn(s, CAT["packs"][pack]["skills"], f"{pack}:{s}")

    def test_aster(self):
        r = sel("aster")
        self.assertEqual(r["oversight_level"], "high")
        self.assertIn("space-low-gravity-mobility", r["selected_packs"]["space-engineering"]["skills"])
        for ex in ("finance-credit", "product", "ai-governance"):
            self.assertIn(ex, r["excluded_packs"])
        self.assertIn("safety-risk-reviewer", r["agents"])
        self.assertTrue(any("safety authority" in s for s in r["human_signoffs"]))

    def test_mortgage(self):
        r = sel("mortgage")
        fin = r["selected_packs"]["finance-credit"]["skills"]
        self.assertIn("finance-fca-scope-check", fin)
        self.assertIn("credit-criteria-modelling", fin)
        self.assertNotIn("finance-npv-irr", fin)
        self.assertIn("ai-human-oversight", r["selected_packs"]["ai-governance"]["skills"])
        self.assertEqual(r["oversight_level"], "high")
        self.assertIn("credit-regulatory-reviewer", r["agents"])
        self.assertTrue(any("credit decisions" in s for s in r["human_signoffs"]))

    def test_aiops(self):
        r = sel("aiops")
        self.assertIn("systems-engineering", r["excluded_packs"])
        self.assertEqual(r["selected_packs"]["finance-credit"]["skills"], ["finance-unit-economics"])
        self.assertIn("ai-human-oversight", r["selected_packs"]["ai-governance"]["skills"])  # agentic tools
        self.assertEqual(r["oversight_level"], "medium")
        # readiness blocks on a missing SLO, so the SLO skill must be proposed whenever readiness is
        rs = r["selected_packs"]["reliability-security"]["skills"]
        self.assertIn("sre-production-readiness", rs)
        self.assertIn("sre-service-level-objectives", rs)

    def test_every_selected_skill_and_agent_exists(self):
        for name in ("aster", "mortgage", "aiops"):
            r = sel(name)
            for s in r["skills"]:
                self.assertTrue(skill_path(s, "SKILL.md").is_file(), s)
            for a in r["agents"]:
                self.assertTrue((ROOT / ".claude" / "agents" / f"{a}.md").is_file(), a)
            self.assertIn("independent-review", r["skills"])
            self.assertIn("--apply", r["install_command"])

    def test_explicit_flag_without_keywords(self):
        p = {"name": "x", "description": "internal tool", "risk_class": "low", "flags": {"ai": True}}
        r = mod.select(p, CAT, RULES)
        self.assertIn("ai-governance", r["selected_packs"])
        self.assertIn("ai-governance", [k for k in r["selected_packs"]])

    def test_keyword_whole_word(self):
        p = {"name": "x", "description": "maintain a garden", "risk_class": "low", "flags": {}}
        r = mod.select(p, CAT, RULES)
        self.assertNotIn("ai-governance", r["selected_packs"])  # 'maintain' must not match 'ai'

    def test_fail_profile(self):
        code, out = run_json(SKILL, "select_frameworks", EX / "profile-fail.json")
        self.assertEqual(code, 1)
        self.assertTrue({"no-description", "risk-class"} <= rules(out["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "select_frameworks", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
