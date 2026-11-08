# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Small first-party facade for archive reads and explicit local reproduction exports.

This module deliberately stays on the publisher side of the repository boundary: it reads committed
paper bundles, resolves their bibliography, and writes only caller-selected local sidecar output.
It does not execute pipelines, upload artifacts, or write back into any nirs4all repository.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .bibliography import Reference, build_bibliography
from .bundle import Bundle, read_bundle
from .model import Catalog, PaperView, load_catalog
from .model import load_paper as _load_paper_view
from .provenance import citation_cff, paper_bibtex
from .site import build_site, write_paper_sidecars


def provider_capabilities() -> dict[str, Any]:
    """Return the supported facade verbs and their archive-boundary constraints."""
    return {
        "provider": "nirs4all-papers",
        "executes": False,
        "writes": "local-output",
        "dependencies": ["PyYAML"],
        "optional_dependencies": {"current-reader": ["nirs4all-core"], "sdk-host-reader": ["nirs4all"]},
        "verbs": {
            "list_papers": "Read the committed papers catalog from a repository root.",
            "load_paper": "Compatibility alias for reading one paper bundle into its reproduction view model.",
            "load_paper_bundle": "Read one paper directory into its reproduction view model.",
            "inspect_bundle": "Inspect current V1 through Core and SDK owner JSON APIs, without fitted-object loading.",
            "build_methods_section": "Resolve method ids to bibliography references and citation mapping.",
            "citation": "Render one paper bundle's CITATION.cff text without writing files.",
            "bibtex": "Render one paper bundle's BibTeX entry without writing files.",
            "build_repro_page": "Build the static reproduction site into an explicit local output directory.",
            "export_sidecars": "Write one paper's reproduction sidecars into an explicit local output directory.",
        },
        "non_goals": [
            "runtime_execution",
            "upload_service",
            "ecosystem_writeback",
        ],
    }


def list_papers(root: str | Path, *, read_current: bool = False) -> Catalog:
    """Return the catalog loaded from ``root``."""
    return load_catalog(root, read_current=read_current)


def load_paper_bundle(paper_dir: str | Path, *, read_current: bool = False) -> PaperView:
    """Return the public reproduction view for one paper directory."""
    return _load_paper_view(paper_dir, read_current=read_current)


def load_paper(paper_dir: str | Path, *, read_current: bool = False) -> PaperView:
    """Compatibility alias for :func:`load_paper_bundle`."""
    return load_paper_bundle(paper_dir, read_current=read_current)


def inspect_bundle(
    path: str | Path, *, entrypoint: str | None = None, operation: str | None = None,
    memory_budget_bytes: int | None = None,
) -> Bundle:
    """Return detached current Core/SDK owner evidence without loading fitted objects."""
    return read_bundle(path, entrypoint=entrypoint, operation=operation, memory_budget_bytes=memory_budget_bytes)


def build_methods_section(method_ids: list[str]) -> dict[str, Any]:
    """Resolve method ids into a structured bibliography summary without rendering a page."""
    references, id_to_ref = build_bibliography(method_ids)
    return {
        "method_ids": list(method_ids),
        "references": [_reference_record(ref) for ref in references],
        "citation_map": {method_id: ref.number for method_id, ref in id_to_ref.items()},
        "reference_ids": {method_id: ref.id for method_id, ref in id_to_ref.items()},
    }


def citation(paper_dir: str | Path) -> str:
    """Return one paper bundle's ``CITATION.cff`` text without writing files."""
    return citation_cff(load_paper_bundle(paper_dir))


def bibtex(paper_dir: str | Path) -> str:
    """Return one paper bundle's BibTeX entry without writing files."""
    return paper_bibtex(load_paper_bundle(paper_dir))


def build_repro_page(
    root: str | Path, out: str | Path, io_wasm: str | Path | None = None, *, read_current: bool = False,
) -> Path:
    """Build the static reproduction site into ``out``."""
    return build_site(root, out, io_wasm=io_wasm, read_current=read_current)


def export_sidecars(paper_dir: str | Path, out: str | Path, *, read_current: bool = False) -> Path:
    """Write one paper's deposit sidecars into ``out/paper/<slug>/`` and return that crate path."""
    view = _load_paper_view(paper_dir, read_current=read_current)
    return write_paper_sidecars(view, out)


def _reference_record(ref: Reference) -> dict[str, Any]:
    return {
        "id": ref.id,
        "number": ref.number,
        "label": ref.label,
        "authors": ref.authors,
        "year": ref.year,
        "title": ref.title,
        "venue": ref.venue,
        "doi": ref.doi,
        "url": ref.url,
        "link": ref.link,
        "principle": ref.principle,
    }
