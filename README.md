# excess³ — methods, Spanish introduction, and cross-disciplinary guide

**Author:** Johel Padilla-Villanueva  
**ORCID:** [0000-0002-5797-6931](https://orcid.org/0000-0002-5797-6931)  
**Contact:** johelpadilla@gmail.com · joel.padilla2@upr.edu  

**Repository:** https://github.com/johelpadilla/excess3  

This repository holds the **shared family** of three excess³ documents (one statistic, three roles). The **methods** preprint is the canonical specification.

| Folder | Document | Language | Role |
|--------|----------|----------|------|
| [`methods/`](methods/) | *excess³: A Pre-Specified Continuous Proxy…* | EN | Canonical definition, nulls, synthetic validation G0–G3 |
| [`intro/`](intro/) | *excess³: dependencia de orden 3…* | **ES** | Dense motivation, reading, integrated validation figures |
| [`primer/`](primer/) | *Understanding excess³…* | EN | Cross-disciplinary pedagogy, vignettes, teaching notes |

## Citation hierarchy

1. **Cite `methods/`** for equations, null protocol, reporting checklist, and claim-level validation.  
2. Use **`intro/`** for Spanish exposition and narrative results language.  
3. Use **`primer/`** for first contact, lab meetings, and teaching — not as an implementation source.

## Build PDFs

Requires a TeX distribution with `tcolorbox`, `tabularx`, `natbib`, `hyperref`, and (for the Spanish intro) `babel` with Spanish.

```bash
# Methods
cd methods
pdflatex Excess3_Methods_Synthetic_Validation.tex
bibtex Excess3_Methods_Synthetic_Validation
pdflatex Excess3_Methods_Synthetic_Validation.tex
pdflatex Excess3_Methods_Synthetic_Validation.tex

# Spanish introduction (reads figures + numbers from ../methods/)
cd ../intro
pdflatex Excess3_Introduccion_Accesible.tex
bibtex Excess3_Introduccion_Accesible
pdflatex Excess3_Introduccion_Accesible.tex
pdflatex Excess3_Introduccion_Accesible.tex

# English primer
cd ../primer
pdflatex Excess3_Cross_Disciplinary_Guide.tex
bibtex Excess3_Cross_Disciplinary_Guide
pdflatex Excess3_Cross_Disciplinary_Guide.tex
pdflatex Excess3_Cross_Disciplinary_Guide.tex
```

## Re-run synthetic validation (optional)

Precomputed ensemble outputs live in `methods/notes/`. To regenerate (needs NumPy/SciPy/Matplotlib and the Level-3 reference stack, e.g. [academy-learning-tau](https://github.com/johelpadilla/academy-learning-tau) / [systemictau](https://github.com/johelpadilla/systemictau) on `PYTHONPATH`):

```bash
cd methods
python3 scripts/generate_synthetic_validation.py   # long run
python3 scripts/fill_numbers_from_json.py
```

Software stack (related): https://doi.org/10.5281/zenodo.20576241  

**Level-3 implementation (code):** install [`nested-recd`](https://pypi.org/project/nested-recd/) **≥ 0.2** — continuous excess³, Φ₁–Φ₃, phase-shuffle nulls on `|Δ excess3|`.  
`systemictau` consumes it via `pip install "systemictau[nested]"` / `systemictau.nested`.

## Contract (short)

- `excess3 = 0.6·Syn + 0.4·Surp` with weights fixed a priori  
- Continuous excess³ primary; Φ₃ secondary  
- Inference on the full contrast (e.g. `|Δ|`) with phase-shuffle (or equivalent)  
- Proxy ≠ full PID; parallel RECD nesting (no hard Φ₁⇒Φ₂⇒Φ₃)  
- Dependence / surplus language — not causation  

## License

Manuscripts and figures in this repository are intended for distribution under  
[Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).

## Zenodo

**DOI:** [10.5281/zenodo.21385937](https://doi.org/10.5281/zenodo.21385937)

Versioned archival deposit of this repository (methods + intro ES + primer EN).

