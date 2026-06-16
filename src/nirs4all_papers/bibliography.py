# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Map pipeline operators to curated literature references and emit a bibliography + BibTeX.

The seed (``data/bibliography.json``) is distilled from
``nirs4all-methods/docs/_extras/methods_bibliography.py``. Class names appear in two encodings
(fully-qualified module paths in ``pipeline.json`` and short class names in artifact filenames), and
abbreviations differ from the seed ids, so :func:`resolve_method` normalizes both to a stable id.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "bibliography.json"

_LATEX_ESCAPE = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def latex_escape(text: object) -> str:
    """Escape the BibTeX/LaTeX special characters so emitted ``.bib`` entries compile.

    Notably the seed's IKPLS DOI contains a bare ``#`` (a macro-parameter token) that would
    otherwise make pdfLaTeX fail with "Illegal parameter number".
    """
    return "".join(_LATEX_ESCAPE.get(c, c) for c in str(text))

# Normalized class token -> seed reference id. The token is the lowercased class name stripped of all
# non-alphanumerics, so "PLSRegression", "pls", "PLS-Regression" all collapse to "plsregression".
_SYNONYMS: dict[str, str] = {
    "plsregression": "pls", "pls": "pls", "plsr": "pls", "nipalspls": "pls",
    "simpls": "simpls",
    "ikpls": "ikpls", "improvedkernelpls": "ikpls",
    "opls": "opls", "orthogonalpls": "opls",
    "mbpls": "mbpls", "multiblockpls": "mbpls",
    "kernelpls": "kernel_pls_rbf", "kernelplsrbf": "kernel_pls_rbf", "rbfkernelpls": "kernel_pls_rbf",
    "standardnormalvariate": "snv", "snv": "snv",
    "robustnormalvariate": "rnv", "rnv": "rnv",
    "multiplicativescattercorrection": "msc", "msc": "msc",
    "extendedmultiplicativescattercorrection": "emsc", "emsc": "emsc", "extendedmsc": "emsc",
    "savitzkygolay": "savgol", "savgol": "savgol", "savitzkygolayfilter": "savgol",
    "firstderivative": "first_derivative", "firstderivate": "first_derivative",
    "secondderivative": "second_derivative", "secondderivate": "second_derivative",
    "derivative": "first_derivative", "derivate": "first_derivative",
    "detrend": "detrend", "detrending": "detrend",
    "gaussian": "gaussian_filter", "gaussianfilter": "gaussian_filter", "gaussiansmoothing": "gaussian_filter",
    "minmaxscaler": "minmax", "minmax": "minmax", "minmaxscaling": "minmax",
    "standardscaler": "standard_scaler", "standardisation": "standard_scaler",
    "standardization": "standard_scaler", "zscore": "standard_scaler",
    "pca": "pca", "principalcomponentanalysis": "pca",
    "pcr": "pcr", "principalcomponentregression": "pcr",
    "ridge": "ridge", "ridgeregression": "ridge", "ridgepls": "ridge",
    "kennardstone": "kennard_stone", "kennardstonesplitter": "kennard_stone",
    "spxy": "spxy", "spxysplitter": "spxy",
    "vip": "vip_select", "vipselect": "vip_select", "variableimportance": "vip_select",
    "cars": "cars_select", "carsselect": "cars_select",
    "ipls": "ipls_select", "intervalpls": "ipls_select", "iplsselect": "ipls_select",
    "pds": "pds", "piecewisedirectstandardization": "pds",
    "mixup": "mixup",
    "aompls": "aom_pls", "poppls": "aom_pls", "aomridge": "aom_pls", "aom": "aom_pls",
}


@dataclass
class Reference:
    """A resolved literature reference, optionally numbered for the on-page bibliography."""

    id: str
    label: str
    authors: str | None
    year: int | None
    title: str
    venue: str | None
    doi: str | None
    url: str | None
    principle: str | None
    number: int = 0

    @property
    def link(self) -> str | None:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url

    def to_bibtex(self) -> str:
        """A BibTeX ``@article``/``@misc`` entry keyed by the stable reference id."""
        btype = "article" if self.venue and self.year else "misc"
        fields: list[tuple[str, str]] = []
        if self.authors:
            fields.append(("author", self.authors.replace("; ", " and ")))
        fields.append(("title", self.title))
        if self.venue:
            fields.append(("journal", self.venue))
        if self.year:
            fields.append(("year", str(self.year)))
        if self.doi:
            fields.append(("doi", self.doi))
        if self.url and not self.doi:
            fields.append(("url", self.url))
        body = ",\n".join(f"  {k} = {{{latex_escape(v)}}}" for k, v in fields)
        return f"@{btype}{{{self.id},\n{body}\n}}"


@lru_cache(maxsize=1)
def _seed() -> dict[str, Any]:
    return json.loads(_DATA.read_text(encoding="utf-8")).get("references", {})


def _canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def resolve_method(short_name: str, raw: str = "") -> str | None:
    """Resolve an operator class name to a seed reference id, or ``None`` if uncited."""
    for candidate in (short_name, raw.rsplit(".", 1)[-1] if raw else ""):
        token = _canonical(candidate)
        if not token:
            continue
        if token in _SYNONYMS:
            return _SYNONYMS[token]
        if token in _seed():
            return token
    return None


def reference_for(method_id: str | None) -> Reference | None:
    """Build a :class:`Reference` for a resolved method id (``None`` -> ``None``)."""
    if not method_id:
        return None
    entry = _seed().get(method_id)
    if not isinstance(entry, dict):
        return None
    return Reference(
        id=method_id,
        label=str(entry.get("label") or method_id),
        authors=entry.get("authors"),
        year=int(entry["year"]) if isinstance(entry.get("year"), (int, float)) else None,
        title=str(entry.get("title") or entry.get("label") or method_id),
        venue=entry.get("venue"),
        doi=entry.get("doi"),
        url=entry.get("url"),
        principle=entry.get("principle"),
    )


def _citation_key(ref: Reference) -> str:
    """A content key so two method ids that cite the *same* paper collapse to one reference."""
    if ref.doi:
        return "doi:" + ref.doi.strip().lower()
    return f"{ref.title}|{ref.year}|{ref.venue}".strip().lower()


def build_bibliography(method_ids: list[str]) -> tuple[list[Reference], dict[str, Reference]]:
    """Resolve method ids to a de-duplicated, 1-numbered reference list.

    Returns ``(ordered_refs, id_to_ref)``: references are merged by *citation content* (so e.g.
    ``minmax`` and ``standard_scaler``, which both cite scikit-learn, appear once), while
    ``id_to_ref`` maps every method id to the single shared reference for its citation superscript.
    """
    by_key: dict[str, Reference] = {}
    id_to_ref: dict[str, Reference] = {}
    order: list[Reference] = []
    for mid in method_ids:
        if not mid or mid in id_to_ref:
            continue
        ref = reference_for(mid)
        if ref is None:
            continue
        key = _citation_key(ref)
        if key in by_key:
            id_to_ref[mid] = by_key[key]
        else:
            by_key[key] = ref
            order.append(ref)
            id_to_ref[mid] = ref
    for i, ref in enumerate(order, start=1):
        ref.number = i
    return order, id_to_ref


def references_to_bibtex(refs: list[Reference]) -> str:
    """Concatenate BibTeX entries with a generated-file header."""
    header = "% Generated by nirs4all-papers — methods bibliography for one reproduction document.\n"
    return header + "\n\n".join(ref.to_bibtex() for ref in refs) + "\n"
