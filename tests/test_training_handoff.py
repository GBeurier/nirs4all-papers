# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Inspection-only source regressions; no Repository subprocess, fit or replay."""
from __future__ import annotations

from copy import deepcopy

import pytest

from nirs4all_papers.model import load_paper
from tests.conftest import write_sdk_paper
from tests.e2e.test_repository_refit_export import UnsupportedTrainingRecipeError, _refit_recipe_from_paper


def test_lossless_nested_owner_training_handoff(current_view):
    declared = current_view.bundle.document("training_declaration").value
    before = deepcopy(declared)
    recipe = _refit_recipe_from_paper(current_view)
    assert recipe["pipeline"] == declared["steps"]
    assert recipe["targets"] == declared["targets"]
    assert recipe["options"] == declared["options"]
    assert recipe["pipeline"][1]["branch"] == declared["steps"][1]["branch"]
    assert {("steps" if key == "pipeline" else key): value for key, value in recipe.items()} == before
    recipe["pipeline"][0]["params"]["feature_range"][0] = -1
    assert declared == before


def test_predict_only_is_named_refusal_not_cosmetic_recipe(tmp_path):
    paper = write_sdk_paper(tmp_path, predict_only=True)
    view = load_paper(paper, read_current=True)
    assert view.reading_status == "documents_readable", view.reading_detail
    assert view.bundle.document("prediction_config") is not None
    assert view.bundle.document("training_declaration") is None
    with pytest.raises(UnsupportedTrainingRecipeError, match="prediction config"):
        _refit_recipe_from_paper(view)


def test_supplied_owner_repository_recipe_is_preserved(current_view):
    supplied = {"pipeline": [{"model": "sklearn.linear_model.Ridge", "params": {"alpha": 0.75}}],
                "targets": ["target:z"], "options": {"unknown_additive": False}}
    current_view.meta["repository_refit_recipe"] = supplied
    assert _refit_recipe_from_paper(current_view) == supplied
    assert _refit_recipe_from_paper(current_view) is not supplied
