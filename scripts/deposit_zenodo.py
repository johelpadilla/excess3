#!/usr/bin/env python3
"""Deposit the excess3 family to Zenodo and wire the DOI into PDFs.

Workflow
--------
1. Create deposition with prereserved DOI (needs ZENODO_TOKEN).
2. Write DOI into LaTeX macros, rebuild PDFs, refresh package zip.
3. Upload zip + individual PDFs + metadata.
4. Publish deposition.
5. Print DOI / record URL for git tag notes.

Environment
-----------
  ZENODO_TOKEN   Personal access token with deposit:write + deposit:actions
                 https://zenodo.org/account/settings/applications/tokens/new/
  ZENODO_BASE    Optional, default https://zenodo.org
                 Use https://sandbox.zenodo.org for dry-runs (separate token).

Usage
-----
  export ZENODO_TOKEN=...
  python3 scripts/deposit_zenodo.py              # full: reserve → PDFs → upload → publish
  python3 scripts/deposit_zenodo.py --reserve-only
  python3 scripts/deposit_zenodo.py --doi 10.5281/zenodo.XXXX  # skip reserve; inject + package
  python3 scripts/deposit_zenodo.py --upload-only --deposition-id ID
  python3 scripts/deposit_zenodo.py --publish-only --deposition-id ID
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
META_PATH = ROOT / "zenodo" / "metadata.json"
STATE_PATH = ROOT / "zenodo" / "deposition_state.json"
PACKAGE_PATH = ROOT / "zenodo" / "excess3-v1.0.1.zip"

TEX_FILES = [
    ROOT / "methods" / "Excess3_Methods_Synthetic_Validation.tex",
    ROOT / "intro" / "Excess3_Introduccion_Accesible.tex",
    ROOT / "primer" / "Excess3_Cross_Disciplinary_Guide.tex",
]

BUILD = [
    ("methods", "Excess3_Methods_Synthetic_Validation"),
    ("intro", "Excess3_Introduccion_Accesible"),
    ("primer", "Excess3_Cross_Disciplinary_Guide"),
]


def token_and_base() -> tuple[str, str]:
    tok = os.environ.get("ZENODO_TOKEN", "").strip()
    if not tok:
        for cand in (ROOT / ".zenodo_token", Path.home() / ".zenodo_token"):
            if cand.is_file():
                tok = cand.read_text(encoding="utf-8").strip().splitlines()[0].strip()
                if tok:
                    break
    if not tok:
        sys.exit(
            "Missing ZENODO_TOKEN.\n"
            "Create one at https://zenodo.org/account/settings/applications/tokens/new/\n"
            "Scopes: deposit:write and deposit:actions\n"
            "Then:  export ZENODO_TOKEN='...'\n"
            "       python3 scripts/deposit_zenodo.py"
        )
    base = os.environ.get("ZENODO_BASE", "https://zenodo.org").rstrip("/")
    return tok, base


def headers(tok: str, json_body: bool = False) -> dict:
    h = {"Authorization": f"Bearer {tok}"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def load_metadata() -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {STATE_PATH}")


def create_deposition(tok: str, base: str, metadata: dict) -> dict:
    # Step 1: empty deposition (prereserves DOI)
    r = requests.post(
        f"{base}/api/deposit/depositions",
        params={},
        json={},
        headers=headers(tok, json_body=True),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"Create deposition failed {r.status_code}: {r.text}")
    dep = r.json()
    dep_id = dep["id"]
    doi = dep["metadata"]["prereserve_doi"]["doi"]
    print(f"Deposition id={dep_id}  reserved DOI={doi}")

    # Step 2: put full metadata
    body = {"metadata": metadata}
    r = requests.put(
        f"{base}/api/deposit/depositions/{dep_id}",
        data=json.dumps(body),
        headers=headers(tok, json_body=True),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"Put metadata failed {r.status_code}: {r.text}")
    dep = r.json()
    state = {
        "deposition_id": dep_id,
        "doi": doi,
        "doi_url": f"https://doi.org/{doi}",
        "bucket": dep["links"]["bucket"],
        "html": dep["links"]["html"],
        "base": base,
        "created": date.today().isoformat(),
    }
    save_state(state)
    return state


def inject_doi(doi: str) -> None:
    """Activate \\ExcessThreeDOI and add title-page / data-code mentions."""
    doi_url = f"https://doi.org/{doi}"
    for path in TEX_FILES:
        text = path.read_text(encoding="utf-8")
        # Ensure macro exists / is active
        if r"\newcommand{\ExcessThreeDOI}" in text:
            text = re.sub(
                r"%?\s*\\newcommand\{\\ExcessThreeDOI\}\{[^}]*\}",
                rf"\\newcommand{{\\ExcessThreeDOI}}{{{doi}}}",
                text,
                count=1,
            )
        else:
            text = text.replace(
                r"\newcommand{\ExcessThreeRepoShort}{github.com/johelpadilla/excess3}",
                r"\newcommand{\ExcessThreeRepoShort}{github.com/johelpadilla/excess3}"
                + "\n"
                + rf"\newcommand{{\ExcessThreeDOI}}{{{doi}}}"
                + "\n"
                + rf"\newcommand{{\ExcessThreeDOIURL}}{{{doi_url}}}",
            )
        if r"\newcommand{\ExcessThreeDOIURL}" in text:
            text = re.sub(
                r"\\newcommand\{\\ExcessThreeDOIURL\}\{[^}]*\}",
                rf"\\newcommand{{\\ExcessThreeDOIURL}}{{{doi_url}}}",
                text,
                count=1,
            )
        else:
            # after ExcessThreeDOI
            text = text.replace(
                rf"\newcommand{{\ExcessThreeDOI}}{{{doi}}}",
                rf"\newcommand{{\ExcessThreeDOI}}{{{doi}}}"
                + "\n"
                + rf"\newcommand{{\ExcessThreeDOIURL}}{{{doi_url}}}",
            )

        # Title date line: add DOI under repository if missing
        if r"\ExcessThreeDOI" not in text.split(r"\date{")[1].split("}")[0] if r"\date{" in text else "":
            # methods EN
            text = text.replace(
                r"\small Repository: \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}}",
                r"\small Repository: \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}\\[0.15em]"
                r"\small DOI: \href{\ExcessThreeDOIURL}{\ExcessThreeDOI}}",
            )
            # intro ES
            text = text.replace(
                r"\small Repositorio: \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}}",
                r"\small Repositorio: \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}\\[0.15em]"
                r"\small DOI: \href{\ExcessThreeDOIURL}{\ExcessThreeDOI}}",
            )

        # Data/code: ensure DOI sentence
        if "Zenodo release" in text or "release de Zenodo" in text or "Zenodo record" in text:
            if r"\ExcessThreeDOI" not in text[text.find("Data and code") if "Data and code" in text else 0 :]:
                pass  # patched below with explicit blocks

        # Methods data block
        text = text.replace(
            "A versioned archival DOI will be added upon Zenodo release.",
            r"Archival DOI: \href{\ExcessThreeDOIURL}{\ExcessThreeDOI}.",
        )
        text = text.replace(
            r"El DOI de archivo se a\~nadir\'a en el release de Zenodo.",
            r"DOI de archivo: \href{\ExcessThreeDOIURL}{\ExcessThreeDOI}.",
        )

        # Primer companions: add DOI item if missing
        if "Shared repository" in text and r"\ExcessThreeDOI" not in text[
            text.find("Shared repository") : text.find("Shared repository") + 400
        ]:
            text = text.replace(
                r"""  \item \textbf{Shared repository:}
  \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}
  (all three documents, figures, and validation outputs).""",
                r"""  \item \textbf{Shared repository:}
  \href{\ExcessThreeRepo}{\ExcessThreeRepoShort}
  (all three documents, figures, and validation outputs).
  \item \textbf{Archival DOI:}
  \href{\ExcessThreeDOIURL}{\ExcessThreeDOI}.""",
            )

        path.write_text(text, encoding="utf-8")
        print(f"Injected DOI into {path.relative_to(ROOT)}")


def rebuild_pdfs() -> None:
    for folder, stem in BUILD:
        cwd = ROOT / folder
        for _ in range(2):
            r = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                cwd=cwd,
                capture_output=True,
            )
            out = (r.stdout or b"") + (r.stderr or b"")
            out_s = out.decode("utf-8", errors="replace")
            if r.returncode != 0 and "Output written" not in out_s:
                print(out_s[-2000:])
                sys.exit(f"pdflatex failed in {folder}")
        # one bibtex + two more for citations if .bib present
        bib = cwd / f"{stem}.aux"
        if bib.exists():
            subprocess.run(["bibtex", stem], cwd=cwd, capture_output=True)
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                    cwd=cwd,
                    capture_output=True,
                )
        log = (cwd / f"{stem}.log").read_text(errors="replace")
        if re.search(r"^! ", log, re.M):
            sys.exit(f"LaTeX errors in {folder}")
        over = re.findall(r"Overfull \\hbox", log)
        print(f"Built {folder}/{stem}.pdf  overfulls={len(over)}")


def update_readme_citation(doi: str) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    doi_url = f"https://doi.org/{doi}"
    block = (
        f"## Zenodo\n\n"
        f"**DOI:** [{doi}]({doi_url})\n\n"
        f"Versioned archival deposit of this repository (methods + intro ES + primer EN).\n"
    )
    if "## Zenodo" in text:
        text = re.sub(
            r"## Zenodo\n\n.*?(?=\n## |\Z)",
            block + "\n",
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + block
    readme.write_text(text, encoding="utf-8")

    cff = ROOT / "CITATION.cff"
    c = cff.read_text(encoding="utf-8")
    if "doi:" in c:
        c = re.sub(r"^doi:.*$", f'doi: "{doi}"', c, flags=re.M)
    else:
        c = c.replace(
            'repository-code: "https://github.com/johelpadilla/excess3"',
            f'repository-code: "https://github.com/johelpadilla/excess3"\ndoi: "{doi}"',
        )
    if "version:" in c:
        c = re.sub(r'^version: ".*"$', 'version: "1.0.1"', c, flags=re.M)
    cff.write_text(c, encoding="utf-8")
    print("Updated README.md and CITATION.cff")


def update_bib_entries(doi: str) -> None:
    doi_url = f"https://doi.org/{doi}"
    for bib in [
        ROOT / "methods" / "references.bib",
        ROOT / "intro" / "references.bib",
        ROOT / "primer" / "references.bib",
    ]:
        t = bib.read_text(encoding="utf-8")
        # Padilla2026excess3 family self-cite
        t = re.sub(
            r"(@misc\{Padilla2026excess3,.*?note\s*=\s*\{)[^}]*(\})",
            rf'\1Canonical methods preprint; DOI {doi}; repo https://github.com/johelpadilla/excess3\2',
            t,
            count=1,
            flags=re.S,
        )
        if "doi" not in t[t.find("Padilla2026excess3") : t.find("Padilla2026excess3") + 400]:
            t = t.replace(
                "@misc{Padilla2026excess3,\n",
                "@misc{Padilla2026excess3,\n"
                f'  doi          = {{{doi}}},\n'
                f'  url          = {{{doi_url}}},\n',
            )
        bib.write_text(t, encoding="utf-8")
        print(f"Updated {bib.relative_to(ROOT)}")


def make_package() -> Path:
    PACKAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PACKAGE_PATH.exists():
        PACKAGE_PATH.unlink()
    include_dirs = ["methods", "intro", "primer"]
    include_root = ["README.md", "LICENSE", "CITATION.cff", ".gitignore"]
    with zipfile.ZipFile(PACKAGE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in include_root:
            p = ROOT / name
            if p.exists():
                zf.write(p, arcname=name)
        for d in include_dirs:
            base = ROOT / d
            for path in base.rglob("*"):
                if path.is_dir():
                    continue
                if path.suffix in {".aux", ".log", ".out", ".toc", ".blg", ".bbl", ".synctex.gz"}:
                    continue
                if path.name == ".DS_Store":
                    continue
                zf.write(path, arcname=str(path.relative_to(ROOT)))
    print(f"Package {PACKAGE_PATH} ({PACKAGE_PATH.stat().st_size // 1024} KB)")
    return PACKAGE_PATH


def upload_files(tok: str, base: str, state: dict) -> None:
    bucket = state["bucket"]
    dep_id = state["deposition_id"]
    files = [
        PACKAGE_PATH,
        ROOT / "methods" / "Excess3_Methods_Synthetic_Validation.pdf",
        ROOT / "intro" / "Excess3_Introduccion_Accesible.pdf",
        ROOT / "primer" / "Excess3_Cross_Disciplinary_Guide.pdf",
    ]
    for path in files:
        if not path.exists():
            sys.exit(f"Missing upload file: {path}")
        url = f"{bucket}/{path.name}"
        print(f"Uploading {path.name} ...")
        with path.open("rb") as fp:
            r = requests.put(url, data=fp, headers=headers(tok), timeout=600)
        if r.status_code not in (200, 201):
            sys.exit(f"Upload failed for {path.name}: {r.status_code} {r.text}")
    # refresh state files list
    r = requests.get(
        f"{base}/api/deposit/depositions/{dep_id}",
        headers=headers(tok),
        timeout=60,
    )
    r.raise_for_status()
    state["files"] = [f["filename"] for f in r.json().get("files", [])]
    save_state(state)


def publish(tok: str, base: str, dep_id: int) -> dict:
    r = requests.post(
        f"{base}/api/deposit/depositions/{dep_id}/actions/publish",
        headers=headers(tok),
        timeout=120,
    )
    if r.status_code not in (200, 201, 202):
        sys.exit(f"Publish failed {r.status_code}: {r.text}")
    dep = r.json()
    print("PUBLISHED")
    print("  DOI:", dep.get("doi") or dep.get("metadata", {}).get("doi"))
    print("  record:", dep.get("links", {}).get("record_html") or dep.get("links", {}).get("latest_html"))
    return dep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reserve-only", action="store_true")
    ap.add_argument("--upload-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    ap.add_argument("--doi", help="Use existing DOI (skip reserve)")
    ap.add_argument("--deposition-id", type=int)
    ap.add_argument("--no-publish", action="store_true", help="Stop after upload")
    args = ap.parse_args()

    if args.publish_only:
        tok, base = token_and_base()
        dep_id = args.deposition_id
        if not dep_id and STATE_PATH.exists():
            dep_id = json.loads(STATE_PATH.read_text())["deposition_id"]
        if not dep_id:
            sys.exit("Need --deposition-id")
        publish(tok, base, dep_id)
        return

    if args.upload_only:
        tok, base = token_and_base()
        state = json.loads(STATE_PATH.read_text())
        if args.deposition_id:
            state["deposition_id"] = args.deposition_id
        make_package()
        upload_files(tok, base, state)
        if not args.no_publish:
            publish(tok, base, state["deposition_id"])
        return

    metadata = load_metadata()
    if args.doi:
        doi = args.doi
        state = {
            "deposition_id": args.deposition_id,
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}",
        }
        if STATE_PATH.exists():
            state = {**json.loads(STATE_PATH.read_text()), **state}
    else:
        tok, base = token_and_base()
        state = create_deposition(tok, base, metadata)
        doi = state["doi"]

    inject_doi(doi)
    update_readme_citation(doi)
    update_bib_entries(doi)
    rebuild_pdfs()
    make_package()

    if args.reserve_only:
        print("Reserved and local files updated. Review PDFs, then re-run without --reserve-only")
        print("or: python3 scripts/deposit_zenodo.py --upload-only && publish")
        return

    tok, base = token_and_base()
    # refresh bucket if needed
    if "bucket" not in state or not state.get("bucket"):
        r = requests.get(
            f"{base}/api/deposit/depositions/{state['deposition_id']}",
            headers=headers(tok),
            timeout=60,
        )
        r.raise_for_status()
        state["bucket"] = r.json()["links"]["bucket"]
        save_state(state)

    upload_files(tok, base, state)
    if args.no_publish:
        print(f"Uploaded. Review at {state.get('html')} then publish.")
        return
    publish(tok, base, state["deposition_id"])


if __name__ == "__main__":
    main()
