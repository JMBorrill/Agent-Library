"""Figures from the raw result files in results/ (no new computation)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import numpy as np  # noqa: E402

R, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"  # fixed categorical order
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#d9d8d2"
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6,
                     "legend.frameon": False, "figure.dpi": 150})


def load(name):
    return json.loads((R / f"{name}.json").read_text())


def fig_attractors():
    from fputv.model import FPUT
    s = FPUT(0.0045)
    z = np.load(R / "exp2_F0.0045_strobe_last16384.npz")
    Q, P = s.modal(z["Y"])
    cat = load("exp3_multistability")["results"]["full"]["A_catalogue_F0.0045"]["orbits"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    ax[0].plot(Q[:, 0], P[:, 0], ".", ms=1.2, color=C1, alpha=.5, label="modulated state (16 384 strobe samples)")
    marks = {"branch": (C2, "o", "locked orbit, continued branch (stable)"),
             "stable": (C3, "s", "locked orbit, high amplitude (stable)"),
             "saddle": (MUTED, "x", "locked orbit, saddle (1 unstable multiplier)")}
    for o in cat:
        key = next(k for k in marks if o["name"].startswith(k))
        q, p = s.modal(np.array(o["y"]))
        col, mk, lab = marks[key]
        ax[0].plot(q[0], p[0], mk, ms=8, color=col, mec=col if mk == "x" else "white", mew=2 if mk == "x" else 1.2, label=lab)
    ax[0].set(xlabel="mode-1 coordinate $Q_1$ at $t=nT$", ylabel="mode-1 velocity $\\dot Q_1$ at $t=nT$",
              title="Stroboscopic section, N=8, F=0.0045")
    ax[0].legend(loc="lower left", fontsize=7.5, markerscale=1.0)
    e = np.load(R / "exp1_trajectories_E.npz")
    E0 = e["zero__RK4_1280"][:, 0]
    E1l = e["locked_plus_1e-2__RK4_1280"][:, 0]
    n = np.arange(1, len(E0) + 1)
    ax[1].plot(n, E0, color=C1, lw=0.7, label="from rest")
    ax[1].plot(n, E1l, color=C2, lw=1.4, label="locked orbit + 0.01 in $Q_1$")
    ax[1].set(xlim=(2800, 3500), xlabel="drive period n", ylabel="mode-1 linear energy $E_1(nT)$",
              title="Two long-time states at identical parameters")
    ax[1].set_ylim(0, 0.62)
    ax[1].legend(loc="upper center", ncol=2)
    fig.savefig(FIG / "fig1_attractors.png"); plt.close(fig)


def fig_convergence():
    d = load("exp1_reproduction")["runs"]["zero"]
    ref = d["DOP853/rtol1e-12"]["E1_range_last750"]
    steps = [160, 320, 640, 1280]
    err = [abs(d[f"RK4/{n}"]["E1_range_last750"] - ref) for n in steps]
    f4 = load("exp4_floquet_reduced")["partA_threshold_verification"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    ax[0].loglog(steps, err, "o-", color=C1, ms=6, label="RK4, E1 range (modulated)")
    others = {k: abs(v["E1_range_last750"] - ref) for k, v in d.items() if k.startswith(("DOP", "LSODA")) and k != "DOP853/rtol1e-12"}
    for i, (k, v) in enumerate(others.items()):
        ax[0].axhline(max(v, 1e-12), color=[C2, C3, C4][i % 3], lw=1, ls="--", label=f"{k} vs DOP853/1e-12")
    ax[0].loglog(steps, err[0] * (np.array(steps) / 160.) ** -4, color=MUTED, lw=0.8, ls=":", label="slope -4")
    ax[0].set(xlabel="RK4 steps per drive period", ylabel="|observable - DOP853(rtol 1e-12)|",
              title="Exp 1: modulated-state E1 range, 3500 periods")
    ax[0].legend(fontsize=7)
    for col, (lab, key) in zip((C1, C2), (("full chain", "full"), ("4-mode truncation", "modes1234"))):
        r = f4[key]
        ns = [200, 400, 800, 1600]
        e = [abs(r["rk4_full_period"][str(n)]["F_c"] - r["dop853"]["F_c"]) for n in ns]
        ax[1].loglog(ns, e, "o-", color=col, ms=6, label=lab)
        ax[1].plot([720], [abs(r["baseline_reported_RK4_720"] - r["dop853"]["F_c"])], "D", color=col, mec=INK, ms=7)
    ax[1].plot([], [], "D", color="white", mec=INK, label="baseline report (RK4/720)")
    ax[1].set(xlabel="RK4 steps per drive period", ylabel="|F_c(RK4) - F_c(DOP853)|",
              title="Exp 4: Floquet threshold convergence")
    ax[1].legend(fontsize=7.5)
    fig.savefig(FIG / "fig2_convergence.png"); plt.close(fig)


def fig_classification():
    d = load("exp2_classification")["results"]["F0.0045"]
    z = np.load(R / "exp2_F0.0045_strobe_last16384.npz")
    E1 = z["E"][:, 0]
    x = E1 - E1.mean()
    S = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x))
    rho = d["abs_rho"]["richardson"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    ax[0].semilogy(f, S / S.max(), color=C1, lw=0.7)
    for k in range(1, 21):
        ax[0].axvline(abs(((k * rho + .5) % 1) - .5), color=MUTED, lw=0.4, ls=":", zorder=0)
    ax[0].set(xlim=(0, 0.5), ylim=(1e-30, 2), xlabel="frequency (cycles per drive period)",
              ylabel="normalised power of $E_1(nT)$",
              title=f"Line spectrum: harmonics of $\\rho$={rho:.8f} (dotted)")
    run200 = z["lyap_running_200"]
    run400 = z["lyap_running_400"]
    n = np.arange(1, len(run200) + 1)
    ax[1].loglog(n, np.abs(run200[:, 0]), color=C1, lw=1, label="$|\\lambda_1|$ cumulative, RK4/200")
    ax[1].loglog(n, np.abs(run400[:, 0]), color=C3, lw=1, label="$|\\lambda_1|$ cumulative, RK4/400")
    ax[1].loglog(n, np.abs(run200[:, 1]), color=C2, lw=1, label="$|\\lambda_2|$ cumulative, RK4/200")
    ax[1].loglog(n, 1.5 / (n * 2 * np.pi / .347), color=MUTED, lw=0.8, ls=":", label="$\\propto 1/t$")
    ax[1].axhline(0.0025 / 2, color=MUTED, lw=0.8, ls="--", label="$\\eta/2$")
    ax[1].set(xlabel="drive periods", ylabel="|exponent| (per unit time)", title="Lyapunov exponents, modulated state")
    ax[1].legend(fontsize=7.5, loc="lower left")
    fig.savefig(FIG / "fig3_classification.png"); plt.close(fig)


def fig_hysteresis():
    d = load("exp3_multistability")["results"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.9), layout="constrained", sharey=True)
    for a, (key, lab, Fc) in zip(ax, (("full", "full chain (N=8)", 0.004693158), ("modes1234", "4-mode truncation", 0.005084645))):
        C = d[key]["C_hysteresis"]
        for br, col, mk, name in (("up", C2, "^", "upward from locked orbit"), ("down", C1, "v", "downward from modulated state")):
            F = [r["F"] for r in C[br]]
            v = [r.get("E1_range", np.nan) for r in C[br]]
            a.plot(F, v, mk + "-", color=col, ms=6, lw=1, label=name)
        a.axvline(Fc, color=MUTED, ls="--", lw=0.9)
        a.text(Fc, 0.78, f" $F_c$={Fc:.6f}", color=MUTED, fontsize=8)
        a.axvspan(0.0043, 0.0053, color=GRID, alpha=0.25, zorder=0)
        a.set(xlabel="drive amplitude F", title=lab)
    ax[0].set_ylabel("$E_1$ range over final 1000 periods")
    ax[0].legend(loc="center left", fontsize=8)
    fig.savefig(FIG / "fig4_hysteresis.png"); plt.close(fig)


def fig_subcritical():
    b = load("exp3b_subcritical_scaling")
    d2 = load("exp3_multistability")["results"]["full"]["D2_above_Fc"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    x = np.array([r["F_c_minus_F"] for r in b["rows"]])
    for k, col in enumerate((C1, C2, C3, C4)):
        r = np.array([row["radius_by_direction"][k] for row in b["rows"]])
        capped = np.array([row["status"][k].startswith("bracket_hi") for row in b["rows"]])
        ax[0].loglog(x, r, "-", color=col, lw=1, label=f"direction phase {k}$\\pi$/4")
        ax[0].loglog(x[~capped], r[~capped], "o", color=col, ms=5)
        ax[0].loglog(x[capped], r[capped], "o", mfc="white", mec=col, ms=6)
    xx = np.geomspace(x.min(), x.max(), 10)
    rm = np.array([row["radius_min"] for row in b["rows"]])
    ax[0].loglog(xx, rm[-1] * (xx / x[-1]) ** 0.5, color=MUTED, ls=":", lw=1, label="slope 1/2 (subcritical NS)")
    ax[0].plot([], [], "o", mfc="white", mec=MUTED, label="lower bound (bracket cap 2)")
    ax[0].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[0].set(xlabel="$F_c - F$", ylabel="basin radius of locked orbit", title="Exp 3b: basin shrinks as F -> $F_c^-$")
    ax[0].set_xticks([1e-5, 3e-5, 1e-4, 3e-4], ["1e-5", "3e-5", "1e-4", "3e-4"])
    ax[0].set_yticks([0.2, 0.3, 0.5, 1, 2], ["0.2", "0.3", "0.5", "1", "2"])
    ax[0].legend(fontsize=7.5)
    for row, col in zip(d2, (C1, C2, C3)):
        blk = np.array(row["E1_range_per_500_block"])
        ax[1].semilogy(np.arange(len(blk)) * 500 + 500, np.maximum(blk, 1e-12), "-", color=col, lw=1.4, label=f"F={row['F']}")
    ax[1].set(xlabel="drive period", ylabel="$E_1$ range per 500-period block",
              title="F > $F_c$: 1e-6 kick grows straight to the large state")
    ax[1].legend(fontsize=8)
    fig.savefig(FIG / "fig5_subcritical.png"); plt.close(fig)


def fig_krein():
    d = load("exp4_floquet_reduced")
    B = d["partB_subsets"]
    v = d["partB_verdict"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    for key, col, lab in (("12345678", C1, "full (1-8)"), ("12345", C3, "modes 1-5"), ("1234", C2, "modes 1-4")):
        sc = np.array(B[key]["scan"])
        ax[0].plot(sc[:, 0], sc[:, 1], color=col, lw=1.6, label=lab)
        ax[0].plot([B[key]["F_K"]], [np.exp(-.0025 * np.pi / .347) * (1 + 1e-4)], "|", color=col, ms=14, mew=2)
    ax[0].axhline(np.exp(-.0025 * np.pi / .347), color=MUTED, ls="--", lw=0.8)
    ax[0].axhline(1, color=INK, lw=0.8)
    ax[0].text(0.0021, 0.979, "$e^{-\\eta T/2}$: all multipliers until Krein collision", color=MUTED, fontsize=7.5)
    ax[0].set(xlim=(0.002, 0.0056), ylim=(0.97, 1.01), xlabel="drive amplitude F", ylabel="largest |Floquet multiplier|",
              title="Krein collision ($|$) then crossing of |$\\mu$|=1")
    ax[0].legend(fontsize=8, loc="upper left")
    rec = v["fraction_of_gap_recovered_by_adding_mode_k_to_1234"]
    loo = v["fraction_of_gap_reopened_by_removing_mode_k_from_full"]
    ks = ["5", "6", "7", "8"]
    xk = np.arange(4)
    ax[1].bar(xk - 0.2, [100 * rec[k] for k in ks], 0.38, color=C1, label="add mode k to {1,2,3,4}")
    ax[1].bar(xk + 0.2, [-100 * loo[k] for k in ks], 0.38, color=C2, label="remove mode k from full chain")
    for i, k in enumerate(ks):
        ax[1].text(i - 0.2, 100 * rec[k] + 2, f"{abs(100 * rec[k]):.0f}%", ha="center", fontsize=8, color=INK)
    ax[1].set_xticks(xk, [f"mode {k}" for k in ks])
    ax[1].set(ylabel="% of threshold gap $F_c^{(8)}-F_c^{(4)}$", title="Which omitted mode carries the gap")
    ax[1].legend(fontsize=8)
    fig.savefig(FIG / "fig6_krein_modes.png"); plt.close(fig)


if __name__ == "__main__":
    for f in (fig_attractors, fig_convergence, fig_classification, fig_hysteresis, fig_subcritical, fig_krein):
        try:
            f()
            print("ok", f.__name__)
        except FileNotFoundError as e:
            print("skipped", f.__name__, e)
