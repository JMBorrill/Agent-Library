#!/usr/bin/env python3
"""Small-body low-gravity mobility helper: body gravity, ballistic hops, take-off impulse, bounce
settling and rotational effects, with physical input validation and JSON output.

Subcommands:
  body      --radius-m R (--density RHO | --mass-kg M) | --preset NAME  [--rotation-period-h P]
  hop       --speed V --angle-deg A  (body options | --g G)  [--rotation-period-h P]
  impulse   --mass-kg m --speed V [--angle-deg A] [--push-time-s T] [--friction-coefficient MU] [body options | --g G]
  bounce    --speed V0 --restitution E --threshold-speed VT  (body options | --g G)
  rotation  (body options) --rotation-period-h P [--latitude-deg PHI]
  batch     cases.json   (list of {"id", "command", "params"})
Add --json for machine-readable output.

Model (stated assumptions): homogeneous sphere; point-mass gravity g = GM/r^2 at the surface;
v_esc = sqrt(2GM/r); circular orbit speed at the surface v_circ = sqrt(GM/r); hops use a flat,
uniform gravity field (no curvature, no variation of g with height, no Coriolis), no atmosphere;
bounces are vertical with a constant coefficient of restitution. G = 6.67430e-11 m^3 kg^-1 s^-2
(CODATA 2018 recommended value).

Exit codes: 0 no blocking findings, 1 blocking findings (e.g. model invalid, escape, outward net
gravity), 2 invalid input.

Scope: first-order analysis aid for concept studies; not a substitute for shape-model gravity,
contact dynamics simulation or test. Physical tests need authorisation by a qualified human.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

G = 6.67430e-11  # m^3 kg^-1 s^-2, CODATA 2018 recommended value
G_SOURCE = "CODATA 2018 recommended value"
SCOPE = ("Scope: first-order point-mass/flat-gravity analysis aid with stated assumptions; results are "
         "not a design sign-off and physical tests need authorisation by a competent, authorised human.")

# Synthetic bodies for examples and tests. NOT real asteroids.
PRESETS = {
    "aster-target": {"radius_m": 250.0, "density_kg_m3": 1900.0, "rotation_period_h": 4.0,
                     "label": "synthetic ASTER-target body (illustrative values, not a real asteroid)"},
    "fast-rotator-synthetic": {"radius_m": 150.0, "density_kg_m3": 1500.0, "rotation_period_h": 2.0,
                               "label": "synthetic fast rotator (illustrative values, not a real asteroid)"},
}

# Heuristic thresholds for flagging the flat/uniform-gravity hop approximation (configurable).
DEFAULT_APPROX_RATIO = 0.3      # warn when launch speed / circular speed exceeds this
DEFAULT_RANGE_FRACTION = 0.1    # warn when range / body radius exceeds this
MAX_BOUNCES = 1_000_000


class InputError(ValueError):
    """Invalid physical input (exit 2)."""


def _f(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def _pos(name: str, value: float | None, allow_zero: bool = False) -> float:
    if value is None:
        raise InputError(f"{name} is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{name} must be a finite number")
    if value < 0 or (value == 0 and not allow_zero):
        raise InputError(f"{name} must be {'>= 0' if allow_zero else '> 0'} (got {value})")
    return float(value)


# ----------------------------------------------------------------------------- physics
def body(radius_m: float, density_kg_m3: float | None = None, mass_kg: float | None = None) -> dict:
    r = _pos("radius_m", radius_m)
    if (density_kg_m3 is None) == (mass_kg is None):
        raise InputError("give exactly one of density_kg_m3 or mass_kg")
    volume = 4.0 / 3.0 * math.pi * r ** 3
    if mass_kg is None:
        rho = _pos("density_kg_m3", density_kg_m3)
        m = volume * rho
    else:
        m = _pos("mass_kg", mass_kg)
        rho = m / volume
    gm = G * m
    return {"radius_m": r, "density_kg_m3": rho, "volume_m3": volume, "mass_kg": m, "gm_m3_s2": gm,
            "surface_gravity_m_s2": gm / r ** 2, "escape_speed_m_s": math.sqrt(2 * gm / r),
            "circular_speed_m_s": math.sqrt(gm / r),
            "circular_period_h": 2 * math.pi * math.sqrt(r ** 3 / gm) / 3600.0}


def rotation(radius_m: float, gm: float, period_h: float, latitude_deg: float = 0.0) -> dict:
    r, gm, p = _pos("radius_m", radius_m), _pos("gm", gm), _pos("rotation_period_h", period_h)
    if not -90.0 <= latitude_deg <= 90.0:
        raise InputError("latitude_deg must be within [-90, 90]")
    omega = 2 * math.pi / (p * 3600.0)
    g = gm / r ** 2
    phi = math.radians(latitude_deg)
    a_eq = omega ** 2 * r
    a_rad = a_eq * math.cos(phi) ** 2           # outward component along the local radial
    a_tan = a_eq * math.cos(phi) * math.sin(phi)  # component along the surface toward the equator
    net = g - a_rad
    return {"omega_rad_s": omega, "centrifugal_equator_m_s2": a_eq, "centrifugal_radial_m_s2": a_rad,
            "centrifugal_tangential_m_s2": a_tan, "gravity_m_s2": g, "net_radial_gravity_m_s2": net,
            "centrifugal_to_gravity_ratio": a_rad / g,
            "critical_period_h": 2 * math.pi * math.sqrt(r ** 3 / gm) / 3600.0,
            "latitude_deg": latitude_deg}


def rotation_findings(rot: dict) -> list[dict]:
    out = []
    ratio = rot["centrifugal_to_gravity_ratio"]
    if rot["net_radial_gravity_m_s2"] <= 0:
        out.append(_f("rotation", "error", "net-gravity-outward",
                      "centrifugal acceleration exceeds gravity here: net surface acceleration points "
                      "outward; unanchored robot and loose regolith would lift off"))
    elif ratio > 0.5:
        out.append(_f("rotation", "warning", "rotation-dominant",
                      f"centrifugal term is {ratio:.0%} of gravity; use net gravity and check slopes"))
    elif ratio > 0.1:
        out.append(_f("rotation", "info", "rotation-significant",
                      f"centrifugal term is {ratio:.0%} of gravity; include it"))
    return out


def hop(speed: float, angle_deg: float, g: float) -> dict:
    v, g = _pos("speed", speed), _pos("g", g)
    if not 0.0 < angle_deg <= 90.0:
        raise InputError("angle_deg must be in (0, 90]")
    th = math.radians(angle_deg)
    vz, vx = v * math.sin(th), v * math.cos(th)
    t = 2 * vz / g
    return {"flight_time_s": t, "range_m": vx * t, "apex_height_m": vz ** 2 / (2 * g),
            "vertical_speed_m_s": vz, "horizontal_speed_m_s": vx, "g_used_m_s2": g}


def hop_findings(res: dict, speed: float, bp: dict | None, approx_ratio: float,
                 range_fraction: float) -> list[dict]:
    out = []
    if bp is None:
        out.append(_f("hop", "info", "no-body-check",
                      "gravity given directly; launch speed not compared with escape/orbital speed"))
        return out
    vesc, vcirc, r = bp["escape_speed_m_s"], bp["circular_speed_m_s"], bp["radius_m"]
    if speed >= vesc:
        out.append(_f("hop", "error", "exceeds-escape-speed",
                      f"launch speed {speed:.4g} m/s >= escape speed {vesc:.4g} m/s: robot would leave the body"))
    elif speed >= vcirc:
        out.append(_f("hop", "error", "exceeds-orbital-speed",
                      f"launch speed >= circular orbit speed {vcirc:.4g} m/s: flat-gravity hop model invalid"))
    elif speed / vcirc > approx_ratio:
        out.append(_f("hop", "warning", "flat-gravity-approx-questionable",
                      f"launch speed is {speed / vcirc:.0%} of circular speed (> {approx_ratio:.0%}): "
                      "curvature and gravity variation matter; use a central-force trajectory"))
    if speed < vcirc and res["range_m"] > range_fraction * r:
        out.append(_f("hop", "warning", "range-large-vs-radius",
                      f"range {res['range_m']:.3g} m exceeds {range_fraction:.0%} of body radius {r:.3g} m"))
    return out


def impulse(mass_kg: float, speed: float, angle_deg: float | None = None,
            push_time_s: float | None = None, g: float | None = None,
            friction_coefficient: float | None = None) -> dict:
    m, v = _pos("mass_kg", mass_kg), _pos("speed", speed)
    j = m * v
    out: dict = {"impulse_n_s": j, "kinetic_energy_j": 0.5 * m * v * v}
    if angle_deg is not None:
        if not 0.0 < angle_deg <= 90.0:
            raise InputError("angle_deg must be in (0, 90]")
        th = math.radians(angle_deg)
        out.update(impulse_vertical_n_s=j * math.sin(th), impulse_horizontal_n_s=j * math.cos(th))
    if push_time_s is not None:
        out["mean_force_n"] = j / _pos("push_time_s", push_time_s)
    if g is not None:
        g = _pos("g", g)
        out["weight_n"] = m * g
        if friction_coefficient is not None:
            mu = _pos("friction_coefficient", friction_coefficient, allow_zero=True)
            out.update(max_traction_n=mu * m * g, max_drive_accel_m_s2=mu * g)
        if "mean_force_n" in out:
            out["mean_force_to_weight_ratio"] = out["mean_force_n"] / out["weight_n"]
    elif friction_coefficient is not None:
        raise InputError("friction_coefficient needs gravity (body options or --g)")
    return out


def bounce(speed: float, restitution: float, threshold_speed: float, g: float) -> dict:
    v0, vt, g = _pos("speed", speed), _pos("threshold_speed", threshold_speed), _pos("g", g)
    e = restitution
    if isinstance(e, bool) or not isinstance(e, (int, float)) or not 0.0 < e < 1.0:
        raise InputError("restitution must satisfy 0 < e < 1")
    rebounds, heights, t, v = 0, [], 0.0, v0
    while True:
        v *= e  # rebound speed after the next contact
        if v < vt:
            break
        rebounds += 1
        if rebounds > MAX_BOUNCES:
            raise InputError("more than 1e6 rebounds; restitution too close to 1 for this threshold")
        t += 2 * v / g
        if len(heights) < 20:
            heights.append(v * v / (2 * g))
    return {"rebounds_above_threshold": rebounds, "contacts_to_settle": rebounds + 1,
            "time_to_settle_s": t, "first_rebound_speed_m_s": e * v0,
            "rebound_heights_m_first20": heights,
            "infinite_series_time_s": 2 * v0 * e / (g * (1 - e)), "g_used_m_s2": g}


# ----------------------------------------------------------------------------- dispatch
def _body_from(params: dict) -> tuple[dict | None, dict, list[str]]:
    """Return (body params or None, preset info, notes)."""
    notes: list[str] = []
    preset = params.get("preset")
    info: dict = {}
    if preset:
        if preset not in PRESETS:
            raise InputError(f"unknown preset '{preset}' (known: {sorted(PRESETS)})")
        info = dict(PRESETS[preset])
        notes.append(info["label"])
        bp = body(info["radius_m"], info["density_kg_m3"])
        if params.get("rotation_period_h") is None:
            params = dict(params, rotation_period_h=info["rotation_period_h"])
        return bp, params, notes
    if params.get("radius_m") is not None:
        return body(params["radius_m"], params.get("density_kg_m3"), params.get("mass_kg_body")), params, notes
    return None, params, notes


def run(command: str, params: dict) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    findings: list[dict] = []
    bp, params, notes = _body_from(params)
    assumptions = ["homogeneous sphere, point-mass surface gravity", f"G = {G} m^3 kg^-1 s^-2 ({G_SOURCE})"]
    results: dict = {}
    g_eff = None
    rot = None
    if bp is not None:
        g_eff = bp["surface_gravity_m_s2"]
        if params.get("rotation_period_h") is not None:
            rot = rotation(bp["radius_m"], bp["gm_m3_s2"], params["rotation_period_h"],
                           params.get("latitude_deg", 0.0))
            findings += rotation_findings(rot)
            g_eff = rot["net_radial_gravity_m_s2"]
    elif "g" in params:
        g_eff = _pos("g", params["g"])
        assumptions.append("gravity supplied directly; no body/rotation checks")
        if "rotation_period_h" in params:
            raise InputError("rotation_period_h needs body options (radius and density/mass or preset)")

    if command == "body":
        if bp is None:
            raise InputError("body needs --radius-m with --density/--mass-kg, or --preset")
        results = {"body": bp}
        if rot:
            results["rotation"] = rot
    elif command == "rotation":
        if bp is None or rot is None:
            raise InputError("rotation needs body options and --rotation-period-h")
        results = {"body": bp, "rotation": rot}
    elif command in ("hop", "bounce"):
        if g_eff is None:
            raise InputError(f"{command} needs body options or --g")
        if g_eff <= 0:
            results = {"rotation": rot} if rot else {}
            findings.append(_f(command, "error", "no-ballistic-solution",
                               "net gravity is not inward; ballistic flight/settling undefined"))
        elif command == "hop":
            results = hop(params.get("speed"), params.get("angle_deg", 45.0), g_eff)
            findings += hop_findings(results, params["speed"], bp,
                                     params.get("approx_ratio", DEFAULT_APPROX_RATIO),
                                     params.get("range_fraction", DEFAULT_RANGE_FRACTION))
            assumptions.append("flat, uniform gravity; no Coriolis; launch and landing at the same level")
        else:
            results = bounce(params.get("speed"), params.get("restitution"),
                             params.get("threshold_speed"), g_eff)
            assumptions.append("vertical bounces, constant restitution, level rigid surface")
            if bp is not None and results["first_rebound_speed_m_s"] >= bp["escape_speed_m_s"]:
                findings.append(_f("bounce", "error", "rebound-exceeds-escape-speed",
                                   "first rebound speed exceeds escape speed"))
            elif bp is not None and results["first_rebound_speed_m_s"] >= bp["circular_speed_m_s"]:
                findings.append(_f("bounce", "error", "rebound-exceeds-orbital-speed",
                                   "first rebound speed exceeds circular orbit speed; flat model invalid"))
        if rot is not None and g_eff > 0:
            assumptions.append("gravity reduced by equatorial-plane centrifugal term at given latitude")
    elif command == "impulse":
        results = impulse(params.get("mass_kg"), params.get("speed"), params.get("angle_deg"),
                          params.get("push_time_s"), g_eff, params.get("friction_coefficient"))
        if bp is not None and params["speed"] >= bp["escape_speed_m_s"]:
            findings.append(_f("impulse", "error", "exceeds-escape-speed",
                               "imparted speed exceeds escape speed of the body"))
        if results.get("mean_force_to_weight_ratio", 0) > 1:
            findings.append(_f("impulse", "info", "force-exceeds-weight",
                               "mean push force exceeds local weight: reaction from the surface or "
                               "anchoring is needed to apply it without lifting off early"))
    else:
        raise InputError(f"unknown command '{command}'")
    passed = not any(f["severity"] == "error" for f in findings)
    return {"command": command, "inputs": params, "results": results, "assumptions": assumptions,
            "notes": notes, "constants": {"G_m3_kg_s2": G, "G_source": G_SOURCE},
            "findings": findings, "passed": passed}


def run_batch(cases: object) -> dict:
    if not isinstance(cases, dict) or not isinstance(cases.get("cases"), list) or not cases["cases"]:
        raise InputError("batch file must be {\"cases\": [ {\"id\", \"command\", \"params\"}, ... ]}")
    out = []
    for i, c in enumerate(cases["cases"]):
        if not isinstance(c, dict) or not isinstance(c.get("params", {}), dict):
            raise InputError(f"case {i} malformed")
        cid = str(c.get("id", f"case-{i}"))
        try:
            res = run(str(c.get("command", "")), dict(c.get("params", {})))
        except InputError as exc:
            raise InputError(f"case {cid}: {exc}") from exc
        for f in res["findings"]:
            f["id"] = f"{cid}:{f['id']}"
        out.append({"id": cid, **res})
    findings = [f for r in out for f in r["findings"]]
    return {"command": "batch", "cases": out, "findings": findings,
            "passed": not any(f["severity"] == "error" for f in findings),
            "constants": {"G_m3_kg_s2": G, "G_source": G_SOURCE}}


# ----------------------------------------------------------------------------- CLI
def _add_body(p: argparse.ArgumentParser, allow_g: bool = True) -> None:
    p.add_argument("--preset", choices=sorted(PRESETS))
    p.add_argument("--radius-m", type=float)
    p.add_argument("--density", dest="density_kg_m3", type=float, help="bulk density kg/m^3")
    p.add_argument("--body-mass-kg", dest="mass_kg_body", type=float, help="body mass kg (instead of density)")
    p.add_argument("--rotation-period-h", type=float)
    p.add_argument("--latitude-deg", type=float)
    if allow_g:
        p.add_argument("--g", type=float, help="surface gravity m/s^2 (instead of body options)")
    p.add_argument("--json", action="store_true")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Low-gravity small-body mobility calculator.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("body", help="gravity, escape and orbital speed of a spherical body")
    _add_body(b, allow_g=False)
    h = sub.add_parser("hop", help="ballistic hop in uniform gravity")
    h.add_argument("--speed", type=float, required=True)
    h.add_argument("--angle-deg", type=float, default=45.0)
    h.add_argument("--approx-ratio", type=float, default=DEFAULT_APPROX_RATIO)
    h.add_argument("--range-fraction", type=float, default=DEFAULT_RANGE_FRACTION)
    _add_body(h)
    i = sub.add_parser("impulse", help="take-off impulse, force and traction limits")
    i.add_argument("--mass-kg", type=float, required=True, help="robot mass kg")
    i.add_argument("--speed", type=float, required=True)
    i.add_argument("--angle-deg", type=float)
    i.add_argument("--push-time-s", type=float)
    i.add_argument("--friction-coefficient", type=float)
    _add_body(i)
    bo = sub.add_parser("bounce", help="settling with coefficient of restitution")
    bo.add_argument("--speed", type=float, required=True, help="first impact (normal) speed m/s")
    bo.add_argument("--restitution", type=float, required=True)
    bo.add_argument("--threshold-speed", type=float, required=True)
    _add_body(bo)
    r = sub.add_parser("rotation", help="centrifugal effect and net gravity")
    _add_body(r, allow_g=False)
    bt = sub.add_parser("batch", help="run a JSON list of cases")
    bt.add_argument("cases", type=Path)
    bt.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "batch":
            res = run_batch(json.loads(args.cases.read_text(encoding="utf-8")))
        else:
            params = {k: v for k, v in vars(args).items() if k not in ("cmd", "json")}
            res = run(args.cmd, params)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "passed": False}))
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    res["scope"] = SCOPE
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(json.dumps({k: v for k, v in res.items() if k not in ("findings", "scope")}, indent=2))
        for f in res["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<22} {f['rule']:<34} {f['message']}")
        print(f"\n{'PASS' if res['passed'] else 'FAIL'}")
        print(SCOPE)
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
