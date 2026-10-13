# Terrestrial low-gravity test analogues (planning notes)

General engineering knowledge, not drawn from a cited source in this repository; check facility
capabilities with the facility operator. Every physical test requires authorisation by a qualified
human under the programme's test-safety process.

| Analogue | What it represents well | Main limitations |
|---|---|---|
| Gravity offload rig (counterweight, constant-force spring or active cable tracking) | Long-duration, mostly vertical offload of a whole vehicle; hop take-off mechanics; leg/wheel loading at reduced weight | Cable adds inertia, friction and lag; lateral motion needs tracking; rotation/tumble poorly represented; offload accuracy limits how small a residual g can be reproduced (small-body g is ~10⁻⁴ m/s², far below what most rigs can hold) |
| Drop tower / drop shaft | Clean free fall for a few seconds; contact and settling of small samples; mechanism actuation in near-zero g | Very short duration; small payload volume; high deceleration at capture; reproduces ~0 g, not a small steady g, unless a controlled residual is added |
| Parabolic flight | Tens of seconds of reduced gravity per parabola, repeated many times; human-tended experiments | Residual g jitter that can exceed small-body gravity; short windows; limited volume; cost and scheduling; flight-safety rules on hardware |
| Air-bearing table (planar) | Frictionless planar motion: docking, contact, momentum exchange, horizontal dynamics, long duration | 2-D only (3 DOF); table flatness/tilt introduces residual acceleration; air bearings dislike regolith simulant; vertical dynamics absent |
| Neutral buoyancy | Long-duration reduced apparent weight for large structures | Water drag and added mass dominate dynamics; not representative for hopping or contact dynamics |
| Pendulum / inclined-plane rigs | Reduced effective normal load on a contact surface; impact tests at low speed | Only the component along the constrained path is reduced; geometry constrains motion |
| Numerical simulation (multibody + granular/DEM) | Exact target gravity; parameter sweeps | Validity hinges on contact and regolith models that themselves need test data |

## Planning checklist
1. State the behaviour to verify and the requirement it supports.
2. Compute target-condition numbers with `lowg_calc.py` (cite case IDs).
3. Choose the analogue(s) whose faithful aspects cover the behaviour; list what is not represented.
4. Write a scaling/similarity argument (which non-dimensional groups are matched, e.g. ratio of
   launch speed to escape speed, Froude-type number v²/(g·L)).
5. Define instrumentation and quantitative pass/fail criteria.
6. Record hazards (stored energy in hop springs, drop capture loads, cable failure) and controls.
7. Obtain sign-off from the qualified test authority before any test; record name and date.
