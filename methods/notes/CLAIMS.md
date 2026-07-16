# Claim checklist — excess³ preprint v0.1

| # | Claim | Section | Evidence |
|---|--------|---------|----------|
| 1 | Definition: 0.6 Syn + 0.4 Surp | §3 | eq. excess3; matches `recd_levels.py` (Counter joint fix) |
| 2 | Weights fixed a priori (falsifiability) | §3.4, tab params | Methods text |
| 3 | Continuous primary; Φ₃ secondary | §3.4, §7 | Fig 4–5; θ sensitivity |
| 4 | Proxy not full PID | §2 table, §4 | Comparative table |
| 5 | Phase-shuffle on full Δ | §5, §7 | Fig 3; p-values |
| 6 | Parallel nesting, no hard ⇒ chain | §3.5 RECD | Text + software |
| 7 | Not causation | §4 | Boundaries |
| 8 | Synthetic G0–G3 behave as predicted | §7 | Table results + figures |
| 9 | Toy XOR example reproduces excess3=1 | §3.5 | `scripts/toy_example.py` |

## Pre-specified success (design)

- [x] G0: median p not systematically < 0.05 *(median p = 0.560; frac = 4%)*
- [x] G1: ≥ 80% realisations with p < 0.05 *(92%; mean Δ = −0.0977, two-sided)*
- [x] Continuous separation more stable than Φ₃ under strict θ₃ *(sat. at ref θ₃; continuous Δ discriminates)*
- [x] No universal threshold claim for real data *(stated; sign of Δ is generator-dependent)*

## Arm summary after joint-count fix (R=25, B=99, T=1000)

| Arm | mean Δ | median p | frac p<0.05 | Note |
|-----|--------|----------|-------------|------|
| G0 | +0.0028 | 0.560 | 4% | near-null ✓ |
| G1 | −0.0977 | 0.010 | 92% | detectable; sign − (pairwise baseline up) |
| G2 | −0.0081 | 0.510 | 8% | near-null for this logistic design |
| G3 | −0.0482 | 0.080 | 40% | intermediate (not pure null) |

## Comprehension additions (reviewer feedback)

- [x] Toy numerical XOR example
- [x] Comparison table (II / O-info / PID / excess³)
- [x] Glossary table
- [x] Intuitive magnitude reading
- [x] Reporting checklist
- [x] Fig1 caption, weights row, phase-shuffle note
