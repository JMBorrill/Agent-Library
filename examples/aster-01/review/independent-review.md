# Independent review: Project ASTER demonstration (aster-01)

> Filed verbatim by the lead from the final report of a separate `safety-risk-reviewer` agent run
> (read-only tools; it did not author the demo). Lead responses: [`lead-response.md`](lead-response.md).

| Field | Value |
|---|---|
| Reviewer role | `safety-risk-reviewer` agent. I did not write this demo and am independent of its author agents (`systems-engineer`, `requirements-engineer`, `systems-architect`, `vv-engineer`). |
| Date | 2026-10-13 |
| Scope | `examples/aster-01/` README.md, `inputs/`, `outputs/` (including `outputs/RUN-SUMMARY.md`). Focus areas: hazards of the spring/flywheel hopping demonstrator and its counterweight offload rig (stored energy, uncontrolled motion, pinch/impact, battery); whether the risk register and FMEA cover them; whether the physics-derived requirement values hold; how honestly V&V is reported; whether the SRR recommendation is justified; overclaiming; human sign-offs; limitations. |
| Nature | A method review of synthetic artifacts. It is not a hazard acceptance, test authorisation or gate decision. Those belong to the laboratory test-safety authority and the ASTER Phase 1 project lead (both synthetic roles), and neither has recorded a decision. |
| Files modified | None. |

## Sources and access status
- `sources/registry.json`: `nasa-se`, `nasa-se-design`, `nasa-se-realize`, `nasa-se-manage`, `ecss-se` and `nasa-software` are all **INACCESSIBLE**. Any standards-practice statement in this review is therefore *unverified*. No standard clause is cited.
- The G value (CODATA 2018, 6.67430e-11) is as stated by `lowg_calc.py`; not checked against the primary source (*unverified*).
- Observed evidence is limited to the files listed above and the commands below. All project data is synthetic.

## Checks run (exact commands and exit codes)
Run from the repository root (S=`.claude/skills`, D=`examples/aster-01`).

| Command | Exit | Result |
|---|---|---|
| `python3 $S/se-risk-analysis/scripts/risk_check.py $D/inputs/risk-register.csv --policy $D/inputs/risk-matrix-policy.json --as-of 2026-10-13 --known-ids $D/inputs/requirements.csv $D/inputs/verification-matrix.csv $D/inputs/icd.csv` | 0 | PASS: 8 risks, 8 open, 1 high, 7 medium, 0 errors, 5 `safety-escalation` warnings (RSK-001/002/003/004/008), 1 info `consequence-reduced` (RSK-004). Matches `outputs/11-risk-check.json`. |
| `python3 $S/se-risk-analysis/scripts/fmea_calc.py $D/inputs/fmea.csv` | 0 | PASS: 7 modes, 4 need action. `high-severity` on FM-001 (S9, RPN 135), FM-002 (S10, RPN 120), FM-006 (S9, RPN 90). FM-007 RPN 140. Matches `outputs/12-fmea.json`. |
| `python3 $S/independent-review/scripts/claim_check.py $D/README.md $D/inputs` | 0 | PASS: 4 files, 0 errors, 0 warnings |
| `python3 $S/independent-review/scripts/claim_check.py $D/outputs/RUN-SUMMARY.md …` | 1 | 1 error, `RUN-SUMMARY.md:12 assurance-claim 'approved'` — see F-13. |
| `python3 examples/run_demos.py --demo aster-01 --check` | 0 | PASS: 19 steps, expected exit codes, no drift |
| own physics recomputation script | 0 | See Recomputations |
| two one-liners (tolerance stack; V&V evidence fields empty; `accepted_by` blank) | 0 | 16/16 activities `not_tested` with empty `evidence_ref`, `run_date`, `performed_by`; `accepted_by` blank for all 8 risks. |

Caveats: `risk_check.py` exit 0 only shows the register conforms to a policy, not that the risk list is complete or the scores are correct. The matrix policy is a library example awaiting approval, so all risk levels here are **provisional**.

## Findings
Severity scale: critical / major / minor / observation. No owner has accepted any of these findings.

| ID | Severity | Location | Finding | Evidence checked | Requested action / evidence |
|---|---|---|---|---|---|
| F-01 | major | `inputs/icd.csv` ASTER-IF-001; `fmea.csv` FM-003; ConOps S5 | **E-stop or power loss can itself cause uncontrolled motion, or leave energy trapped.** IF-001 says loss of supply leaves the flywheel "brake applied"; FM-003 defines that brake as the element that transfers momentum to the body, so an e-stop on the flywheel option could produce an uncommanded hop or lurch. On the spring option power loss holds the latch closed, keeping energy stored. Nothing defines how SYS-006 safing (dump below 0.1 J in 60 s) works once e-stop has removed actuator power. | IF-001, FM-003, SYS-005, SYS-006, ConOps S5 | Define an e-stop end state per concept (coast-down/braking without momentum transfer to the body; a dump path that works without actuator power). Add requirement + verification, re-score RSK-001/002, send to the safety authority (RID-003). |
| F-02 | major | `risk-register.csv` RSK-001/002/004/008 vs `related_ids`; `requirements.csv` | **Key hazard controls are not requirements and have no verification link, yet residual scores rely on them** (guard interlock, second safety pin, containment ring, overspeed trip, two-hand arming, preload end-stop, dual contactors, independent dump path, fire-safe charging container). Residuals already set low (RSK-001 1×5, RSK-002 1×5, RSK-008 1×4, RSK-004 2×3). | risk register, requirements, V&V matrix, FMEA | Turn each control into a proposed requirement with acceptance criterion and VER ID, or mark the residual "unsubstantiated". Safety authority review (RID-003). |
| F-03 | major | RSK-008; `fmea.csv`; `integration-plan.json` I1 | **Battery hazard coverage is narrow** — only thermal events during charging; no drop/impact, short circuit during integration, transport/storage; no battery FMEA row or requirement; the temperature trigger has no monitoring requirement. | RSK-008, FMEA, IF-008, integration plan | Add battery FMEA rows and requirements for pack protection, temperature monitoring and post-drop inspection, linked to VER activities. |
| F-04 | major | `icd.csv` IF-009; `test-analogue-plan.md` TP-006 | **Approach decision depends on one energy sensor with no protection against an in-range low reading**; no FMEA row for the sensor; IF-009 refers to a "zone locked" interlock that no requirement defines. | IF-009, TP-006, FMEA | Add sensor FMEA mode; require independent confirmation; add a zone-interlock requirement with verification. |
| F-05 | major | `outputs/04b-lowg-sizing.json`; README step 04b; SYS-001 rationale | **Loss-of-vehicle warning understated.** README says "info findings only" but 04b has two `surface-rotation-speed-significant` **warnings**. Worst-case inertial launch speed at the limit is 0.2014 m/s = 47.6 % of v_esc, 67.3 % of v_circ; the SYS-001 rationale quotes only surface-relative figures; no heading constraint. | 04b JSON, README, skill decision table, recomputation | Correct README; add inertial worst case to SYS-001 rationale; constrain heading or re-run with `--heading-deg`; add rotation to RSK-005. |
| F-06 | major | ASTER-SUB-001/002 vs SYS-001/002 | **Tolerances allow the parent limit to be exceeded.** SUB-002 accepts 1.02 N·s +5 % → 0.0893 m/s (> 0.085 limit; range ≈ 42 m > 40 m VER-002 bound). SUB-001 inhibits on the *estimate* with no guard band for estimator error (1σ up to 0.010 m/s). | requirements, TPM, recomputation | Allocate a speed budget (nominal + actuator tolerance + estimator 3σ ≤ limit) and derive the inhibit threshold and impulse upper bound from it. |
| F-07 | major | FM-001 vs FM-004; RSK-001 vs RSK-003 | **Severity inconsistent with energy; maximum stored energy unbounded.** Nominal spring energy (~0.145 J) is ~1000× smaller than the falling-mass hazard, yet scores higher; FM-004 (crush) drops out of `needs_action`. No maximum spring energy/flywheel speed requirement; rig drop height and counterweight mass not given, so the 600 N / 0.3 m arrest values cannot be checked. | FMEA, risk register, IF-008, SYS-008 | State maximum credible stored energy per concept and rig drop height/mass; re-score FM-001/004/005; action FM-004 regardless of RPN. |
| F-08 | minor | `inputs/review-srr.json` ASTER-RID-003 | RID routing five safety-escalated risks and three S ≥ 9 FMEA modes is rated "minor". | review-srr.json | Re-rate major or justify; keep it a hard precondition for hardware/test work. |
| F-09 | minor | RSK-004 | Residual consequence drops 4 → 3 through controls that mostly reduce likelihood. | risk_check output | Justify or restore C = 4. |
| F-10 | minor | SYS-003 vs HOP-MAX | Landing normal speed at the limit is 0.0601 m/s vs 0.06 used; settle 2315 s vs 2312 s reported; horizontal drift during settling unmodelled. | recomputation | Bound landing speed ≥ 0.0601 m/s (or toleranced value); note drift as unmodelled. |
| F-11 | minor | risk register | Uncontrolled motion inside the rig (strike on structure, single-cable swing) not stated as a risk. | risk register, test plan | Add or extend RSK-003; define rig travel limits. |
| F-12 | observation | README §4/§8; policy files | Policies honestly labelled as examples; every risk level and SRR-05 judgement is provisional. | policy files | Approve or replace the matrix policy before decision use. |
| F-13 | observation | `outputs/RUN-SUMMARY.md:12` | `claim_check` false positive on the status word `approved` in a step purpose. | claim_check run | Quote the status value (e.g. `status=approved`). |
| F-14 | observation | V&V | **Reported honestly** — all 16 activities `not_tested`, configurations "(not built)"; no text implies a test passed. | one-liner, vmatrix output | None. |
| F-15 | observation | sign-offs | **Human sign-offs correctly pending** (DEC-001, SRR decision, test authorisation, `accepted_by`). | files listed | None. |

No critical finding. Nothing here blocks paper design work. F-01 to F-07 would need resolving before any hardware build or physical test; that decision sits with the safety authority.

## Recomputations (reviewer's own Python)
Inputs: R = 400 m, ρ = 2000 kg/m³, T = 6 h, G = 6.67430e-11 (*unverified* constant), 45° hops, equator.

| Quantity | Reviewer value | Demo value | Agrees |
|---|---|---|---|
| Surface g / net g | 2.2366e-4 / 1.8981e-4 m/s² | 2.237e-4 / 1.898e-4 | yes |
| v_esc / v_circ | 0.4230 / 0.2991 m/s | 0.4230 / 0.2991 | yes |
| SYS-001: 0.085 as % of v_circ / v_esc | 28.4 % / 20.1 % | 28.4 % / 20.1 % | yes |
| SYS-002: range at 0.05 / 0.085 m/s | 13.17 m / 38.06 m (373 s / 633 s) | 13.2 / 38.1 m; 373 / 633 s | yes |
| SUB-002: impulse / KE at 0.085 m/s, 12 kg | 1.020 N·s / 0.0434 J | 1.02 N·s / 0.043 J | yes |
| SYS-006: spring energy at 30 % efficiency | 0.145 J | "about 0.15 J" | yes |
| SYS-003: settle at 0.06 m/s, e = 0.2/0.5/0.8 | 126 / 553 / 2312 s | 126 / 553 / 2312 s | yes |
| Draft 500 m hop speed | 0.308 m/s | 0.31 m/s | yes |
| Flywheel ½Iω² (I = 0.002, ω = 76.5) / impulse via 0.15 m lever | 5.85 J / 1.020 N·s | "about 5.9 J" / IMP-MAX | yes |
| Wheel traction limit μ·g_net | 7.59e-5 m/s² | 7.6e-5 | yes |
| IF-007 cable tension, 12 kg × 9.80665 | 117.7 N | 118 N | yes |
| **Worst-case inertial speed** (0.085 + ωR = 0.1164) | 0.2014 m/s = 47.6 % v_esc | in 04b; not in README/SYS-001 | see F-05 |
| SUB-002 upper bound +5 % | 0.0893 m/s | above the 0.085 limit | see F-06 |
| Settle at 0.0601 m/s, e = 0.8 | 2315 s | n/a | see F-10 |

The requirement values follow arithmetically from 04b under its stated assumptions; the problems are in the margins and tolerances around them (F-05, F-06), not the arithmetic.

## Is SRR GO_WITH_CONDITIONS justified?
Partly. On recorded evidence and generic criteria it is a reasonable *recommendation*: requirements traced and lint-clean, V&V planned at 100 % with 0 % passed (expected at SRR), open items are conditions with owners and dates, decision left to the gate authority. Weaknesses: RID-003 rated minor (F-08); SRR-05 rests on an unapproved policy (F-12); conditions do not yet include F-01 to F-07; `review-not-evidenced` stands until this review is cited as `independent_review_ref`.

## What I could not check
- Hazard-list completeness against a real laboratory hazard analysis (referenced documents are synthetic and absent).
- Any hardware, software, rig or test result — none exist.
- Rig geometry, drop height, counterweight mass, net/brake design; battery chemistry and pack design.
- Correctness of ordinal scores; stakeholder validation of needs or weights.
- Any standard clause (all NASA and ECSS sources INACCESSIBLE, *unverified*); the CODATA G value.
- Orbital-mechanics or Coriolis effects beyond the flat-gravity model.

## Recommendation
**GO_WITH_CONDITIONS** for "proceed to PDR-level design work (no physical tests)". A reviewer recommendation only — **the decision belongs to the human gate authority, the ASTER Phase 1 project lead (synthetic); safety findings go to the laboratory test-safety authority (synthetic). Neither has recorded a decision.**

Proposed conditions:
1. Add F-01 to F-07 to the SRR action list with owners and due dates no later than PDR entry; each closes with a requirement, a VER link and a re-scored risk/FMEA row, not narrative.
2. Re-rate ASTER-RID-003 and keep it a hard precondition: no hardware build, energised integration step or physical test until the safety authority has reviewed the safety-escalated risks, S ≥ 9 FMEA modes and this review, and given written authorisation per test.
3. Correct README step 04b and the SYS-001 rationale to show the inertial worst case (F-05).
4. Approve or replace the example risk-matrix and margin policies before risk levels are used in a decision.
5. Cite this review as `independent_review_ref` in `review-srr.json` and re-run step 16.

**Escalation:** F-01, F-02, F-04 and F-07 are sent directly to the laboratory test-safety authority — they concern people's exposure to stored energy and falling masses during future trials. This review accepts no risk; no residual risk has an accountable acceptor recorded.
