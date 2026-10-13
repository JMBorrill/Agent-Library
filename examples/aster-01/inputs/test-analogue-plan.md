# ASTER-01 verification procedures and low-gravity test-analogue plan (synthetic)

Status: PLANNED ONLY. Nothing in this plan has been executed. Every result in
`verification-matrix.csv` is `not_tested`. No physical test may start until the laboratory
test-safety authority (synthetic) has authorised it in writing and a TRR-style review has been held;
this demonstration records no such authorisation.

## Target condition (analysis input)
Synthetic body ASTER-T1: radius 400 m, bulk density 2000 kg/m³, rotation period 6 h.
From `lowg_calc.py` (outputs/04b-lowg-sizing.json, G = 6.67430e-11 m³ kg⁻¹ s⁻² CODATA 2018):
surface gravity 2.237e-4 m/s², net equatorial gravity 1.898e-4 m/s², escape speed 0.4230 m/s,
circular-orbit speed 0.2991 m/s, critical spin period 2.33 h (body spins at 6 h, centrifugal term 15 %).

## Analysis procedures (verification by analysis)
| ID | Requirement | Procedure | Pass/fail rule |
|---|---|---|---|
| AP-001 (ASTER-VER-001) | ASTER-SYS-001 | Re-run `lowg_calc.py batch` for every commanded hop case at the speed limit; an independent reviewer checks inputs against the ConOps | All cases ≤ 0.085 m/s with no `exceeds-orbital-speed` / `exceeds-escape-speed` finding |
| AP-002 (ASTER-VER-002) | ASTER-SYS-002 | Hop cases at 0.05 and 0.085 m/s, 45°, net equatorial gravity | Range ≥ 10 m and ≤ 40 m (10 % of radius) |
| AP-003 (ASTER-VER-003) | ASTER-SYS-003 | Bounce cases at 0.06 m/s impact with restitution 0.2 / 0.5 / 0.8 | Settle time ≤ 2400 s in all three cases |

The first draft sizing (inputs/lowg-cases-draft.json, a single 500 m hop at 0.31 m/s) exceeded the
circular-orbit speed and was rejected by the checker; it is kept as a record, not as a design case.

## Test procedures (physical; all require safety-authority authorisation)
| ID | Requirement | Analogue / setup | Instrumentation | Pass/fail rule | Hazards and controls |
|---|---|---|---|---|---|
| TP-004 | ASTER-SYS-004 | Demonstrator in offload rig | Logger, IMU | Sample interval ≤ 5.0 ms in 3 trials | Stored energy: guard, safety pin |
| TP-005 | ASTER-SYS-005 | Demonstrator on bench, actuator powered | Contactor monitor, scope | Latency ≤ 0.5 s, 10/10, independent witness | Stored energy; witness outside guard |
| TP-006 | ASTER-SYS-006 | Demonstrator armed, then safing command | Spring deflection or flywheel speed sensor | Residual energy < 0.1 J within 60 s, 10/10 | Stored energy; approach only after reading |
| TP-007 | ASTER-SYS-007 | Rig with inert calibration mass | Accelerometer on mass | Residual ≤ 0.1 m/s² averaged over 1 s, 5 drops | Suspended mass; exclusion zone |
| TP-008 | ASTER-SUB-001 | Software-in-the-loop bench | SIL logs | 0/50 over-speed releases; 50/50 nominal releases | None (no stored energy) |
| TP-009 | ASTER-SUB-002 | Actuator on load-cell bench | Load cell 1 kHz | 0.30–1.02 N s ± 5 % over 10 firings | Stored energy; guard and pin |
| TP-010 | ASTER-SUB-003 | Logger on bench | Reference clock | Increments ≤ 1 ms over 60 s | None |
| IP-011 | ASTER-SUB-004 | Schematic review | — | No software element in e-stop chain | None |
| TP-012 | ASTER-SYS-008 | Rig, induced cable release with inert mass | Displacement sensor | Arrest ≤ 0.3 m, 5/5 | Falling mass; TRR mandatory |

## What the counterweight offload rig represents — and what it does not
- Represents: vertical take-off impulse and inertia of the full 12 kg (TBR) demonstrator; logging,
  release-inhibit and safing behaviour; operator procedures.
- Does NOT represent: 1.9e-4 m/s² gravity (residual achievable is unknown, placeholder ≤ 0.1 m/s²,
  ConOps Q1); horizontal low-gravity ballistics over tens of metres; regolith contact and restitution;
  rotation and Coriolis effects; vacuum and thermal environment.
- Scaling argument: take-off impulse and launch-speed control are compared at full speed (0.085 m/s),
  but flight times and ranges are taken from analysis only. Alternatives (drop tower, parabolic flight,
  air-bearing table) are open options for Phase 2.

## Test authorisation
Test authorised by: not yet authorised — requires the laboratory test-safety authority (synthetic),
name and date, before any physical test.
