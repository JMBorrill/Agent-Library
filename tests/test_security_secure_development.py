import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests.helpers import ROOT, assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "security-secure-development"
ssdf = load_script(SKILL, "ssdf_evidence_check")
deps = load_script(SKILL, "dependency_pin_check")
EX = skill_path(SKILL, "assets", "examples")
DATA = skill_path(SKILL, "assets", "data", "nist-ssdf-practices.json")
PRACTICES = ssdf.load_practices(DATA)
SSDF_SCHEMA = skill_path(SKILL, "assets", "schemas", "ssdf-evidence.output.schema.json")
FINDINGS_SCHEMA = skill_path(SKILL, "assets", "schemas", "findings-report.schema.json")
COLS = ssdf.COLUMNS


def ev(pid, task="", ref="doc-1", d="2026-09-01", owner="o", status="implemented", just=""):
    return dict(zip(COLS, [pid, task, ref, d, owner, status, just]))


class SsdfEvidenceTests(unittest.TestCase):
    def test_bundled_practices_match_extract(self):
        extract = json.loads((ROOT / "sources" / "extracts" / "nist-ssdf-practices.json").read_text())
        self.assertEqual(json.loads(DATA.read_text())["practices"], extract["practices"])
        self.assertEqual(len(PRACTICES), 19)
        self.assertNotIn("PW.3", PRACTICES)
        self.assertEqual(sum(len(p["tasks"]) for p in PRACTICES.values()), 42)

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "ssdf_evidence_check", EX / "evidence-pass.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 0)
        self.assertEqual(out["summary"]["practices_covered"], 19)
        self.assertEqual(out["summary"]["groups"]["PW"]["practices"], 8)
        assert_schema(self, out, SSDF_SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "ssdf_evidence_check", EX / "evidence-fail.csv", "--as-of", "2026-10-13")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"),
                         {"unknown-practice", "version-mismatch", "task-practice-mismatch", "no-evidence",
                          "future-evidence-date", "na-without-justification", "bad-evidence-date", "status-value"})
        self.assertTrue({"stale-evidence", "practice-not-covered", "no-owner"} <= rules(out["findings"], "warning"))
        assert_schema(self, out, SSDF_SCHEMA)

    def test_freshness_boundary(self):
        as_of = date(2026, 10, 13)
        ok = ssdf.check(COLS, [ev("PO.1", d="2025-10-13")], PRACTICES, as_of, 365)  # exactly 365 days
        self.assertNotIn("stale-evidence", rules(ok["findings"]))
        old = ssdf.check(COLS, [ev("PO.1", d="2025-10-12")], PRACTICES, as_of, 365)
        self.assertIn("stale-evidence", rules(old["findings"]))
        no_date = ssdf.check(COLS, [ev("PO.1")], PRACTICES, None)
        self.assertIn("freshness-not-checked", rules(no_date["findings"], "info"))

    def test_planned_is_not_coverage_and_require_all(self):
        res = ssdf.check(COLS, [ev("PO.1", status="planned")], PRACTICES, require_all=True)
        self.assertEqual(res["summary"]["practices_covered"], 0)
        self.assertIn("practice-not-covered", rules(res["findings"], "error"))

    def test_justified_na_counts(self):
        res = ssdf.check(COLS, [ev("PS.3", ref="", status="not_applicable", just="No released binaries; SaaS only")],
                         PRACTICES)
        self.assertEqual(res["summary"]["groups"]["PS"]["covered"], 1)

    def test_empty_and_bad_inputs(self):
        res = ssdf.check(COLS, [], PRACTICES)
        self.assertEqual(res["summary"]["practices_covered"], 0)
        self.assertIn("missing-columns", rules(ssdf.check(["x"], [], PRACTICES)["findings"], "error"))
        self.assertIn("bad-practice-id", rules(ssdf.check(COLS, [ev("PO.1.1")], PRACTICES)["findings"], "error"))
        self.assertEqual(run_cli(SKILL, "ssdf_evidence_check", EX / "evidence-pass.csv", "--as-of", "13/10/2026").returncode, 2)
        self.assertEqual(run_cli(SKILL, "ssdf_evidence_check", "nope.csv").returncode, 2)


class DependencyPinTests(unittest.TestCase):
    def tmp(self, files):
        d = Path(tempfile.mkdtemp())
        for name, text in files.items():
            (d / name).write_text(text)
        return d

    def test_pass_fixture(self):
        code, out = run_json(SKILL, "dependency_pin_check", EX / "deps-pass")
        self.assertEqual(code, 0)
        self.assertEqual(len(out["summary"]["manifests"]), 3)
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_fail_fixture(self):
        code, out = run_json(SKILL, "dependency_pin_check", EX / "deps-fail")
        self.assertEqual(code, 1)
        self.assertEqual(rules(out["findings"], "error"), {"unpinned-dependency", "unpinned-vcs", "missing-lockfile"})
        assert_schema(self, out, FINDINGS_SCHEMA)

    def test_pep508_pins(self):
        self.assertTrue(deps.pep508_pinned("==1.2.3")[0])
        self.assertTrue(deps.pep508_pinned("===1.2.3")[0])
        self.assertFalse(deps.pep508_pinned("==1.2.*")[0])
        self.assertFalse(deps.pep508_pinned(">=1,<2")[0])
        self.assertFalse(deps.pep508_pinned("")[0])
        self.assertTrue(deps.pep508_pinned("==2.0 ; python_version >= '3.12'")[0])

    def test_npm_range_with_lockfile_is_warning(self):
        d = self.tmp({"package.json": json.dumps({"dependencies": {"zod": "^3.23.8"}}), "package-lock.json": "{}"})
        res = deps.check([d])
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertIn("range-specifier", rules(res["findings"], "warning"))

    def test_library_mode_relaxes(self):
        d = self.tmp({"requirements.txt": "httpx>=0.27\n"})
        self.assertEqual(deps.check([d], "library")["summary"]["errors"], 0)
        self.assertEqual(deps.check([d], "app")["summary"]["errors"], 1)

    def test_vcs_with_commit_and_continuation(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        d = self.tmp({"requirements.txt": f"pkg @ git+https://example.invalid/pkg.git@{sha}\n"
                                          "flask==3.0.3 \\\n    --hash=sha256:abc\n"})
        res = deps.check([d])
        self.assertEqual(res["summary"]["errors"], 0)
        self.assertNotIn("no-hashes", rules(res["findings"]))

    def test_malformed_and_missing(self):
        d = self.tmp({"package.json": "{not json"})
        self.assertIn("unreadable-manifest", rules(deps.check([d])["findings"], "error"))
        empty = self.tmp({})
        self.assertIn("no-manifests", rules(deps.check([empty])["findings"], "warning"))
        self.assertEqual(run_cli(SKILL, "dependency_pin_check", "no/such/dir").returncode, 2)


if __name__ == "__main__":
    unittest.main()
