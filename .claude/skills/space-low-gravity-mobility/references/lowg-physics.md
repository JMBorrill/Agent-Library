# Low-gravity mobility physics notes

Original wording. Standard Newtonian mechanics; general engineering knowledge. Constant used:
G = 6.67430 × 10⁻¹¹ m³ kg⁻¹ s⁻² (CODATA 2018 recommended value, as stated in `lowg_calc.py`).

## Body (homogeneous sphere)
| Quantity | Formula |
|---|---|
| Mass | M = (4/3)·π·r³·ρ |
| Surface gravity | g = GM/r² = (4/3)·π·G·ρ·r |
| Escape speed | v_esc = √(2GM/r) |
| Circular orbit speed at the surface | v_circ = √(GM/r) = v_esc/√2 |
| Surface orbit period = critical spin period | T = 2π√(r³/GM) = √(3π/(Gρ)) — independent of radius for a sphere |

Worked example (synthetic ASTER-target, r = 250 m, ρ = 1900 kg/m³):
V = 6.545 × 10⁷ m³; M = 1.2435 × 10¹¹ kg; GM = 8.2998 m³/s²; g = 1.3280 × 10⁻⁴ m/s² (about 1/73 850
of Earth's 9.80665 m/s²); v_esc = 0.2577 m/s; v_circ = 0.1822 m/s; critical period 2.395 h.

Because g ∝ ρ·r, a body twice the size has twice the gravity at the same density; escape speed scales
with r. Real small bodies are often porous aggregates with irregular shapes: local gravity can differ
from the sphere value substantially (and is not radial), so treat these numbers as order-of-magnitude.

## Ballistic hop (flat, uniform gravity)
With launch speed v at elevation θ and gravity g: flight time t = 2v·sinθ/g, range R = v²·sin2θ/g,
apex h = v²·sin²θ/(2g). Example: g = 1.328e-4, v = 0.05 m/s, θ = 45° → t ≈ 532 s, R ≈ 18.8 m,
h ≈ 4.71 m.

Validity: h/r = (v/v_circ)²·sin²θ/2 and R/r = (v/v_circ)²·sin2θ, so the speed ratio v/v_circ controls
the error. The script warns above 0.3 (heuristic) and blocks at v_circ and v_esc. On a rotating body
the launch speed is relative to a moving surface and Coriolis deflects the path — neither is modelled.

## Take-off impulse and traction
J = m·Δv; mean force over push time T is J/T. Weight is m·g — on the ASTER-target a 20 kg robot weighs
about 2.7 mN. Horizontal traction from friction is limited to μ·m·g, so the maximum drive acceleration
is μ·g (≈ 6.6 × 10⁻⁵ m/s² at μ = 0.5): wheeled driving is extremely slow to accelerate and any bump
can launch the vehicle. Pushing harder than the weight needs reaction from the surface (the contact
must hold) or anchoring.

## Bounce settling
For vertical impacts with constant restitution e, the n-th rebound speed is eⁿ·v₀. The script counts
rebounds whose speed is at or above a threshold v_t and sums their flight times 2·v_k/g. The infinite
series total 2·v₀·e/(g(1−e)) is an upper bound. Example: v₀ = 0.1 m/s, e = 0.5, v_t = 0.01 m/s,
g = 0.001 m/s² → 3 rebounds (0.05, 0.025, 0.0125 m/s), settle time 175 s. Regolith restitution is
poorly constrained and varies with impact speed and angle; always analyse a range.

## Rotation
Centrifugal acceleration at the equator a = ω²r, ω = 2π/P. At latitude φ its outward radial component
is ω²r·cos²φ and its along-surface component ω²r·cosφ·sinφ (towards the equator). Net radial
gravity g − ω²r·cos²φ becomes negative (outward) for P shorter than the critical period: loose material
and an unanchored robot would leave the surface. The along-surface component tilts effective "down",
changing apparent slopes.

## Not modelled
Irregular shape and non-radial gravity; gravity variation with height; Coriolis; regolith
cohesion/granular mechanics; solar radiation pressure on long hops; electrostatic effects; terrain.
