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
