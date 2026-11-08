# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Display-only synthetic views; no owner admission, fitted objects or deposited content."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from nirs4all_papers.bundle import Bundle
from nirs4all_papers.model import PaperView
from nirs4all_papers.site.shared_ui import paper_projection, projection_json


def test_projection_json_is_inert_and_keeps_published_nonfinite_text():
    hostile = '</script><!--<img src=x onerror="alert(1)">&\u2028\u2029'
    view = PaperView(
        slug="synthetic-display", bundle=None, steps=[], references=[], replay=None,
        bundle_filename="original.n4a", paper_dir=Path("synthetic-context-only"),
        reading_detail="EXCLUDED local exception and path", raw_download_sha256="a" * 64,
        meta={"private": "EXCLUDED metadata", "recipe": {"steps": ["EXCLUDED recipe"]}, "metrics": [
            {"name": hostile, "value": float("nan"), "partition": "All"},
            {"name": hostile, "value": float("inf"), "partition": None},
            {"name": "score", "value": float("-inf"), "partition": ""},
            {"name": "score", "value": None, "partition": "All"},
        ]},
    )
    wire = projection_json(view)
    data = json.loads(wire)
    assert not any(character in wire for character in "<>&\u2028\u2029")
    assert "EXCLUDED" not in wire and "synthetic-context-only" not in wire and "original.n4a" not in wire
    assert data["metrics"] == [
        {"name": hostile, "valueText": "nan", "partition": "All"},
        {"name": hostile, "valueText": "inf", "partition": None},
        {"name": "score", "valueText": "-inf", "partition": ""},
        {"name": "score", "valueText": "—", "partition": "All"},
    ]
    assert "coreContainerSha256" not in data and "ownerProfile" not in data


def test_projection_keeps_detached_identity_namespaces_separate():
    # Synthetic detached display evidence only; this does not fabricate an owner admission/proof.
    bundle = Bundle(
        path=Path("synthetic-context-only.n4a"), manifest_bytes=b"{}", manifest={},
        view={"readability": {"container_sha256": "b" * 64, "manifest_sha256": "c" * 64}},
        profile="synthetic-owner-profile",
        owner_view={"recipe": "EXCLUDED owner recipe", "predictions": [123, 456]},
    )
    view = PaperView(
        slug="synthetic-display", meta={"provenance": {"bundle_fingerprint": "EXCLUDED historical namespace"}},
        bundle=bundle, steps=[], references=[], replay=None, bundle_filename="original.n4a",
        paper_dir=Path("synthetic-context-only"), raw_download_sha256="a" * 64,
        reading_status="documents_readable",
    )
    data = paper_projection(view)
    assert data["rawDownloadSha256"] == "a" * 64
    assert data["coreContainerSha256"] == "b" * 64
    assert data["coreManifestSha256"] == "c" * 64
    assert data["ownerProfile"] == "synthetic-owner-profile"
    assert data["readingStatus"] == "documents_readable"
    assert "EXCLUDED" not in projection_json(view) and "predictions" not in projection_json(view)
    assert "does not establish executability" in data["readingExplanation"]


@pytest.mark.parametrize(("status", "explanation"), [
    ("archive_only", "has not been evaluated"),
    ("dependency_unavailable", "not a format refusal"),
    ("current_reading_refused", "original archive remains downloadable"),
])
def test_projection_does_not_conflate_reading_states(status, explanation):
    view = PaperView(
        slug="synthetic-display", meta={}, bundle=None, steps=[], references=[], replay=None,
        bundle_filename="original.n4a", paper_dir=Path("synthetic-context-only"), reading_status=status,
    )
    data = paper_projection(view)
    assert data["readingStatus"] == status
    assert explanation in data["readingExplanation"]
    assert "completed" not in data["readingExplanation"].lower()
