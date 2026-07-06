# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Node-independent contract for the cross-language replay export.

``replay_plan()`` turns a deposited pipeline into a small JSON ``plan`` — the *export* that a
cross-language engine re-runs to reproduce the paper's scores. Two engines consume that exact plan:
the bundled pure-JS reference engine (:data:`~nirs4all_papers.site.assets.REPLAY_JS`) and, at the
documented swap seam (``replay_panel`` → libn4m ``runPortablePipeline`` in ``nirs4all-web``), the
production WebAssembly engine.

The end-to-end parity tests in ``test_replay_js.py`` execute the JS engine, but they **skip when
node is unavailable** (minimal CI runners, offline dev boxes). That leaves the load-bearing
Python→JS/WASM invariant unguarded: *every op the exporter can emit must be implemented by the
consumer*. If ``_SUPPORTED_FEATURE_OPS`` gains an op the engine's ``OPS`` table lacks, the plan
emits a step the consumer silently drops (``if (!op) return;``) and the "reproduction" quietly
computes the wrong number.

These tests pin that op vocabulary and the plan schema in **pure Python**, so the contract is
enforced in every environment, with or without node.
"""
from __future__ import annotations

import re

from nirs4all_papers.site import assets

# The non-null target transforms replay_plan can emit (model.py maps target steps to one of these).
_EMITTABLE_Y_TRANSFORMS = {"minmax", "standard_scaler"}


def _js_engine_op_keys(js: str) -> set[str]:
    """Extract the feature-op names implemented by the JS/WASM reference engine's ``OPS`` table.

    Brace-matches the ``var OPS = { ... }`` object literal, then collects its top-level keys
    (``name: { ... }``). Kept deliberately simple: the OPS block contains no string/brace literals,
    so a balanced-brace slice plus a ``key: {`` scan recovers exactly the op names.
    """
    marker = "var OPS = {"
    start = js.index(marker)
    open_brace = js.index("{", start)
    depth = 0
    end = -1
    for pos in range(open_brace, len(js)):
        char = js[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = pos
                break
    assert end != -1, "unbalanced OPS object literal in REPLAY_JS"
    block = js[open_brace : end + 1]
    return set(re.findall(r"(\w+)\s*:\s*\{", block))


def test_replay_plan_schema_is_stable(demo_view):
    """The exported plan keeps the exact shape both replay engines parse."""
    plan = assets.replay_plan(demo_view)
    assert set(plan) == {"features", "yTransform", "model", "cv", "unsupported"}

    assert isinstance(plan["features"], list)
    for step in plan["features"]:
        assert set(step) == {"op", "params"}
        assert step["op"] in assets._SUPPORTED_FEATURE_OPS
        assert isinstance(step["params"], dict)

    assert plan["yTransform"] in (None, *_EMITTABLE_Y_TRANSFORMS)
    assert isinstance(plan["cv"], int) and plan["cv"] >= 2
    assert isinstance(plan["unsupported"], list)

    model = plan["model"]
    assert model is not None, "the demo pipeline must carry a model step"
    assert model["op"] == "pls"
    assert isinstance(model["n_components"], int)
    assert isinstance(model["supported"], bool)
    assert isinstance(model["name"], str)


def test_emittable_feature_ops_match_the_replay_engine():
    """Every feature op the exporter can emit is implemented by the consumer engine, and vice versa.

    Equality (not just subset) is the right invariant: an op the JS/WASM engine implements is only
    reachable if ``replay_plan`` is allowed to emit it, i.e. it is in ``_SUPPORTED_FEATURE_OPS`` —
    otherwise the plan routes it to ``unsupported`` and it is never exercised.
    """
    engine_ops = _js_engine_op_keys(assets.REPLAY_JS)
    assert engine_ops == set(assets._SUPPORTED_FEATURE_OPS)


def test_emittable_y_transforms_are_implemented_by_the_replay_engine():
    """The JS/WASM ``fitYScaler`` handles every target transform the exporter can emit."""
    js = assets.REPLAY_JS
    for transform in _EMITTABLE_Y_TRANSFORMS:
        assert f'kind === "{transform}"' in js, f"replay engine cannot invert y-transform {transform!r}"


def test_model_op_pls_is_understood_by_the_replay_engine():
    """``replay_plan`` only emits ``model.op == "pls"``; the engine must implement a PLS fit."""
    assert "function plsFit(" in assets.REPLAY_JS
    assert "function plsPredict(" in assets.REPLAY_JS
