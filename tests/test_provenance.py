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


def test_citation_cff_valid_yaml_and_every_reference_has_authors(current_view):
    # force in a reference whose seed has no authors (gaussian_filter) to lock the CFF fallback
    current_view.references[:], _ = build_bibliography(["gaussian_filter", "pls"])
    cff = provenance.citation_cff(current_view)
    data = yaml.safe_load(cff)
    assert data["cff-version"] == "1.2.0"
    assert data["authors"]
    for ref in data.get("references", []):
        assert ref.get("authors"), "every CFF reference must carry authors"


def test_citation_cff_no_fake_version(current_view):
    # version should not be the nirs4all library version
    cff = yaml.safe_load(provenance.citation_cff(current_view))
    assert cff.get("version") is None
    ids = cff.get("identifiers", [])
    assert any("n4a-container-sha256:" in str(item.get("value", "")) for item in ids)
    assert not any("nirs4all-bundle:" in str(item.get("value", "")) for item in ids)
    current_view.meta["provenance"] = {"bundle_fingerprint": "historical-value"}
    historical = yaml.safe_load(provenance.citation_cff(current_view))
    assert any(item.get("value") == "nirs4all-bundle:historical-value" for item in historical["identifiers"])


def test_ro_crate_main_entity_in_haspart(current_view):
    crate_files = [{"name": "model.n4a", "size": 1, "sha256": "x", "encodingFormat": "application/json"}]
    crate = provenance.ro_crate(current_view, crate_files)
    json.dumps(crate)  # serializable
    root = next(e for e in crate["@graph"] if e.get("@id") == "./")
    assert root["mainEntity"]["@id"] == "model.n4a"
    assert {"@id": "model.n4a"} in root["hasPart"]
    assert not any(e.get("@id") == "#pipeline" for e in crate["@graph"])
    pj = next(e for e in crate["@graph"] if e.get("@id") == "model.n4a")
    assert pj["@type"] == "File"
    assert "programmingLanguage" not in pj
    assert all(".predict(" not in text for _, text in provenance.reproduction_commands(current_view))
