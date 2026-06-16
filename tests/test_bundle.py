# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import pytest

from nirs4all_papers.bundle import read_bundle
from tests.conftest import make_n4a


def test_rejects_non_zip(tmp_path):
    p = tmp_path / "x.n4a"
    p.write_text("not a zip")
    with pytest.raises(ValueError):
        read_bundle(p)


def test_rejects_missing_manifest(tmp_path):
    import zipfile

    p = tmp_path / "x.n4a"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("pipeline.json", "{}")
    with pytest.raises(ValueError):
        read_bundle(p)


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_bundle(tmp_path / "nope.n4a")


def test_step_typing_and_repr_sanitized(tmp_path):
    steps = [
        {"step": "sklearn.preprocessing._data.MinMaxScaler"},
        {"step": "<nirs4all.pipeline.execution.refit.executor._FullTrainFoldSplitter object at 0x75004fe8f990>"},
        {"step": "nirs4all.operators.transforms.scalers.StandardNormalVariate"},
        {"y_processing": "sklearn.preprocessing._data.StandardScaler"},
        {"class": "sklearn.cross_decomposition._pls.PLSRegression", "params": {"n_components": 10}},
    ]
    b = read_bundle(make_n4a(tmp_path / "b.n4a", steps, model_step_index=5))
    sv = b.steps()
    kinds = [s.kind for s in sv]
    assert kinds == ["preprocessing", "split", "preprocessing", "target", "model"]
    # the splitter repr's volatile memory address must be stripped everywhere
    splitter = sv[1]
    assert splitter.kind == "split" and splitter.reproducible is False
    assert "0x" not in splitter.raw
    assert "0x" not in b.pipeline["steps"][1]["step"]
    assert splitter.short_name == "FullTrainFoldSplitter"
    model = sv[4]
    assert model.kind == "model" and model.short_name == "PLSRegression" and model.params["n_components"] == 10


def test_fingerprint_is_deterministic(tmp_path):
    steps = [{"class": "sklearn.cross_decomposition._pls.PLSRegression", "params": {}}]
    b1 = read_bundle(make_n4a(tmp_path / "a.n4a", steps, model_step_index=1))
    b2 = read_bundle(make_n4a(tmp_path / "b.n4a", steps, model_step_index=1))
    assert b1.fingerprint == b2.fingerprint and len(b1.fingerprint) == 64


def test_fold_weights_int_keys(tmp_path):
    b = read_bundle(make_n4a(tmp_path / "f.n4a", [{"class": "x.PLSRegression"}], model_step_index=1, fold_weights={"0": 1.0, "1": 0.5}))
    assert b.fold_weights == {0: 1.0, 1: 0.5}
