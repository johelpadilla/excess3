# Joint-tuple counting moves the window-13 excess3 maximum into developed chaos

**Author:** Johel Padilla-Villanueva  
**ORCID:** [0000-0002-5797-6931](https://orcid.org/0000-0002-5797-6931)  
**Affiliation:** Department of Environmental Health, University of Puerto Rico Medical Sciences Campus  
**Contact:** johelpadilla@gmail.com  
**Date:** 25 September 2026  
**DOI:** [10.5281/zenodo.22970080](https://doi.org/10.5281/zenodo.22970080)  
**Version 1:** [10.5281/zenodo.22945800](https://doi.org/10.5281/zenodo.22945800)  
**License:** [CC BY 4.0](../LICENSE)

Version 2 of the accumulation-point note. Version 1 placed the window-13 excess3 maximum at r = 3.5675 because nested-recd ≤ 0.2.2 flattened joint tuples inside Syn. This version counts joint tuples with nested-recd 0.2.3 ([10.5281/zenodo.22970079](https://doi.org/10.5281/zenodo.22970079)). The window-13 maximum is at r = 3.95 (2.897 ± 0.006). Surprise and the collapse to about four joint tuples remain in the accumulation band. This note does not replace the methods specification [10.5281/zenodo.21385937](https://doi.org/10.5281/zenodo.21385937).

## Files

| Path | Role |
|------|------|
| `excess3_peak.pdf` | Article. The version-2 DOI is printed on the title page. |
| `excess3_peak.tex`, `references.bib` | Source |
| `figures/` | Four figures |
| `generated/` | Numeric tables |
| `data/corrected_flat.csv`, `data/corrected_agg.csv`, `data/mc_stations.json` | Joint-tuple recount, 25 September 2026 |
| `data/peak_*_20260924_145527.*` | Version-1 archive. Reproduced by `legacy_pooled_counting`. |
| `make_figures.py` | Draws the figures from the corrected aggregate joined to the version-1 columns the bug does not touch |

Build the PDF with TeX Live (`latexmk`, `natbib`, `booktabs`, `hyperref`):

```bash
latexmk -pdf excess3_peak.tex
```
