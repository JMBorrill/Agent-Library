# Concept of operations — ASTER-01 low-gravity locomotion demonstrator (synthetic)

All names, bodies and data in this document are synthetic and exist only to demonstrate the library.
Status: draft for stakeholder walk-through; not validated by the stakeholders listed below.

## Mission need
Project ASTER (an autonomous asteroid-mining robot concept) needs credible, repeatable evidence of how
a robot can relocate between work sites on a small, weak-gravity body without being lost to space, so
that one locomotion concept can be carried into preliminary design. Phase 1 must produce that
evidence from analysis and from a ground demonstrator operated in a reduced-gravity analogue.

Candidate concepts (kept separate from the need): latched-spring hopper; internal-flywheel hopper;
wheeled rover (reference only).

## Stakeholders
Phase 1 project lead (decision owner), mission systems architect, laboratory test-safety authority,
test operators, research sponsor. See stakeholders.csv for interests and decision rights. Needs are
drafted from the Phase 1 kick-off minutes [evidence: ASTER-MIN-2026-09-15 (synthetic)] and the
laboratory safety policy [evidence: LAB-SAF-POL-04 (synthetic)]; they are hypotheses until the
stakeholders validate them.

## Operational scenarios
### Nominal scenarios
- S1 Flight-like relocation (analysis only): the robot estimates launch speed, hops between two sites
  13–38 m apart on the synthetic body ASTER-T1, lands, bounces and settles before resuming work.
- S2 Ground trial: operators arm the demonstrator in the offload rig, leave the guarded zone, the
  controller executes one hop, the logger records command time and body acceleration, the actuator is
  returned to zero stored energy, operators re-enter.
- S3 Data export: the trial data set is exported with configuration identifiers for analysis.

### Off-nominal and contingency scenarios
- S4 Over-speed command: the estimated launch speed exceeds the limit; the controller inhibits release
  and reports a fault (flight-like and ground).
- S5 Emergency stop during an armed state: actuator power is removed; spring or flywheel energy must be
  dissipated before anyone approaches.
- S6 Offload cable snag or counterweight runaway: trial aborted, rig brake applied, demonstrator
  caught by the safety net.
- S7 Logger failure mid-trial: trial voided and repeated; no partial data set is used.
- S8 Excessive rebound after landing (high restitution regolith): robot remains mobile for up to ~40
  minutes before settling; operations wait for the settle criterion before the next command.

## Operational modes
Safe (no stored energy), setup, armed, trial, settle/wait, maintenance.

## Operating environment
- Flight-like (analysis only): synthetic body ASTER-T1 — radius 400 m, bulk density 2000 kg/m³,
  rotation period 6 h. lowg_calc.py gives surface gravity 2.237e-4 m/s², net equatorial gravity
  1.898e-4 m/s², escape speed 0.423 m/s, circular-orbit speed 0.299 m/s (G = 6.67430e-11, CODATA 2018).
- Ground: indoor laboratory, 15–25 °C, vertical counterweight offload rig. The rig cannot reproduce
  1.9e-4 m/s²; the residual effective gravity it can achieve is unknown (TBR, see open questions).

## Constraints
- Operators must be outside the guarded zone whenever the actuator holds stored energy.
- Every physical trial requires written authorisation by the laboratory test-safety authority.
- Phase 1 budget and schedule are fixed by the sponsor; no flight hardware is built.

## Measures of effectiveness
- MOE-1 (ASTER-STK-001): hop range repeatability in the analogue, 1-sigma spread ≤ 10 % over 10 trials.
- MOE-2 (ASTER-STK-002): predicted launch speed ≤ 30 % of circular-orbit speed in all analysed cases.
- MOE-3 (ASTER-STK-003): zero operator entries into the guarded zone while energy is stored, over 20 trials.
- MOE-4 (ASTER-STK-004): predicted settle time ≤ 2400 s for restitution up to 0.8.
See needs.csv.

## Assumptions
- A1 ASTER-T1 is represented as a homogeneous sphere; real targets may be irregular (owner: mission systems architect).
- A2 Regolith restitution lies between 0.2 and 0.8 (owner: mission systems architect).
- A3 Rig friction and counterweight inertia can be characterised to within 5 % (owner: test lead).

## Open questions
- Q1 What residual effective gravity can the offload rig achieve, and is it representative enough? (owner: vv-engineer)
- Q2 Which real target body, if any, should replace ASTER-T1 in Phase 2? (owner: decision owner)
- Q3 Is attitude control in flight needed for safe landing? (owner: systems-architect)
