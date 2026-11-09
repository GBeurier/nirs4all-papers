# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Synthetic reader fixtures only; no deposited paper/model/data is opened.

Current fixtures use actual public owner writers. Missing owner dependencies are
errors, never skips. The old ZIP helper is a negative transport witness only.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
# Context only for accessor-only tests; never read this path.
DEMO_DIR = Path("synthetic-paper-context")
FIXTURES = Path(__file__).parent / "fixtures" / "core_v1"


def make_n4a(path: Path, steps: list[dict[str, Any]], *, model_step_index=None, manifest=None, fold_weights=None) -> Path:
    """Write an unsupported historical physical ZIP, never a current positive fixture."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest or {"bundle_format_version": "1.0"}))
        archive.writestr("pipeline.json", json.dumps({"steps": steps, "model_step_index": model_step_index}))
        if fold_weights:
            archive.writestr("fold_weights.json", json.dumps(fold_weights))
    return path


def write_sdk_paper(root: Path, *, training: dict[str, Any] | None = None, predict_only: bool = False) -> Path:
    """Write an actual SDK/Core host container with inert model bytes; no fit."""
    from nirs4all.pipeline.bundle.constants import BUNDLE_FORMAT_VERSION
    from nirs4all.pipeline.dagml.host_container import (
        BUNDLE_CONTENT_TYPE,
        BUNDLE_MANIFEST_MEMBER,
        JOBLIB_CONTENT_TYPE,
        JSON_CONTENT_TYPE,
        HostMember,
        write_host_container,
    )

    paper = root / "papers" / "synthetic-reader"
    paper.mkdir(parents=True)
    meta = {"title": "Synthetic reader evidence", "slug": "synthetic-reader", "bundle": "model.n4a",
            "year": 2026, "authors": [{"name": "Reader Test"}], "method_ids": ["minmax", "pls"],
            "metrics": [{"name": "RMSE", "value": 2.0, "partition": "published synthetic"}]}
    (paper / "paper.json").write_text(json.dumps(meta))
    manifest = {"bundle_format_version": BUNDLE_FORMAT_VERSION, "source_type": "inspection_synthetic",
                "extra": {"owner_string": "<Opaque object at 0x123abc>", "targets": ["target:b", "target:a"]},
                "relation_replay_manifest": {"path": "relations.json"}}
    recipe = training if training is not None else {"steps": [
        {"class": "sklearn.preprocessing.MinMaxScaler", "params": {"feature_range": [0, 1]}},
        {"branch": [[{"class": "sklearn.preprocessing.StandardScaler"}], [{"model": "sklearn.linear_model.Ridge"}]]},
        {"y_processing": {"class": "sklearn.preprocessing.StandardScaler", "params": {"with_mean": False}}},
        {"model": {"class": "sklearn.cross_decomposition.PLSRegression", "params": {"n_components": 2}}},
    ], "targets": ["target:b", "target:a"], "options": {"search": {"n_components": [1, 2]}}}
    payloads = {
        BUNDLE_MANIFEST_MEMBER: manifest,
        "pipeline.json": {"steps": [{"model": {"class": "CosmeticLabel"}}]},
        "chain.json": {"unknown_additive": {"branch_ids": ["right", "left"]}},
        "trace.json": {"trace_id": "trace:synthetic", "pipeline_uid": "pipeline:synthetic", "steps": []},
        "fold_weights.json": {"0": 1.0},
        "relations.json": {"sample_ids": ["s:2", "s:1"], "observation_ids": ["o:2", "o:1"], "target_ids": ["t:2", "t:1"]},
        "scores.json": {"score": {"value": 1.25, "metric": "rmse", "partition": "validation",
                                   "target": "t:2", "level": "sample", "selection": "owner-declared", "aggregation": "mean"}},
    }
    if not predict_only:
        payloads["train_pipeline.json"] = recipe
    members = [HostMember(name, json.dumps(value).encode(), "provenance" if name == BUNDLE_MANIFEST_MEMBER else "recipe",
                          BUNDLE_CONTENT_TYPE if name == BUNDLE_MANIFEST_MEMBER else JSON_CONTENT_TYPE)
               for name, value in payloads.items()]
    members.append(HostMember("artifacts/step_1_foldfinal_inert.joblib", b"inert: not a pickle", "model", JOBLIB_CONTENT_TYPE))
    write_host_container(paper / "model.n4a", members)
    return paper


@pytest.fixture
def sdk_paper(tmp_path):
    return write_sdk_paper(tmp_path / "input")


@pytest.fixture
def current_view(sdk_paper):
    from nirs4all_papers.model import load_paper

    view = load_paper(sdk_paper, read_current=True)
    assert view.reading_status == "documents_readable", view.reading_detail
    assert view.bundle.profile == "nirs4all.python-host"
    return view


@pytest.fixture
def native_files(tmp_path):
    import nirs4all_core as core

    package = (FIXTURES / "predictor_package.json").read_bytes()
    outcome = (FIXTURES / "training_outcome.json").read_bytes()
    child = (FIXTURES / "child_refit_v3.json").read_bytes()
    parent_path, child_path = tmp_path / "parent.n4a", tmp_path / "child.n4a"
    core.write_native_predictor_package(parent_path, outcome, package, container_id="papers:synthetic-parent")
    core.write_native_refit_package(child_path, child, container_id="papers:synthetic-child")
    return parent_path, child_path, package, outcome, child


@pytest.fixture
def demo_view():
    """Isolated approximate-JS input, not a current bundle or paper-science witness."""
    from nirs4all_papers.bundle import StepInfo
    from nirs4all_papers.model import PaperView, StepView

    steps = [StepView(StepInfo(i, kind, name, name, params), method, None)
             for i, (kind, name, params, method) in enumerate([
                 ("preprocessing", "MinMaxScaler", {}, "minmax"),
                 ("split", "SyntheticSplitter", {}, None),
                 ("preprocessing", "StandardNormalVariate", {}, "snv"),
                 ("target", "StandardScaler", {}, "standard_scaler"),
                 ("model", "PLSRegression", {"n_components": 1}, "pls"),
             ], 1)]
    # This synthetic constant-feature reference is independent of deposited data.
    replay = {"X": [[1.0, 2.0, 3.0] for _ in range(20)], "y": [2.0, -2.0] * 10,
              "axis": [1000, 1100, 1200], "target": "target", "name": "Synthetic isolated JS reference", "synthetic": True}
    return PaperView("synthetic-js", {"title": "Synthetic JS reference"}, None, steps, [], replay, "unused.n4a", Path("."))
