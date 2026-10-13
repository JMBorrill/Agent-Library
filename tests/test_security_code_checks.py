import json
import unittest

from tests.helpers import ROOT, assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "security-code-checks"
mod = load_script(SKILL, "static_checks")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "static-checks.output.schema.json")
CFG = EX / "aiops-config.json"
ALL_RULES = {v[0] for v in mod.RULES.values()}


def ids(text, path="x.py", tables=None):
    return {f["rule_id"] for f in mod.scan_text(path, text, tables) if f["severity"] == "error"}


class StaticChecksTests(unittest.TestCase):
    def test_fail_fixture_triggers_every_rule(self):
        code, out = run_json(SKILL, "static_checks", EX / "vulnerable-app-fail", "--config", CFG)
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"), ALL_RULES)
        assert_schema(self, out, SCHEMA)

    def test_pass_fixture_clean(self):
        code, out = run_json(SKILL, "static_checks", EX / "fixed-app-pass", "--config", CFG)
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["errors"], 0)
        assert_schema(self, out, SCHEMA)

    def test_asvs_refs_exist_in_index(self):
        index = json.loads((ROOT / "sources" / "extracts" / "owasp-asvs-5.0.0-index.json").read_text())
        chapters = {c["id"]: c for c in index["chapters"]}
        sections = {s["id"]: s["title"] for c in index["chapters"] for s in c["sections"]}
        for code, (_, ref, title) in mod.RULES.items():
            if "." in ref:
                self.assertEqual(sections.get(ref), title, code)
            else:
                self.assertEqual(chapters[ref]["title"], title, code)

    def test_secrets_masked(self):
        _, out = run_json(SKILL, "static_checks", EX / "vulnerable-app-fail", "--config", CFG)
        text = json.dumps(out)
        self.assertNotIn("AKIAFAKEFAKEFAKEFAKE", text)
        self.assertNotIn("sk-FAKE-0000-do-not-use", text)

    def test_individual_patterns(self):
        self.assertEqual(ids('q = "SELECT * FROM t WHERE id = " + uid'), {"SC002"})
        self.assertEqual(ids("const q = `DELETE FROM t WHERE id=${id}`;", "a.ts"), {"SC002"})
        self.assertEqual(ids('cur.execute("SELECT * FROM t WHERE id = %s", (uid,))'), set())
        self.assertEqual(ids("data = yaml.load(s, Loader=yaml.SafeLoader)"), set())
        self.assertEqual(ids("data = yaml.load(s, Loader=yaml.FullLoader)"), {"SC006"})
        self.assertEqual(ids("digest = hashlib.md5(file_bytes).hexdigest()"), set())  # not password-related
        self.assertEqual(ids("opts = {rejectUnauthorized: false}", "a.js"), {"SC007"})
        self.assertEqual(ids('token = os.environ["API_TOKEN"]'), set())

    def test_cors_needs_credentials(self):
        self.assertEqual(ids('CORS(app, origins="*")'), set())
        self.assertEqual(ids('CORS(app,\n     origins="*",\n     supports_credentials=True)'), {"SC008"})

    def test_tenant_filter(self):
        t = {"appointments"}
        self.assertEqual(ids('Q = "SELECT * FROM appointments WHERE id = %s"', tables=t), {"SC003"})
        self.assertEqual(ids('Q = "SELECT * FROM appointments WHERE tenant_id = %s"', tables=t), set())
        self.assertEqual(ids('Q = "INSERT INTO appointments (id, starts_at) VALUES (%s, %s)"', tables=t), {"SC003"})
        self.assertEqual(ids("SELECT a.id FROM appointments a JOIN users u ON u.id = a.user_id;", "r.sql", t), {"SC003"})
        self.assertEqual(ids('Q = "SELECT * FROM other WHERE id = %s"', tables=t), set())

    def test_tenant_check_inactive_without_config(self):
        code, out = run_json(SKILL, "static_checks", EX / "vulnerable-app-fail")
        self.assertIn("tenant-check-inactive", rules(out["findings"], "info"))
        self.assertNotIn("missing-tenant-filter", rules(out["findings"]))

    def test_suppression_requires_reason(self):
        line = 'resp = requests.get(url, verify=False)  # static-checks: ignore[SC007] test stub against local mock'
        res = mod.scan_text("x.py", line)
        self.assertEqual([f["rule"] for f in res], ["suppressed"])
        res = mod.scan_text("x.py", 'requests.get(url, verify=False)  # static-checks: ignore[SC007]')
        self.assertEqual(res[0]["severity"], "error")

    def test_empty_file_and_missing_path(self):
        self.assertEqual(mod.scan_text("x.py", ""), [])
        self.assertEqual(run_cli(SKILL, "static_checks", "no/such/dir").returncode, 2)


if __name__ == "__main__":
    unittest.main()
