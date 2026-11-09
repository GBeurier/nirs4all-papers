# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import json

from nirs4all_papers.provider import (
    bibtex,
    build_methods_section,
    build_repro_page,
    citation,
    export_sidecars,
    inspect_bundle,
    list_papers,
    load_paper,
    load_paper_bundle,
    provider_capabilities,
)
from nirs4all_papers.site import write_paper_sidecars


def test_provider_capabilities_document_archive_boundaries():
    caps = provider_capabilities()
    assert caps["provider"] == "nirs4all-papers"
    assert caps["executes"] is False
    assert caps["writes"] == "local-output"
    assert "runtime_execution" in caps["non_goals"]
    assert "load_paper" in caps["verbs"]
    assert "citation" in caps["verbs"]
    assert "bibtex" in caps["verbs"]
    assert "export_sidecars" in caps["verbs"]
    assert "core_dependency" not in caps["non_goals"]
    assert caps["optional_dependencies"]["sdk-host-reader"] == ["nirs4all"]


def test_provider_wraps_catalog_paper_and_bundle_reads(sdk_paper):
    catalog = list_papers(sdk_paper.parents[1], read_current=True)
    assert [paper.slug for paper in catalog.papers] == ["synthetic-reader"]

    paper = load_paper_bundle(sdk_paper, read_current=True)
    assert load_paper(sdk_paper, read_current=True).slug == paper.slug
    assert paper.slug == "synthetic-reader"
    assert paper.bundle_filename == "model.n4a"

    bundle = inspect_bundle(sdk_paper / "model.n4a")
    assert bundle.path.name == "model.n4a"
    assert bundle.document("training_declaration").value["steps"]
    assert bundle.container_sha256 == paper.bundle.container_sha256


def test_citation_and_bibtex_are_pure_read_helpers(sdk_paper):
    cff = citation(sdk_paper)
    bib = bibtex(sdk_paper)
    assert "cff-version: 1.2.0" in cff
    assert "@article{" in bib or "@misc{" in bib


def test_build_methods_section_is_structured_without_rendering_pages():
    section = build_methods_section(["minmax", "standard_scaler", "pls"])
    assert section["method_ids"] == ["minmax", "standard_scaler", "pls"]
    assert len(section["references"]) == 2
    assert section["citation_map"]["minmax"] == section["citation_map"]["standard_scaler"]
    assert section["citation_map"]["pls"] == 2
    assert {ref["id"] for ref in section["references"]} == {"minmax", "pls"}


def test_export_sidecars_writes_only_the_reproduction_crate(tmp_path, sdk_paper):
    crate = export_sidecars(sdk_paper, tmp_path / "export")
    assert crate == tmp_path / "export" / "paper" / "synthetic-reader"
    assert sorted(p.name for p in crate.iterdir()) == [
        "CITATION.cff",
        "model.n4a",
        "references.bib",
        "ro-crate-metadata.json",
    ]
    assert not (tmp_path / "export" / "index.html").exists()
    json.loads((crate / "ro-crate-metadata.json").read_text(encoding="utf-8"))


def test_public_sidecar_writer_matches_provider_export(tmp_path, current_view):
    crate = write_paper_sidecars(current_view, tmp_path / "manual")
    assert crate == tmp_path / "manual" / "paper" / current_view.slug
    assert not (crate / "pipeline.json").exists()
    assert (crate / "container-manifest.json").read_bytes() == current_view.bundle.manifest_bytes
    for name, raw in current_view.document_downloads:
        assert (crate / name).read_bytes() == raw


def test_build_repro_page_wraps_site_build(tmp_path, sdk_paper):
    out = build_repro_page(sdk_paper.parents[1], tmp_path / "site", read_current=True)
    assert (out / "index.html").exists()
    assert (out / "paper" / "synthetic-reader" / "CITATION.cff").exists()
