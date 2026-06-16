# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

from nirs4all_papers.site import assets


def test_replay_panel_has_byod_upload(demo_view):
    html = assets.replay_panel(demo_view, "../")
    assert "Run on your own dataset" in html
    assert 'id="byod-file"' in html
    assert '"ioBase": ""' in html
    # without an io base, the panel points users to nirs4all-web for vendor formats
    assert "nirs4all-web" in html


def test_replay_panel_io_wasm_base_enables_vendor(demo_view):
    html = assets.replay_panel(demo_view, "../", io_wasm_base="../wasm")
    assert '"ioBase": "../wasm"' in html
    assert "nirs4all-formats + nirs4all-io WASM" in html
