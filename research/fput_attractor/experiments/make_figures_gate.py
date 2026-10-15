"""Figures for the validation gate (Exp 5-9), generated from results/ only."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from fputv.model import FPUT  # noqa: E402

R, FIG = ROOT / "results", ROOT / "figures"
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#d9d8d2"
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6,
                     "legend.frameon": False, "figure.dpi": 150})
load = lambda n: json.loads((R / f"{n}.json").read_text())  # noqa: E731


def fig7():
    d = load("exp5_long_time_validation")
    z = np.load(R / "exp5_trajectories.npz")
    mu = d["locked_fixed_points_max_abs_mu"]["DOP853/1e-12"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    n = np.arange(1, 30001)
    for lab, col in (("L1e-2", C1), ("Ein", C2)):
        E = z[f"{lab}__DOP853_1e-12__E"][:, 0].astype(float)
        ax[0].semilogy(n, np.abs(E - E[-1]) + 1e-16, color=col, lw=1, label=f"{lab}, DOP853 1e-12")
    ax[0].semilogy(n, 0.02 * mu ** n, color=MUTED, ls="--", lw=1, label="$|\\mu_{max}|^n$ (Floquet)")
    ax[0].set(xlim=(0, 8000), ylim=(1e-9, 1), xlabel="drive period n", ylabel="$|E_1(nT) - E_1^{*}|$",
              title="Locked starts converge at the Floquet rate")
    ax[0].legend(fontsize=8)
    cr = d["cross_method_vs_DOP853_1e-12"]
    for m, col in (("RK4/400", C4), ("RK4/800", C3), ("RK4/1600", C2), ("DOP853/1e-10", C1)):
        c = cr[f"zero|{m}"]
        ns = [3500, 10000, 30000]
        ax[1].loglog(ns, [c[str(k)]["pointwise_supdiff"] for k in ns], "o-", color=col, ms=5, lw=1, label=f"{m}: pointwise")
        ax[1].loglog(ns, [max(c[str(k)]["distance_to_reference_curve"], 1e-12) for k in ns], "s:", color=col, ms=4, lw=1)
    ax[1].plot([], [], "s:", color=MUTED, label="distance to invariant curve (fit floor ~3e-6)")
    ax[1].set(xlabel="drive period", ylabel="difference vs DOP853 1e-12", title="Torus: drift is along the curve, not off it")
    ax[1].legend(fontsize=7)
    fig.savefig(FIG / "fig7_long_time_validation.png"); plt.close(fig)


def fig8():
    d = load("exp6_classification_convergence")["results"]
    T = 2 * np.pi / 0.347
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    for key, col in (("lyapunov_rk4_200", C1), ("lyapunov_rk4_400", C2)):
        ca = d[key]["cumulative_average"]
        ns = np.array([int(k) for k in ca]); v = np.array([abs(ca[k][0]) for k in ca])
        ax[0].loglog(ns, v, "o-", color=col, ms=5, lw=1, label=f"$|\\lambda_1|$ cumulative, {key[-7:].replace('_', '/')}")
    ns = np.geomspace(1e3, 1e5, 10)
    ax[0].loglog(ns, 2.59e-4 * 1e3 / ns, color=MUTED, ls=":", lw=1, label="$\\propto 1/t$ (bounded log-stretch)")
    ax[0].axhline(1.25e-3, color=MUTED, ls="--", lw=0.8)
    ax[0].text(1.1e3, 1.4e-3, "$|\\lambda_2| = \\eta/2$", color=MUTED, fontsize=8)
    ax[0].set(xlabel="drive periods", ylabel="per unit time", title="Neutral exponent: error decays as 1/t")
    ax[0].legend(fontsize=7.5, loc="lower left")
    b = np.array(d["lyapunov_rk4_400"]["blocks_lambda1"])
    ax[1].bar(np.arange(1, 11), b * 1e6, color=[MUTED, MUTED] + [C1] * 8)
    m, se = d["lyapunov_rk4_400"]["block_mean"][0], d["lyapunov_rk4_400"]["block_sem"][0]
    ax[1].axhspan((m - 2 * se) * 1e6, (m + 2 * se) * 1e6, color=C2, alpha=0.2, zorder=0)
    ax[1].set(xlabel="block of 10 000 periods (grey: excluded transient)", ylabel="$\\lambda_1$ block estimate ($10^{-6}$ per time)",
              title=f"$\\lambda_1$ = {m*1e6:.1f} ± {2*se*1e6:.1f} ×10$^{{-6}}$ (2 s.e.)")
    fig.savefig(FIG / "fig8_lyapunov_convergence.png"); plt.close(fig)


def fig9():
    d = load("exp7_ns_normal_form")
    rows = d["basin_radius_prediction_vs_exp3b"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    for k, col in enumerate((C1, C2, C3, C4)):
        r = [row["r_normal_form"] for row in rows]
        q = [row["ratio_measured_over_predicted"][k] for row in rows]
        capped = [s.startswith("bracket") for s in [row["status_exp3b"][k] for row in rows]]
        ax[0].plot(r, q, "-", color=col, lw=1)
        for ri, qi, c in zip(r, q, capped):
            ax[0].plot(ri, qi, "o", color=col, mfc="white" if c else col, ms=6)
        ax[0].plot([], [], "o-", color=col, label=f"direction {k}$\\pi$/4")
    ax[0].axhline(1, color=INK, lw=0.8)
    ax[0].set(xlabel="normal-form circle radius r(F) = $\\sqrt{(1-|\\mu|)/d}$", ylabel="measured / predicted basin radius",
              title="Parameter-free NS prediction → 1 as r → 0")
    ax[0].legend(fontsize=8)
    cr = d["crossings"]
    labs = ["full", "modes12345", "modes1234"]
    ax[1].bar(range(3), [cr[l]["normal_form"]["DOP853"]["d"] for l in labs], color=[C1, C3, C2])
    ax[1].set_xticks(range(3), ["full chain", "modes 1-5", "modes 1-4"])
    ax[1].set(ylabel="d = Re($e^{-i\\theta}c_1$)", title="d > 0 (subcritical) in all three models")
    fig.savefig(FIG / "fig9_normal_form.png"); plt.close(fig)


def fig10():
    d = load("exp8_edge_and_fold")["results"]
    z = np.load(R / "exp8_edge_histories.npz")
    e7 = load("exp7_ns_normal_form")["crossings"]["full"]
    Fc, th = e7["F_c_dop853"], e7["theta_over_2pi"]
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9), layout="constrained")
    s = FPUT(0.0045)
    cols = {0.00465: C4, 0.0045: C1, 0.0043: C3, 0.0042165625: C2}
    for F, col in cols.items():
        H = z[f"edge_F{F}"][1500:]
        Q, P = s.modal(H)
        ax[0].plot(Q[:, 0], P[:, 0], ".", ms=0.8, color=col)
        ax[0].plot([], [], "o", color=col, label=f"unstable circle, F={F:.7g}")
    T = z["torus_F0.0045"]; Q, P = s.modal(T)
    ax[0].plot(Q[:, 0], P[:, 0], ".", ms=0.6, color=MUTED, alpha=0.5)
    ax[0].plot([], [], "o", color=MUTED, label="stable torus, F=0.0045")
    ax[0].set(xlabel="$Q_1(nT)$", ylabel="$\\dot Q_1(nT)$", title="Edge states are invariant circles")
    ax[0].legend(fontsize=7, markerscale=1.2, loc="lower left")
    E = d["E_edge_states"]
    Fe = [e["F"] for e in E]
    ax[1].plot(Fe, [e["abs_rho_naff"] for e in E], "o-", color=C2, ms=5, label="unstable (edge) circle")
    tor = {float(k.split("F")[1]): v for k, v in z.items() if k.startswith("torus")}
    from fputv import diagnostics as D
    Ft = sorted(tor)
    rt = []
    for F in Ft:
        Pp, _ = D.pca_plane(tor[F]); rt.append(abs(D.refined_frequency(Pp[:, 0] + 1j * Pp[:, 1])))
    ax[1].plot(Ft, rt, "s-", color=C1, ms=5, label="stable torus")
    ax[1].plot([Fc], [th], "*", color=INK, ms=11, label="NS point: $\\theta/2\\pi$ at $F_c$")
    ax[1].axvline(d["B_lower_edge"]["F_low_estimate"], color=MUTED, ls="--", lw=0.8)
    ax[1].set(xlabel="F", ylabel="rotation number", title="Branch from NS point to the fold")
    ax[1].legend(fontsize=7.5)
    Tp = 2 * np.pi / 0.347
    ax[2].plot(Fe, [e["instability_rate_per_period"] for e in E], "o-", color=C2, ms=5, label="edge circle: instability rate")
    L = d["D_lyapunov_vs_F"]
    ax[2].plot([x["F"] for x in L], [-x["lambda"][1] * Tp for x in L], "s-", color=C1, ms=5, label="stable torus: $-\\lambda_2 T$")
    try:
        b = load("exp8b_fold_scaling")["results"]
        fs = b["fold_side"]
        ax[2].plot([x["F"] for x in fs], [x["edge"]["instability_rate_per_period"] for x in fs], "o", color=C2, mfc="white", ms=5)
        ax[2].plot([x["F"] for x in fs], [-x["lambda2_per_time"] * Tp for x in fs], "s", color=C1, mfc="white", ms=5)
        ax[2].plot([], [], "o", color=MUTED, mfc="white", label="Exp 8b refinement")
    except FileNotFoundError:
        pass
    ax[2].axvline(d["B_lower_edge"]["F_low_estimate"], color=MUTED, ls="--", lw=0.8)
    ax[2].set(xlabel="F", ylabel="normal rate per drive period", title="Both normal rates → 0 at $F_{low}$")
    ax[2].legend(fontsize=7.5)
    fig.savefig(FIG / "fig10_edge_fold.png"); plt.close(fig)


def fig11():
    d = load("exp9_modal_knockouts")["cases"]
    keys = ["full_minus_235", "full_minus_145", "full_minus_156", "full_minus_257", "full_minus_all_mode5_triads",
            "full_minus_246_and_336", "full_minus_all_mode6_triads", "full_no_forcing_5_7"]
    labels = ["{2,3,5}", "{1,4,5}", "{1,5,6}", "{2,5,7}", "all mode-5\ntriads", "{2,4,6}+{3,3,6}", "all mode-6\ntriads", "forcing of\nmodes 5,7"]
    v = [100 * d[k]["shift_from_full_over_gap"] for k in keys]
    fig, ax = plt.subplots(figsize=(9, 3.6), layout="constrained")
    ax.bar(range(len(v)), v, color=[C1] * 5 + [C3] * 2 + [MUTED])
    for i, x in enumerate(v):
        ax.text(i, x + 1.5, f"{x:.0f}%", ha="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(v)), labels, fontsize=8)
    ax.set(ylabel="% of $F_c^{(4)}-F_c^{(8)}$ gap reopened", title="Knock-out of symmetric couplings in the full chain (removing one coupling group)")
    fig.savefig(FIG / "fig11_knockouts.png"); plt.close(fig)


if __name__ == "__main__":
    for f in (fig7, fig8, fig9, fig10, fig11):
        try:
            f(); print("ok", f.__name__)
        except FileNotFoundError as e:
            print("skipped", f.__name__, e)
