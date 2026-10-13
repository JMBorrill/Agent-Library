# Independent library review

| Field | Value |
|---|---|
| Artifact | The Agent-Library as a whole (`/home/user/Agent-Library`, VERSION file as found on 2026-10-13) |
| Reviewer | `independent-reviewer` subagent, following `.claude/skills/independent-review/SKILL.md` |
| Independence | I did not write any part of this library. I made no edits to it; the only file I wrote is this review |
| Date | 2026-10-13 |
| Decision supported | Whether the library may be used as an internal professional aid |
| Decision owner | The library owner. This review is a recommendation, not a decision |

## 1. Scope and method

Five questions, as briefed:

1. **Honesty about sources.** Sample: 20 SKILL.md files, at least one from each of the 9 packs in
   `packs/packs.json`: se-requirements, se-risk-analysis, se-decision-analysis, se-review-gates,
   space-technical-budgets, space-low-gravity-mobility, software-delivery-metrics,
   security-asvs-controls, sre-service-level-objectives, product-experiment-design, product-shaping,
   ux-accessibility-review, finance-npv-irr, finance-fca-scope-check, credit-criteria-modelling,
   credit-risk-governance, finance-unit-economics, ai-risk-assessment, select-frameworks and
   independent-review. I also read selected `references/` files: se-requirements, se-risk-analysis,
   finance-fca-scope-check triage table, finance-options appraisal method, space-low-gravity-mobility
   physics notes. I compared each against `sources/registry.json` `access_status` and the
   `sources/audits/*.md` files. Fourteen of the 19 registered sources are INACCESSIBLE; their audits
   record "Verified content: None".
   I also grepped every SKILL.md and reference file for section numbers, clause IDs, rates and the
   word "verified".
2. **Technical correctness.** I read 8 calculators in full and ran each on crafted inputs in the
   session scratchpad (`.../scratchpad/review/`). I recomputed the answers with independent Python
   one-liners. I also tried edge cases: zero rates, boundary values, typos, unit mismatches and
   frames of reference.
3. **Safety and authority boundaries.** I checked the `tools:` lists, read-only statements and
   `## Human approval required` sections in all 14 files in `.claude/agents/`. I grepped every
   script for strings that produce an outcome (`GO`, `eligible_indicative`, `RECOMMEND_SHIP`, `PASS`)
   and read how each one is worded.
4. **Test quality.** I ran the full suite. I used an AST scan to count tests with one assertion or
   with exit-code-only assertions, then read the flagged tests by hand.
5. **Usability.** I checked each sampled SKILL.md for Inputs, Procedure, Decision criteria,
   Validation, Examples, Escalation and "Do not use when". I read four of them in full.

Commands run (exact), all from `/home/user/Agent-Library` unless stated:

| Command | Exit / final line |
|---|---|
| `python3 -m unittest discover -s tests -t .` | `Ran 564 tests in 30.159s` then `OK` (exit 0) |
| `python3 .claude/skills/independent-review/scripts/claim_check.py .claude/skills README.md` | `FAIL: {'files': 121, 'errors': 50, 'warnings': 44}`. Most hits are in deliberate `*-fail*` fixtures; see F14 |
| `cashflow.py cf1.json` | exit 0, values in section 3 |
| `affordability_calc.py aff1.json` / `aff2.json` | exit 0 / exit 0 (see F02) |
| `slo_calc.py budget ...`, `alerts --policy pol.json --observations obs.json --json` | exit 0; alert not firing at exact threshold (see F03) |
| `lowg_calc.py hop --preset aster-target --speed 0.15 --angle-deg 10 --json` | `passed: true`, exit 0 (see F01) |
| `experiment_calc.py sample-size / evaluate / mde` | exit 0, values in section 3 |
| `decision_matrix.py dm.json` / `dm2.json` / `dm3.json` | exit 0 / traceback `KeyError: 'id'` / exit 0 (see F08) |
| `link_budget.py fspl ...` and `evaluate link.json` | exit 0, values in section 3 |
| `unit_economics.py ue.json --json` / `ue2.json --json` | exit 0 / exit 0 (see F05, F06) |

## 2. Findings

Severity follows the decision-criteria table in the independent-review skill. Evidence marked
**run** comes from executing the tool. Evidence marked **read** comes from reading code or text only.

| ID | Severity | Location | Claim | Evidence checked | Result | Recommended fix |
|---|---|---|---|---|---|---|
| F01 | major | `.claude/skills/space-low-gravity-mobility/scripts/lowg_calc.py:143` (also `SKILL.md:3`) | The skill says it is for checking that a hop stays well below escape speed, and the script blocks at v_esc and v_circ | **run**: on preset `aster-target` (r 250 m, rho 1900, P 4 h), the surface moves at 0.10908 m/s, which is 42% of v_esc 0.25768 m/s. A 0.15 m/s hop at 10 degrees, launched eastward, has inertial speed 0.25812 m/s, which is above v_esc. The script returns `passed: true`, exit 0, with warnings only. The check compares launch speed relative to the surface against non-rotating v_esc. The limitation appears only in `references/lowg-physics.md:29-30` | contradicted for fast rotators | Add a rotation-aware worst case: (v_rel + omega r cos(lat)) compared with v_esc and v_circ, giving an error. Or block when omega r is more than about 10% of v_esc. Move the caveat into SKILL.md and add a test using this preset |
| F02 | major | `.claude/skills/credit-criteria-modelling/scripts/affordability_calc.py:183` (finding at :146) | The tool does arithmetic only and gives no affordability verdict | **run**: `aff1.json` prints `PASS` with exit 0 although stressed NDI is -143.63/month and DTI is 52.31%. `aff2.json` (second charge) prints `PASS` with NDI -816.67/month. Negative NDI is only a warning. A broker or product UI that shows exit status or the PASS banner could present this as affordable. The scope line underneath disclaims it, but the banner contradicts it | partially supported | Replace `PASS/FAIL` with neutral wording such as `ARITHMETIC_COMPLETE` / `INPUT_ERRORS`. Make negative NDI a `refer` signal (its own exit code or a top-level `refer: true`). Add a warning when `stress_margin_pct` is 0 |
| F03 | minor | `.claude/skills/sre-service-level-objectives/scripts/slo_calc.py:138` | The docstring at :12 says an alert fires when burn is at or above the threshold over both windows | **run**: target 0.999, 1h error_rate 0.0144, 5m burn 15.0, threshold 14.4. Output: `burn_long: 14.4`, `firing: false`. The burn is 14.399999999999999 in floating point and the display rounds it, so the output contradicts itself | contradicted at boundary | Compare with a tolerance (`bl >= thr - 1e-9`) or on the rounded values. Add a boundary test; the current test at `tests/test_sre_service_level_objectives.py:35` checks only that burn is approximately 14.4 |
| F04 | minor | `slo_calc.py:88` | Budget consumed is reported | **run**: `--total-events 1000000 --bad-events 500 --bad-minutes 43.2`. The events give 50% consumed, but the output says `budget_consumed: 1.0` and `budget_exhausted: True`. The minutes value overrides the events value without any message | partially supported | Report both measures, or reject the input when both are given |
| F05 | minor | `.claude/skills/finance-unit-economics/scripts/unit_economics.py:210` | Scenarios override inputs | **run**: scenario `{"monthly_chrn": 0.5}` (a typo) returns LTV 3500.0, identical to base, with no finding | unsupported for typos | Add an error finding for override keys that are not REQUIRED or OPTIONAL inputs |
| F06 | minor | `unit_economics.py:161` (`expected_lifetime`, :145) | The simple and discounted LTV figures are comparable | **run**: churn 0.01, horizon 60, discount 0.0 gives simple `ltv` 4800.0 but `ltv_discounted` 3622.75. The cap applies to 1/churn, not to expected survival inside the horizon. For churn 0.02 (life 50 < H) no cap applies, yet survival within 60 months averages only 35.1 months | partially supported (definition mismatch) | Compute the simple LTV as the undiscounted survival sum to H, or state the difference in the output and in SKILL.md |
| F07 | minor | `.claude/skills/finance-npv-irr/scripts/cashflow.py:412` | CSV input takes a `period` column | **run**: periods 3, 4, 5 are treated as t0 (flows[0] undiscounted, NPV 41.3223). The period values are ignored except for a start of 1 | partially supported | Reject a first period other than 0 or 1, or discount by the actual period index |
| F08 | minor | `.claude/skills/se-decision-analysis/scripts/decision_matrix.py:87,104,143` | The tool exits 2 on unreadable input, 1 on input errors | **run**: a criterion without `id` gives a `KeyError` traceback instead of a finding. With `normalisation: none` and `scale_max: 5`, a score of 50 gives a total of 10.0 with no finding | partially supported | Validate `id` on criteria and alternatives. Raise an error finding when a score falls outside 0..scale_max |
| F09 | minor | `tests/test_software_code_review.py:76` | `test_strict_blocks_warnings` | **read**: the test asserts exit 0 for the pass fixture under `--strict`. It never checks that warnings block | test would pass with `--strict` broken | Use a fixture that has warnings and assert exit 1 under `--strict` and exit 0 without it |
| F10 | minor | `tests/` (lowg, slo, unit-economics, affordability) | The suite gates the behaviour of the tools | **run**: all 564 tests pass while F01-F05 and F07-F08 behave as described above. No test covers the rotating frame, exact burn threshold, unknown override keys, CSV period offset or missing criterion id | gap | Add one regression test per finding when fixing |
| F11 | observation | `.claude/agents/independent-reviewer.md:4` (also ai-governance-, credit-regulatory-, safety-risk-, security-, software-quality-reviewer) | Reviewers are read-only | **read**: the tools list omits Write/Edit but includes Bash, which can write files. So read-only is a matter of instruction, not tool restriction. All 14 agents have a `## Human approval required` section | partially supported | Say in the agent files that read-only is procedural, or enforce it with harness permission rules |
| F12 | observation | `.claude/skills/finance-fca-scope-check/scripts/reg_triage.py:188` | Provenance is marked | **run**: the text output prints `(unverified) (unverified)` because the provenance strings already contain the marker | cosmetic | Do not append the label when it is already present |
| F13 | observation | `.claude/skills/product-experiment-design/scripts/experiment_calc.py:320-321` | Ship recommendation | **read** (not executed): `RECOMMEND_SHIP` needs only significance and a CI wholly on the predicted side. It does not compare the effect with the planned MDE. `SKILL.md:66` says the result remains subject to `ship_if` and a human decision | supported with caveat | Add a `below-planned-mde` info finding when the point estimate is below the MDE |
| F14 | observation | `independent-review/scripts/claim_check.py` on the library itself | The language screen is useful as a gate | **run**: 50 errors and 44 warnings over `.claude/skills`. Most are in deliberate `*-fail*` fixtures. The non-fixture hits I opened were false positives: descriptive or negated wording at `ai-risk-assessment/SKILL.md:94`, `ux-accessibility-review/SKILL.md:94`, `credit-risk-governance/references/credit-governance-areas.md:8` and `ai-prompt-injection-review/references/injection-method.md:14` | noisy | Add an allowlist or ignore marker for method text that describes patterns, so real hits stand out |
| F15 | observation (positive) | 20 sampled SKILL.md files plus the references listed in section 1 | Section numbers, rates, dates and clause IDs from INACCESSIBLE sources are marked unverified | **read**: every sampled citation carries an inline unverified or secondary marker and a pointer to `sources/audits/`. This covers the NASA handbook section numbers, FCA sourcebook references and Consumer Duty dates, the Green Book STPR schedule, the Google SRE chapter numbers and burn-rate thresholds, the Basel four-area grouping and the NIST AI RMF category counts. I found no invented citation. VERIFIED sources (DORA, OWASP ASVS, GOV.UK Design System) are cited at file and section level, consistent with their audits | supported in sample | Keep. `claim_check` warns at `credit-criteria-modelling/SKILL.md:110` and `finance-fca-scope-check/SKILL.md:97` because the marker sits on the next line of the same bullet. Putting it on the same line silences the warning |

Counts: critical 0, major 2, minor 8, observation 5.

## 3. Recomputation table

My values come from standalone Python formulas written for this review, not from importing the library.

| Tool | Case | Library output | Independent value | Agreement |
|---|---|---|---|---|
| `finance-npv-irr/cashflow.py` | flows -1000, 300, 400, 500 at 10%, t0 | NPV -21.0368; IRR 0.0889633947; MIRR 0.0922; PI 0.9790; simple payback 2.6000 | NPV -21.03681; IRR 0.0889634; MIRR 0.0922318; PI 0.978963; payback 2.6 | agree |
| same | DCF FCF 100, 110, 121, r 10%, g 2%; CAPM 4% + 1.2 x 5%; WACC 60/40, Kd 6%, tax 25% | EV 1,431.8182; Ke 0.1000; WACC 0.0780 | EV 1431.81818 (TV 1542.75); Ke 0.10; WACC 0.078 | agree |
| same | flows -100, 230, -132 at 10% | roots [0.1, 0.2], `multiple-possible` | roots 10% and 20% (NPV is 0 at both) | agree |
| `credit-criteria-modelling/affordability_calc.py` | 200,000 over 25 y at 5% and stressed 8%; income 40,000; commitments 200; essentials 1,000; net 2,600 | 1,169.18; 1,543.63; DTI 52.31%; NDI -143.63; LTV 80.00 | 1169.1801; 1543.6324; 52.309%; -143.632; 80.0 | agree (see F02 on wording) |
| `sre-service-level-objectives/slo_calc.py` | 99.9% over 30 d; 21.6 bad min after 10 d; alert 14.4 x 1h | 43.2 min; consumed 0.5; avg burn 1.5; budget at detection 0.02 | 43.2; 0.5; 1.5; 0.02 | agree (boundary issue F03) |
| same | example observations 1h 118000/120000, 5m 9790/10000 | SKILL.md:96 says 16.7x and 21x | 16.667x and 21.0x | agree |
| `space-low-gravity-mobility/lowg_calc.py` | preset r 250 m, rho 1900 | M 1.24354709e11 kg; g 1.32797e-4; v_esc 0.257679; v_circ 0.182207; net g at P 4 h 8.52004e-5 | identical to 6 significant figures | agree |
| same | hop 0.15 m/s, 10 deg, net g | t 611.434 s; range 90.322 m | t 611.434 s; range 90.322 m | agree (frame issue F01) |
| same | bounce v0 0.1, e 0.5, vt 0.01, g 1e-4 | 3 rebounds; 1750.0 s; series 2000.0 s | 3; 1750.0; 2000.0 | agree |
| `product-experiment-design/experiment_calc.py` | p1 0.10, p2 0.12, alpha 0.05, power 0.8 | pooled 3841 (3840.847); unpooled 3839 (3838.102) | 3840.8475; 3838.1022 | agree |
| same | 100/1000 vs 130/1000 | z 2.102741; p 0.035488; Wald CI [0.002068, 0.057932] | z 2.1027406; p 0.0354885; CI [0.0020679, 0.0579321] | agree |
| same | MDE at n 3841 | 0.0199996 | about 0.02 (inverse of the row above) | agree |
| `se-decision-analysis/decision_matrix.py` | A/B/C, cost (min) w 0.6, perf w 0.4, min-max | A 0.6, B 0.4, C 0.4; cost switch 0.499 to B; perf switch 0.501 to B; flips within 20% | A 0.6, B 0.4, C 0.4; A beats B only for w_cost > 0.5, so first flip at 0.499; 0.6 x 0.8 = 0.48 < 0.5, so it flips | agree |
| `space-technical-budgets/link_budget.py` | FSPL at 2.4 GHz, 1 km | 100.052008 dB | 100.0520081 dB | agree |
| same | 8.4 GHz, 1000 km, 10 W, Gt 6 dBi, Lt 1, other 2, G/T 20, 1 Mbps, req 4.4 + impl 1; Gr 40, sens -120 dBm | FSPL 170.933369; C/N0 90.665798; Eb/N0 margin 25.265798; Prx -87.933369 dBm; margin 32.066631 | 170.9333689; 90.6657982; 25.2657982; -87.9333689; 32.0666311 | agree |
| `finance-unit-economics/unit_economics.py` | S&M 100,000 / 200 new; ARPA 100; GM 0.8; var 10; churn 0.02; 10% annual | CAC 500; contribution 70; life 50; LTV 3500; LTV:CAC 7; payback 7.142857; discounted LTV 2039.99132 | 500; 70; 50; 3500; 7; 7.142857; 2039.99132 | agree (definition issue F06) |
| `finance-options` reference (`references/appraisal-method.md:17-20`) | DF year 31, DF year 76, 10-year annuity | 0.345901; 0.091916; 8.316605 | 0.3459014; 0.0919159; 8.3166053 | agree (the STPR rates themselves are unverified per the skill) |

The arithmetic agrees in every case I tried. The problems are at boundaries and in definitions:
F01, F03, F04, F06, F07, F08.

## 4. What I could not check

- **Primary sources.** I did not access the network, so I could not confirm any content of the 14
  INACCESSIBLE sources. My source-honesty finding (F15) covers only how claims are labelled, not
  whether the unverified statements are correct. That includes, for example, the FCA dates, the
  Green Book rates and the NASA section numbering.
- **Unread files.** I did not read 25 of the 45 skills, or 44 of the 52 scripts in full, including
  `budget_calc.py`, `options_appraisal.py`, `criteria_engine.py`, `run_eval.py`, `dora_metrics.py`
  and the security scanners. The demo pipeline (`examples/run_demos.py`) and `scripts/run_all_checks.py`
  were not run.
- **Test strength.** The weak-test count (section 1, item 4) comes from a heuristic. I did not do
  mutation testing, so other tests that would pass against a broken implementation may exist.
- **F13** comes from reading the code; I did not run a plan and results file pair to reproduce it.
- **Fitness for a regulated purpose.** Whether any output is fit for regulated use, such as FCA
  conduct, credit decisions or flight hardware, is outside this review and needs the named
  domain authorities.

## 5. Overall recommendation

**GO_WITH_CONDITIONS** for using the library as an internal professional aid.

The reasons below rest on the evidence above:

- The library labels the limits of its sources honestly in every file I sampled (F15).
- The arithmetic of 8 calculators agrees with independent recomputation in every case I tried
  (section 3).
- Each agent file has a human approval section, and each script carries a scope disclaimer.
- The test suite runs cleanly: 564 tests, OK.

Conditions I recommend before relying on the affected tools:

1. **F01.** Fix the rotating-frame escape check, or label it prominently in SKILL.md, before anyone
   uses `lowg_calc.py` hop or bounce results to size real mobility for a fast-rotating body.
2. **F02.** Remove the `PASS` banner from `affordability_calc.py`, or reword it, before it sits
   behind any customer-facing or broker-facing view.
3. **F03-F10.** Fix the minor findings and add regression tests within the next maintenance cycle.
   Until then, users should be told about the boundary behaviours listed here.

**The library owner decides.** This review recommends; it does not accept the library or any
residual issue. Escalation: F01 should go to the `safety-risk-reviewer` and the Project ASTER
systems lead. F02 should go to the `credit-regulatory-reviewer`.
