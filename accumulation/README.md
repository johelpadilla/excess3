# A low-diversity ordinal regime produces the excess3 peak near the logistic accumulation point

**Author:** Johel Padilla-Villanueva  
**ORCID:** [0000-0002-5797-6931](https://orcid.org/0000-0002-5797-6931)  
**Affiliation:** Department of Environmental Health, University of Puerto Rico Medical Sciences Campus  
**Contact:** johelpadilla@gmail.com  
**Date:** 24 September 2026  
**DOI:** [10.5281/zenodo.22945800](https://doi.org/10.5281/zenodo.22945800)  
**License:** [CC BY 4.0](../LICENSE)

This note is a separate preprint. It reports why the excess3 proxy peaks near the logistic accumulation point on the four diffusively coupled logistic maps of the foundations cascade. It does not replace the methods specification archived at [10.5281/zenodo.21385937](https://doi.org/10.5281/zenodo.21385937).

## Files

| Path | Role |
|------|------|
| `excess3_peak.pdf` | Article. The DOI is printed on the title page and in the data-availability statement. |
| `excess3_peak.tex`, `references.bib` | Source |
| `figures/` | Four figures included by the source |
| `generated/` | Numeric tables included by the source |
| `data/` | Decomposition of 24 September 2026 (`peak_flat`, `peak_agg`, and `peak_results`, stamp `20260924_145527`) |
| `make_figures.py` | Draws the figures from that archive |

`make_figures.py` reads the foundations working tree where the run was produced. The copies in `data/` are those same files.

Build the PDF with a TeX Live installation that provides `latexmk`, `natbib`, `booktabs`, and `hyperref`:

```bash
latexmk -pdf excess3_peak.tex
```
