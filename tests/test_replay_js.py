# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Run the in-browser replay engine under Node (if available) and check it matches the reference."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from nirs4all_papers.site import assets

_HARNESS = r"""
const fs=require('fs');
const payload=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const els={};
function mk(id){return els[id]||(els[id]={innerHTML:'',className:'',textContent:'',addEventListener(){},classList:{add(){},remove(){},toggle(){}},style:{}});}
global.window={__N4A_REPLAY__:payload,addEventListener(){}};
global.document={readyState:'complete',getElementById:mk,addEventListener(){},createElementNS(){return{setAttribute(){},classList:{add(){}},style:{}};}};
eval(fs.readFileSync(process.argv[3],'utf8'));
setTimeout(()=>{ fs.writeFileSync(process.argv[4], JSON.stringify({metrics:els['replay-metrics'].innerHTML, status:els['replay-status'].textContent})); }, 600);
"""


_CSV_HARNESS = r"""
const fs=require('fs');
const payload=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const csv=fs.readFileSync(process.argv[3],'utf8');
global.window={__N4A_REPLAY__:payload,addEventListener(){}};
global.document={readyState:'loading',getElementById(){return null;},addEventListener(){},createElementNS(){return{setAttribute(){},classList:{add(){}},style:{}};}};
eval(fs.readFileSync(process.argv[4],'utf8'));
const T=window.__N4A_TEST__;
const p=T.parseCsv(csv, payload.dataset.target);
const m=T.metrics(p.y, T.crossValidate(payload.plan, p.X, p.y));
fs.writeFileSync(process.argv[5], JSON.stringify({rows:p.X.length, cols:p.X[0].length, rmse:m.rmse, n:m.n}));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_csv_upload_path(demo_view, tmp_path):
    # Build a CSV (header = axis + 'target', rows = X + y) and re-run the pipeline on it via the hook.
    r = demo_view.replay
    axis, X, y = r["axis"], r["X"], r["y"]
    lines = [",".join(str(a) for a in axis) + ",target"]
    for row, t in zip(X, y, strict=True):
        lines.append(",".join(str(v) for v in row) + f",{t}")
    (tmp_path / "data.csv").write_text("\n".join(lines))
    plan = assets.replay_plan(demo_view)
    payload = {"plan": plan, "ioBase": "", "dataset": {"target": "target"}}
    (tmp_path / "payload.json").write_text(json.dumps(payload))
    (tmp_path / "engine.js").write_text(assets.REPLAY_JS)
    (tmp_path / "harness.js").write_text(_CSV_HARNESS)
    out = tmp_path / "out.json"
    subprocess.run(
        ["node", str(tmp_path / "harness.js"), str(tmp_path / "payload.json"), str(tmp_path / "data.csv"), str(tmp_path / "engine.js"), str(out)],
        check=True, timeout=60,
    )
    res = json.loads(out.read_text())
    assert res["rows"] == len(X) and res["cols"] == len(X[0])
    assert res["n"] == len(y)
    assert 1.0 < res["rmse"] < 2.5  # same data as the bundled demo -> same ballpark


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_replay_engine_matches_reference(demo_view, tmp_path):
    plan = assets.replay_plan(demo_view)
    payload = {"plan": plan, "dataset": {k: demo_view.replay[k] for k in ("X", "y", "axis", "target", "name")}}
    (tmp_path / "payload.json").write_text(json.dumps(payload))
    (tmp_path / "engine.js").write_text(assets.REPLAY_JS)
    (tmp_path / "harness.js").write_text(_HARNESS)
    out = tmp_path / "out.json"
    subprocess.run(
        ["node", str(tmp_path / "harness.js"), str(tmp_path / "payload.json"), str(tmp_path / "engine.js"), str(out)],
        check=True,
        timeout=60,
    )
    result = json.loads(out.read_text())
    assert "done" in result["status"]
    m = re.search(r"<b>([\d.]+)</b><span>RMSE", result["metrics"])
    assert m, result["metrics"]
    rmse = float(m.group(1))
    # the NIPALS reference engine should land near the sklearn CV reference (~1.7) on the demo data
    assert 1.0 < rmse < 2.5, rmse
