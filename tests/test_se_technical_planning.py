import json
import unittest

from tests.helpers import load_script, rules, run_cli, run_json, skill_path

SKILL = "se-technical-planning"
mod = load_script(SKILL, "tailor_process")
EX = skill_path(SKILL, "assets", "examples")
DATA = json.loads(skill_path(SKILL, "assets", "data", "tailoring.json").read_text())


def prof(**kw):
    p = {"risk_class": "low", "safety_critical": False, "regulated": False, "novel_technology": False,
         "hardware": True, "software": True, "team_size": 2, "decision_owner": "o"}
    p.update(kw)
    return p


class TailorTests(unittest.TestCase):
    def test_all_17_processes(self):
        res = mod.tailor(prof(), DATA)
        self.assertEqual([p["id"] for p in res["processes"]], [f"SE-{i:02d}" for i in range(1, 18)])
        self.assertTrue(all(p["rigour"] == "light" for p in res["processes"]))

    def test_safety_raises_and_requires_authority(self):
        res = mod.tailor(prof(risk_class="moderate", safety_critical=True), DATA)
        self.assertIn("no-safety-authority", rules(res["findings"], "error"))
        res = mod.tailor(prof(risk_class="moderate", safety_critical=True, safety_authority="s"), DATA)
        lv = {p["id"]: p["rigour"] for p in res["processes"]}
        self.assertEqual(lv["SE-13"], "rigorous")
        self.assertEqual(lv["SE-01"], "standard")
        self.assertIn("TRR", res["reviews"])

    def test_low_but_safety_warns(self):
        res = mod.tailor(prof(safety_critical=True, safety_authority="s"), DATA)
        self.assertIn("risk-understated", rules(res["findings"], "warning"))

    def test_software_only_lightens_integration(self):
        res = mod.tailor(prof(risk_class="moderate", hardware=False), DATA)
        lv = {p["id"]: p["rigour"] for p in res["processes"]}
        self.assertEqual(lv["SE-06"], "light")

    def test_fixtures(self):
        code, out = run_json(SKILL, "tailor_process", EX / "profile-aster.json")
        self.assertEqual(code, 0)
        self.assertEqual(sum(p["rigour"] == "rigorous" for p in out["processes"]), 7)
        code, out = run_json(SKILL, "tailor_process", EX / "profile-fail.json")
        self.assertEqual(code, 1)
        self.assertTrue({"risk-class", "no-decision-owner", "team-size"} <= rules(out["findings"], "error"))

    def test_skills_in_tailoring_exist(self):
        for p in DATA["processes"]:
            self.assertTrue(skill_path(p["skill"], "SKILL.md").is_file(), p["skill"])

    def test_unreadable(self):
        self.assertEqual(run_cli(SKILL, "tailor_process", "missing.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
