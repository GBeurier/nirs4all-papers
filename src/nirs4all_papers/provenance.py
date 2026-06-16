# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Emit the machine-readable deposit sidecars: ``CITATION.cff`` and an RO-Crate ``ro-crate-metadata``.

A nirs4all ``.n4a`` is produced by the Python library (not by ``dag-ml``), so a published run rarely
carries a ``dag-ml`` research-provenance package. We therefore *synthesize* the RO-Crate here —
including the author / license / citation entities that ``dag-ml`` deliberately does not emit — from
the bundle fingerprints + ``paper.yaml``. RO-Crate JSON-LD is designed to be extended this way.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .bibliography import latex_escape

if TYPE_CHECKING:
    from .model import Author, PaperView

_RO_CRATE_CONTEXT = "https://w3id.org/ro/crate/1.1/context"


_ORG_HINTS = (
    "ecosystem", "lab", "team", "group", "consortium", "institute",
    "university", "inc", "ltd", "gmbh", "centre", "center", "project",
)


def _is_entity(name: str) -> bool:
    """Heuristic: treat a comma-less name as an organisation (CFF entity, not a person).

    Person names are "First Last" with capitalised tokens; an org has a lowercase token
    (e.g. "nirs4all ecosystem") or a known org keyword. Used to avoid splitting an org into
    bogus family/given names in CFF.
    """
    if "," in name:
        return False
    tokens = name.split()
    if len(tokens) == 1:
        return True
    low = name.lower()
    if any(h in low for h in _ORG_HINTS):
        return True
    # A person name is "First Last" with capitalised tokens (allowing lowercase particles like
    # "van der"). Treat as an organisation only when *every* alphabetic token is lowercase
    # (e.g. "nirs4all ecosystem") — so "van der Berg" stays a person.
    alpha = [t for t in tokens if t[:1].isalpha()]
    return bool(alpha) and all(t[:1].islower() for t in alpha)


def _split_name(full: str) -> tuple[str, str]:
    """Split a display name into ``(family, given)`` — handles "Last, First" and "First Last"."""
    full = full.strip()
    if "," in full:
        family, given = (p.strip() for p in full.split(",", 1))
        return family, given
    parts = full.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


_CC_LICENSES = {
    "cc-by-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "cc-by-sa-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "cc-by-nc-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "cc0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}


def _license_id(license_str: str) -> str:
    """Resolve a license string to a canonical URL ``@id`` (SPDX / Creative Commons), else a fragment."""
    key = str(license_str).strip().lower()
    if key in _CC_LICENSES:
        return _CC_LICENSES[key]
    # SPDX expression (no spaces, looks like an SPDX id) -> the SPDX license page.
    if key and " " not in key and "or" not in key.split() and "and" not in key.split():
        return f"https://spdx.org/licenses/{str(license_str).strip()}.html"
    return "#manuscript-license"


def _author_id(author: Author, idx: int) -> str:
    if author.orcid:
        orcid = author.orcid.strip()
        return orcid if orcid.startswith("http") else f"https://orcid.org/{orcid}"
    return f"#author-{idx}"


def citation_cff(paper: PaperView) -> str:
    """Render a CFF 1.2.0 citation file (hand-built YAML; avoids a yaml dump dependency on order)."""
    lines: list[str] = [
        "cff-version: 1.2.0",
        'message: "If you use this reproduction bundle, please cite the associated paper."',
        f'title: {_yaml_str(paper.title)}',
    ]
    if paper.abstract:
        lines.append(f"abstract: {_yaml_str(paper.abstract)}")
    lines.append("authors:")
    if paper.authors:
        for a in paper.authors:
            if _is_entity(a.name):
                lines.append(f"  - name: {_yaml_str(a.name)}")
                if a.affiliation:
                    lines.append(f"    affiliation: {_yaml_str(a.affiliation)}")
                continue
            family, given = _split_name(a.name)
            lines.append(f"  - family-names: {_yaml_str(family)}")
            if given:
                lines.append(f"    given-names: {_yaml_str(given)}")
            if a.orcid:
                orcid = a.orcid if a.orcid.startswith("http") else f"https://orcid.org/{a.orcid}"
                lines.append(f"    orcid: {_yaml_str(orcid)}")
            if a.affiliation:
                lines.append(f"    affiliation: {_yaml_str(a.affiliation)}")
    else:
        lines.append('  - name: "nirs4all ecosystem"')
    date = paper.meta.get("date")
    if date:
        lines.append(f"date-released: {_yaml_str(date)}")
    if paper.doi:
        lines.append(f"doi: {_yaml_str(paper.doi)}")
    version = paper.meta.get("version")
    if version:
        lines.append(f"version: {_yaml_str(version)}")
    # Machine-readable identifiers: the paper DOI and the reproducibility-bundle fingerprint
    # (NOT the nirs4all library version, which is software metadata, not the artifact version).
    lines.append("identifiers:")
    if paper.doi:
        lines.append("  - type: doi")
        lines.append(f"    value: {_yaml_str(paper.doi)}")
        lines.append('    description: "Paper DOI"')
    lines.append("  - type: other")
    lines.append(f"    value: {_yaml_str('nirs4all-bundle:' + paper.bundle.fingerprint)}")
    _fp_desc = "Reproducibility bundle fingerprint (SHA-256), produced with nirs4all " + paper.bundle.nirs4all_version
    lines.append(f"    description: {_yaml_str(_fp_desc)}")
    keywords = paper.keywords
    if keywords:
        lines.append("keywords:")
        lines.extend(f"  - {_yaml_str(k)}" for k in keywords)
    ds = paper.dataset
    if paper.references or ds.get("doi"):
        lines.append("references:")
        if ds.get("doi"):
            lines.append("  - type: data")
            lines.append(f"    title: {_yaml_str(ds.get('name') or 'Calibration dataset')}")
            lines.append("    authors:")
            lines.append(f"      - name: {_yaml_str(ds.get('name') or 'Dataset providers')}")
            lines.append(f"    doi: {_yaml_str(ds.get('doi'))}")
        for ref in paper.references:
            lines.append("  - type: article")
            lines.append(f"    title: {_yaml_str(ref.title)}")
            # CFF requires every reference to carry at least one author.
            lines.append("    authors:")
            pieces = [p.strip() for p in ref.authors.split(";")] if ref.authors else []
            pieces = [p for p in pieces if p]
            if not pieces:
                lines.append('      - name: "Unknown"')
            for piece in pieces:
                if _is_entity(piece):
                    lines.append(f"      - name: {_yaml_str(piece)}")
                    continue
                family, given = _split_name(piece)
                lines.append(f"      - family-names: {_yaml_str(family)}")
                if given:
                    lines.append(f"        given-names: {_yaml_str(given)}")
            if ref.venue:
                lines.append(f"    journal: {_yaml_str(ref.venue)}")
            if ref.year:
                lines.append(f"    year: {ref.year}")
            if ref.doi:
                lines.append(f"    doi: {_yaml_str(ref.doi)}")
    return "\n".join(lines) + "\n"


def ro_crate(paper: PaperView, crate_files: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an RO-Crate 1.1 metadata graph describing the reproduction bundle.

    ``crate_files`` is a list of ``{name, size, sha256, encodingFormat}`` for the files written into
    the crate directory (the ``.n4a``, ``pipeline.json``, sidecars, the page).
    """
    graph: list[dict[str, Any]] = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        }
    ]

    author_refs = [{"@id": _author_id(a, i)} for i, a in enumerate(paper.authors, start=1)]

    root: dict[str, Any] = {
        "@id": "./",
        "@type": "Dataset",
        "name": f"Reproduction bundle — {paper.title}",
        "description": paper.abstract or "nirs4all reproduction document and pipeline replay bundle.",
        "mainEntity": {"@id": "pipeline.json"},
        "hasPart": [{"@id": f["name"]} for f in crate_files],
        "dagml:nirs4all_version": paper.bundle.nirs4all_version,
    }
    if author_refs:
        root["author"] = author_refs
    if paper.year:
        root["datePublished"] = f"{paper.year}"
    license_id = _license_id(paper.manuscript_license) if paper.manuscript_license else None
    if license_id:
        root["license"] = {"@id": license_id}
    if paper.doi:
        root["citation"] = {"@id": f"https://doi.org/{paper.doi}"}
    ds = paper.dataset
    dataset_id = (f"https://doi.org/{ds['doi']}" if ds.get("doi") else "#dataset") if (ds.get("doi") or ds.get("name")) else None
    if dataset_id:
        root["mentions"] = [{"@id": dataset_id}]
    graph.append(root)

    if dataset_id:
        dataset_entity: dict[str, Any] = {"@id": dataset_id, "@type": "Dataset", "name": ds.get("name") or "Calibration dataset"}
        if ds.get("doi"):
            dataset_entity["identifier"] = ds["doi"]
        if ds.get("target"):
            dataset_entity["variableMeasured"] = ds["target"]
        graph.append(dataset_entity)

    # Authors as Person entities (ORCID @id where available).
    for i, a in enumerate(paper.authors, start=1):
        person: dict[str, Any] = {"@id": _author_id(a, i), "@type": "Person", "name": a.name}
        if a.affiliation:
            person["affiliation"] = a.affiliation
        graph.append(person)

    # The published article.
    if paper.doi:
        article: dict[str, Any] = {
            "@id": f"https://doi.org/{paper.doi}",
            "@type": "ScholarlyArticle",
            "name": paper.title,
        }
        if author_refs:
            article["author"] = author_refs
        if paper.venue:
            article["publication"] = paper.venue
        graph.append(article)

    if license_id:
        graph.append({"@id": license_id, "@type": "CreativeWork", "name": str(paper.manuscript_license)})

    # File entities (checksum-rich) for every deposited file. pipeline.json is also the crate's
    # main entity — the computational workflow — so it carries the workflow typing + fingerprints.
    for f in crate_files:
        entity: dict[str, Any] = {
            "@id": f["name"],
            "@type": "File",
            "name": f["name"],
            "contentSize": f.get("size"),
            "encodingFormat": f.get("encodingFormat", "application/octet-stream"),
            "sha256": f.get("sha256"),
        }
        if f["name"] == "pipeline.json":
            entity["@type"] = ["File", "SoftwareSourceCode", "ComputationalWorkflow"]
            entity["programmingLanguage"] = "Python"
            entity["softwareVersion"] = f"nirs4all {paper.bundle.nirs4all_version}"
            entity["dagml:pipeline_uid"] = paper.bundle.pipeline_uid
            entity["dagml:bundle_fingerprint"] = paper.bundle.fingerprint
            entity["step"] = [_step_ld(sv) for sv in paper.steps]
        graph.append(entity)

    return {"@context": _RO_CRATE_CONTEXT, "@graph": graph}


def _step_ld(step_view: Any) -> dict[str, Any]:
    info = step_view.info
    entity: dict[str, Any] = {
        "@type": "HowToStep",
        "position": info.index,
        "name": info.short_name,
        "dagml:operator": info.raw,
        "dagml:role": info.kind,
    }
    if info.params:
        entity["dagml:params"] = info.params
    if step_view.reference and step_view.reference.doi:
        entity["citation"] = {"@id": f"https://doi.org/{step_view.reference.doi}"}
    return entity


def _yaml_str(value: Any) -> str:
    """A double-quoted YAML scalar, with embedded quotes/backslashes/newlines escaped."""
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{text}"'


def paper_bibtex(paper: PaperView) -> str:
    """A BibTeX entry for the paper itself, synthesized from ``paper.yaml``."""
    first = paper.authors[0].name if paper.authors else "nirs4all"
    family, _ = _split_name(first)
    key = f"{family.lower() or 'nirs4all'}{paper.year or ''}".replace(" ", "")
    btype = "article" if paper.venue else "misc"
    fields: list[tuple[str, str]] = []
    if paper.authors:
        fields.append(("author", " and ".join(a.name for a in paper.authors)))
    fields.append(("title", paper.title))
    if paper.venue:
        fields.append(("journal", str(paper.venue)))
    if paper.year:
        fields.append(("year", str(paper.year)))
    if paper.doi:
        fields.append(("doi", str(paper.doi)))
    body = ",\n".join(f"  {k} = {{{latex_escape(v)}}}" for k, v in fields)
    return f"@{btype}{{{key},\n{body}\n}}"


def reproduction_commands(paper: PaperView) -> list[tuple[str, str]]:
    """A copy-pasteable reproduction snippet (lines of ``(css_class, text)``)."""
    version = paper.bundle.nirs4all_version
    spec = f'"nirs4all=={version}"' if version and version != "—" else "nirs4all"
    return [
        ("c", "# 1. install the exact library version this bundle was produced with"),
        ("k", f"pip install {spec}"),
        ("", ""),
        ("c", "# 2. re-run the published pipeline on your own spectra X (n_samples x n_wavelengths)"),
        ("", "from nirs4all.pipeline.bundle import BundleLoader"),
        ("", f'bundle = BundleLoader("{paper.bundle_filename}")'),
        ("", "y_pred = bundle.predict(X)   # full preprocessing + CV ensemble + inverse target transform"),
    ]
