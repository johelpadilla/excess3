#!/usr/bin/env python3
"""Synthetic validation for the excess³ methods preprint (Approach B).

Arms
----
G0  Independent AR(1), N=3          — near-null
G1  Shared latent coupling jump     — planted joint reorg
G2  Coupled logistic maps           — nonlinear ordinal reorg
G3  Pure pairwise (no triple lock)  — specificity control

Outputs (under docs/papers/excess3/):
  figures/*.png
  notes/validation_results.json
  notes/validation_summary.md
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths / imports
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
NOTES = ROOT / "notes"
FIG.mkdir(parents=True, exist_ok=True)
NOTES.mkdir(parents=True, exist_ok=True)

# Prefer academy-learning-tau implementation
STP = Path("/Users/johelpadilla/grok-safe/academy-learning-tau/src")
if STP.is_dir() and str(STP) not in sys.path:
    sys.path.insert(0, str(STP))

from stp.core.recd_levels import compute_recd_from_conjunctions, compute_phi3_excess  # noqa: E402
from stp.core.ordinal import multivariate_symbols  # noqa: E402
from stp.core.surrogates import phase_shuffle_independent  # noqa: E402


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def gen_g0_ar(T: int = 1200, N: int = 3, phi: float = 0.55, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X = np.zeros((T, N))
    for t in range(1, T):
        X[t] = phi * X[t - 1] + rng.normal(0.0, 1.0, size=N)
    return X


def gen_g1_shared(
    T: int = 1200,
    N: int = 3,
    event_at: int = 600,
    c_before: float = 0.05,
    c_after: float = 0.80,
    phi: float = 0.55,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X = np.zeros((T, N))
    for t in range(1, T):
        c = c_after if t >= event_at else c_before
        noise = rng.normal(0.0, 1.0, size=N)
        shared = rng.normal(0.0, 1.0)
        innov = (1.0 - c) * noise + c * shared
        X[t] = phi * X[t - 1] + innov
    return X


def gen_g2_logistic(
    T: int = 1200,
    r: float = 3.8,
    coupling: float = 0.20,
    switch_at: int = 600,
    seed: int = 0,
) -> np.ndarray:
    """Two maps + a weakly driven third coordinate for N=3 RECD."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, size=2)
    out = np.zeros((T, 3))
    c = 0.0
    for t in range(T):
        if t >= switch_at:
            c = coupling
        x0 = (1 - c) * r * x[0] * (1 - x[0]) + c * r * x[1] * (1 - x[1])
        x1 = (1 - c) * r * x[1] * (1 - x[1]) + c * r * x[0] * (1 - x[0])
        x = np.array([x0, x1])
        # third channel: mix of both + small noise (joint structure only post-switch)
        mix = 0.5 * x0 + 0.5 * x1 if t >= switch_at else rng.uniform(0.1, 0.9)
        out[t, 0] = x0
        out[t, 1] = x1
        out[t, 2] = mix + 0.02 * rng.normal()
    return out


def gen_g3_pairwise(
    T: int = 1200,
    event_at: int = 600,
    seed: int = 0,
) -> np.ndarray:
    """Pairwise coupling only: (0,1) couple post-event; 2 independent.

    Designed so true triple synergy stays weak relative to G1.
    """
    rng = np.random.default_rng(seed)
    X = np.zeros((T, 3))
    for t in range(1, T):
        e0 = rng.normal()
        e1 = rng.normal()
        e2 = rng.normal()
        if t >= event_at:
            shared01 = rng.normal()
            e0 = 0.35 * e0 + 0.65 * shared01
            e1 = 0.35 * e1 + 0.65 * shared01
            # channel 2 stays independent
        X[t, 0] = 0.5 * X[t - 1, 0] + e0
        X[t, 1] = 0.5 * X[t - 1, 1] + e1
        X[t, 2] = 0.5 * X[t - 1, 2] + e2
    return X


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def excess3_series(
    X: np.ndarray,
    m: int = 3,
    delay: int = 1,
    window: int = 13,
    theta3: float = 0.08,
    stride: int = 3,
) -> dict[str, np.ndarray]:
    """Level-3 only (fast path). phi1/phi2 omitted — not needed for excess³ claims."""
    S = multivariate_symbols(X, m=m, delay=delay)
    if len(S) == 0:
        z = np.array([])
        return {"phi3": z, "excess3": z, "symbols": S}
    w = min(window, max(5, len(S) // 4))
    phi3, excess3 = compute_phi3_excess(S, window=w, theta=theta3, stride=stride)
    return {"phi3": phi3, "excess3": excess3, "symbols": S}


def mean_excess_pre_post(
    excess: np.ndarray, split: int
) -> tuple[float, float, float]:
    pre = excess[:split]
    post = excess[split:]
    pre = pre[np.isfinite(pre)]
    post = post[np.isfinite(post)]
    m_pre = float(np.mean(pre)) if len(pre) else float("nan")
    m_post = float(np.mean(post)) if len(post) else float("nan")
    return m_pre, m_post, m_post - m_pre


def delta_excess3(
    X: np.ndarray,
    split: int,
    m: int = 3,
    delay: int = 1,
    window: int = 13,
    theta3: float = 0.08,
    stride: int = 3,
) -> float:
    recd = excess3_series(
        X, m=m, delay=delay, window=window, theta3=theta3, stride=stride
    )
    # split is in raw time; symbols are shorter by (m-1)*delay — use proportional split
    T_ex = len(recd["excess3"])
    T_raw = len(X)
    split_s = int(round(split * T_ex / max(T_raw, 1)))
    split_s = min(max(split_s, 1), T_ex - 1)
    _, _, d = mean_excess_pre_post(recd["excess3"], split_s)
    return d


def phase_shuffle_pvalue(
    X: np.ndarray,
    split: int,
    n_surr: int = 99,
    seed: int = 0,
    **kw,
) -> tuple[float, float, list[float]]:
    """Two-sided p on |Δ| under independent phase-shuffle surrogates."""
    obs = delta_excess3(X, split, **kw)
    null = []
    for b in range(n_surr):
        Xs = phase_shuffle_independent(X, seed=seed + 1000 + b)
        null.append(delta_excess3(Xs, split, **kw))
    null_a = np.asarray(null, dtype=float)
    p = (1.0 + np.sum(np.abs(null_a) >= abs(obs))) / (n_surr + 1.0)
    return float(obs), float(p), null


def phi3_occupancy(phi3: np.ndarray, split_frac: float) -> tuple[float, float]:
    """split_frac in [0,1] relative to length of phi3 series."""
    n = len(phi3)
    split = int(round(split_frac * n))
    split = min(max(split, 1), n - 1)
    pre = phi3[:split]
    post = phi3[split:]
    pre = pre[np.isfinite(pre)]
    post = post[np.isfinite(post)]
    o_pre = float(np.mean(pre > 0.5)) if len(pre) else float("nan")
    o_post = float(np.mean(post > 0.5)) if len(post) else float("nan")
    return o_pre, o_post


# ---------------------------------------------------------------------------
# Experiment runners
# ---------------------------------------------------------------------------

REF = dict(m=3, delay=1, window=13, theta3=0.08, stride=3)


def _pad_trajs(trajs: list[np.ndarray]) -> np.ndarray:
    """Stack trajectories to a common length (right-pad with NaN)."""
    if not trajs:
        return np.empty((0, 0))
    max_len = max(len(t) for t in trajs)
    out = np.full((len(trajs), max_len), np.nan, dtype=float)
    for i, t in enumerate(trajs):
        a = np.asarray(t, dtype=float)
        out[i, : len(a)] = a
    return out


def _stack_traj_mean(trajs: list[np.ndarray]) -> np.ndarray:
    stacked = _pad_trajs(trajs)
    if stacked.size == 0:
        return np.array([])
    with np.errstate(all="ignore"):
        return np.nanmean(stacked, axis=0)


def _stack_traj_std(trajs: list[np.ndarray]) -> np.ndarray:
    stacked = _pad_trajs(trajs)
    if stacked.size == 0:
        return np.array([])
    with np.errstate(all="ignore"):
        return np.nanstd(stacked, axis=0)


def run_arm(
    name: str,
    gen_fn,
    event_at: int | None,
    R: int = 25,
    n_surr: int = 99,
    T: int = 1200,
    base_seed: int = 0,
) -> dict:
    print(f"\n=== {name}  R={R}  B={n_surr} ===", flush=True)
    deltas = []
    means_pre = []
    means_post = []
    pvals = []
    occ_pre = []
    occ_post = []
    trajs = []
    null_example = None
    obs_example = None

    split = event_at if event_at is not None else T // 2
    split_frac = split / T

    t0 = time.time()
    for r in range(R):
        seed = base_seed + r
        if name == "G0":
            X = gen_fn(T=T, seed=seed)
        elif name == "G1":
            X = gen_fn(T=T, event_at=event_at, seed=seed)
        elif name == "G2":
            X = gen_fn(T=T, switch_at=event_at, seed=seed)
        elif name == "G3":
            X = gen_fn(T=T, event_at=event_at, seed=seed)
        else:
            raise ValueError(name)

        recd = excess3_series(X, **REF)
        ex = recd["excess3"]
        T_ex = len(ex)
        split_s = int(round(split_frac * T_ex))
        split_s = min(max(split_s, 1), T_ex - 1)
        m_pre, m_post, d = mean_excess_pre_post(ex, split_s)
        means_pre.append(m_pre)
        means_post.append(m_post)
        deltas.append(d)
        op, oq = phi3_occupancy(recd["phi3"], split_frac)
        occ_pre.append(op)
        occ_post.append(oq)
        trajs.append(ex)

        # Surrogates (full statistic Δ)
        obs, p, null = phase_shuffle_pvalue(
            X, split, n_surr=n_surr, seed=10_000 + seed, **REF
        )
        pvals.append(p)
        if r == 0:
            null_example = null
            obs_example = obs
        print(f"  r={r:02d}  Δ={d:+.4f}  p={p:.3f}  mean_pre={m_pre:.4f} mean_post={m_post:.4f}", flush=True)

    elapsed = time.time() - t0
    pvals_a = np.asarray(pvals)
    frac_sig = float(np.mean(pvals_a < 0.05))
    out = {
        "name": name,
        "R": R,
        "n_surr": n_surr,
        "T": T,
        "split": split,
        "event_at": event_at,
        "elapsed_sec": elapsed,
        "mean_excess_pre": float(np.nanmean(means_pre)),
        "mean_excess_post": float(np.nanmean(means_post)),
        "mean_delta": float(np.nanmean(deltas)),
        "std_delta": float(np.nanstd(deltas)),
        "median_p": float(np.median(pvals_a)),
        "frac_p_lt_0.05": frac_sig,
        "mean_phi3_occ_pre": float(np.nanmean(occ_pre)),
        "mean_phi3_occ_post": float(np.nanmean(occ_post)),
        "deltas": [float(x) for x in deltas],
        "pvals": [float(x) for x in pvals],
        "obs_example": float(obs_example) if obs_example is not None else None,
        "null_example": [float(x) for x in (null_example or [])],
        "traj_mean": _stack_traj_mean(trajs).tolist(),
        "traj_std": _stack_traj_std(trajs).tolist(),
    }
    print(
        f"  SUMMARY {name}: meanΔ={out['mean_delta']:+.4f}  "
        f"median_p={out['median_p']:.3f}  frac_p<0.05={frac_sig:.2f}  ({elapsed:.1f}s)",
        flush=True,
    )
    return out


def sensitivity_window(
    R: int = 10,
    windows: list[int] | None = None,
    T: int = 1000,
    event_at: int = 500,
) -> dict:
    windows = windows or [7, 13, 21, 31]
    print("\n=== Sensitivity on window w (G0 vs G1) ===", flush=True)
    rows = []
    for w in windows:
        d0, d1 = [], []
        for r in range(R):
            X0 = gen_g0_ar(T=T, seed=100 + r)
            X1 = gen_g1_shared(T=T, event_at=event_at, seed=200 + r)
            kw = dict(m=3, delay=1, window=w, theta3=0.08, stride=3)
            d0.append(delta_excess3(X0, event_at, **kw))
            d1.append(delta_excess3(X1, event_at, **kw))
        rows.append(
            {
                "w": w,
                "G0_mean_delta": float(np.mean(d0)),
                "G1_mean_delta": float(np.mean(d1)),
                "separation": float(np.mean(d1) - np.mean(d0)),
            }
        )
        print(
            f"  w={w}: G0 Δ={rows[-1]['G0_mean_delta']:+.4f}  "
            f"G1 Δ={rows[-1]['G1_mean_delta']:+.4f}",
            flush=True,
        )
    return {"windows": rows}


def sensitivity_theta(
    R: int = 10,
    thetas: list[float] | None = None,
    T: int = 1000,
    event_at: int = 500,
) -> dict:
    # excess3 typically lives near O(1); reference θ₃=0.08 saturates Φ₃ on
    # these generators. Probe the bulk of the distribution for occupancy contrast.
    thetas = thetas or [0.08, 0.50, 1.00, 1.20, 1.40, 1.50, 1.60]
    print("\n=== Sensitivity on θ₃ (Φ₃ occupancy, G1) ===", flush=True)
    rows = []
    split_frac = event_at / T
    for th in thetas:
        pre_o, post_o = [], []
        for r in range(R):
            X = gen_g1_shared(T=T, event_at=event_at, seed=300 + r)
            recd = excess3_series(X, m=3, delay=1, window=13, theta3=th, stride=3)
            op, oq = phi3_occupancy(recd["phi3"], split_frac)
            pre_o.append(op)
            post_o.append(oq)
        rows.append(
            {
                "theta3": th,
                "occ_pre": float(np.mean(pre_o)),
                "occ_post": float(np.mean(post_o)),
            }
        )
        print(
            f"  θ={th}: occ_pre={rows[-1]['occ_pre']:.3f} "
            f"occ_post={rows[-1]['occ_post']:.3f}",
            flush=True,
        )
    return {"thetas": rows}


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def fig_schematic():
    """Fig 1: conceptual pipeline (text boxes)."""
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    boxes = [
        (0.3, 1.2, "Multivariate\nsymbols S_t"),
        (2.3, 1.2, "TC  &  I_pair"),
        (4.3, 1.8, "Syn = [TC−I_pair]₊"),
        (4.3, 0.5, "Surp (vs indep.)"),
        (6.5, 1.2, "excess³\n0.6 Syn + 0.4 Surp"),
        (8.5, 1.2, "Φ₃ =\n1{ex>θ₃}"),
    ]
    for x, y, txt in boxes:
        ax.add_patch(
            plt.Rectangle((x, y), 1.6, 1.0, fill=True, facecolor="#EDE7F6", edgecolor="#5B4B8A", lw=1.5)
        )
        ax.text(x + 0.8, y + 0.5, txt, ha="center", va="center", fontsize=8)
    # arrows
    for x0, x1, y in [(1.9, 2.3, 1.7), (3.9, 4.3, 1.7), (5.9, 6.5, 1.7), (8.1, 8.5, 1.7)]:
        ax.annotate("", xy=(x1, y), xytext=(x0, y), arrowprops=dict(arrowstyle="->", color="#333"))
    ax.annotate("", xy=(5.1, 1.5), xytext=(5.1, 1.5), arrowprops=dict(arrowstyle="->"))
    ax.plot([5.1, 5.1], [1.5, 1.8], color="#333", lw=1)
    ax.set_title("excess³ pipeline (Level-3 continuous surplus → optional binary ticks)", fontsize=11)
    fig.tight_layout()
    path = FIG / "fig1_schematic.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


def fig_trajectories(results: dict):
    """Fig 2: mean ± band excess3(t) for G0 and G1."""
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    for ax, key, color, title in [
        (axes[0], "G0", "#607D8B", "G0 — independent AR(1)"),
        (axes[1], "G1", "#5B4B8A", "G1 — shared latent coupling jump"),
    ]:
        r = results[key]
        mu = np.asarray(r["traj_mean"])
        sd = np.asarray(r["traj_std"])
        t = np.arange(len(mu))
        ax.plot(t, mu, color=color, lw=1.5, label="mean excess³")
        ax.fill_between(t, mu - sd, mu + sd, color=color, alpha=0.25, label="±1 SD")
        ax.axvline(r["split"], color="crimson", ls="--", lw=1, label="split / event")
        ax.set_ylabel("excess³")
        ax.set_title(title)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
    axes[1].set_xlabel("time index (symbol units)")
    fig.suptitle("Continuous Level-3 surplus under null and planted joint reorganisation", fontsize=11)
    fig.tight_layout()
    path = FIG / "fig2_g0_g1_trajectories.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


def fig_nulls(results: dict):
    """Fig 3: null distributions of Δ for first realisation examples + observed."""
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=False)
    for ax, key, color in [(axes[0], "G0", "#607D8B"), (axes[1], "G1", "#5B4B8A")]:
        r = results[key]
        null = np.asarray(r["null_example"], dtype=float)
        obs = r["obs_example"]
        ax.hist(null, bins=18, color=color, alpha=0.75, edgecolor="white")
        ax.axvline(obs, color="crimson", lw=2, label=f"obs Δ={obs:+.3f}")
        ax.set_title(f"{key}: phase-shuffle null of Δexcess³\n(median p over R={r['R']}: {r['median_p']:.3f})")
        ax.set_xlabel("Δexcess³")
        ax.set_ylabel("count")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Full-statistic nulls (example realisation; inference uses full ensemble of p-values)", fontsize=10)
    fig.tight_layout()
    path = FIG / "fig3_nulls_delta.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


def fig_sensitivity(sens_w: dict, sens_th: dict):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    ws = [row["w"] for row in sens_w["windows"]]
    g0 = [row["G0_mean_delta"] for row in sens_w["windows"]]
    g1 = [row["G1_mean_delta"] for row in sens_w["windows"]]
    axes[0].plot(ws, g0, "o-", color="#607D8B", label="G0")
    axes[0].plot(ws, g1, "s-", color="#5B4B8A", label="G1")
    axes[0].axhline(0, color="gray", lw=0.8)
    axes[0].set_xlabel("window w")
    axes[0].set_ylabel("mean Δexcess³")
    axes[0].set_title("Sensitivity to window length")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    th = [row["theta3"] for row in sens_th["thetas"]]
    pre = [row["occ_pre"] for row in sens_th["thetas"]]
    post = [row["occ_post"] for row in sens_th["thetas"]]
    axes[1].plot(th, pre, "o-", color="#90A4AE", label="G1 Φ₃ occ. pre")
    axes[1].plot(th, post, "s-", color="#5B4B8A", label="G1 Φ₃ occ. post")
    axes[1].set_xlabel(r"$\theta_3$")
    axes[1].set_ylabel("Φ₃ occupancy")
    axes[1].set_title("Binary Level-3 occupancy vs threshold")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    path = FIG / "fig4_sensitivity.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


def fig_components_g1(T: int = 1200, event_at: int = 600, seed: int = 7):
    """Fig 5: mean trajectory is excess3; show single-run series for G1."""
    X = gen_g1_shared(T=T, event_at=event_at, seed=seed)
    recd = excess3_series(X, **REF)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    t = np.arange(len(recd["excess3"]))
    ax.plot(t, recd["excess3"], color="#5B4B8A", lw=1.2, label="excess³")
    ax.plot(t, recd["phi3"] * np.nanmax(recd["excess3"]), color="#E91E63", alpha=0.5, lw=0.8, label="Φ₃ (scaled)")
    ax.axvline(event_at, color="crimson", ls="--", lw=1)
    ax.set_xlabel("time")
    ax.set_ylabel("excess³")
    ax.set_title("G1 single realisation: continuous excess³ vs binary Φ₃ ticks")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = FIG / "fig5_continuous_vs_binary.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


def fig_summary_bars(results: dict):
    """Extra: mean Δ and frac significant across arms."""
    keys = [k for k in ("G0", "G1", "G2", "G3") if k in results]
    deltas = [results[k]["mean_delta"] for k in keys]
    fracs = [results[k]["frac_p_lt_0.05"] for k in keys]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
    colors = {"G0": "#607D8B", "G1": "#5B4B8A", "G2": "#00897B", "G3": "#FFA000"}
    axes[0].bar(keys, deltas, color=[colors[k] for k in keys])
    axes[0].axhline(0, color="gray", lw=0.8)
    axes[0].set_ylabel("mean Δexcess³")
    axes[0].set_title("Effect size by arm")
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[1].bar(keys, fracs, color=[colors[k] for k in keys])
    axes[1].axhline(0.05, color="crimson", ls="--", lw=1, label="5% line (ref.)")
    axes[1].set_ylabel("fraction of realisations with p < 0.05")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("Null extremity rate (phase-shuffle)")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    path = FIG / "fig6_arm_summary.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# Markdown summary for paper numbers
# ---------------------------------------------------------------------------


def write_summary(results: dict, sens_w: dict, sens_th: dict):
    lines = [
        "# excess³ synthetic validation summary",
        "",
        f"Reference params: m={REF['m']}, delay={REF['delay']}, w={REF['window']}, "
        f"θ₃={REF['theta3']}, stride={REF['stride']}, weights 0.6/0.4.",
        "",
        "## Arms",
        "",
        "| Arm | mean excess³ pre | mean excess³ post | mean Δ | median p | frac p<0.05 | Φ₃ occ pre | Φ₃ occ post |",
        "|-----|------------------|-------------------|--------|----------|-------------|------------|-------------|",
    ]
    for k, r in results.items():
        lines.append(
            f"| {k} | {r['mean_excess_pre']:.4f} | {r['mean_excess_post']:.4f} | "
            f"{r['mean_delta']:+.4f} | {r['median_p']:.3f} | {r['frac_p_lt_0.05']:.2f} | "
            f"{r['mean_phi3_occ_pre']:.3f} | {r['mean_phi3_occ_post']:.3f} |"
        )
    lines += ["", "## Window sensitivity (mean Δ)", ""]
    for row in sens_w["windows"]:
        lines.append(
            f"- w={row['w']}: G0 Δ={row['G0_mean_delta']:+.4f}, G1 Δ={row['G1_mean_delta']:+.4f}"
        )
    lines += ["", "## θ₃ sensitivity (G1 Φ₃ occupancy)", ""]
    for row in sens_th["thetas"]:
        lines.append(f"- θ={row['theta3']}: pre={row['occ_pre']:.3f}, post={row['occ_post']:.3f}")
    path = NOTES / "validation_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")

    def _default(o):
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))

    jpath = NOTES / "validation_results.json"
    serial = {
        "reference": REF,
        "arms": results,
        "sensitivity_window": sens_w,
        "sensitivity_theta": sens_th,
    }
    jpath.write_text(json.dumps(serial, indent=2, default=_default), encoding="utf-8")
    print(f"wrote {jpath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # R=25, B=99 as design; stride=3 keeps wall-time practical
    R = 25
    B = 99
    T = 1000
    event = 500

    fig_schematic()
    fig_components_g1(T=T, event_at=event)

    results = {}
    results["G0"] = run_arm("G0", gen_g0_ar, event_at=event, R=R, n_surr=B, T=T, base_seed=0)
    results["G1"] = run_arm("G1", gen_g1_shared, event_at=event, R=R, n_surr=B, T=T, base_seed=1000)
    results["G2"] = run_arm("G2", gen_g2_logistic, event_at=event, R=R, n_surr=B, T=T, base_seed=2000)
    results["G3"] = run_arm("G3", gen_g3_pairwise, event_at=event, R=R, n_surr=B, T=T, base_seed=3000)

    sens_w = sensitivity_window(R=10, T=T, event_at=event)
    sens_th = sensitivity_theta(R=10, T=T, event_at=event)

    fig_trajectories(results)
    fig_nulls(results)
    fig_sensitivity(sens_w, sens_th)
    fig_summary_bars(results)
    write_summary(results, sens_w, sens_th)
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
