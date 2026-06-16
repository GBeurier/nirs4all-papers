# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import json

import pytest

from nirs4all_papers.site.escape import Safe, cell, esc, inline_json, locator_link, safe_url, slugify


def test_cell_escapes_untrusted_but_passes_safe():
    assert cell("<img src=x onerror=alert(1)>") == "&lt;img src=x onerror=alert(1)&gt;"
    assert cell(Safe("<b>ok</b>")) == "<b>ok</b>"


def test_safe_url_blocks_active_schemes():
    assert safe_url("javascript:alert(1)") is None
    assert safe_url("data:text/html,<script>") is None
    assert safe_url("https://nirs4all.org") == "https://nirs4all.org"
    assert safe_url("mailto:a@b.c") == "mailto:a@b.c"


def test_locator_link_is_safe_and_scheme_checked():
    assert isinstance(locator_link("10.1/x"), Safe)
    assert "doi.org/10.1/x" in locator_link("10.1/x")
    # a javascript: locator renders as escaped text, never a link
    assert "<a" not in locator_link("javascript:alert(1)")


def test_inline_json_neutralizes_script_and_refuses_nan():
    assert "<\\/script>" in inline_json({"x": "</script>"})
    with pytest.raises(ValueError):
        inline_json({"x": float("nan")})
    # round-trips otherwise
    assert json.loads(inline_json({"a": [1, 2]})) == {"a": [1, 2]}


def test_slugify():
    assert slugify("PLS_NIRS Demo!") == "pls-nirs-demo"
    assert slugify("///") == "paper"


def test_esc_none():
    assert esc(None) == ""
