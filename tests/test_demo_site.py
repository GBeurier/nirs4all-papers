# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Public demo publication must retain its independent replay and bibliography."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from nirs4all_papers.model import load_paper
from nirs4all_papers.site import build_site
from nirs4all_papers.site.assets import replay_plan

PUBLIC_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DEMO = PUBLIC_ROOT / "papers" / "2026-pls-nirs-demo"


def test_public_demo_build_keeps_replay_citations_and_raw_archive(tmp_path, monkeypatch):
    from nirs4all_papers import bundle

    original_import = bundle.importlib.import_module

    def refuse_owner_import(name, package=None):
        if name.partition(".")[0] in {"nirs4all_core", "nirs4all", "n4a"}:
            pytest.fail("archive-only browser companion imported an optional current reader")
        return original_import(name, package)

    monkeypatch.setattr(bundle.importlib, "import_module", refuse_owner_import)
    view = load_paper(PUBLIC_DEMO)
    assert view.bundle is None and view.steps == []
    assert view.reading_status == "archive_only"
    assert view.replay is not None and len(view.replay["X"]) == 120
    assert len(view.references) == 3
    assert replay_plan(view)["model"]["n_components"] == 10

    out = build_site(PUBLIC_ROOT, tmp_path / "site")
    html = (out / "paper/2026-pls-nirs-demo.html").read_text()
    assert 'id="replay-run"' in html
    assert 'id="byod-file"' in html
    assert 'id="bibliography"' in html
    assert "3 references" in html
    assert "does not execute the deposited" in html
    assert 'id="papers-ui"' in html
    assert "browser replays" in (out / "index.html").read_text()
    crate = out / "paper/2026-pls-nirs-demo"
    assert (crate / "model.n4a").read_bytes() == (PUBLIC_DEMO / "model.n4a").read_bytes()
    assert (crate / "references.bib").read_text().count("@") == 3
    assert json.loads((crate / "ro-crate-metadata.json").read_text())["@graph"]


@pytest.mark.parametrize("field,value", [
    ("features", [{"op": "unknown", "params": {}}]),
    ("model", {"op": "ridge", "n_components": 10}),
    ("yTransform", "unknown"),
    ("cv", True),
])
def test_declared_companion_refuses_unsupported_plans(field, value):
    view = load_paper(PUBLIC_DEMO)
    view.meta = copy.deepcopy(view.meta)
    view.meta["replay_plan"][field] = value
    with pytest.raises(ValueError, match="replay_plan"):
        replay_plan(view)
