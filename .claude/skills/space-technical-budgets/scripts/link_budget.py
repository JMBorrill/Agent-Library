#!/usr/bin/env python3
"""Radio link budget: free-space path loss, EIRP, G/T, C/N0, Eb/N0 and/or received power, and margin
versus the required value and a programme-supplied minimum margin. Every quantity carries a unit,
which is validated (and converted where unambiguous) before use.

Usage:
  link_budget.py evaluate link.json [--json]
  link_budget.py fspl --frequency-hz 2.4e9 --distance-m 1000 [--json]

Equations (standard radio-engineering relations, stated here so they can be checked):
  lambda = c / f,  c = 299 792 458 m/s
  FSPL [dB] = 20 log10(4 pi d / lambda)
  EIRP [dBW] = P_tx [dBW] + G_tx [dBi] - L_tx [dB]
  C/N0 [dBHz] = EIRP - FSPL - sum(other losses) + G/T [dB/K] - 10 log10(k),  k = 1.380649e-23 J/K
  Eb/N0 [dB] = C/N0 - 10 log10(R_b [bit/s]);  margin = Eb/N0 - required Eb/N0 - implementation loss
  P_rx [dBm] = EIRP + 30 - FSPL - sum(other losses) + G_rx - L_rx;  margin = P_rx - sensitivity
Exit codes: 0 margins meet the supplied minimum, 1 negative or insufficient margin, 2 invalid input.

Scope: idealised line-of-sight link with the losses you list; no multipath, fading statistics,
modulation/coding curves or interference. Analysis aid only; margins need programme sign-off.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

C = 299_792_458.0
K_BOLTZMANN = 1.380649e-23
K_DB = 10 * math.log10(K_BOLTZMANN)  # about -228.6 dBW/(K*Hz)
SCOPE = ("Scope: idealised free-space link with listed losses only; analysis aid — required margins are "
         "programme-supplied proposals needing human sign-off.")

FREQ = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9}
DIST = {"m": 1.0, "km": 1e3, "AU": 1.495978707e11}
RATE = {"bps": 1.0, "kbps": 1e3, "Mbps": 1e6, "Gbps": 1e9}


class InputError(ValueError):
    """Invalid or unit-inconsistent link input (exit 2)."""


def fspl_db(frequency_hz: float, distance_m: float) -> float:
    if frequency_hz <= 0 or distance_m <= 0:
        raise InputError("frequency and distance must be positive")
    lam = C / frequency_hz
    return 20 * math.log10(4 * math.pi * distance_m / lam)


def _q(data: dict, key: str, required: bool = True) -> dict | None:
    v = data.get(key)
    if v is None:
        if required:
            raise InputError(f"missing '{key}'")
        return None
    if not isinstance(v, dict) or "value" not in v or "unit" not in v:
        raise InputError(f"'{key}' must be an object {{\"value\": number, \"unit\": string}}")
    val = v["value"]
    if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(val):
        raise InputError(f"'{key}.value' must be a finite number")
    return v


def _scaled(v: dict, key: str, table: dict, positive: bool = True) -> float:
    if v["unit"] not in table:
        raise InputError(f"'{key}' unit '{v['unit']}' not in {sorted(table)}")
    x = v["value"] * table[v["unit"]]
    if positive and x <= 0:
        raise InputError(f"'{key}' must be positive")
    return x


def _db(v: dict | None, key: str, allowed: tuple[str, ...], loss: bool = False) -> float:
    if v is None:
        return 0.0
    if v["unit"] not in allowed:
        raise InputError(f"'{key}' unit '{v['unit']}' must be one of {list(allowed)}")
    if loss and v["value"] < 0:
        raise InputError(f"'{key}' is a loss and must be >= 0 dB (enter gains separately)")
    return float(v["value"])


def power_dbw(v: dict, key: str) -> float:
    u, x = v["unit"], v["value"]
    if u == "dBW":
        return x
    if u == "dBm":
        return x - 30
    if u in ("W", "mW"):
        watts = x * (1e-3 if u == "mW" else 1.0)
        if watts <= 0:
            raise InputError(f"'{key}' must be positive in linear units")
        return 10 * math.log10(watts)
    raise InputError(f"'{key}' unit '{u}' must be dBW, dBm, W or mW")


def evaluate(link: dict) -> dict:
    if not isinstance(link, dict):
        raise InputError("link file must be a JSON object")
    f_hz = _scaled(_q(link, "frequency"), "frequency", FREQ)
    d_m = _scaled(_q(link, "distance"), "distance", DIST)
    fspl = fspl_db(f_hz, d_m)
    eirp_q = _q(link, "eirp", required=False)
    if eirp_q is not None:
        eirp = power_dbw(eirp_q, "eirp")
        if eirp_q["unit"] in ("W", "mW"):
            raise InputError("'eirp' must be given in dBW or dBm")
        ptx = gtx = ltx = None
    else:
        ptx = power_dbw(_q(link, "tx_power"), "tx_power")
        gtx = _db(_q(link, "tx_antenna_gain"), "tx_antenna_gain", ("dBi",))
        ltx = _db(_q(link, "tx_losses", required=False), "tx_losses", ("dB",), loss=True)
        eirp = ptx + gtx - ltx
    other = link.get("other_losses", [])
    if not isinstance(other, list):
        raise InputError("'other_losses' must be a list")
    other_total = 0.0
    for i, item in enumerate(other):
        if not isinstance(item, dict):
            raise InputError(f"other_losses[{i}] must be an object")
        name = item.get("name", f"other_losses[{i}]")
        other_total += _db(_q({"x": item}, "x"), str(name), ("dB",), loss=True)
    req_margin = _db(_q(link, "required_margin", required=False), "required_margin", ("dB",), loss=True)

    out: dict = {"name": link.get("name", ""), "frequency_hz": f_hz, "distance_m": d_m,
                 "wavelength_m": C / f_hz, "fspl_db": fspl, "eirp_dbw": eirp,
                 "tx_power_dbw": ptx, "other_losses_db": other_total,
                 "required_margin_db": req_margin}
    findings: list[dict] = []
    checks = 0

    gt_q = _q(link, "rx_gt", required=False)
    if gt_q is not None:
        gt = _db(gt_q, "rx_gt", ("dB/K",))
        cn0 = eirp - fspl - other_total + gt - K_DB
        out.update(rx_gt_db_per_k=gt, c_n0_dbhz=cn0)
        rate_q = _q(link, "data_rate", required=False)
        if rate_q is not None:
            if rate_q["unit"] == "dBHz":
                rate_db = rate_q["value"]
            else:
                rate_db = 10 * math.log10(_scaled(rate_q, "data_rate", RATE))
            ebn0 = cn0 - rate_db
            out.update(data_rate_dbhz=rate_db, eb_n0_db=ebn0)
            req_q = _q(link, "required_eb_n0", required=False)
            if req_q is not None:
                req = _db(req_q, "required_eb_n0", ("dB",))
                impl = _db(_q(link, "implementation_loss", required=False), "implementation_loss",
                           ("dB",), loss=True)
                margin = ebn0 - req - impl
                out.update(required_eb_n0_db=req, implementation_loss_db=impl, eb_n0_margin_db=margin)
                checks += 1
                findings += _margin_findings("eb-n0", margin, req_margin)
    prx_inputs = _q(link, "rx_antenna_gain", required=False)
    if prx_inputs is not None:
        grx = _db(prx_inputs, "rx_antenna_gain", ("dBi",))
        lrx = _db(_q(link, "rx_losses", required=False), "rx_losses", ("dB",), loss=True)
        prx_dbm = eirp + 30 - fspl - other_total + grx - lrx
        out.update(rx_antenna_gain_dbi=grx, rx_losses_db=lrx, rx_power_dbm=prx_dbm)
        sens_q = _q(link, "rx_sensitivity", required=False)
        if sens_q is not None:
            sens = power_dbw(sens_q, "rx_sensitivity") + 30
            margin = prx_dbm - sens
            out.update(rx_sensitivity_dbm=sens, rx_power_margin_db=margin)
            checks += 1
            findings += _margin_findings("rx-power", margin, req_margin)
    if checks == 0:
        findings.append({"id": "link", "severity": "warning", "rule": "no-margin-computed",
                         "message": "give rx_gt+data_rate+required_eb_n0 and/or rx_antenna_gain+rx_sensitivity"})
    if req_margin == 0:
        findings.append({"id": "link", "severity": "warning", "rule": "no-required-margin",
                         "message": "no programme-supplied required_margin; only sign of margin checked"})
    if f_hz < 1e6 or f_hz > 3e11:
        findings.append({"id": "link", "severity": "warning", "rule": "frequency-out-of-range",
                         "message": "frequency outside 1 MHz-300 GHz; check units"})
    out = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()}
    return out | {"findings": findings}


def _margin_findings(kind: str, margin: float, req: float) -> list[dict]:
    if margin < 0:
        return [{"id": kind, "severity": "error", "rule": "negative-link-margin",
                 "message": f"{kind} margin {margin:.2f} dB is negative"}]
    if margin < req:
        return [{"id": kind, "severity": "error", "rule": "link-margin-below-policy",
                 "message": f"{kind} margin {margin:.2f} dB < required {req:.2f} dB"}]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Radio link budget with unit validation.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluate", help="evaluate a link JSON file")
    e.add_argument("link", type=Path)
    e.add_argument("--json", action="store_true")
    f = sub.add_parser("fspl", help="free-space path loss only")
    f.add_argument("--frequency-hz", type=float, required=True)
    f.add_argument("--distance-m", type=float, required=True)
    f.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "fspl":
            res = {"frequency_hz": args.frequency_hz, "distance_m": args.distance_m,
                   "fspl_db": round(fspl_db(args.frequency_hz, args.distance_m), 6), "findings": []}
        else:
            res = evaluate(json.loads(args.link.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"error": str(exc), "passed": False}))
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    failed = any(x["severity"] == "error" for x in res["findings"])
    res["passed"] = not failed
    res["scope"] = SCOPE
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        for k, v in res.items():
            if k not in ("findings", "scope", "passed") and v is not None:
                print(f"{k:<26} {v}")
        for x in res["findings"]:
            print(f"{x['severity'].upper():8} {x['id']:<10} {x['rule']:<26} {x['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}")
        print(SCOPE)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
