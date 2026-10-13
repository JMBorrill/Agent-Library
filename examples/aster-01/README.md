# ASTER-01: illustration, not an engineering approval

**Project ASTER (synthetic)** is a concept for an autonomous asteroid-mining robot. Phase 1 focuses on a
low-gravity locomotion system and a ground demonstrator: two hopping concept candidates (latched spring,
internal flywheel), to be tested in a reduced-gravity analogue rig. This worked example shows the library
being used from framework selection to an SRR-style readiness recommendation.

It is **not** a flight-qualification, test-authorisation or operating specification. Every name, body and
number is synthetic. All design values are *proposed*; the target body **ASTER-T1 is invented** (radius
400 m, bulk density 2000 kg/m³, rotation 6 h) and is not a real asteroid. G = 6.67430e-11 m³ kg⁻¹ s⁻²
(CODATA 2018, as stated by `lowg_calc.py`; not re-verified in this environment).

Contents: `demo.json` (the steps), `inputs/` (synthetic artifacts written for this demo), `outputs/`
(generated only by `examples/run_demos.py`, see [outputs/RUN-SUMMARY.md](outputs/RUN-SUMMARY.md)),
`review/` (left for the independent reviewer), and `starter-review-notes.md` (the original provisional
notes, kept unchanged). The starter `requirements.csv` was moved to `inputs/` and replaced by the
derived register; its two starter requirements continue as ASTER-SYS-004 and ASTER-SYS-005.

## 1. Framework selection

Step `01-framework-selection` ran `select-frameworks` on [inputs/profile.json](inputs/profile.json)
(adapted from the skill's `profile-aster.json`; the same file also carries the keys `tailor_process.py`
reads). Output: [outputs/01-framework-selection.md](outputs/01-framework-selection.md).

**Oversight level: high** — the profile is safety-critical (stored-energy actuators, suspended masses,
physical tests) and novel.

| Selected pack | Why |
|---|---|
| systems-engineering | hardware, physical tests, safety-critical, multidisciplinary robot |
| space-engineering | asteroid / low-gravity environment: `space-low-gravity-mobility`, `space-technical-budgets` |
| software | embedded hop-controller software (release inhibit, logging) |
| orchestration | `independent-review` is always selected |

| Rejected pack | Why not |
|---|---|
| finance-credit (NPV, options, unit economics, FCA, credit) | no business case, revenue model or lending in Phase 1; a funding case would be a separate scope change |
| product, ux | no external users, market or user interface — internal research demonstrator |
| ai-governance | no AI/ML component; the estimator is deterministic signal processing. Re-run selection if learned perception or autonomy is added |
| reliability-security | no deployed service, personal data or multi-tenancy |

`se-technical-planning` (step 02) proposed standard base rigour with seven processes raised to rigorous
(design solution, verification, interfaces, risk, configuration, assessment, decision analysis), reviews
SRR, PDR, CDR, TRR, SAR, and two named authorities. The selection and the tailoring are proposals;
the decision owner has not agreed them (SRR-06 is `partial`).

## 2. Agent selection — authors and reviewers per phase

An author never reviews their own artifact.

| Phase | Author agent(s) | Reviewer agent(s) |
|---|---|---|
| Frame and tailor (profile, tailoring, ConOps) | `systems-engineer` | `independent-reviewer` |
| Low-gravity sizing (lowg cases) | `systems-architect` | `safety-risk-reviewer` (escape / loss-of-vehicle), `independent-reviewer` |
| Requirements (draft → fixed register) | `requirements-engineer` | `independent-reviewer` |
| Decomposition, trades, decision, ICD, budgets | `systems-architect` (ICD with `requirements-engineer`) | `independent-reviewer` |
| Risk register and FMEA | `systems-engineer` | `safety-risk-reviewer` |
| V&V matrix, test-analogue plan, integration plan | `vv-engineer` | `safety-risk-reviewer` (test hazards), `independent-reviewer` |
| Hop-controller software (Phase 1 code not yet written) | — | `software-quality-reviewer` (once code exists; `software-code-review`, `software-requirements-traceability`) |
| TPMs and SRR readiness package | `systems-engineer` | `independent-reviewer` (review pending, see `review/`) |

## 3. Skill execution

19 steps across 3 packs (orchestration — `select-frameworks` and `independent-review` —, systems-engineering and
space-engineering). Exit codes and outputs: **[outputs/RUN-SUMMARY.md](outputs/RUN-SUMMARY.md)**.

| Step | Skill / script | Expected exit | What it showed |
|---|---|---|---|
| 01 | select-frameworks | 0 | 4 packs, oversight high |
| 02 | se-technical-planning `tailor_process.py` | 0 | 7 rigorous processes; SRR–SAR; safety authority named |
| 03 | se-stakeholder-conops `conops_check.py` | 0 | 0 errors, 0 warnings |
| 04a | space-low-gravity-mobility `lowg_calc.py` (draft) | **1** | `exceeds-orbital-speed`: a single 500 m hop needs 0.31 m/s > v_circ 0.2991 m/s |
| 04b | `lowg_calc.py` (fixed) | 0 | body, rotation, hop, impulse and bounce cases; 2 `surface-rotation-speed-significant` warnings — worst-case inertial launch speed 0.2014 m/s = 47.6 % of v_esc (corrected after independent review F-05) |
| 05a | se-requirements `req_lint.py` (draft) | **1** | 6 errors: duplicate ID, TBR in an `approved` row, ID format, unknown parent, invalid method `simulation`; 11 warnings (ambiguous `safe`/`robust`/`quickly`, escape clause, non-atomic) |
| 05b | `req_lint.py` (fixed) | 0 | 0 errors; 10 `tbd-open` warnings (TBR values tracked) |
| 06 | se-logical-decomposition `function_check.py` | 0 | 12 functions, 11 leaves allocated, flows closed |
| 07 | se-architecture-trades `trade_space.py` | 0 | 18 combinations, 12 feasible, 8 with immature options (TRL < 4) |
| 08 | se-decision-analysis `decision_matrix.py` | 0 | SPRING-CAM leads (margin 0.087); WHEEL-REF screened by the mass must; weak-evidence warning |
| 09 | se-interface-control `icd_check.py --n2` | 0 | 9 draft interfaces; N² gaps noted below |
| 10 | space-technical-budgets `budget_calc.py` | 0 | mass 9.76 kg vs 12 kg (18.7 %); `example-policy-in-use` warning |
| 11 | se-risk-analysis `risk_check.py` | 0 | 8 risks, 1 high; 5 `safety-escalation` warnings |
| 12 | se-risk-analysis `fmea_calc.py` | 0 | 4 modes need action; FM-001/002/006 severity ≥ 9 |
| 13 | se-verification-validation `vmatrix_check.py` | 0 | 100 % planned coverage; 0 % passed; every result `not_tested` |
| 14 | se-implementation-integration `integration_check.py` | 0 | 5-step sequence; 12 warnings (no component exists or is unit-verified) |
| 15 | se-technical-assessment `tpm_track.py` | 0 | settle-time TPM in alert (3.7 %); mass TPM projects 12.9 kg at PDR |
| 16 | se-review-gates `review_readiness.py` | **1** | **NO_GO** recommendation after the independent review added 7 major safety-design actions (F-01–F-07); see `review/lead-response.md`; decision pending |
| 17 | independent-review `claim_check.py` | 0 | language screen of this README and `inputs/` |

**Draft → fix pairs**
1. *Low-gravity sizing* (04a → 04b). The first draft tried to reach a site 500 m away in one 45° hop
   (v = √(range·g_net) ≈ 0.31 m/s). The checker blocked it: above circular-orbit speed, flat-gravity model
   invalid. The fix keeps every hop ≤ 0.085 m/s (28.4 % of v_circ, 20.1 % of v_esc) and relocates in
   13–38 m hops.
2. *Requirements* (05a → 05b). The draft is what a kick-off typically produces: a copy-pasted duplicate
   ID, a TBR row set to status `approved` in the meeting, a two-digit ID, a parent from an old numbering,
   `simulation` as a method, and vague words. The fixed register splits, quantifies and traces each
   requirement, and keeps every requirement `proposed`. The linter could *not* see two draft defects the
   author fixed by hand: SYS-002's 10 m value had no source, and the duplicated row's owner was `TBD`
   on a proposed row.

## 4. Specification (inputs)

- [conops.md](inputs/conops.md), [stakeholders.csv](inputs/stakeholders.csv), [needs.csv](inputs/needs.csv) — mission need, 8 scenarios (5 off-nominal), MOE-1..4.
- [requirements.csv](inputs/requirements.csv) — ASTER-STK-001..004, ASTER-SYS-001..008, ASTER-SUB-001..004.
- [functions.csv](inputs/functions.csv), [components.csv](inputs/components.csv) — function tree and allocation.
- [trade-space.json](inputs/trade-space.json), [criteria.json](inputs/criteria.json), [decision.json](inputs/decision.json), [decision-log.md](inputs/decision-log.md) — ASTER-TRADE-001 / ASTER-DEC-001.
- [icd.csv](inputs/icd.csv) — ASTER-IF-001..009, all `draft`.
- [budget.csv](inputs/budget.csv), [margin-policy.json](inputs/margin-policy.json) — the policy is labelled as an example-value proposal (`is_example: true`), not from ECSS or NASA.
- [risk-register.csv](inputs/risk-register.csv), [fmea.csv](inputs/fmea.csv), [risk-matrix-policy.json](inputs/risk-matrix-policy.json) — ASTER-RSK-001..008; the matrix policy is a library example pending approval.
- [tpm.csv](inputs/tpm.csv), [integration-plan.json](inputs/integration-plan.json), [review-srr.json](inputs/review-srr.json).

**Where the numbers come from** (step 04b, [outputs/04b-lowg-sizing.json](outputs/04b-lowg-sizing.json)):

| Quantity (ASTER-T1, synthetic) | Value | Used in |
|---|---|---|
| Surface gravity / net equatorial gravity (6 h spin) | 2.237e-4 / 1.898e-4 m/s² | all hop and bounce cases |
| Escape speed / circular-orbit speed | 0.4230 / 0.2991 m/s | ASTER-SYS-001 limit 0.085 m/s (TBR) |
| Hop at 0.05 m/s / 0.085 m/s, 45° | range 13.2 m / 38.1 m; flight 373 s / 633 s | ASTER-SYS-002 (≥ 10 m, TBR) |
| Take-off at 0.085 m/s, 12 kg (TBR) | impulse 1.02 N s; kinetic energy 0.043 J | ASTER-SUB-002, ASTER-SYS-006 |
| Traction limit for wheels (μ 0.4) | 7.6e-5 m/s² drive acceleration | reason wheels are a reference only |
| Settle from 0.06 m/s impact, e = 0.2 / 0.5 / 0.8 | 126 / 553 / 2312 s | ASTER-SYS-003 (≤ 2400 s, TBR) |

Values not derivable from `lowg_calc` (e-stop latency, residual rig acceleration, energy threshold,
arrest distance, sampling rate) are marked TBR with their rationale in the register.

## 5. Verification procedures

[verification-matrix.csv](inputs/verification-matrix.csv) plans ASTER-VER-001..012 (3 analyses, 8 tests,
1 inspection) and ASTER-VAL-001..004; [test-analogue-plan.md](inputs/test-analogue-plan.md) gives the
procedures, pass/fail rules, hazards and what the counterweight rig can and cannot represent.
**Every result is `not_tested`.** The lowg_calc output is supporting analysis, not a closed verification
record, and no physical test was or could be executed by this demo. **Every physical test requires
written authorisation by the human laboratory test-safety authority** (and a TRR for hazardous tests);
none has been given.

## 6. Limitations and unknowns

- First-order physics only: homogeneous sphere, flat uniform-gravity hops, no Coriolis, no regolith
  mechanics, no shape model. ASTER-T1 is invented; a real target needs cited, current data (ConOps Q2).
- The counterweight rig cannot reproduce 1.9e-4 m/s²; its achievable residual is unknown (Q1, ASTER-RSK-006).
- Restitution is unknown (0.2–0.8 assumed); the settle-time TPM is already in alert (3.7 % margin).
- All decision scores are estimates or first-order analysis (75 % of the leading score); weights are
  proposed, not confirmed. The C4 (TRL) criterion does not discriminate between feasible alternatives.
- Mass, power and flywheel-energy figures are estimates; the mass trend projects a breach (12.9 kg vs
  12 kg) at the planned PDR. The TPM-VERR projection (-0.007 m/s) is physically meaningless — a linear
  heuristic on two points.
- N² gaps: no power interfaces PWR→CTRL/EST/LOG and no EST mechanical mount yet (ASTER-RID-002).
- Integration plan: no component exists or is unit-verified.
- Margin and risk-matrix policies are library example values, not programme policy.
- The SRR readiness tool now requires a cited independent-review record; none exists yet, so this is an
  explicit condition (`independent-review-record`) in step 16.

## 7. Evidence actually checked

Only what the scripts computed on the synthetic inputs: structure, traceability and arithmetic (exit codes
in [outputs/RUN-SUMMARY.md](outputs/RUN-SUMMARY.md)), and the lowg_calc physics under its stated
assumptions. Not checked: technical adequacy or completeness of any requirement, risk or interface; any
hardware, software or test result (none exist); stakeholder validation of needs; source documents marked
*(synthetic)*. Library framework sources (NASA SE handbook, ECSS) are INACCESSIBLE in this environment per
the selection output, so no clause is cited.

## 8. Human sign-offs required (none given)

| Who (synthetic role) | Must decide |
|---|---|
| ASTER Phase 1 project lead (decision owner, gate authority) | framework selection and tailoring; requirement baseline; ASTER-DEC-001 weights and decision; SRR gate decision; margin policy |
| Laboratory test-safety authority | hazard analysis, ASTER-RSK-001..004/-008 and FMEA severity ≥ 9 modes; authorisation of every physical test; residual safety risk acceptance; ASTER-SYS-005/-006/-008 values |
| Mission systems architect | ASTER-SYS-001..003 limits and the ASTER-T1 assumptions; validation of STK-002/-004 |
| Interface owners (both sides) | moving any ASTER-IF row from draft to agreed |
| Independent reviewer (separate agent / person) | review in `review/` before the gate |

The SRR output is a recommendation; only the gate authority can record a decision, and none is recorded.

## 9. Reproduce

```
python3 examples/run_demos.py --demo aster-01          # regenerate outputs/ and RUN-SUMMARY.md
python3 examples/run_demos.py --demo aster-01 --check  # must print PASS (no exit-code or output drift)
python3 .claude/skills/independent-review/scripts/claim_check.py examples/aster-01/README.md examples/aster-01/inputs
```
All scripts are Python stdlib only; date-dependent steps use `--as-of 2026-10-13` / `--milestone 2027-03-15`.
