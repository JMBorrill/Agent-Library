"""HM Treasury Green Book (2026 edition) deterministic appraisal tools.

CLI: ``python -m agentlib greenbook <command>``

Commands
--------
``npv``            discounted costs/benefits, NPSV, BCR, RPSC per option, ranked
``real``           nominal -> real conversion with a user-supplied GDP deflator series
``switching``      switching values and +/- % sensitivity tables
``optimism-bias``  apply a user-supplied optimism bias percentage (with mitigation)
``check-case``     structural checker for a business case Markdown document
``params``         print the 2026 parameters (with citations) and what is NOT in the edition
``factors``        print the STPR (and health) discount factor table
``welfare-weight`` distributional welfare weight for a group (para 7.11)

All parameters come from ``catalog/green-book.json`` (extracted from the pinned
2026 PDF by ``scripts/extract/greenbook.py``). Values the 2026 text defers to
supplementary guidance (optimism bias percentages, gilt rate, GDP deflators...)
are never hard-coded: they must be passed in by the user.

Grader functions (``grade_*``) are used by ``evals/green-book-appraisal``.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

from agentlib.paths import load_catalog, repo_root

CATALOG_ID = "green-book"
SOURCE_ID = "treasury-green"
EDITION = "HM Treasury Green Book, 2026 edition"


class GreenBookError(ValueError):
    """Raised for invalid user input; the CLI prints it and exits with status 2."""


# ====================================================================== catalog
_CATALOG: dict | None = None


def catalog() -> dict:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = load_catalog(CATALOG_ID)
    return _CATALOG


def item(item_id: str) -> dict:
    for it in catalog()["items"]:
        if it["id"] == item_id:
            return it
    raise KeyError(item_id)


def cite(item_id: str) -> str:
    """Human-readable citation for a catalog item, e.g. ``Green Book 2026, para 6.54, PDF p.46 (printed p.40)``."""
    it = item(item_id)
    c = it["citation"]
    return f"Green Book 2026, {c.get('section', it['title'])}, PDF p.{c['pdf_page']} (printed p.{c['printed_page']})"


def param_cite(cit: dict) -> str:
    return f"Green Book 2026, {cit.get('section', '')}, PDF p.{cit['pdf_page']} (printed p.{cit['printed_page']})"


def parameters() -> dict:
    return catalog()["parameters"]


def stpr_bands() -> list[dict]:
    return [dict(b) for b in parameters()["stpr"]["bands"]]


def health_rate() -> float:
    return float(parameters()["health_discount_rate"]["rate"])


# ====================================================================== discounting
def _validate_bands(bands: list[dict]) -> None:
    if not bands:
        raise GreenBookError("discount schedule has no bands")
    expect = 1
    for i, b in enumerate(bands):
        if int(b["from_year"]) != expect:
            raise GreenBookError(f"discount band {i} starts at year {b['from_year']}, expected {expect}")
        if b.get("to_year") is None:
            if i != len(bands) - 1:
                raise GreenBookError("only the last discount band may be open-ended")
            return
        if int(b["to_year"]) < int(b["from_year"]):
            raise GreenBookError(f"discount band {i} ends before it starts")
        if float(b["rate"]) <= -1:
            raise GreenBookError("discount rate must be greater than -100%")
        expect = int(b["to_year"]) + 1
    raise GreenBookError("last discount band must be open-ended (to_year: null)")


def rate_for_year(year: int, bands: list[dict] | None = None) -> float:
    """The discount rate applying to the step from year-1 to ``year`` (year >= 1)."""
    bands = bands or stpr_bands()
    for b in bands:
        if year >= b["from_year"] and (b.get("to_year") is None or year <= b["to_year"]):
            return float(b["rate"])
    raise GreenBookError(f"no discount band covers year {year}")


def discount_factor(year: int, bands: list[dict] | None = None, flat_rate: float | None = None) -> float:
    """Discount factor for appraisal ``year`` (year 0 = 1.0).

    With the STPR schedule the factor compounds across bands:
    ``DF(t) = prod_{k=1..t} 1/(1+r_k)`` where ``r_k`` is the band rate for year k
    (Green Book 2026 para 6.54: 3.50% years 1-30, 3.00% years 31-75, 2.50% year 76 onwards).
    """
    if not isinstance(year, int) or isinstance(year, bool):
        raise GreenBookError(f"year must be an integer, got {year!r}")
    if year < 0:
        raise GreenBookError("negative appraisal years are not allowed: costs/benefits already incurred are sunk "
                             f"and must not be discounted retrospectively ({cite('discount.no-retrospective')})")
    if flat_rate is not None:
        if flat_rate <= -1:
            raise GreenBookError("discount rate must be greater than -100%")
        return (1.0 + flat_rate) ** -year
    bands = bands or stpr_bands()
    _validate_bands(bands)
    df = 1.0
    for b in bands:
        lo = int(b["from_year"])
        hi = year if b.get("to_year") is None else min(year, int(b["to_year"]))
        n = hi - lo + 1
        if n > 0:
            df *= (1.0 + float(b["rate"])) ** -n
        if b.get("to_year") is None or year <= int(b["to_year"]):
            break
    return df


def health_discount_factor(year: int, rate: float | None = None) -> float:
    """Health/life effects: a constant rate (1.5% in the 2026 edition, para 6.58) in every year."""
    return discount_factor(year, flat_rate=health_rate() if rate is None else rate)


# ====================================================================== cash-flow input
KIND_ALIASES = {"benefit": "benefit", "benefits": "benefit", "b": "benefit",
                "cost": "cost", "costs": "cost", "c": "cost"}
STREAM_ALIASES = {"": "standard", "standard": "standard", "std": "standard", "stpr": "standard",
                  "health": "health", "life": "health", "health/life": "health"}
BEARER_ALIASES = {"public": "public", "public sector": "public", "public-sector": "public",
                  "non-public": "non-public", "nonpublic": "non-public", "non public": "non-public",
                  "private": "non-public", "other": "non-public", "society": "non-public"}


@dataclass
class Flow:
    option: str
    item: str
    kind: str                     # benefit | cost
    values: dict[int, float]      # appraisal year -> real value
    stream: str = "standard"      # standard | health
    bearer: str | None = None     # public | non-public | None (costs only)


@dataclass
class Appraisal:
    flows: list[Flow]
    options: list[str]
    meta: dict = field(default_factory=dict)


def _num(value, where: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
    else:
        s = str(value).strip().replace(",", "").replace("£", "")
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        try:
            v = float(s)
        except ValueError:
            raise GreenBookError(f"{where}: not a number: {value!r}") from None
    if math.isnan(v) or math.isinf(v):
        raise GreenBookError(f"{where}: value must be finite")
    return v


def _year(value, base_year: int | None, calendar: bool, where: str) -> int:
    try:
        y = int(str(value).strip())
    except ValueError:
        raise GreenBookError(f"{where}: year must be an integer, got {value!r}") from None
    if calendar:
        if base_year is None:
            raise GreenBookError(f"{where}: calendar years need a base year (--base-year or base_year:)")
        y -= base_year
    if y < 0:
        raise GreenBookError(f"{where}: year is before year 0. Exclude sunk costs and do not discount "
                             f"retrospectively ({cite('shortlist.sunk-costs')}; {cite('discount.no-retrospective')})")
    return y


def _int_year(value, where: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise GreenBookError(f"{where}: year must be an integer (e.g. 2027, not a financial year like "
                             f"'2027/28'), got {value!r}") from None


def _norm_kind(v, where):
    k = KIND_ALIASES.get(str(v).strip().lower())
    if not k:
        raise GreenBookError(f"{where}: type must be 'benefit' or 'cost', got {v!r}")
    return k


def _norm_stream(v, where):
    s = STREAM_ALIASES.get(str(v or "").strip().lower())
    if not s:
        raise GreenBookError(f"{where}: stream must be 'standard' or 'health', got {v!r}")
    return s


def _norm_bearer(v, where):
    if v is None or str(v).strip() == "":
        return None
    b = BEARER_ALIASES.get(str(v).strip().lower())
    if not b:
        raise GreenBookError(f"{where}: bearer must be 'public' or 'non-public', got {v!r}")
    return b


def load_flows(path: str | Path, base_year: int | None = None) -> Appraisal:
    """Load real-terms annual flows from CSV (long format) or YAML/JSON.

    CSV columns: ``option``, ``year`` (appraisal year, 0 = year 0) *or* ``calendar_year``
    (needs ``base_year``), ``type`` (benefit|cost), ``value``; optional ``item``,
    ``stream`` (standard|health), ``bearer`` (public|non-public, for costs).

    YAML/JSON::

        base_year: 2026          # optional: calendar year of year 0
        price_year: 2026         # optional: label only (values must already be real)
        options:
          - name: Do minimum
            flows:
              - {item: Capex, type: cost, bearer: public, values: {0: 100, 1: 20}}
              - {item: QALYs, type: benefit, stream: health, values: [0, 5, 5, 5]}
    """
    p = Path(path)
    if not p.is_file():
        raise GreenBookError(f"file not found: {p}")
    text = p.read_text(encoding="utf-8-sig")
    flows: list[Flow] = []
    meta: dict = {}
    order: list[str] = []
    if p.suffix.lower() == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        cols = {c.strip().lower() for c in (reader.fieldnames or [])}
        need = {"option", "type", "value"}
        if not need <= cols or not ({"year", "calendar_year"} & cols):
            raise GreenBookError(f"{p.name}: CSV needs columns option, year (or calendar_year), type, value; "
                                 f"got {sorted(cols)}")
        calendar = "calendar_year" in cols and "year" not in cols
        index: dict[tuple, Flow] = {}
        for n, raw in enumerate(reader, start=2):
            row = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            if not any(row.values()):
                continue
            where = f"{p.name} line {n}"
            opt = row["option"]
            if not opt:
                raise GreenBookError(f"{where}: empty option name")
            kind = _norm_kind(row["type"], where)
            stream = _norm_stream(row.get("stream", ""), where)
            bearer = _norm_bearer(row.get("bearer"), where)
            item_name = row.get("item") or kind
            yr = _year(row["calendar_year"] if calendar else row["year"], base_year, calendar, where)
            val = _num(row["value"], where)
            key = (opt, item_name, kind, stream, bearer)
            f = index.get(key)
            if f is None:
                f = index[key] = Flow(opt, item_name, kind, {}, stream, bearer)
                flows.append(f)
            f.values[yr] = f.values.get(yr, 0.0) + val
            if opt not in order:
                order.append(opt)
    elif p.suffix.lower() in (".yaml", ".yml", ".json"):
        try:
            data = json.loads(text) if p.suffix.lower() == ".json" else yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise GreenBookError(f"{p.name}: cannot parse: {exc}") from None
        if not isinstance(data, dict) or not isinstance(data.get("options"), list) or not data["options"]:
            raise GreenBookError(f"{p.name}: expected a mapping with a non-empty 'options' list")
        base_year = base_year if base_year is not None else data.get("base_year")
        meta = {k: data[k] for k in ("base_year", "price_year", "title", "units") if k in data}
        for oi, opt in enumerate(data["options"]):
            if not isinstance(opt, dict):
                raise GreenBookError(f"{p.name}: option {oi} must be a mapping with 'name' and 'flows', "
                                     f"got {opt!r}")
            name = str(opt.get("name") or "").strip()
            if not name:
                raise GreenBookError(f"{p.name}: option {oi} has no name")
            order.append(name)
            opt_flows = opt.get("flows") or []
            if not isinstance(opt_flows, list):
                raise GreenBookError(f"{p.name}: option '{name}': 'flows' must be a list")
            for fi, fl in enumerate(opt_flows):
                where = f"{p.name}: option '{name}' flow {fi}"
                if not isinstance(fl, dict):
                    raise GreenBookError(f"{where}: flow must be a mapping (item, type, values), got {fl!r}")
                kind = _norm_kind(fl.get("type"), where)
                vals = fl.get("values")
                calendar = bool(fl.get("calendar_years", False))
                if isinstance(vals, list):
                    values = {i: _num(v, where) for i, v in enumerate(vals)}
                elif isinstance(vals, dict):
                    values = {}
                    for k, v in vals.items():
                        values[_year(k, base_year, calendar, where)] = _num(v, where)
                else:
                    raise GreenBookError(f"{where}: 'values' must be a list or a year->value mapping")
                flows.append(Flow(name, str(fl.get("item") or kind), kind, values,
                                  _norm_stream(fl.get("stream", ""), where), _norm_bearer(fl.get("bearer"), where)))
    else:
        raise GreenBookError(f"{p.name}: unsupported file type (use .csv, .yaml, .yml or .json)")
    if not flows:
        raise GreenBookError(f"{p.name}: no cash flows found")
    if len(set(order)) != len(order):
        raise GreenBookError(f"{p.name}: duplicate option names")
    if base_year is not None:
        meta.setdefault("base_year", base_year)
    return Appraisal(flows, order, meta)


# ====================================================================== appraisal
@dataclass
class OptionResult:
    option: str
    pvb: float
    pvc: float
    pvc_public: float | None
    pvc_non_public: float | None
    npsv: float
    bcr: float | None
    rpsc: float | None
    undiscounted_benefits: float
    undiscounted_costs: float
    items: list[dict]
    rank: int = 0
    npsv_vs_bau: float | None = None
    pvc_gilt: float | None = None

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Settings:
    flat_rate: float | None = None          # custom flat rate replacing the STPR
    health_rate: float | None = None        # override for the health stream
    separate_health: bool = True            # discount 'health' stream at the health rate
    gilt_rate: float | None = None          # Annex A costs-only sensitivity
    bau: str | None = None

    def describe(self) -> list[str]:
        p = parameters()
        lines = []
        if self.flat_rate is None:
            b = p["stpr"]["bands"]
            lines.append(f"Standard discount rate: STPR {b[0]['rate']:.2%} years {b[0]['from_year']}-{b[0]['to_year']}, "
                         f"{b[1]['rate']:.2%} years {b[1]['from_year']}-{b[1]['to_year']}, {b[2]['rate']:.2%} year "
                         f"{b[2]['from_year']} onwards; year 0 undiscounted; factors compound across bands "
                         f"({param_cite(p['stpr']['citation'])}).")
        else:
            lines.append(f"Standard discount rate: CUSTOM flat {self.flat_rate:.2%} supplied by the user "
                         f"(not the Green Book STPR; {param_cite(p['stpr']['citation'])} states the STPR).")
        if self.separate_health:
            hr = health_rate() if self.health_rate is None else self.health_rate
            src = (param_cite(p['health_discount_rate']['citation']) if self.health_rate is None
                   else "user-supplied override")
            lines.append(f"Health/life effects (stream=health): {hr:.2%} in every year ({src}).")
        else:
            lines.append("Health/life effects: discounted at the standard rate (separate health rate disabled by user).")
        lines.append(f"Values must be in real terms (general inflation removed with the GDP deflator) before "
                     f"discounting ({cite('discount.real-only')}).")
        if self.gilt_rate is not None:
            lines.append(f"Additional costs-only sensitivity at the user-supplied risk-free real gilt rate "
                         f"{self.gilt_rate:.2%} ({cite('pf.gilt-sensitivity')}).")
        return lines


def _factor(flow: Flow, year: int, s: Settings) -> float:
    if flow.stream == "health" and s.separate_health:
        return health_discount_factor(year, s.health_rate)
    return discount_factor(year, flat_rate=s.flat_rate)


def appraise(app: Appraisal, settings: Settings | None = None) -> list[OptionResult]:
    s = settings or Settings()
    results = []
    for opt in app.options:
        pvb = pvc = undb = undc = 0.0
        pub = nonpub = 0.0
        bearer_known = True
        has_cost = False
        pvc_gilt = 0.0
        items = []
        for f in (fl for fl in app.flows if fl.option == opt):
            pv = sum(v * _factor(f, y, s) for y, v in f.values.items())
            und = sum(f.values.values())
            items.append({"item": f.item, "type": f.kind, "stream": f.stream, "bearer": f.bearer,
                          "undiscounted": und, "pv": pv})
            if f.kind == "benefit":
                pvb += pv
                undb += und
            else:
                has_cost = True
                pvc += pv
                undc += und
                if s.gilt_rate is not None:
                    pvc_gilt += sum(v * discount_factor(y, flat_rate=s.gilt_rate) for y, v in f.values.items())
                if f.bearer == "public":
                    pub += pv
                elif f.bearer == "non-public":
                    nonpub += pv
                else:
                    bearer_known = False
        npsv = pvb - pvc
        bcr = pvb / pvc if pvc > 0 else None
        rpsc = None
        if has_cost and bearer_known and pub > 0:
            rpsc = (pvb - nonpub) / pub
        results.append(OptionResult(opt, pvb, pvc, pub if (has_cost and bearer_known) else None,
                                    nonpub if (has_cost and bearer_known) else None, npsv, bcr, rpsc, undb, undc,
                                    items, pvc_gilt=pvc_gilt if s.gilt_rate is not None else None))
    ranked = sorted(results, key=lambda r: -r.npsv)
    for i, r in enumerate(ranked, start=1):
        r.rank = i
    if s.bau:
        base = next((r for r in results if r.option.lower() == s.bau.lower()), None)
        if base is None:
            raise GreenBookError(f"--bau option '{s.bau}' not found; options are {app.options}")
        for r in results:
            r.npsv_vs_bau = r.npsv - base.npsv
    return ranked


# ====================================================================== formatting
def _fmt(v: float | None, dp: int = 2) -> str:
    if v is None:
        return "n/a"
    return f"{v:,.{dp}f}"


def npv_report(results: list[OptionResult], settings: Settings, meta: dict | None = None) -> dict:
    meta = meta or {}
    return {
        "source": SOURCE_ID, "edition": EDITION, "catalog": CATALOG_ID,
        "meta": meta,
        "parameters_used": settings.describe(),
        "options": [r.as_dict() for r in results],
        "preferred_by_npsv": results[0].option if results else None,
        "notes": [
            f"Ranking by NPSV is an initial ranking only; the preferred option needs a balanced value-for-money "
            f"judgement including unmonetisable impacts, risk, public sector financial impact and distribution "
            f"({cite('metrics.ranking-not-sufficient')}).",
            f"Do not apply BCR thresholds ({cite('metrics.no-bcr-thresholds')}).",
            f"NPSV = PVB - PVC; BCR = PVB / PVC; RPSC = (PVB - PVC non-public) / PVC public ({cite('metrics.npsv')}).",
            f"Present options in absolute terms rather than normalising BAU to zero ({cite('rationale.bau-absolute')}).",
        ],
    }


def npv_markdown(report: dict) -> str:
    out = ["# Economic appraisal summary (Green Book 2026)", ""]
    m = report.get("meta") or {}
    if m:
        out.append("; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in m.items()))
        out.append("")
    out += ["## Parameters used", ""] + [f"- {p}" for p in report["parameters_used"]] + [""]
    out += ["## Results (ranked by NPSV)", ""]
    has_bau = any(o["npsv_vs_bau"] is not None for o in report["options"])
    has_gilt = any(o["pvc_gilt"] is not None for o in report["options"])
    head = ["Rank", "Option", "PV benefits (PVB)", "PV costs (PVC)", "NPSV", "BCR", "RPSC"]
    if has_bau:
        head.append("NPSV vs BAU")
    if has_gilt:
        head.append("PVC at gilt rate")
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    for o in report["options"]:
        row = [str(o["rank"]), o["option"], _fmt(o["pvb"]), _fmt(o["pvc"]), _fmt(o["npsv"]), _fmt(o["bcr"]),
               _fmt(o["rpsc"])]
        if has_bau:
            row.append(_fmt(o["npsv_vs_bau"]))
        if has_gilt:
            row.append(_fmt(o["pvc_gilt"]))
        out.append("| " + " | ".join(row) + " |")
    out += ["", "## Present value by item", "", "| Option | Item | Type | Stream | Bearer | Undiscounted | Present value |",
            "|---|---|---|---|---|---|---|"]
    for o in report["options"]:
        for it in o["items"]:
            out.append(f"| {o['option']} | {it['item']} | {it['type']} | {it['stream']} | {it['bearer'] or '-'} | "
                       f"{_fmt(it['undiscounted'])} | {_fmt(it['pv'])} |")
    out += ["", "## Notes", ""] + [f"- {n}" for n in report["notes"]]
    return "\n".join(out) + "\n"


# ====================================================================== switching values / sensitivity
def switching(results: list[OptionResult], pcts: Iterable[float] = (-20, -10, 10, 20)) -> dict:
    pcts = list(pcts)
    if not results:
        raise GreenBookError("no options to analyse")
    per_option = []
    for r in results:
        sv = {"option": r.option, "npsv": r.npsv,
              "benefits_change_pct_to_zero_npsv": (-r.npsv / r.pvb * 100) if r.pvb else None,
              "costs_change_pct_to_zero_npsv": (r.npsv / r.pvc * 100) if r.pvc else None,
              "items": []}
        for it in r.items:
            if not it["pv"]:
                continue
            change = (-r.npsv / it["pv"]) if it["type"] == "benefit" else (r.npsv / it["pv"])
            sv["items"].append({"item": it["item"], "type": it["type"], "pv": it["pv"],
                                "change_pct_to_zero_npsv": change * 100,
                                "switching_pv": it["pv"] * (1 + change)})
        per_option.append(sv)
    preferred = results[0]
    ranking = []
    for other in results[1:]:
        gap = preferred.npsv - other.npsv
        ranking.append({"preferred": preferred.option, "challenger": other.option, "npsv_gap": gap,
                        "preferred_benefits_change_pct": (-gap / preferred.pvb * 100) if preferred.pvb else None,
                        "preferred_costs_change_pct": (gap / preferred.pvc * 100) if preferred.pvc else None})
    sens = []
    for p in pcts:
        f = 1 + p / 100
        row_b = {r.option: r.pvb * f - r.pvc for r in results}
        row_c = {r.option: r.pvb - r.pvc * f for r in results}
        sens.append({"pct": p, "benefits_scaled_npsv": row_b, "costs_scaled_npsv": row_c,
                     "top_if_benefits_scaled": max(row_b, key=row_b.get),
                     "top_if_costs_scaled": max(row_c, key=row_c.get)})
    return {"source": SOURCE_ID, "edition": EDITION, "preferred_by_npsv": preferred.option,
            "switching_values": per_option, "ranking_switches": ranking, "sensitivity": sens,
            "notes": [f"Switching value: the change in a key variable at which an option stops being value for "
                      f"money, e.g. NPSV turns negative or the preferred option is overtaken "
                      f"({cite('metrics.switching-values')}).",
                      f"At minimum report sensitivity analysis and switching values for the preferred option "
                      f"({cite('metrics.sensitivity')})."]}


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v:+.1f}%"


def switching_markdown(rep: dict) -> str:
    out = ["# Switching values and sensitivity (Green Book 2026)", "",
           f"Preferred option by NPSV: **{rep['preferred_by_npsv']}**", "",
           "## Switching values to NPSV = 0", "",
           "| Option | NPSV | Change in total benefits | Change in total costs |", "|---|---|---|---|"]
    for sv in rep["switching_values"]:
        out.append(f"| {sv['option']} | {_fmt(sv['npsv'])} | {_pct(sv['benefits_change_pct_to_zero_npsv'])} | "
                   f"{_pct(sv['costs_change_pct_to_zero_npsv'])} |")
    out += ["", "### By item", "", "| Option | Item | Type | PV | Change to NPSV = 0 | Switching PV |",
            "|---|---|---|---|---|---|"]
    for sv in rep["switching_values"]:
        for it in sv["items"]:
            out.append(f"| {sv['option']} | {it['item']} | {it['type']} | {_fmt(it['pv'])} | "
                       f"{_pct(it['change_pct_to_zero_npsv'])} | {_fmt(it['switching_pv'])} |")
    if rep["ranking_switches"]:
        out += ["", "## Ranking switches (preferred option overtaken)", "",
                "| Preferred | Challenger | NPSV gap | Preferred benefits change | Preferred costs change |",
                "|---|---|---|---|---|"]
        for r in rep["ranking_switches"]:
            out.append(f"| {r['preferred']} | {r['challenger']} | {_fmt(r['npsv_gap'])} | "
                       f"{_pct(r['preferred_benefits_change_pct'])} | {_pct(r['preferred_costs_change_pct'])} |")
    options = [sv["option"] for sv in rep["switching_values"]]
    for key, label in (("benefits_scaled_npsv", "benefits"), ("costs_scaled_npsv", "costs")):
        out += ["", f"## Sensitivity: NPSV when all {label} change by", "",
                "| Change | " + " | ".join(options) + " | Top option |", "|---|" + "---|" * (len(options) + 1)]
        for row in rep["sensitivity"]:
            vals = row[key]
            top = row["top_if_benefits_scaled" if label == "benefits" else "top_if_costs_scaled"]
            out.append(f"| {row['pct']:+g}% | " + " | ".join(_fmt(vals[o]) for o in options) + f" | {top} |")
    out += ["", "## Notes", ""] + [f"- {n}" for n in rep["notes"]]
    return "\n".join(out) + "\n"


# ====================================================================== optimism bias
def optimism_bias(capex: float, upper_pct: float, mitigation_pct: float = 0.0, *,
                  opex: float | None = None, opex_upper_pct: float | None = None,
                  benefits: float | None = None, benefits_pct: float | None = None,
                  duration: float | None = None, duration_upper_pct: float | None = None,
                  source: str | None = None) -> dict:
    """Apply user-supplied optimism bias percentages.

    adjustment % = upper % x (1 - mitigation % / 100); costs and durations are increased,
    benefits decreased. The 2026 Green Book gives NO percentages: they come from the
    organisation's historical forecast errors or the supplementary guidance (paras 6.80-6.81).
    """
    def chk(name, v, lo=0.0, hi=None):
        if v is None:
            return
        if math.isnan(v) or math.isinf(v):
            raise GreenBookError(f"{name} must be finite")
        if v < lo or (hi is not None and v > hi):
            raise GreenBookError(f"{name} must be between {lo} and {hi if hi is not None else 'inf'}, got {v}")

    chk("capex", capex)
    chk("upper-pct", upper_pct)
    chk("mitigation", mitigation_pct, 0, 100)
    chk("opex", opex); chk("opex-upper-pct", opex_upper_pct)
    chk("benefits", benefits); chk("benefits-pct", benefits_pct, 0, 100)
    chk("duration", duration); chk("duration-upper-pct", duration_upper_pct)
    keep = 1 - mitigation_pct / 100

    def adj(base, pct, sign=1):
        applied = pct * keep
        return {"base": base, "upper_pct": pct, "applied_pct": applied,
                "adjusted": base * (1 + sign * applied / 100), "adjustment": base * sign * applied / 100}

    res = {"source": SOURCE_ID, "edition": EDITION, "mitigation_pct": mitigation_pct,
           "capex": adj(capex, upper_pct)}
    if opex is not None:
        if opex_upper_pct is None:
            raise GreenBookError("--opex needs --opex-upper-pct")
        res["opex"] = adj(opex, opex_upper_pct)
    if benefits is not None:
        if benefits_pct is None:
            raise GreenBookError("--benefits needs --benefits-pct")
        res["benefits"] = adj(benefits, benefits_pct, sign=-1)
    if duration is not None:
        if duration_upper_pct is None:
            raise GreenBookError("--duration needs --duration-upper-pct")
        res["duration"] = adj(duration, duration_upper_pct)
    res["remaining_cost_adjustment_for_contingency"] = res["capex"]["adjustment"] + (
        res["opex"]["adjustment"] if "opex" in res else 0.0)
    res["percentages_source"] = source or "USER-SUPPLIED (state the evidence: organisation forecast errors or the " \
                                          "Green Book supplementary guidance on optimism bias)"
    res["notes"] = [
        f"Optimism bias must be adjusted for explicitly at the outset: increase costs and durations, decrease "
        f"benefits ({cite('risk.optimism-bias')}).",
        "The 2026 Green Book does not state optimism bias percentages; it directs practitioners to their own "
        "historical forecast errors or to the generic values in the Green Book supplementary guidance on optimism "
        "bias (paras 6.80-6.81). The percentages used here are user inputs.",
        "Mitigation reduces the adjustment in proportion to the level of risk prevented (para 6.82); prevention "
        "costs belong in core costs.",
        f"The remaining adjustment (plus unprevented risk) informs contingency in the financial case, converted to "
        f"nominal terms ({cite('risk.contingency')}).",
    ]
    return res


def optimism_bias_markdown(res: dict) -> str:
    out = ["# Optimism bias adjustment (Green Book 2026)", "",
           f"Percentages source: {res['percentages_source']}", f"Mitigation applied: {res['mitigation_pct']:g}%", "",
           "| Element | Base | Upper bound % | Applied % | Adjustment | Adjusted value |", "|---|---|---|---|---|---|"]
    for key, label in (("capex", "Capital costs"), ("opex", "Operating costs"), ("benefits", "Benefits"),
                       ("duration", "Duration")):
        if key in res:
            r = res[key]
            out.append(f"| {label} | {_fmt(r['base'])} | {r['upper_pct']:g}% | {r['applied_pct']:.2f}% | "
                       f"{_fmt(r['adjustment'])} | {_fmt(r['adjusted'])} |")
    out += ["", f"Remaining cost adjustment carried to contingency: {_fmt(res['remaining_cost_adjustment_for_contingency'])}",
            "", "## Notes", ""] + [f"- {n}" for n in res["notes"]]
    return "\n".join(out) + "\n"


# ====================================================================== nominal -> real
def read_table(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        raise GreenBookError(f"file not found: {p}")
    text = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".csv":
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(io.StringIO(text))]
    if p.suffix.lower() in (".yaml", ".yml", ".json"):
        try:
            data = json.loads(text) if p.suffix.lower() == ".json" else yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise GreenBookError(f"{p.name}: cannot parse: {exc}") from None
        if isinstance(data, dict):
            data = data.get("rows") or data.get("deflators") or data.get("data")
        if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
            raise GreenBookError(f"{p.name}: expected a list of rows (mappings)")
        return [dict(r) for r in data]
    raise GreenBookError(f"{p.name}: unsupported file type")


def deflator_index(rows: list[dict]) -> dict[int, float]:
    """Build {year: index level} from rows with ``year`` and either ``index``/``deflator`` (level)
    or ``growth_pct`` (annual % change; the first year's growth is ignored, base = 100)."""
    if not rows:
        raise GreenBookError("deflator series is empty")
    cols = {k.lower(): k for k in rows[0]}
    if "year" not in cols:
        raise GreenBookError("deflator series needs a 'year' column")
    level_col = cols.get("index") or cols.get("deflator") or cols.get("gdp_deflator")
    growth_col = cols.get("growth_pct") or cols.get("inflation_pct")
    if not level_col and not growth_col:
        raise GreenBookError("deflator series needs an 'index'/'deflator' level column or a 'growth_pct' column")
    parsed = sorted(((_int_year(r.get(cols["year"]), "deflator series"), r) for r in rows), key=lambda t: t[0])
    years = [y for y, _ in parsed]
    if len(set(years)) != len(years):
        raise GreenBookError("duplicate years in deflator series")
    idx: dict[int, float] = {}
    if level_col:
        for y, r in parsed:
            v = _num(r[level_col], f"deflator {y}")
            if v <= 0:
                raise GreenBookError(f"deflator for {y} must be positive")
            idx[y] = v
    else:
        level = 100.0
        prev = None
        for y, r in parsed:
            if prev is not None:
                if y != prev + 1:
                    raise GreenBookError(f"growth series has a gap between {prev} and {y}")
                level *= 1 + _num(r[growth_col], f"growth {y}") / 100
            idx[y] = level
            prev = y
    return idx


def nominal_to_real(rows: list[dict], deflators: dict[int, float], price_year: int | None = None,
                    year_col: str = "year", columns: list[str] | None = None) -> tuple[list[dict], dict]:
    """Convert nominal values to real prices of ``price_year`` (default: first year = year 0, so nominal = real
    in year 0, para 6.47): real = nominal x deflator[price_year] / deflator[year]."""
    if not rows:
        raise GreenBookError("no rows to convert")
    if year_col not in rows[0]:
        raise GreenBookError(f"input has no '{year_col}' column (use --year-col)")
    years = [_int_year(r.get(year_col), f"row {n}") for n, r in enumerate(rows, start=1)]
    price_year = min(years) if price_year is None else price_year
    if price_year not in deflators:
        raise GreenBookError(f"no deflator for price year {price_year}")
    if columns is None:
        columns = []
        for k in rows[0]:
            if k == year_col:
                continue
            try:
                [_num(r[k], k) for r in rows if str(r.get(k, "")).strip() != ""]
                columns.append(k)
            except GreenBookError:
                pass
    out = []
    for r, y in zip(rows, years):
        if y not in deflators:
            raise GreenBookError(f"no deflator for year {y}; supply a complete GDP deflator series "
                                 f"({cite('prices.gdp-deflator-source')})")
        f = deflators[price_year] / deflators[y]
        new = dict(r)
        for c in columns:
            if str(r.get(c, "")).strip() == "":
                continue
            new[c] = round(_num(r[c], f"{c} {y}") * f, 6)
        new["deflator_factor"] = round(f, 6)
        out.append(new)
    info = {"price_year": price_year, "converted_columns": columns, "source": SOURCE_ID,
            "notes": [f"Real = nominal x deflator(price year) / deflator(year); general inflation removed with the "
                      f"user-supplied GDP deflator ({cite('prices.real-terms')}).",
                      f"Deflator series is a user input: OBR forecasts are the recommended source "
                      f"({cite('prices.gdp-deflator-source')}).",
                      f"Discount only after converting to real terms ({cite('discount.real-only')})."]}
    return out, info


# ====================================================================== welfare weights
def welfare_weight(national_median: float, group_median: float) -> float:
    if national_median <= 0 or group_median <= 0:
        raise GreenBookError("median incomes must be positive (equivalise them first)")
    eta = float(parameters()["welfare_weight_elasticity"]["value"])
    return (national_median / group_median) ** eta


# ====================================================================== business case checker
_NEG = re.compile(r"\b(not|no|never|avoid|without|shouldn't|mustn't|don't|doesn't|against|instead of)\b", re.I)


def _headings(text: str) -> list[str]:
    return [h.strip().lower() for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", text, re.M)]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n\s*\n|\n\s*[-*|]", text) if s.strip()]


def _has(text: str, *patterns: str) -> bool:
    return any(re.search(p, text, re.I | re.M) for p in patterns)


def _section(text: str, heading_rx: str) -> str:
    """Text under the first heading matching ``heading_rx`` up to the next heading of same/higher level."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m and re.search(heading_rx, m.group(2), re.I):
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                m2 = re.match(r"^(#{1,6})\s+", nxt)
                if m2 and len(m2.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


@dataclass
class Finding:
    id: str
    status: str      # pass | fail | warn
    severity: str    # error | warning
    message: str
    ref: str

    def as_dict(self):
        return {"id": self.id, "status": self.status, "severity": self.severity, "message": self.message,
                "ref": self.ref, "citation": cite(self.ref)}


def check_case_text(text: str) -> dict:
    """Structural checks of a business case / appraisal write-up against the 2026 Green Book."""
    heads = _headings(text)
    findings: list[Finding] = []

    def req(fid, ok, msg_ok, msg_bad, ref, severity="error"):
        findings.append(Finding(fid, "pass" if ok else ("fail" if severity == "error" else "warn"),
                                severity, msg_ok if ok else msg_bad, ref))

    for case in ("strategic", "economic", "commercial", "financial", "management"):
        ok = any(re.search(rf"\b{case}\s+(case|dimension)\b", h) for h in heads)
        req(f"five-case.{case}", ok, f"{case.title()} case section present.",
            f"No '{case.title()} case' heading found; the Five Case Model needs all five dimensions.", f"case.{case}")

    req("rationale.smart", _has(text, r"\bSMART\b", r"specific,\s*measurable"),
        "SMART objectives referenced.", "Objectives are not shown to be SMART.", "rationale.smart-objectives")
    req("rationale.case-for-change", _has(text, r"case for change", r"rationale for (intervention|change)",
                                          r"market failure"),
        "Case for change / rationale present.", "No case for change or rationale for intervention.",
        "rationale.case-for-change")
    req("rationale.theory-of-change", _has(text, r"theory of change", r"logic model"),
        "Theory of change present.", "No theory of change (inputs -> outputs -> outcomes with assumptions).",
        "rationale.theory-of-change", "warning")
    bau = _has(text, r"business as usual", r"\bBAU\b", r"status quo")
    req("options.bau", bau, "Business as usual (BAU) option included.",
        "No business as usual (BAU) option: BAU must always be taken to the shortlist as the benchmark.",
        "shortlist.bau-always")
    req("options.do-minimum", _has(text, r"do[\s-]+minimum"), "Do minimum option included.",
        "No do minimum option on the shortlist.", "shortlist.do-minimum")
    req("options.longlist", _has(text, r"long[\s-]?list"), "Longlist of options documented.",
        "No longlist: options generation and longlist appraisal must be documented with reasons.",
        "longlist.documented")
    req("options.csfs", _has(text, r"critical success factor", r"\bCSFs?\b"), "Critical success factors defined.",
        "No critical success factors against which options are assessed.", "csf.1-objectives-strategic-fit")
    req("options.method", _has(text, r"options framework", r"\bOFF\b", r"\bMCDA\b", r"\bSWOT\b"),
        "Longlist appraisal method stated.", "Longlist method not stated (options framework filter recommended).",
        "longlist.off", "warning")
    req("options.shortlist", _has(text, r"short[\s-]?list"), "Shortlist identified.",
        "No shortlist of options identified.", "shortlist.composition")

    pref = _has(text, r"preferred option", r"preferred way forward", r"recommended option")
    justified = False
    if pref:
        for s in _sentences(text):
            if re.search(r"preferred (option|way forward)|recommended option", s, re.I) and re.search(
                    r"\bNPSV\b|net present social value|value for money|\bBCR\b|because|as it|since|"
                    r"highest|best|optimis", s, re.I):
                justified = True
                break
    req("preferred.justified", pref and justified, "Preferred option identified and justified.",
        "Preferred option is missing or not justified against value for money / summary metrics.",
        "stage.4-preferred-option")
    req("economic.npsv", _has(text, r"\bNPSV\b", r"net present social value", r"net present unit cost", r"\bNPUC\b"),
        "NPSV (or NPUC for CEA) reported.", "No NPSV (or NPUC) reported for shortlisted options.", "metrics.npsv")
    req("economic.bcr", _has(text, r"\bBCR\b", r"benefit[\s-]cost ratio"), "BCR reported.",
        "No benefit-cost ratio reported.", "metrics.bcr", "warning")
    req("economic.discounting", _has(text, r"\bSTPR\b", r"social time preference", r"3\.5\s?%"),
        "Discounting at the STPR stated.", "Discount rate (STPR) not stated.", "discount.stpr", "warning")
    req("economic.real-terms", _has(text, r"real (terms|prices)", r"GDP deflator"),
        "Real-terms basis stated.", "Price basis (real terms, GDP deflator) not stated.", "prices.real-terms", "warning")
    req("economic.unmonetisable", _has(text, r"un-?monetis", r"non-?monetis", r"qualitative (benefit|impact|cost)"),
        "Unmonetisable impacts considered.", "Unmonetisable costs and benefits not described.",
        "shortlist.classification", "warning")
    req("economic.sensitivity", _has(text, r"sensitivity"), "Sensitivity analysis present.",
        "No sensitivity analysis.", "metrics.sensitivity")
    req("economic.switching", _has(text, r"switching value"), "Switching values present.",
        "No switching values for the preferred option.", "metrics.switching-values")
    req("economic.optimism-bias", _has(text, r"optimism bias"), "Optimism bias adjustment addressed.",
        "No explicit optimism bias adjustment.", "risk.optimism-bias")
    req("risk.register", _has(text, r"risk register", r"risk log", r"^#{1,6}.*\brisks?\b"),
        "Risks identified.", "No risk register or risk section.", "risk.risk-uncertainty")
    assumptions_sec = _section(text, r"assumption")
    has_sources = bool(assumptions_sec) and _has(assumptions_sec, r"\bsource", r"evidence", r"reference")
    req("assumptions.sourced", has_sources, "Assumptions log with sources present.",
        "No assumptions section with sources/evidence for each assumption.", "rationale.theory-of-change")
    req("financial.affordability", _has(text, r"affordab"), "Affordability addressed.",
        "Affordability for the public bodies involved not addressed.", "case.financial")
    req("financial.psfi", _has(text, r"public sector financial", r"\bRDEL\b|\bCDEL\b|\bAME\b", r"funding"),
        "Public sector financial impact / budgets addressed.", "Public sector financial impact not set out.",
        "metrics.public-sector-financial-impact", "warning")
    req("management.me-plan", _has(text, r"monitoring and evaluation", r"evaluation plan", r"\bM&E\b"),
        "Monitoring and evaluation plan present.", "No monitoring and evaluation plan.", "me.plan")
    req("management.benefits", _has(text, r"benefits? realisation", r"benefits? register"),
        "Benefits realisation addressed.", "No benefits realisation plan / register.", "case.management", "warning")
    req("distributional", _has(text, r"distributional", r"equality", r"\bPSED\b", r"place-based"),
        "Distributional / equality effects considered.", "Distributional and equality effects not considered.",
        "distributional.proportionate", "warning")
    req("presentation.ast", _has(text, r"appraisal summary table", r"\bAST\b"), "Appraisal summary table present.",
        "No appraisal summary table (AST).", "presentation.ast", "warning")

    # ---- anti-patterns
    sents = _sentences(text)

    def anti(fid, rx_all, msg, ref, severity="error", exclude=None):
        hits = [s for s in sents if all(re.search(r, s, re.I) for r in rx_all) and not _NEG.search(s)
                and not (exclude and re.search(exclude, s, re.I))]
        if hits:
            findings.append(Finding(fid, "fail" if severity == "error" else "warn", severity,
                                    f"{msg} Evidence: \"{hits[0][:160]}\"", ref))
        else:
            findings.append(Finding(fid, "pass", severity, "Not detected.", ref))

    anti("anti.bcr-threshold", [r"\bBCR\b|benefit[\s-]cost ratio",
                                r"below|less than|under|threshold|minimum|at least|<",
                                r"reject|discard|exclud|rul\w* out|drop|fail|unacceptable|not progress|threshold"],
         "Options appear to be judged against a BCR threshold, which the Green Book rules out.",
         "metrics.no-bcr-thresholds")
    anti("anti.sunk-costs", [r"sunk cost|already (been )?(spent|incurred|paid)|spent to date", r"includ"], "Sunk costs appear to be included in the appraisal.",
         "shortlist.sunk-costs")
    anti("anti.multipliers", [r"multiplier|GVA|GDP", r"benefit"],
         "Keynesian multipliers or GDP/GVA appear to be counted as social benefits.", "shortlist.no-macro", "warning")
    anti("anti.nominal-discounting", [r"discount", r"nominal|includ\w* (general )?inflation|inflation[- ]adjusted cash"],
         "Discounting appears to be applied to nominal / inflation-inclusive values (the STPR is a real rate).",
         "discount.real-only", "error", exclude=r"\breal\b|remov|deflat|strip|net of|financial case")
    anti("anti.bau-normalised", [r"BAU|business as usual", r"normalis|set to zero|= ?0\b"],
         "BAU appears normalised to zero; present options in absolute terms.", "rationale.bau-absolute", "warning")

    errors = [f for f in findings if f.status == "fail"]
    warns = [f for f in findings if f.status == "warn"]
    return {"source": SOURCE_ID, "edition": EDITION,
            "summary": {"checks": len(findings), "passed": sum(f.status == "pass" for f in findings),
                        "failed": len(errors), "warnings": len(warns)},
            "findings": [f.as_dict() for f in findings],
            "note": "Structural, keyword-based screening only: it supports but does not replace professional "
                    "review, HM Treasury/departmental assurance or approval."}


def check_case_markdown(rep: dict) -> str:
    s = rep["summary"]
    out = ["# Business case structural check (Green Book 2026)", "",
           f"{s['checks']} checks: {s['passed']} passed, {s['failed']} failed, {s['warnings']} warnings.", "",
           "| Status | Check | Finding | Reference |", "|---|---|---|---|"]
    order = {"fail": 0, "warn": 1, "pass": 2}
    for f in sorted(rep["findings"], key=lambda f: order[f["status"]]):
        out.append(f"| {f['status'].upper()} | {f['id']} | {f['message'].replace('|', '/')} | {f['citation']} |")
    out += ["", f"_{rep['note']}_"]
    return "\n".join(out) + "\n"


# ====================================================================== graders
_NUM_RX = re.compile(r"(?<![\w.])(\(|-|−|–)?\s*£?\s*(\d[\d,]*(?:\.\d+)?)\s*\)?\s*(bn|billion|m|million|k|thousand)?(?![\w])",
                     re.I)
_SCALE = {"bn": 1e9, "billion": 1e9, "m": 1e6, "million": 1e6, "k": 1e3, "thousand": 1e3}


def parse_amounts(line: str) -> list[float]:
    """All numbers in a line, as written (sign applied; unit suffix NOT applied) plus suffix-scaled variants."""
    vals = []
    for m in _NUM_RX.finditer(line):
        try:
            v = float(m.group(2).replace(",", ""))
        except ValueError:
            continue
        if m.group(1):
            v = -v
        vals.append(v)
        if m.group(3):
            vals.append(v * _SCALE[m.group(3).lower()])
    return vals


def _close(a: float, b: float, rel: float, abs_tol: float) -> bool:
    return abs(a - b) <= max(abs_tol, rel * abs(b))


def _option_lines(output: str, option: str) -> list[str]:
    return [ln for ln in output.splitlines() if option.lower() in ln.lower()]


def _resolve_fixture(check: dict) -> Path:
    fx = check.get("fixture")
    if not fx:
        raise GreenBookError("check needs 'fixture' (path relative to repository root)")
    p = Path(fx)
    return p if p.is_absolute() else repo_root() / p


def _settings_from_check(check: dict) -> Settings:
    return Settings(flat_rate=check.get("rate"), health_rate=check.get("health_rate"),
                    separate_health=check.get("separate_health", True))


def grade_npsv_matches(output: str, check: dict) -> tuple[bool, str]:
    """Recompute the fixture and require each option's metrics to appear on a line naming that option.

    check keys: ``fixture`` (repo-relative), ``metrics`` (default [npsv]; also pvb, pvc, bcr, rpsc),
    ``scale`` (units the answer uses, e.g. 1000000 for £m; default 1), ``tolerance`` (relative, default 0.005),
    ``options`` (subset), ``base_year``, ``rate``/``health_rate`` (to recompute a variant).
    """
    app = load_flows(_resolve_fixture(check), check.get("base_year"))
    res = appraise(app, _settings_from_check(check))
    scale = float(check.get("scale", 1))
    rel = float(check.get("tolerance", 0.005))
    metrics = check.get("metrics", ["npsv"])
    wanted = check.get("options") or [r.option for r in res]
    problems = []
    for r in res:
        if r.option not in wanted:
            continue
        lines = _option_lines(output, r.option)
        if not lines:
            problems.append(f"{r.option}: not mentioned")
            continue
        nums = [n for ln in lines for n in parse_amounts(ln)]
        for m in metrics:
            exp = getattr(r, m)
            if exp is None:
                continue
            target = exp / scale if m not in ("bcr", "rpsc") else exp
            abs_tol = 0.006 if m in ("bcr", "rpsc") else max(0.5 / scale, 0.006)
            if not any(_close(n, target, rel, abs_tol) for n in nums):
                problems.append(f"{r.option}: {m} {target:,.3f} not found")
    return (not problems, "all recomputed figures present" if not problems else "; ".join(problems))


def grade_ranking(output: str, check: dict) -> tuple[bool, str]:
    """The option with the highest recomputed NPSV must be named as preferred / rank 1 in the output."""
    res = appraise(load_flows(_resolve_fixture(check), check.get("base_year")), _settings_from_check(check))
    top = res[0].option
    pats = [rf"preferred[^\n]{{0,80}}{re.escape(top)}", rf"{re.escape(top)}[^\n]{{0,80}}preferred",
            rf"^\|\s*1\s*\|\s*{re.escape(top)}\s*\|"]
    ok = any(re.search(p, output, re.I | re.M) for p in pats)
    return ok, f"top option by NPSV is '{top}'" + ("" if ok else " but it is not identified as preferred/rank 1")


def grade_optimism_bias(output: str, check: dict) -> tuple[bool, str]:
    """Recompute ``capex x (1 + upper% x (1 - mitigation%))`` and require it in the output (tolerance 0.5%)."""
    res = optimism_bias(float(check["capex"]), float(check["upper_pct"]), float(check.get("mitigation_pct", 0)))
    exp = res["capex"]["adjusted"]
    nums = parse_amounts(output)
    rel = float(check.get("tolerance", 0.005))
    ok = any(_close(n, exp, rel, 0.01) for n in nums)
    return ok, f"expected adjusted capex {exp:,.2f} {'found' if ok else 'not found'}"


def grade_switching_value(output: str, check: dict) -> tuple[bool, str]:
    """Recompute switching values and require the % for ``option`` (default preferred) and ``measure``
    (benefits|costs) to appear as a percentage within ``tolerance_pp`` percentage points (default 0.5)."""
    res = appraise(load_flows(_resolve_fixture(check), check.get("base_year")), _settings_from_check(check))
    sw = switching(res)
    opt = check.get("option") or sw["preferred_by_npsv"]
    sv = next((s for s in sw["switching_values"] if s["option"] == opt), None)
    if sv is None:
        return False, f"option {opt} not in fixture"
    tol = float(check.get("tolerance_pp", 0.5))
    pcts = [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", output)]
    problems = []
    for measure in check.get("measures", ["benefits", "costs"]):
        exp = abs(sv[f"{measure}_change_pct_to_zero_npsv"])
        if not any(abs(p - exp) <= tol for p in pcts):
            problems.append(f"{measure} switching value {exp:.1f}% not found")
    return (not problems, "switching values present" if not problems else "; ".join(problems))


def grade_case_structure(output: str, check: dict) -> tuple[bool, str]:
    """Run the business case checker on the output. ``require``: finding ids that must pass
    (default: every error-severity check); ``max_fail`` (default 0)."""
    rep = check_case_text(output)
    req = check.get("require")
    failing = [f["id"] for f in rep["findings"]
               if f["status"] != "pass" and (f["id"] in req if req else f["severity"] == "error")]
    ok = len(failing) <= int(check.get("max_fail", 0))
    return ok, "structure ok" if ok else f"failing: {failing}"


def grade_stpr_2026(output: str, check: dict) -> tuple[bool, str]:
    """The answer must state the 2026 STPR bands (3.5% yrs 1-30, 3% 31-75, 2.5% 76+) and, if
    ``health: true``, the 1.5% health rate; it must not import earlier-edition step-downs (e.g. 2% or 1%
    rates for years 126+ / 201+)."""
    t = output.replace("–", "-").replace("−", "-")
    problems = []
    if not re.search(r"3\.5\s*%[^\n]{0,60}\b(1|0)\s*(-|to)\s*30\b|\b(1|0)\s*(-|to)\s*30\b[^\n]{0,60}3\.5\s*%", t, re.I):
        problems.append("3.5% for years 1-30 not stated")
    if not re.search(r"3(\.0+)?\s*%[^\n]{0,60}31\s*(-|to)\s*75|31\s*(-|to)\s*75[^\n]{0,60}3(\.0+)?\s*%", t, re.I):
        problems.append("3.0% for years 31-75 not stated")
    if not re.search(r"2\.5\s*%[^\n]{0,60}76|76[^\n]{0,60}2\.5\s*%", t, re.I):
        problems.append("2.5% from year 76 not stated")
    if check.get("health") and not re.search(r"1\.5\s*%", t):
        problems.append("1.5% health rate not stated")
    if re.search(r"\b(126|201|301)\b\s*(-|to)|\b76\s*(-|to)\s*125\b", t):
        problems.append("earlier-edition band boundaries (125/126/200/201/300) cited")
    return (not problems, "2026 STPR schedule stated" if not problems else "; ".join(problems))


def grade_discount_factors(output: str, check: dict) -> tuple[bool, str]:
    """Each STPR factor for ``years`` and health factor for ``health_years`` must appear (to ``tolerance``,
    default 0.0005) on a line that mentions that year number."""
    tol = float(check.get("tolerance", 0.0005))
    lines = output.splitlines()
    problems = []

    def found(year: int, exp: float) -> bool:
        for ln in lines:
            if re.search(rf"\b{year}\b", ln) and any(abs(n - exp) <= tol for n in parse_amounts(ln)):
                return True
        return False

    for y in check.get("years", []):
        exp = discount_factor(int(y))
        if not found(int(y), exp):
            problems.append(f"year {y} STPR factor {exp:.4f} not found")
    for y in check.get("health_years", []):
        exp = health_discount_factor(int(y))
        if not found(int(y), exp):
            problems.append(f"year {y} health factor {exp:.4f} not found")
    return (not problems, "discount factors correct" if not problems else "; ".join(problems))


def grade_no_hardcoded_optimism_bias(output: str, check: dict) -> tuple[bool, str]:
    """Answer must attribute optimism bias percentages to supplementary guidance / organisational evidence /
    user input, not claim the 2026 Green Book itself sets them."""
    t = output.lower()
    attributed = "supplementary guidance" in t or "forecast error" in t or "user-supplied" in t or "user supplied" in t
    bad = re.search(r"green book (2026 )?(sets|specifies|prescribes|requires|mandates) (an? )?(optimism bias )?"
                    r"(uplift|percentage|adjustment) of \d", t)
    ok = attributed and not bad
    return ok, "attribution ok" if ok else "optimism bias % not attributed to supplementary guidance/evidence"


# ====================================================================== CLI
def _emit(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.write(text)


def _settings_from_args(a) -> Settings:
    for name in ("rate", "health_rate", "gilt_rate"):
        v = getattr(a, name, None)
        if v is not None and (v <= -1 or v > 1):
            raise GreenBookError(f"--{name.replace('_', '-')} is a decimal rate, e.g. 0.035 for 3.5%")
    return Settings(flat_rate=a.rate, health_rate=a.health_rate, separate_health=not a.no_health_rate,
                    gilt_rate=getattr(a, "gilt_rate", None), bau=getattr(a, "bau", None))


def _cmd_npv(a) -> int:
    app = load_flows(a.file, a.base_year)
    s = _settings_from_args(a)
    rep = npv_report(appraise(app, s), s, app.meta)
    _emit(json.dumps(rep, indent=2) + "\n" if a.format == "json" else npv_markdown(rep), a.out)
    return 0


def _cmd_switching(a) -> int:
    app = load_flows(a.file, a.base_year)
    rep = switching(appraise(app, _settings_from_args(a)), a.pcts)
    _emit(json.dumps(rep, indent=2) + "\n" if a.format == "json" else switching_markdown(rep), a.out)
    return 0


def _cmd_real(a) -> int:
    rows = read_table(a.file)
    idx = deflator_index(read_table(a.deflators))
    out, info = nominal_to_real(rows, idx, a.price_year, a.year_col, a.columns)
    if a.format == "json":
        text = json.dumps({**info, "rows": out}, indent=2) + "\n"
    elif a.format == "md":
        cols = list(out[0])
        text = "\n".join([f"# Real terms ({info['price_year']} prices)", "", "| " + " | ".join(cols) + " |",
                          "|" + "---|" * len(cols)] + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in out]
                         + ["", *[f"- {n}" for n in info["notes"]]]) + "\n"
    else:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
        text = buf.getvalue()
    _emit(text, a.out)
    return 0


def _cmd_ob(a) -> int:
    res = optimism_bias(a.capex, a.upper_pct, a.mitigation, opex=a.opex, opex_upper_pct=a.opex_upper_pct,
                        benefits=a.benefits, benefits_pct=a.benefits_pct, duration=a.duration,
                        duration_upper_pct=a.duration_upper_pct, source=a.source)
    _emit(json.dumps(res, indent=2) + "\n" if a.format == "json" else optimism_bias_markdown(res), a.out)
    return 0


def _cmd_check(a) -> int:
    p = Path(a.file)
    if not p.is_file():
        raise GreenBookError(f"file not found: {p}")
    rep = check_case_text(p.read_text(encoding="utf-8-sig"))
    _emit(json.dumps(rep, indent=2) + "\n" if a.format == "json" else check_case_markdown(rep), a.out)
    return 1 if (a.strict and rep["summary"]["failed"]) else 0


def _cmd_params(a) -> int:
    p = parameters()
    if a.format == "json":
        _emit(json.dumps(p, indent=2) + "\n", None)
        return 0
    b = p["stpr"]["bands"]
    lines = ["# Green Book 2026 appraisal parameters", "", "| Parameter | Value | Citation |", "|---|---|---|"]
    for band in b:
        rng = f"years {band['from_year']}-{band['to_year']}" if band["to_year"] else f"year {band['from_year']} onwards"
        lines.append(f"| STPR {rng} | {band['rate']:.2%} | {param_cite(p['stpr']['citation'])} |")
    lines.append(f"| Health/life discount rate (all years) | {p['health_discount_rate']['rate']:.2%} | "
                 f"{param_cite(p['health_discount_rate']['citation'])} |")
    th = p["time_horizons_years_after_year0"]
    lines.append(f"| Time horizons (years after year 0) | infrastructure {th['infrastructure']}, refurbishment "
                 f"{th['refurbishment']}, regulations {th['regulations']}, other {th['other']} | {param_cite(th['citation'])} |")
    ww = p["welfare_weight_elasticity"]
    lines.append(f"| Welfare weight elasticity | {ww['value']} | {param_cite(ww['citation'])} |")
    eq = p["equivalisation_scores"]
    lines.append(f"| Equivalisation scores | first adult {eq['first_adult']}, additional adult {eq['additional_adult']}, "
                 f"child 14+ {eq['child_14_and_over']}, child <14 {eq['child_under_14']} | {param_cite(eq['citation'])} |")
    lines.append(f"| Shortlist size | around {p['shortlist_size']['value']} | {param_cite(p['shortlist_size']['citation'])} |")
    g = p["ghg_negligible_threshold_mtco2e_per_year"]
    lines.append(f"| Negligible GHG threshold | < {g['value']} MtCO2e every year | {param_cite(g['citation'])} |")
    lines.append(f"| BCR threshold | none permitted | {param_cite(p['bcr_threshold']['citation'])} |")
    lines += ["", "## Not stated in the 2026 edition (user must supply)", "", "| Parameter | Where to get it | Citation |",
              "|---|---|---|"]
    for n in p["not_in_edition"]:
        lines.append(f"| {n['parameter']} | {n['statement']} | {param_cite(n['citation'])} |")
    _emit("\n".join(lines) + "\n", a.out)
    return 0


def _cmd_factors(a) -> int:
    if a.years < 0:
        raise GreenBookError("--years must be >= 0")
    rows = [{"year": t, "rate": (rate_for_year(t) if t else 0.0) if a.rate is None else a.rate,
             "discount_factor": discount_factor(t, flat_rate=a.rate),
             "health_factor": health_discount_factor(t, a.health_rate)} for t in range(a.years + 1)]
    if a.format == "json":
        text = json.dumps(rows, indent=2) + "\n"
    else:
        text = "\n".join(["| Year | Rate | Discount factor | Health factor |", "|---|---|---|---|"] +
                         [f"| {r['year']} | {r['rate']:.2%} | {r['discount_factor']:.4f} | {r['health_factor']:.4f} |"
                          for r in rows]) + f"\n\nSource: {cite('discount.stpr')}; {cite('discount.health')}\n"
    _emit(text, a.out)
    return 0


def _cmd_ww(a) -> int:
    w = welfare_weight(a.national, a.group)
    out = {"welfare_weight": w, "formula": parameters()["welfare_weight_elasticity"]["formula"],
           "citation": cite("distributional.welfare-weights"),
           "note": "Present weighted estimates alongside unweighted ones (para 7.13)."}
    if a.income_change is not None:
        out["weighted_impact"] = a.income_change * w
    _emit(json.dumps(out, indent=2) + "\n", None)
    return 0


def _wrap(fn):
    def run(a):
        try:
            return fn(a)
        except GreenBookError as exc:
            print(f"greenbook: error: {exc}", file=sys.stderr)
            return 2
    return run


def register(subparsers) -> None:
    gb = subparsers.add_parser("greenbook", help="HM Treasury Green Book (2026) appraisal tools",
                               description=__doc__.split("\n\n")[0])
    sub = gb.add_subparsers(dest="gb_command", required=True)

    def rates(p, gilt=False):
        p.add_argument("--rate", type=float, help="custom flat real discount rate (decimal) replacing the STPR")
        p.add_argument("--health-rate", type=float, help="override the health discount rate (decimal)")
        p.add_argument("--no-health-rate", action="store_true", help="discount 'health' stream at the standard rate")
        p.add_argument("--base-year", type=int, help="calendar year of appraisal year 0 (for calendar_year inputs)")
        if gilt:
            p.add_argument("--gilt-rate", type=float, help="risk-free real gilt rate for the Annex A costs-only sensitivity")
        p.add_argument("--format", choices=["md", "json"], default="md")
        p.add_argument("--out", help="write to file instead of stdout")

    p = sub.add_parser("npv", help="NPSV, BCR, RPSC per option from real-terms annual flows (CSV/YAML/JSON)")
    p.add_argument("file")
    p.add_argument("--bau", help="name of the BAU option (adds an NPSV-vs-BAU column; absolute values still shown)")
    rates(p, gilt=True)
    p.set_defaults(func=_wrap(_cmd_npv))

    p = sub.add_parser("switching", help="switching values and +/- %% sensitivity tables")
    p.add_argument("file")
    p.add_argument("--pcts", type=float, nargs="+", default=[-20, -10, 10, 20], help="percentage changes to test")
    rates(p)
    p.set_defaults(func=_wrap(_cmd_switching))

    p = sub.add_parser("real", help="convert nominal values to real terms with a supplied GDP deflator series")
    p.add_argument("file", help="CSV/YAML/JSON rows with a year column and nominal value columns")
    p.add_argument("--deflators", required=True, help="CSV/YAML/JSON with year and index (level) or growth_pct")
    p.add_argument("--price-year", type=int, help="price base year (default: first year in the data)")
    p.add_argument("--year-col", default="year")
    p.add_argument("--columns", nargs="+", help="columns to convert (default: all numeric except year)")
    p.add_argument("--format", choices=["csv", "json", "md"], default="csv")
    p.add_argument("--out")
    p.set_defaults(func=_wrap(_cmd_real))

    p = sub.add_parser("optimism-bias", help="apply user-supplied optimism bias percentages")
    p.add_argument("--capex", type=float, required=True, help="base capital cost estimate")
    p.add_argument("--upper-pct", type=float, required=True, help="upper-bound optimism bias %% (user-supplied)")
    p.add_argument("--mitigation", type=float, default=0.0, help="%% of the upper bound mitigated (0-100)")
    p.add_argument("--opex", type=float)
    p.add_argument("--opex-upper-pct", type=float)
    p.add_argument("--benefits", type=float)
    p.add_argument("--benefits-pct", type=float, help="%% reduction to benefits before mitigation")
    p.add_argument("--duration", type=float, help="base duration (e.g. months)")
    p.add_argument("--duration-upper-pct", type=float)
    p.add_argument("--source", help="where the percentages come from (evidence / supplementary guidance table)")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--out")
    p.set_defaults(func=_wrap(_cmd_ob))

    p = sub.add_parser("check-case", help="structural check of a business case Markdown document")
    p.add_argument("file")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--strict", action="store_true", help="exit 1 if any error-severity check fails")
    p.add_argument("--out")
    p.set_defaults(func=_wrap(_cmd_check))

    p = sub.add_parser("params", help="print the 2026 parameters with citations and the gaps")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--out")
    p.set_defaults(func=_wrap(_cmd_params))

    p = sub.add_parser("factors", help="print discount factors (STPR and health)")
    p.add_argument("--years", type=int, default=30)
    p.add_argument("--rate", type=float)
    p.add_argument("--health-rate", type=float)
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--out")
    p.set_defaults(func=_wrap(_cmd_factors))

    p = sub.add_parser("welfare-weight", help="distributional welfare weight (para 7.11)")
    p.add_argument("--national", type=float, required=True, help="national median equivalised income")
    p.add_argument("--group", type=float, required=True, help="group median equivalised income")
    p.add_argument("--income-change", type=float, help="change in income for the group (to weight)")
    p.set_defaults(func=_wrap(_cmd_ww))
