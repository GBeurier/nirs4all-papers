# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import json

from nirs4all_papers.provider import (
    build_methods_section,
    build_repro_page,
    export_sidecars,
    inspect_bundle,
    list_papers,
    load_paper_bundle,
    provider_capabilities,
)
from nirs4all_papers.site import write_paper_sidecars
from tests.conftest import DEMO_DIR, REPO_ROOT


def test_provider_capabilities_document_archive_boundaries():
    caps = provider_capabilities()
    assert caps["provider"] == "nirs4all-papers"
    assert caps["executes"] is False
    assert caps["writes"] == "local_output"
    assert "runtime_execution" in caps["non_goals"]
    assert "export_sidecars" in caps["verbs"]


def test_provider_wraps_catalog_paper_and_bundle_reads():
    catalog = list_papers(REPO_ROOT)
    assert [paper.slug for paper in catalog.papers] == ["2026-pls-nirs-demo"]

    paper = load_paper_bundle(DEMO_DIR)
    assert paper.slug == "2026-pls-nirs-demo"
    assert paper.bundle_filename == "model.n4a"

    bundle = inspect_bundle(DEMO_DIR / "model.n4a")
    assert bundle.path.name == "model.n4a"
    assert bundle.pipeline["steps"]
    assert bundle.fingerprint == paper.bundle.fingerprint


def test_build_methods_section_is_structured_without_rendering_pages():
    section = build_methods_section(["minmax", "standard_scaler", "pls"])
    assert section["method_ids"] == ["minmax", "standard_scaler", "pls"]
    assert len(section["references"]) == 2
    assert section["citation_map"]["minmax"] == section["citation_map"]["standard_scaler"]
    assert section["citation_map"]["pls"] == 2
    assert {ref["id"] for ref in section["references"]} == {"minmax", "pls"}


def test_export_sidecars_writes_only_the_reproduction_crate(tmp_path):
    crate = export_sidecars(DEMO_DIR, tmp_path / "export")
    assert crate == tmp_path / "export" / "paper" / "2026-pls-nirs-demo"
    assert sorted(p.name for p in crate.iterdir()) == [
        "CITATION.cff",
        "model.n4a",
        "pipeline.json",
        "references.bib",
        "ro-crate-metadata.json",
    ]
    assert not (tmp_path / "export" / "index.html").exists()
    json.loads((crate / "ro-crate-metadata.json").read_text(encoding="utf-8"))


def test_public_sidecar_writer_matches_provider_export(tmp_path, demo_view):
    crate = write_paper_sidecars(demo_view, tmp_path / "manual")
    assert crate == tmp_path / "manual" / "paper" / demo_view.slug
    assert (crate / "pipeline.json").exists()


def test_build_repro_page_wraps_site_build(tmp_path):
    out = build_repro_page(REPO_ROOT, tmp_path / "site")
    assert (out / "index.html").exists()
    assert (out / "paper" / "2026-pls-nirs-demo" / "CITATION.cff").exists()
