# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import json

import pytest

from nirs4all_papers.model import PaperView, _load_replay, load_catalog, load_paper
from tests.conftest import DEMO_DIR, make_n4a


def _meta(**kw):
    base = {"title": "t", "bundle": "model.n4a"}
    base.update(kw)
    return base


def _mk_view(meta):
    # minimal PaperView for accessor tests (no bundle needed)
    return PaperView(slug="s", meta=meta, bundle=None, steps=[], references=[], replay=None, bundle_filename="model.n4a", paper_dir=DEMO_DIR)


def test_malformed_accessors_are_tolerant():
    v = _mk_view(_meta(authors="not-a-list", dataset=["x"], metrics="bad", keywords=None))
    assert v.authors == []
    assert v.dataset == {}
    assert v.metrics == []
    assert v.keywords == []


def test_load_replay_rejects_nan(tmp_path):
    (tmp_path / "replay.json").write_text(json.dumps({"X": [[float("nan")]], "y": [1.0]}).replace("NaN", "NaN"))
    # json.dumps refuses NaN by default; write raw
    (tmp_path / "replay.json").write_text('{"X": [[NaN]], "y": [1.0]}')
    assert _load_replay(tmp_path, {"replay": "replay.json"}) is None


def test_load_replay_rejects_ragged_and_mismatch(tmp_path):
    (tmp_path / "r1.json").write_text(json.dumps({"X": [[1, 2], [3]], "y": [1, 2]}))
    assert _load_replay(tmp_path, {"replay": "r1.json"}) is None
    (tmp_path / "r2.json").write_text(json.dumps({"X": [[1, 2]], "y": [1, 2]}))  # len mismatch
    assert _load_replay(tmp_path, {"replay": "r2.json"}) is None


def test_load_replay_accepts_valid(tmp_path):
    (tmp_path / "r.json").write_text(json.dumps({"X": [[1.0, 2.0], [3.0, 4.0]], "y": [1.0, 2.0], "axis": [10, 20]}))
    out = _load_replay(tmp_path, {"replay": "r.json"})
    assert out is not None and out["X"] == [[1.0, 2.0], [3.0, 4.0]]


def test_slug_collision_raises(tmp_path):
    root = tmp_path
    papers = root / "papers"
    for name in ("PLS_Demo", "pls-demo"):
        d = papers / name
        d.mkdir(parents=True)
        make_n4a(d / "model.n4a", [{"class": "x.PLSRegression"}], model_step_index=1)
        (d / "paper.yaml").write_text("title: x\n")
    with pytest.raises(ValueError):
        load_catalog(root)


def test_bundle_path_traversal_rejected(tmp_path):
    d = tmp_path / "papers" / "p"
    d.mkdir(parents=True)
    make_n4a(tmp_path / "papers" / "evil.n4a", [{"class": "x.PLSRegression"}], model_step_index=1)
    (d / "paper.yaml").write_text("title: x\nbundle: ../evil.n4a\n")
    with pytest.raises(ValueError):
        load_paper(d)


def test_current_view_keeps_complete_owner_documents_without_step_projection(current_view):
    assert current_view.bundle.document("training_declaration").value["steps"]
    assert current_view.model_step is None
    assert current_view.n_steps is None
    assert current_view.steps == []
    assert len(current_view.references) == 2  # explicit public method_ids only
    assert current_view.metrics[0].partition == "published synthetic"


def test_optional_reader_failure_retains_catalog_entry_and_download(tmp_path, monkeypatch):
    from nirs4all_papers import model
    from nirs4all_papers.bundle import ReaderDependencyError

    paper = tmp_path / "papers" / "historical"
    paper.mkdir(parents=True)
    (paper / "paper.json").write_text('{"title":"Historical"}')
    (paper / "model.n4a").write_bytes(b"historical opaque bytes")
    def unavailable(path):
        raise ReaderDependencyError("Core is not installed")
    monkeypatch.setattr(model, "read_bundle", unavailable)
    view = load_catalog(tmp_path, read_current=True).papers[0]
    assert view.reading_status == "dependency_unavailable"
    assert "Core is not installed" in view.reading_detail
    assert view.bundle is None and view.raw_download_sha256
    assert view.archive_path.read_bytes() == b"historical opaque bytes"
