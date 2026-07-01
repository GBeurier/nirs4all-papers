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
from .model import Catalog, PaperView, load_catalog, load_paper
from .site import build_site, write_paper_sidecars


def provider_capabilities() -> dict[str, Any]:
    """Return the supported facade verbs and their archive-boundary constraints."""
    return {
        "provider": "nirs4all-papers",
        "executes": False,
        "writes": "local_output",
        "dependencies": ["PyYAML"],
        "verbs": {
            "list_papers": "Read the committed papers catalog from a repository root.",
            "load_paper_bundle": "Read one paper directory into its reproduction view model.",
            "inspect_bundle": "Inspect a deposited .n4a archive without importing nirs4all core.",
            "build_methods_section": "Resolve method ids to bibliography references and citation mapping.",
            "build_repro_page": "Build the static reproduction site into an explicit local output directory.",
            "export_sidecars": "Write one paper's reproduction sidecars into an explicit local output directory.",
        },
        "non_goals": [
            "runtime_execution",
            "upload_service",
            "ecosystem_writeback",
            "core_dependency",
        ],
    }


def list_papers(root: str | Path) -> Catalog:
    """Return the catalog loaded from ``root``."""
    return load_catalog(root)


def load_paper_bundle(paper_dir: str | Path) -> PaperView:
    """Return the public reproduction view for one paper directory."""
    return load_paper(paper_dir)


def inspect_bundle(path: str | Path) -> Bundle:
    """Return stdlib-only inspection metadata for a deposited ``.n4a`` bundle."""
    return read_bundle(path)


def build_methods_section(method_ids: list[str]) -> dict[str, Any]:
    """Resolve method ids into a structured bibliography summary without rendering a page."""
    references, id_to_ref = build_bibliography(method_ids)
    return {
        "method_ids": list(method_ids),
        "references": [_reference_record(ref) for ref in references],
        "citation_map": {method_id: ref.number for method_id, ref in id_to_ref.items()},
        "reference_ids": {method_id: ref.id for method_id, ref in id_to_ref.items()},
    }


def build_repro_page(root: str | Path, out: str | Path, io_wasm: str | Path | None = None) -> Path:
    """Build the static reproduction site into ``out``."""
    return build_site(root, out, io_wasm=io_wasm)


def export_sidecars(paper_dir: str | Path, out: str | Path) -> Path:
    """Write one paper's deposit sidecars into ``out/paper/<slug>/`` and return that crate path."""
    view = load_paper(paper_dir)
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
