# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import json

import yaml

from nirs4all_papers import provenance
from nirs4all_papers.bibliography import build_bibliography
from nirs4all_papers.provenance import _is_entity, _license_id


def test_is_entity_classification():
    assert _is_entity("nirs4all ecosystem") is True
    assert _is_entity("CIRAD") is True  # single token
    assert _is_entity("Gregory Beurier") is False
    assert _is_entity("van der Berg") is False  # lowercase particle, capitalised surname -> person
    assert _is_entity("de Jong, Sijmen") is False


def test_license_id_mapping():
    assert _license_id("CC-BY-4.0") == "https://creativecommons.org/licenses/by/4.0/"
    assert _license_id("MIT") == "https://spdx.org/licenses/MIT.html"
    assert _license_id("see publisher") == "#manuscript-license"


def test_citation_cff_valid_yaml_and_every_reference_has_authors(demo_view):
    # force in a reference whose seed has no authors (gaussian_filter) to lock the CFF fallback
    demo_view.references[:], _ = build_bibliography(["gaussian_filter", "pls"])
    cff = provenance.citation_cff(demo_view)
    data = yaml.safe_load(cff)
    assert data["cff-version"] == "1.2.0"
    assert data["authors"]
    for ref in data.get("references", []):
        assert ref.get("authors"), "every CFF reference must carry authors"


def test_citation_cff_no_fake_version(demo_view):
    # version should not be the nirs4all library version
    cff = yaml.safe_load(provenance.citation_cff(demo_view))
    assert cff.get("version") != demo_view.bundle.nirs4all_version
    # the bundle fingerprint is exposed as an identifier instead
    ids = cff.get("identifiers", [])
    assert any("nirs4all-bundle:" in str(i.get("value", "")) for i in ids)


def test_ro_crate_main_entity_in_haspart(demo_view):
    crate_files = [{"name": "pipeline.json", "size": 1, "sha256": "x", "encodingFormat": "application/json"}]
    crate = provenance.ro_crate(demo_view, crate_files)
    json.dumps(crate)  # serializable
    root = next(e for e in crate["@graph"] if e.get("@id") == "./")
    assert root["mainEntity"]["@id"] == "pipeline.json"
    assert {"@id": "pipeline.json"} in root["hasPart"]
    assert not any(e.get("@id") == "#pipeline" for e in crate["@graph"])
    pj = next(e for e in crate["@graph"] if e.get("@id") == "pipeline.json")
    assert "ComputationalWorkflow" in pj["@type"]
