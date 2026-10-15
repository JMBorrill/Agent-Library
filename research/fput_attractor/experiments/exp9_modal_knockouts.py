"""Experiment 9 (Priority 4, secondary) - causal coupling pathway of the 8- vs 4-mode threshold gap.

Symmetric knockouts in the normal-mode tensor model (no fitting; F_c by shooting, RK4/800).
Mode-5 triads (selection rule k+-i+-j = 0 mod 18): {1,4,5}, {2,3,5}, {1,5,6}, {2,5,7}, {3,5,8},
{5,5,8}, {5,6,7}. Mode-6 triads: {2,4,6}, {3,3,6}, {1,5,6}, {1,6,7}, {2,6,8}, {4,6,8}, {5,6,7}, {6,6,6}.
Predeclared:
  H9a: within the {1..5} truncation, the mode-5 shift is carried mainly (>= 50 %) by triad {2,3,5}.
  H9b: direct forcing of modes 5 and 7 contributes < 10 % of the full gap (review caveat).
Also: criticality-relevant structure is not tested here (see Exp 7).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / ".numba_cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import numpy as np  # noqa: E402

from fputv.io import Timer, save  # noqa: E402
from fputv.tensor_model import TensorFPUT, coupling_tensor  # noqa: E402

T5 = [(1, 4, 5), (2, 3, 5), (1, 5, 6), (2, 5, 7), (3, 5, 8), (5, 5, 8), (5, 6, 7)]
T6 = [(2, 4, 6), (3, 3, 6), (1, 5, 6), (1, 6, 7), (2, 6, 8), (4, 6, 8), (5, 6, 7), (6, 6, 6)]


def main():
    tm = Timer()
    C = coupling_tensor()
    nz = sorted({tuple(sorted((k + 1, i + 1, j + 1))) for k, i, j in zip(*np.nonzero(np.abs(C) > 1e-12))})
    sel_ok = all((a + b + c) % 18 == 0 or (a + b - c) % 18 == 0 or (a - b + c) % 18 == 0 or (-a + b + c) % 18 == 0 for a, b, c in nz)
    cases = {"full": dict(), "modes1234": dict(modes=(1, 2, 3, 4)), "modes12345": dict(modes=(1, 2, 3, 4, 5))}
    for t in T5:
        cases["full_minus_" + "".join(map(str, t))] = dict(knock_triads=[t])
    cases["full_minus_all_mode5_triads"] = dict(knock_triads=T5)
    cases["full_minus_all_mode6_triads"] = dict(knock_triads=T6)
    cases["full_minus_235_and_145"] = dict(knock_triads=[(2, 3, 5), (1, 4, 5)])
    cases["full_minus_246_and_336"] = dict(knock_triads=[(2, 4, 6), (3, 3, 6)])
    cases["full_no_forcing_5"] = dict(knock_forcing=(5,))
    cases["full_no_forcing_7"] = dict(knock_forcing=(7,))
    cases["full_no_forcing_5_7"] = dict(knock_forcing=(5, 7))
    cases["modes12345_minus_235"] = dict(modes=(1, 2, 3, 4, 5), knock_triads=[(2, 3, 5)])
    cases["modes12345_minus_145"] = dict(modes=(1, 2, 3, 4, 5), knock_triads=[(1, 4, 5)])
    cases["modes12345_no_forcing_5"] = dict(modes=(1, 2, 3, 4, 5), knock_forcing=(5,))
    res = {}
    for name, kw in cases.items():
        Fc, msg = TensorFPUT(**kw).critical_F()
        res[name] = {"F_c": Fc, "status": msg, "spec": {k: [list(x) if isinstance(x, tuple) else x for x in v] if isinstance(v, (list, tuple)) else v for k, v in kw.items()}}
        print(name, Fc, msg, flush=True)
    tm.mark("cases")
    F8, F4, F5 = res["full"]["F_c"], res["modes1234"]["F_c"], res["modes12345"]["F_c"]
    gap = F4 - F8
    for name, r in res.items():
        if r["F_c"] is not None:
            r["shift_from_full_over_gap"] = (r["F_c"] - F8) / gap
    s5 = F4 - F5  # shift carried by adding mode 5 to {1..4}
    v = {"gap_F4_minus_F8": gap, "mode5_shift_F4_minus_F5": s5,
         "H9a_fraction_of_mode5_shift_removed_by_knocking_235_in_1to5": (res["modes12345_minus_235"]["F_c"] - F5) / s5,
         "H9a_fraction_removed_by_knocking_145_in_1to5": (res["modes12345_minus_145"]["F_c"] - F5) / s5,
         "H9b_forcing_5_7_fraction_of_gap": (res["full_no_forcing_5_7"]["F_c"] - F8) / gap}
    v["H9a_supported"] = bool(v["H9a_fraction_of_mode5_shift_removed_by_knocking_235_in_1to5"] >= 0.5)
    v["H9b_supported"] = bool(abs(v["H9b_forcing_5_7_fraction_of_gap"]) < 0.1)
    save("exp9_modal_knockouts", {"config": {"rk4_steps": 800, "selection_rule_holds_for_all_nonzero_C": sel_ok,
                                             "n_nonzero_triads": len(nz), "nonzero_triads": nz},
                                  "cases": res, "verdict": v}, tm)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    main()
