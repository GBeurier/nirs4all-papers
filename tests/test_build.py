# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import pytest

from nirs4all_papers.site import build_site
from nirs4all_papers.site.assets import replay_plan
from tests.conftest import REPO_ROOT


def test_build_emits_pages_and_sidecars(tmp_path):
    out = build_site(REPO_ROOT, tmp_path / "site")
    assert (out / "index.html").exists()
    assert (out / "catalog.html").exists()
    assert (out / "sitemap.xml").exists()
    assert (out / "robots.txt").exists()
    page = out / "paper" / "2026-pls-nirs-demo.html"
    assert page.exists()
    crate = out / "paper" / "2026-pls-nirs-demo"
    for name in ("model.n4a", "pipeline.json", "CITATION.cff", "references.bib", "ro-crate-metadata.json"):
        assert (crate / name).exists(), name
    html = page.read_text(encoding="utf-8")
    assert "citation_title" in html  # scholarly meta
    assert "application/ld+json" in html  # JSON-LD
    assert 'rel="canonical"' in html


def test_build_is_idempotent(tmp_path):
    a = build_site(REPO_ROOT, tmp_path / "a")
    b = build_site(REPO_ROOT, tmp_path / "b")
    fa = (a / "paper" / "2026-pls-nirs-demo.html").read_bytes()
    fb = (b / "paper" / "2026-pls-nirs-demo.html").read_bytes()
    assert fa == fb


def test_rmtree_guard_refuses_unmarked_dir(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    (out / "precious.txt").write_text("do not delete")
    with pytest.raises(ValueError):
        build_site(REPO_ROOT, out)
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
