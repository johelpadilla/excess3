#!/usr/bin/env python3
"""Reproducible toy windows for the excess³ paper (§ toy numerical example).

Matches academy-learning-tau `stp.core.recd_levels._synergy_and_surprise`
after joint/pair Counter fix (tuple frequencies, not flattened unique).
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import numpy as np

# XOR-like synergistic lock (pairs independent; triple determined)
WIN_XOR = np.array(
    [
        [0, 0, 0],
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
        [0, 0, 0],
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ],
    dtype=int,
)

# Pure triple lock (common driver; Syn residual can vanish after I_pair)
WIN_TRIPLE = np.array(
    [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
        [2, 2, 2],
        [2, 2, 2],
    ],
    dtype=int,
)


def entropy_from_counts(counts) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p + 1e-12)))


def breakdown(win: np.ndarray) -> dict:
    w, n = win.shape
    joint = [tuple(int(v) for v in row) for row in win]
    counter = Counter(joint)
    h_margs = []
    for k in range(n):
        _, c = np.unique(win[:, k], return_counts=True)
        h_margs.append(entropy_from_counts(c))
    h_joint = entropy_from_counts(list(counter.values()))
    tc = max(0.0, sum(h_margs) - h_joint)
    pair_mi = []
    for i, j in combinations(range(n), 2):
        pairs = list(zip(win[:, i].tolist(), win[:, j].tolist()))
        h2 = entropy_from_counts(list(Counter(pairs).values()))
        _, ci = np.unique(win[:, i], return_counts=True)
        hi = entropy_from_counts(ci)
        _, cj = np.unique(win[:, j], return_counts=True)
        hj = entropy_from_counts(cj)
        pair_mi.append(max(0.0, hi + hj - h2))
    i_pair = (n - 1) * float(np.mean(pair_mi))
    syn = max(0.0, tc - i_pair)
    surp_terms = []
    for u, cnt in counter.items():
        p_obs = cnt / w
        p_ind = 1.0
        for k, val in enumerate(u):
            p_ind *= max(float(np.mean(win[:, k] == val)), 1e-9)
        ratio = p_obs / max(p_ind, 1e-9)
        el = max(0.0, float(np.log2(ratio))) if ratio > 1 else 0.0
        surp_terms.append(
            {"s": u, "n": cnt, "p_obs": p_obs, "p_ind": p_ind, "log2r": float(np.log2(ratio)), "contrib": el * p_obs}
        )
    surp = float(sum(t["contrib"] for t in surp_terms))
    excess = 0.6 * syn + 0.4 * surp
    return {
        "H_margs": h_margs,
        "H_joint": h_joint,
        "TC": tc,
        "pair_mi": pair_mi,
        "I_pair": i_pair,
        "Syn": syn,
        "Surp": surp,
        "surp_terms": surp_terms,
        "excess3": excess,
        "counter": dict(counter),
    }


def main():
    for name, win in [("XOR", WIN_XOR), ("TRIPLE", WIN_TRIPLE)]:
        r = breakdown(win)
        print(f"=== {name} ===")
        print(f"TC={r['TC']:.4f} I_pair={r['I_pair']:.4f} Syn={r['Syn']:.4f} "
              f"Surp={r['Surp']:.4f} excess3={r['excess3']:.4f}")
        for t in r["surp_terms"]:
            print(f"  {t['s']}: n={t['n']} contrib={t['contrib']:.4f}")
        try:
            import sys
            from pathlib import Path

            stp = Path("/Users/johelpadilla/grok-safe/academy-learning-tau/src")
            if stp.is_dir():
                sys.path.insert(0, str(stp))
                from stp.core.recd_levels import _synergy_and_surprise

                print(f"  software excess3={_synergy_and_surprise(win):.4f}")
        except Exception as e:
            print("  software check skipped:", e)


if __name__ == "__main__":
    main()
