# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import pytest

from nirs4all_papers.site import build_site
from nirs4all_papers.site.assets import replay_plan


def test_build_emits_pages_and_sidecars(tmp_path, sdk_paper):
    out = build_site(sdk_paper.parents[1], tmp_path / "site")
    assert (out / "index.html").exists()
    assert (out / "catalog.html").exists()
    assert (out / "sitemap.xml").exists()
    assert (out / "robots.txt").exists()
    page = out / "paper" / "synthetic-reader.html"
    assert page.exists()
    crate = out / "paper" / "synthetic-reader"
    for name in ("model.n4a", "CITATION.cff", "references.bib", "ro-crate-metadata.json"):
        assert (crate / name).exists(), name
    html = page.read_text(encoding="utf-8")
    assert not (crate / "pipeline.json").exists()
    assert "as published" in html
    assert "Current document reading does not run" in html
    assert "citation_title" in html  # scholarly meta
    assert "application/ld+json" in html  # JSON-LD
    assert 'rel="canonical"' in html


def test_build_is_idempotent(tmp_path, sdk_paper):
    a = build_site(sdk_paper.parents[1], tmp_path / "a")
    b = build_site(sdk_paper.parents[1], tmp_path / "b")
    fa = (a / "paper" / "synthetic-reader.html").read_bytes()
    fb = (b / "paper" / "synthetic-reader.html").read_bytes()
    assert fa == fb


def test_rmtree_guard_refuses_unmarked_dir(tmp_path, sdk_paper):
    out = tmp_path / "site"
    out.mkdir()
    (out / "precious.txt").write_text("do not delete")
    with pytest.raises(ValueError):
        build_site(sdk_paper.parents[1], out)
    assert (out / "precious.txt").exists()


def test_replay_plan_for_demo(demo_view):
    plan = replay_plan(demo_view)
    assert plan["model"]["op"] == "pls" and plan["model"]["supported"] is True
    assert [f["op"] for f in plan["features"]] == ["minmax", "snv"]
    assert plan["yTransform"] == "standard_scaler"


def test_replay_plan_non_pls_unsupported(tmp_path, monkeypatch):
    from nirs4all_papers.bundle import StepInfo
    from nirs4all_papers.model import StepView

    rf = StepView(info=StepInfo(index=1, kind="model", raw="sklearn.ensemble.RandomForestRegressor", short_name="RandomForestRegressor"), method_id=None, reference=None)
    demo = type("V", (), {"steps": [rf], "replay": {"X": [[1.0]], "y": [1.0]}})()
    plan = replay_plan(demo)
    assert plan["model"]["supported"] is False


def test_archive_only_without_readers_preserves_raw_download_and_released_sidecar(tmp_path, monkeypatch):
    import json

    from nirs4all_papers import bundle

    root = tmp_path / "input"
    paper = root / "papers" / "historical"
    paper.mkdir(parents=True)
    raw = b"unsupported historical physical bytes"
    (paper / "model.n4a").write_bytes(raw)
    frozen_cff = b'cff-version: 1.2.0\ntitle: "Frozen citation"\n'
    (paper / "released.cff").write_bytes(frozen_cff)
    (paper / "paper.json").write_text(json.dumps({"title": "Historical", "archive_sidecars": ["released.cff"]}))
    def forbidden(name):
        pytest.fail("archive-only publication imported an optional owner")
    monkeypatch.setattr(bundle.importlib, "import_module", forbidden)
    out = build_site(root, tmp_path / "output")
    assert (out / ".n4a-papers-build").exists()
    assert (out / "paper/historical/model.n4a").read_bytes() == raw
    assert (out / "paper/historical/released.cff").read_bytes() == frozen_cff
    assert not (out / "paper/historical/pipeline.json").exists()
    text = (out / "paper/historical.html").read_text()
    assert 'href="historical/model.n4a"' in text
    assert "archive_only" in text and "do not establish current admission" in text


def test_current_full_documents_are_escaped_and_downloaded_exactly(tmp_path, sdk_paper):
    from nirs4all_papers.model import load_paper

    view = load_paper(sdk_paper, read_current=True)
    assert view.reading_status == "documents_readable", view.reading_detail
    out = build_site(sdk_paper.parents[1], tmp_path / "current", read_current=True)
    page = (out / "paper/synthetic-reader.html").read_text()
    assert "&lt;Opaque object at 0x123abc&gt;" in page
    assert "training_declaration" in page and "prediction_config" in page
    assert "owner-document-" in page
    assert ".predict(" not in page
    for name, raw in view.document_downloads:
        assert (out / "paper/synthetic-reader" / name).read_bytes() == raw
