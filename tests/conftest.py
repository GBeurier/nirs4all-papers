# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Shared fixtures: the committed demo paper + a helper to build synthetic ``.n4a`` bundles."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "papers" / "2026-pls-nirs-demo"


def make_n4a(
    path: Path,
    steps: list[dict[str, Any]],
    *,
    model_step_index: int | None = None,
    manifest: dict[str, Any] | None = None,
    fold_weights: dict[str, float] | None = None,
) -> Path:
    """Write a minimal valid ``.n4a`` (ZIP with manifest.json + pipeline.json [+ fold_weights])."""
    man: dict[str, Any] = {"bundle_format_version": "1.0", "nirs4all_version": "0.10.0"}
    man.update(manifest or {})
    if model_step_index is not None:
        man["model_step_index"] = model_step_index
    pipe: dict[str, Any] = {"steps": steps}
    if model_step_index is not None:
        pipe["model_step_index"] = model_step_index
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", json.dumps(man))
        z.writestr("pipeline.json", json.dumps(pipe))
        if fold_weights:
            z.writestr("fold_weights.json", json.dumps(fold_weights))
    return path


@pytest.fixture
def demo_view():
    from nirs4all_papers.model import load_paper

    return load_paper(DEMO_DIR)
