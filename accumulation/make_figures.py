#!/usr/bin/env python3
"""Figures and numeric tables for the excess3 accumulation-peak note.

Reads the archived 2026-09-24 decomposition and redraws four figures.
The film strip is regenerated from the published coupled-logistic generator.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
NESTED = ROOT.parent / "Investigaciones" / "nested-recd" / "src"
sys.path.insert(0, str(NESTED))
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "cascade_r_sweep", ROOT / "scripts" / "cascade_r_sweep.py"
)
cascade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cascade)

from nested_recd import generate_multivariate_symbols

AGG_PATH = ROOT / "results" / "peak_rinf" / "corrected_20260925" / "merged_agg.csv"
FLAT_PATH = ROOT / "results" / "peak_rinf" / "peak_flat_20260924_145527.csv"
FIG = PAPER / "figures"
GEN = PAPER / "generated"
FIG.mkdir(parents=True, exist_ok=True)
GEN.mkdir(parents=True, exist_ok=True)

PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#CC79A7",
    "#D55E00", "#56B4E9", "#332288", "#882255",
    "#44AA99", "#AA4499", "#117733", "#88CCEE",
    "#DDCC77", "#661100", "#6699CC", "#999933",
]
BLUE = "#0072B2"
ORANGE = "#D55E00"
GOLD = "#C47B00"
GREEN = "#009E73"
BAND = "#F4E4B3"
INK = "#1A1A1A"


def load(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def fcol(rows: list[dict[str, str]], key: str) -> np.ndarray:
    return np.array([float(row[key]) for row in rows])


def nearest(rows: list[dict[str, str]], r: float) -> dict[str, str]:
    return min(rows, key=lambda row: abs(float(row["r"]) - r))


def seed_for(r: float, k: int) -> int:
    return 10_000 + int(r * 10_000) + k * 17


def series_symbols(r: float, k: int) -> np.ndarray:
    X = cascade.logistic_coupled(
        n_steps=2200, n_comp=4, r=r, coupling=0.05,
        noise=0.003, seed=seed_for(r, k), burn_in=400,
    )
    return generate_multivariate_symbols(X, m=3, delay=1)


def window_counts(S: np.ndarray, w: int) -> np.ndarray:
    codes = [tuple(row.tolist()) for row in S]
    out = np.empty(len(codes) - w + 1)
    for i in range(len(out)):
        out[i] = len(set(codes[i:i + w]))
    return out


def representative(r: float, target: float, wshow: int = 16):
    best = None
    for k in range(6):
        S = series_symbols(r, k)
        mean_u = float(window_counts(S, 13).mean())
        show = window_counts(S, wshow)
        j = int(np.argmin(np.abs(show - mean_u)))
        cand = (abs(mean_u - target), k, mean_u, S, j)
        if best is None or cand[0] < best[0]:
            best = cand
    _, k, mean_u, S, j = best
    chunk = S[j:j + wshow]
    ids: list[int] = []
    seen: dict[tuple[int, ...], int] = {}
    for row in chunk:
        key = tuple(int(v) for v in row.tolist())
        if key not in seen:
            seen[key] = len(seen)
        ids.append(seen[key])
    return k, mean_u, ids


def ink_for(hexcolor: str) -> str:
    h = hexcolor.lstrip("#")
    red, green, blue = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return INK if (0.299 * red + 0.587 * green + 0.114 * blue) > 170 else "white"


def style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "axes.labelsize": 9,
        "axes.titlesize": 9.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.facecolor": "white",
    })


def polish(ax, ylabel: str):
    ax.set_xlim(3.08, 3.97)
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", color="#E6E6E6", lw=0.6)
    ax.axvspan(3.544, 3.595, color=BAND, alpha=0.95, zorder=0, lw=0)
    ax.axvline(3.5699456, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)


def save(fig, name: str):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_filmstrip(agg: list[dict[str, str]]):
    stations = [
        (3.30, "(a)  Period 2", r"$r = 3.30$"),
        (3.5675, "(b)  Accumulation", r"$r = 3.5675$"),
        (3.85, "(c)  Developed chaos", r"$r = 3.85$"),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(6.35, 5.15))
    notes = []
    for ax, (r_want, title, rlabel) in zip(axes, stations):
        row = nearest(agg, r_want)
        k, mean_u, ids = representative(float(row["r"]), float(row["n_unique_mean"]))
        n_here = len(set(ids))
        notes.append((float(row["r"]), k, mean_u, n_here, ids))
        ax.set_xlim(-0.62, 7.62)
        ax.set_ylim(-1.72, 0.62)
        for i, cid in enumerate(ids):
            col = i % 8
            y = 0.0 if i < 8 else -1.08
            face = PALETTE[cid % len(PALETTE)]
            ax.add_patch(mpatches.FancyBboxPatch(
                (col - 0.46, y - 0.46), 0.92, 0.92,
                boxstyle="round,pad=0.012,rounding_size=0.12",
                facecolor=face, edgecolor="white", linewidth=0.8,
            ))
            ax.text(
                col, y, str(cid + 1), ha="center", va="center",
                color=ink_for(face), fontsize=8.5, fontweight="bold",
            )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(f"{title}     {rlabel}", loc="left", color=INK, pad=2)
        ax.text(
            0.0, -0.04, f"{n_here} distinct joint symbols in these 16 steps",
            transform=ax.transAxes, ha="left", va="top", fontsize=8, color="#333333",
        )
    fig.tight_layout(h_pad=1.35)
    save(fig, "fig1_filmstrip")
    return notes


def fig_decomposition(agg: list[dict[str, str]]):
    r = fcol(agg, "r")
    fig, axes = plt.subplots(3, 1, figsize=(6.35, 6.15), sharex=True)
    specs = [
        ("excess3", "excess3 (bits)", BLUE),
        ("surp", "Surp (bits)", GOLD),
        ("syn", "Syn (bits)", ORANGE),
    ]
    for ax, (key, label, color) in zip(axes, specs):
        mean = fcol(agg, f"{key}_mean")
        sem = fcol(agg, f"{key}_sem")
        ax.fill_between(r, mean - sem, mean + sem, color=color, alpha=0.18, lw=0)
        ax.plot(r, mean, color=color, lw=1.4)
        polish(ax, label)
    axes[-1].set_xlabel(r"logistic parameter $r$")
    fig.tight_layout(h_pad=0.35)
    save(fig, "fig2_decomposition")


def fig_support_residual(agg: list[dict[str, str]]):
    r = fcol(agg, "r")
    fig, axes = plt.subplots(2, 1, figsize=(6.35, 4.35), sharex=True)
    nu = fcol(agg, "n_unique_mean")
    nus = fcol(agg, "n_unique_sem")
    axes[0].fill_between(r, nu - nus, nu + nus, color=BLUE, alpha=0.18, lw=0)
    axes[0].plot(r, nu, color=BLUE, lw=1.4)
    polish(axes[0], "distinct joint tuples\nin a window of 13")
    res = fcol(agg, "full_res_mean")
    ress = fcol(agg, "full_res_sem")
    axes[1].fill_between(
        r, np.maximum(res - ress, 0), res + ress, color=GREEN, alpha=0.18, lw=0,
    )
    axes[1].plot(r, res, color=GREEN, lw=1.4)
    polish(axes[1], r"full-block $\mathrm{Res}_{\mathrm{pair}}$ (bits)")
    axes[1].set_xlabel(r"logistic parameter $r$")
    fig.tight_layout(h_pad=0.45)
    save(fig, "fig3_support_residual")


def fig_windows(agg: list[dict[str, str]]):
    windows = [6, 8, 10, 13, 20, 26, 40, 52, 78, 104, 156, 208, 312]
    curves = [
        (3.30, r"period 2, $r=3.30$", BLUE, "o"),
        (3.5675, r"accumulation, $r=3.5675$", GOLD, "s"),
        (3.828427, r"period 3, $r=3.828$", "#882255", "D"),
        (3.85, r"chaos, $r=3.85$", ORANGE, "^"),
    ]
    fig, ax = plt.subplots(figsize=(6.35, 3.45))
    for r_want, label, color, marker in curves:
        row = nearest(agg, r_want)
        y = [float(row[f"w{w}_excess3_mean"]) for w in windows]
        e = [float(row[f"w{w}_excess3_sem"]) for w in windows]
        ax.fill_between(windows, np.array(y) - np.array(e), np.array(y) + np.array(e),
                        color=color, alpha=0.12, lw=0)
        ax.plot(windows, y, color=color, lw=1.4, marker=marker, ms=3.5, label=label)
    ax.set_xscale("log")
    ax.set_xlabel("window length (symbols)")
    ax.set_ylabel("excess3 (bits)")
    ax.set_xticks(windows)
    ax.set_xticklabels([str(w) if w in (6, 13, 26, 52, 104, 312) else "" for w in windows])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", color="#E6E6E6", lw=0.6)
    ax.legend(
        frameon=False, ncol=2, loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)
    save(fig, "fig4_windows")


def tex_num(value: float, digits: int) -> str:
    text = f"{abs(value):.{digits}f}"
    return f"$-{text}$" if value < 0 else text


def tex_pm(mean: float, sem: float, digits: int) -> str:
    return f"{tex_num(mean, digits)} $\\pm$ {tex_num(sem, digits)}"


def tex_paren(mean: float, sem: float, digits: int) -> str:
    return f"{tex_num(mean, digits)} ({tex_num(sem, digits)})"


def main():
    style()
    agg = load(AGG_PATH)
    flat = load(FLAT_PATH)
    notes = fig_filmstrip(agg)
    fig_decomposition(agg)
    fig_support_residual(agg)
    fig_windows(agg)

    r = fcol(agg, "r")
    ex = fcol(agg, "excess3_mean")
    i_max = int(np.argmax(ex))
    peak = agg[i_max]
    pre = nearest(agg, 3.30)
    chaos = nearest(agg, 3.85)
    rinf = nearest(agg, 3.5699456)
    p3 = nearest(agg, 3.828427)
    p4 = nearest(agg, 3.44949)
    p8 = nearest(agg, 3.54409)
    near = nearest(agg, 3.566168)
    synmax = agg[int(np.argmax(fcol(agg, "syn_mean")))]
    surpmax = agg[int(np.argmax(fcol(agg, "surp_mean")))]
    resmax = agg[int(np.argmax(fcol(agg, "full_res_mean")))]
    fullex = agg[int(np.argmax(fcol(agg, "full_excess3_mean")))]

    band = [row for row in agg if 3.544 <= float(row["r"]) <= 3.595]
    n_high = sum(float(row["excess3_mean"]) > 2.30 for row in band)

    # Leave-one-seed argmax of the six-seed mean.
    by_r: dict[float, list[float]] = {}
    for row in flat:
        by_r.setdefault(round(float(row["r"]), 6), []).append(float(row["excess3"]))
    rs = sorted(by_r)
    jack = []
    for leave in range(6):
        means = []
        for rv in rs:
            vals = by_r[rv]
            kept = [v for j, v in enumerate(vals) if j != leave]
            means.append(float(np.mean(kept)))
        jack.append(rs[int(np.argmax(means))])

    def corr(a, b):
        return float(np.corrcoef(fcol(agg, a), fcol(agg, b))[0, 1])

    d_ex = float(peak["excess3_mean"]) - float(chaos["excess3_mean"])
    d_syn = 0.6 * (float(peak["syn_mean"]) - float(chaos["syn_mean"]))
    d_surp = 0.4 * (float(peak["surp_mean"]) - float(chaos["surp_mean"]))

    lines = []
    lines.append(f"grid max r={peak['r']} excess={peak['excess3_mean']} sem={peak['excess3_sem']}")
    lines.append(f"syn at peak={peak['syn_mean']} sem={peak['syn_sem']}  0.6syn={0.6*float(peak['syn_mean']):.6f}")
    lines.append(f"surp at peak={peak['surp_mean']} sem={peak['surp_sem']}  0.4surp={0.4*float(peak['surp_mean']):.6f}")
    lines.append(f"delta ex={d_ex:.6f}  0.6 dsyn={d_syn:.6f}  0.4 dsurp={d_surp:.6f}")
    lines.append(f"syn max r={synmax['r']} syn={synmax['syn_mean']}")
    lines.append(f"surp max r={surpmax['r']} surp={surpmax['surp_mean']}")
    lines.append(f"res max r={resmax['r']} res={resmax['full_res_mean']} sem={resmax['full_res_sem']}")
    lines.append(f"full excess max r={fullex['r']} val={fullex['full_excess3_mean']}")
    lines.append(f"band {len(band)} stations, {n_high} above 2.30, "
                 f"min={min(float(row['excess3_mean']) for row in band):.4f} "
                 f"max={max(float(row['excess3_mean']) for row in band):.4f}")
    lines.append("jackknife " + ", ".join(f"{v:.6f}" for v in jack))
    lines.append(f"corr surp={corr('excess3_mean','surp_mean'):.6f} "
                 f"syn={corr('excess3_mean','syn_mean'):.6f} "
                 f"uniq={corr('excess3_mean','n_unique_mean'):.6f}")
    spike = nearest(agg, 3.582612)
    lines.append(
        f"spike r={float(spike['r']):.6f} res={float(spike['full_res_mean']):.6f} "
        f"sem={float(spike['full_res_sem']):.6f}"
    )
    lines.append("film " + repr(notes))
    for name, row in (
        ("pre", pre), ("p4", p4), ("p8", p8), ("near", near),
        ("peak", peak), ("rinf", rinf), ("p3", p3), ("chaos", chaos), ("synmax", synmax),
    ):
        lines.append(
            f"{name} r={float(row['r']):.6f} ex={float(row['excess3_mean']):.6f}±{float(row['excess3_sem']):.6f} "
            f"syn={float(row['syn_mean']):.6f}±{float(row['syn_sem']):.6f} "
            f"surp={float(row['surp_mean']):.6f}±{float(row['surp_sem']):.6f} "
            f"u={float(row['n_unique_mean']):.4f}±{float(row['n_unique_sem']):.4f} "
            f"vis={float(row['visits_mean']):.4f} maxp={float(row['max_p_mean']):.4f} "
            f"res={float(row['full_res_mean']):.6f}±{float(row['full_res_sem']):.6f} "
            f"mcP={float(row['mc_P_excess3_mean']):.4f} mcP2={float(row['mc_P2_excess3_mean']):.4f} "
            f"gapT={float(row['gap_time_mean']):.4f}±{float(row['gap_time_sem']):.4f} "
            f"locP={float(row['local_gap_pair_mean']):.4f}±{float(row['local_gap_pair_sem']):.4f} "
            f"locB={float(row['local_gap_boot_mean']):.4f}±{float(row['local_gap_boot_sem']):.4f} "
            f"fullEx={float(row['full_excess3_mean']):.4f} "
            f"w6={float(row['w6_excess3_mean']):.4f} w13={float(row['w13_excess3_mean']):.4f} "
            f"w104={float(row['w104_excess3_mean']):.4f} w312={float(row['w312_excess3_mean']):.4f} "
            f"w312u={float(row['w312_n_unique_mean']):.2f} w312v={float(row['w312_visits_mean']):.2f} "
            f"mcPu={float(row['mc_P_n_unique_mean']):.3f}"
        )
    (GEN / "numbers.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    def row_tex(row, regime):
        return (
            f"{float(row['r']):.5f} & {regime} & "
            f"{tex_paren(float(row['excess3_mean']), float(row['excess3_sem']), 3)} & "
            f"{tex_paren(float(row['syn_mean']), float(row['syn_sem']), 4)} & "
            f"{tex_paren(float(row['surp_mean']), float(row['surp_sem']), 3)} & "
            f"{tex_paren(float(row['n_unique_mean']), float(row['n_unique_sem']), 2)} & "
            f"{float(row['visits_mean']):.2f} & "
            f"{float(row['max_p_mean']):.3f} & "
            f"{tex_paren(float(row['full_res_mean']), float(row['full_res_sem']), 4)} \\\\"
        )

    stations_tex = "\n".join([
        row_tex(pre, "period 2"),
        row_tex(p4, "period 4"),
        row_tex(p8, "period 8"),
        row_tex(near, "near $r_\\infty$"),
        row_tex(peak, "grid maximum"),
        row_tex(rinf, "$r_\\infty$"),
        row_tex(p3, "period-3 window"),
        row_tex(chaos, "developed chaos"),
    ])
    if stations_tex.endswith("\\\\"):
        stations_tex = stations_tex[:-2].rstrip()
    (GEN / "table_stations.tex").write_text(stations_tex + "\n")

    def ctrl(label, key, digits):
        return (
            f"{label} & "
            f"{tex_pm(float(peak[key + '_mean']), float(peak[key + '_sem']), digits)} & "
            f"{tex_pm(float(chaos[key + '_mean']), float(chaos[key + '_sem']), digits)} \\\\"
        )

    controls = "\n".join([
        ctrl("excess3, $w=13$", "excess3", 3),
        ctrl("Syn", "syn", 4),
        ctrl("Surp", "surp", 3),
        ctrl(r"distinct tuples, $w=13$", "n_unique", 2),
        ctrl("visits per tuple", "visits", 2),
        ctrl("modal mass", "max_p", 4),
        ctrl(r"iid draws from $P$", "mc_P_excess3", 3),
        ctrl(r"iid draws from $P^{(2)}$", "mc_P2_excess3", 3),
        ctrl(r"sliding minus iid $P$", "gap_time", 3),
        ctrl(r"local gap vs.\ $P^{(2)}$", "local_gap_pair", 3),
        ctrl(r"local gap vs.\ own $P$", "local_gap_boot", 3),
        ctrl(r"full-block excess3", "full_excess3", 3),
        ctrl(r"full-block $\mathrm{Res}_{\mathrm{pair}}$", "full_res", 4),
        ctrl(r"excess3, $w=312$", "w312_excess3", 3),
        ctrl(r"distinct tuples, $w=312$", "w312_n_unique", 1),
    ])
    if controls.endswith("\\\\"):
        controls = controls[:-2].rstrip()
    (GEN / "table_controls.tex").write_text(controls + "\n")
    print("wrote figures and tables")


if __name__ == "__main__":
    main()
