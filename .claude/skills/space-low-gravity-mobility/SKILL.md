---
name: space-low-gravity-mobility
description: First-order physics and procedure for robot surface mobility on small bodies (asteroids, comets, small moons) — surface gravity, escape and orbital speed, ballistic hop time/range/apex, take-off impulse and traction limits, bounce settling with coefficient of restitution, rotation (centrifugal) effects — plus planning of terrestrial low-gravity test analogues. Use when sizing hopping, wheeled or legged locomotion for a low-gravity body, checking a hop or bounce stays well below escape speed, assessing fast-rotator surface conditions, or planning offload-rig, drop-tower, parabolic-flight or air-bearing tests (e.g. Project ASTER asteroid-mining robot).
metadata:
  pack: space-engineering
  version: "1.0.0"
  sources: "nasa-se ecss-se"
---

# Small-body low-gravity mobility analysis

## Purpose
Turn a target body's size, bulk density and spin into the numbers a mobility engineer needs first —
how weak gravity is, how fast is too fast, how long a hop or a settle takes, how much impulse and
traction are available — with every assumption written down, and plan how those behaviours could be
approximated on Earth. Results are **analysis aids with stated assumptions** (homogeneous sphere,
point-mass gravity, flat uniform-gravity hops). Any speed limit or design margin derived here is a
**proposal until approved by the programme**, and any **physical test must be authorised by a
qualified human** under the programme's test-safety process.

## When to use
- Concept sizing of hopping, wheeled, legged or anchored locomotion for a small body (ASTER first focus).
- Checking hop/rebound/take-off speeds against escape and circular-orbit speed.
- Estimating settle time after landing or a hop (coefficient of restitution).
- Assessing whether rotation weakens or reverses net surface gravity at a latitude.
- Writing a test-analogue plan (offload rig, drop tower, parabolic flight, air-bearing table).

**Do not use when:** the body is irregular enough that a sphere is misleading (contact binary,
elongated body) — use a shape-model gravity field from a specialist; you need contact/regolith
interaction dynamics (granular mechanics, DEM simulation) or trajectory design across large fractions
of the body; or you need real body parameters — obtain them from a cited, current source, never from
this skill's synthetic presets.

## Inputs
Required (per calculation)
- Body: radius (m) and bulk density (kg/m³) or mass (kg), or a preset; optional rotation period (h)
  and latitude (deg). Presets `aster-target` (r 250 m, ρ 1900 kg/m³, 4 h) and
  `fast-rotator-synthetic` are **synthetic, illustrative values — not real asteroids**.
- Hop: launch speed (m/s), angle (0–90°]. Impulse: robot mass (kg), speed, optional push time,
  friction coefficient. Bounce: impact speed, restitution 0 < e < 1, settle threshold speed.
Optional
- Batch case file `assets/templates/lowg-cases.json` (schema `assets/schemas/lowg-cases.schema.json`).
- Real-body parameters: if used, mark them "approximate public values — verify against current
  mission/catalogue data" with their source and date.

## Procedure
1. **Characterise the body:** `python3 scripts/lowg_calc.py body --radius-m R --density RHO [--rotation-period-h P]`
   Record g, v_esc, v_circ and the critical (spin-limit) period. G = 6.67430e-11 m³ kg⁻¹ s⁻¹ (CODATA 2018).
2. **Check rotation:** `lowg_calc.py rotation ... --rotation-period-h P --latitude-deg PHI`. If net
   gravity is ≤ 0 (`net-gravity-outward`), stop: surface operation there needs anchoring or a
   different site — escalate.
3. **Size hops:** `lowg_calc.py hop --speed V --angle-deg A [--heading-deg AZ] <body options>`. Keep
   launch speed well below v_circ; treat `flat-gravity-approx-questionable` as "use a central-force
   trajectory model". **Rotating bodies:** the surface itself moves east at ω·r·cos(latitude) (0.109 m/s
   on `aster-target`, 42 % of v_esc), so escape/orbital checks use the *inertial* speed = launch
   velocity relative to the surface + surface rotation velocity. Give `--heading-deg` (azimuth from
   north, 90 = east) for the vector sum; without it the worst case |v_rel| + ω·r·cos(latitude) is used.
   An eastward hop that looks safe relative to the surface can exceed escape speed.
4. **Size the actuator:** `lowg_calc.py impulse --mass-kg m --speed V --push-time-s T --friction-coefficient MU <body>`.
   Compare mean force with weight; compare required drive acceleration with μ·g (traction limit).
5. **Landing/settling:** `lowg_calc.py bounce --speed V0 --restitution E --threshold-speed VT <body>`.
   Use a range of e (e.g. low/expected/high) because regolith restitution is poorly known.
6. **Run the set as a batch** for traceable records: `lowg_calc.py batch cases.json --json`.
7. **Plan tests** with [references/test-analogues.md](references/test-analogues.md) and the template
   `assets/templates/test-analogue-plan.md`: state what each analogue represents and what it cannot.
8. **Feed budgets and requirements:** hop energy/impulse into `space-technical-budgets`; speed limits
   and settle times as proposed requirements into `se-requirements` (status `proposed`).

## Decision criteria
| Situation | Rule |
|---|---|
| Inertial launch or rebound speed (relative + surface rotation) ≥ v_esc | Blocking (`exceeds-escape-speed`): loss of vehicle risk; redesign or add control. |
| v_circ ≤ inertial speed < v_esc | Blocking (`exceeds-orbital-speed`): flat model invalid; re-analyse with orbital mechanics. |
| Inertial speed ≥ 50 % of v_esc (below v_circ) | Warning (`approaching-escape-speed`): little margin to loss of vehicle. |
| Surface rotation speed > 10 % of v_esc | Warning (`surface-rotation-speed-significant`): launch direction vs spin changes the escape margin; give `--heading-deg`. |
| speed/v_circ > 0.3 (default, heuristic) | Warning: approximation questionable; cross-check with a central-force model. |
| Range > 10 % of radius (heuristic) | Warning: curvature and gravity variation matter. |
| Net gravity ≤ 0 at site | Blocking: anchoring or site change; escalate to systems-architect and safety-risk-reviewer. |
| Centrifugal term > 50 % of gravity | Warning: use net gravity for all mobility numbers; check local slopes. |
| Restitution unknown | Bound with a range; do not use a single value in a requirement. |
| Using real-body data | Must carry source, date and "approximate — verify"; otherwise use synthetic presets only. |

Heuristic thresholds are engineering judgement defaults, configurable (`--approx-ratio`,
`--range-fraction`); they are not from any standard.

## Outputs
- JSON reports (`--json`), schema `assets/schemas/lowg-report.schema.json`: inputs, results,
  assumptions, constants (G and its source), findings.
- Test-analogue plan (`assets/templates/test-analogue-plan.md`) with limitations and the named human
  test authoriser.
- Proposed mobility requirements/limits routed to `se-requirements` as `proposed`.

## Validation
- `python3 -m unittest tests.test_space_low_gravity_mobility -v` — known answers for the sphere
  r = 250 m, ρ = 1900 kg/m³: M ≈ 1.2435e11 kg, g ≈ 1.328e-4 m/s², v_esc ≈ 0.2577 m/s,
  v_circ ≈ 0.1822 m/s; hop, bounce and impulse hand calculations.
- PASS means the formulas were applied to valid inputs and no speed/rotation limit was crossed under
  the stated model (speed limits checked in the inertial frame, including surface rotation). It does
  **not** mean the mobility concept works: irregular shape, regolith mechanics, Coriolis deflection of
  the hop path, terrain and control are not modelled.

## Examples
- `assets/examples/lowg-cases-pass.json` → exit 0 (info `rotation-significant`, `force-exceeds-weight`).
- `assets/examples/lowg-cases-fail.json` → exit 1 with `exceeds-escape-speed`,
  `exceeds-orbital-speed`, `flat-gravity-approx-questionable`, `range-large-vs-radius`,
  `net-gravity-outward`, `rebound-exceeds-escape-speed`.
- Single commands: `lowg_calc.py hop --g 1.328e-4 --speed 0.05 --angle-deg 45` → flight ≈ 532 s,
  range ≈ 18.8 m, apex ≈ 4.71 m.

## Escalation and stop conditions
- **Stop** and ask for real data when a decision depends on actual body parameters; do not present
  synthetic or remembered values as facts.
- **Stop** before any physical test: a qualified human must authorise it (drop towers, offload rigs and
  parabolic flights carry real hazards).
- Hand to `systems-architect` (locomotion concept trades), `systems-engineer` (requirements and
  budgets), `vv-engineer` (test-analogue selection and verification planning) and
  `safety-risk-reviewer` (escape/loss-of-vehicle, outward net gravity, test hazards).

## References
- Physics: standard Newtonian mechanics (general engineering knowledge); method notes in
  [references/lowg-physics.md](references/lowg-physics.md); G from CODATA 2018 (value stated in the
  script; not re-verified in this environment).
- Test analogues: [references/test-analogues.md](references/test-analogues.md) — general engineering
  knowledge, not from a cited source.
- `nasa-se` — technical assessment/verification context only *(unverified; see
  `sources/audits/nasa-se.md`)*. `ecss-se` — space-sector SE standard, not read; check applicability under
  its own licence (`sources/audits/ecss-se.md`). Neither source provides any formula or threshold here.
