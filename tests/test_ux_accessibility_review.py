import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "ux-accessibility-review"
mod = load_script(SKILL, "html_a11y_check")
EX = skill_path(SKILL, "assets", "examples")
SCHEMA = skill_path(SKILL, "assets", "schemas", "a11y-check.output.schema.json")
EXTRACT = json.loads((ROOT / "sources" / "extracts" / "gov-design-rules.json").read_text(encoding="utf-8"))
EXTRACT_RULES = {r["id"]: r for r in EXTRACT["rules"]}


def page(body: str, title: str = "Request a walk", lang: str = ' lang="en"') -> str:
    return f"<!DOCTYPE html><html{lang}><head><title>{title}</title></head><body><main>{body}</main></body></html>"


def check(body: str, **kw) -> list[dict]:
    return mod.check_html(page(body, **kw))


class RuleProvenanceTests(unittest.TestCase):
    def test_gds_rules_exist_and_are_static_testable(self):
        used = {src for src, _, _ in mod.RULES.values() if src.startswith("GDS-")}
        used |= {rid for rid, _ in mod.PURPOSES.values()}
        for rid in used:
            self.assertIn(rid, EXTRACT_RULES, rid)
            self.assertTrue(EXTRACT_RULES[rid]["testable_in_static_html"], rid)

    def test_wcag_refs_on_gds_rules_are_cited_by_extract(self):
        for slug, (src, wcag, _) in mod.RULES.items():
            if src.startswith("GDS-") and wcag:
                sc = re.search(r"SC (\d+\.\d+\.\d+)", wcag).group(1)
                cited = sc in EXTRACT_RULES[src]["rule_paraphrase"] or sc in EXTRACT["wcag_reference"]
                self.assertTrue(cited, f"{slug}: {wcag} not cited in extract")
            if src.startswith("LOCAL-") and wcag:
                self.assertIn("(unverified)", wcag, slug)


class ExampleTests(unittest.TestCase):
    def test_pass_example(self):
        code, out = run_json(SKILL, "html_a11y_check", EX / "form-pass.html")
        self.assertEqual(code, 0, out["findings"])
        self.assertEqual(out["findings"], [])
        self.assertTrue(out["summary"]["manual_checks_required"])
        assert_schema(self, out, SCHEMA)

    def test_fail_example_detects_each_seeded_defect(self):
        code, out = run_json(SKILL, "html_a11y_check", EX / "form-fail.html")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for expected in ["input-unlabelled", "placeholder-as-label", "options-not-in-fieldset",
                         "fieldset-legend-not-first", "error-not-associated", "summary-link-broken",
                         "summary-link-missing", "error-summary-position", "title-error-prefix",
                         "autocomplete-missing", "paste-blocked", "html-lang-missing", "img-alt-missing",
                         "aria-ref-broken", "duplicate-id"]:
            self.assertIn(expected, errs)
        warns = rules(out["findings"], "warning")
        for expected in ["button-disabled", "date-native-input", "date-incomplete", "required-attribute",
                         "form-novalidate-missing", "error-wording-banned", "error-wording-generic",
                         "label-asterisk", "maxlength-used", "number-input-type", "continue-button-next",
                         "autocomplete-unexpected", "error-summary-heading", "error-prefix-missing"]:
            self.assertIn(expected, warns)
        for f in out["findings"]:
            self.assertRegex(f["source_rule"], r"^(GDS|LOCAL)-")
        ac = [f for f in out["findings"] if f["rule"] == "autocomplete-missing"]
        self.assertTrue(all(f["wcag"] == "WCAG 2.2 SC 1.3.5" for f in ac))
        self.assertEqual({f["related_rule"] for f in ac}, {"GDS-AC-03", "GDS-AC-04"})
        assert_schema(self, out, SCHEMA)

    def test_human_output_states_scope(self):
        proc = run_cli(SKILL, "html_a11y_check", EX / "form-pass.html")
        self.assertIn("does not replace", proc.stdout)


class UnitChecks(unittest.TestCase):
    def test_label_variants(self):
        self.assertNotIn("input-unlabelled", rules(check('<label>Town <input name="town-x" type="text"></label>')))
        self.assertNotIn("input-unlabelled", rules(check('<input name="q" type="text" aria-label="Search">')))
        self.assertNotIn("input-unlabelled", rules(check('<span id="l">Search</span><input name="q" aria-labelledby="l">')))
        self.assertIn("input-unlabelled", rules(check('<select name="s"><option>a</option></select>')))
        self.assertNotIn("input-unlabelled", rules(check('<input type="hidden" name="csrf"><input type="submit" value="Continue">')))

    def test_single_checkbox_needs_no_fieldset(self):
        res = check('<input id="c" name="agree" type="checkbox"><label for="c">I agree</label>')
        self.assertNotIn("options-not-in-fieldset", rules(res))

    def test_preselected_only_on_fresh_pages(self):
        body = ('<fieldset><legend>Walk type</legend><input id="a" name="t" type="radio" checked>'
                '<label for="a">Solo</label><input id="b" name="t" type="radio"><label for="b">Group</label></fieldset>')
        self.assertIn("option-preselected", rules(check(body)))

    def test_date_outside_fieldset_and_dob_autocomplete(self):
        body = ('<label for="dob-day">Day</label><input id="dob-day" name="dob-day">'
                '<label for="dob-month">Month</label><input id="dob-month" name="dob-month" autocomplete="bday-month">'
                '<label for="dob-year">Year</label><input id="dob-year" name="dob-year" autocomplete="bday-year">')
        res = check(body)
        self.assertIn("date-not-in-fieldset", rules(res, "error"))
        missing = [f for f in res if f["rule"] == "autocomplete-missing"]
        self.assertEqual([f["id"] for f in missing], ["input#dob-day"])
        self.assertEqual(missing[0]["related_rule"], "GDS-AC-05")

    def test_non_personal_name_fields_not_flagged(self):
        res = check('<label for="dog-name">Dog name</label><input id="dog-name" name="dog-name">'
                    '<label for="holiday">Holiday</label><input id="holiday" name="holiday">')
        self.assertNotIn("autocomplete-missing", rules(res))
        self.assertNotIn("date-incomplete", rules(res))

    def test_error_page_requires_summary_and_title(self):
        body = ('<h1>Q</h1><label for="e">Email</label><p id="e-error" class="govuk-error-message">Error: Enter an email address</p>'
                '<input id="e" name="email" type="email" autocomplete="email" spellcheck="false" aria-describedby="e-error">')
        res = rules(check(body))
        self.assertIn("error-summary-missing", res)
        self.assertIn("title-error-prefix", res)
        ok = check('<div class="govuk-error-summary"><h2>There is a problem</h2><a href="#e">Enter an email address</a></div>' + body,
                   title="Error: Q")
        self.assertEqual(rules(ok, "error"), set())
        self.assertEqual(rules(ok, "warning"), set())

    def test_role_alert_accepted_as_summary(self):
        body = ('<div role="alert"><h2>There is a problem</h2><a href="#e">Enter an email address</a></div><h1>Q</h1>'
                '<label for="e">Email</label><p id="e-error" class="error-message">Error: Enter an email address</p>'
                '<input id="e" name="email" type="email" autocomplete="email" spellcheck="false" aria-describedby="e-error">')
        self.assertNotIn("error-summary-missing", rules(check(body, title="Error: Q")))

    def test_empty_and_malformed_html(self):
        self.assertIn("empty-document", rules(mod.check_html("  ")))
        res = mod.check_html("<html lang='en'><title>x</title><div><p>unclosed <input name='q'>")
        self.assertIn("input-unlabelled", rules(res))

    def test_unreadable_exit_2(self):
        self.assertEqual(run_cli(SKILL, "html_a11y_check", "missing.html").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.html"
            p.write_bytes(b"\xff\xfe\xfa")
            self.assertEqual(run_cli(SKILL, "html_a11y_check", p).returncode, 2)


if __name__ == "__main__":
    unittest.main()
