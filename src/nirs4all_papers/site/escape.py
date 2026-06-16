# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""HTML/JSON escaping + small formatting primitives (pure stdlib).

Mirrors the helpers in the ``nirs4all-datasets`` site generator so the two sites share rendering
conventions; never touches nirs4all, the network, or anything beyond the stdlib.
"""
from __future__ import annotations

import html
import json
import math
from typing import Any

_URL_SCHEMES_OK = ("http://", "https://", "mailto:")


class Safe(str):
    """Marks a string as already-rendered, trusted HTML (built by our own code).

    Rendering helpers escape everything that is *not* a :class:`Safe`. This replaces the unsound
    "trust a value if it starts with ``<``" heuristic, which let attacker-supplied free-text
    (``paper.yaml`` notes, ``.n4a`` manifest scalars) inject raw HTML.
    """

    __slots__ = ()


def esc(value: Any) -> str:
    """HTML-escape a scalar for text/attribute context (``None`` -> empty string)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def cell(value: Any) -> str:
    """Render a table/inline value: pass :class:`Safe` HTML through, escape everything else."""
    return str(value) if isinstance(value, Safe) else esc(value)


def safe_url(url: Any) -> str | None:
    """Return an escaped URL only if its scheme is on the allowlist, else ``None``.

    Blocks ``javascript:`` / ``data:`` and other active schemes from reaching an ``href``.
    """
    if not url:
        return None
    text = str(url).strip()
    low = text.lower()
    if low.startswith(_URL_SCHEMES_OK) or text.startswith("/") or text.startswith("#"):
        return html.escape(text, quote=True)
    return None


def inline_json(obj: Any) -> str:
    """JSON for embedding inside a ``<script>`` tag (neutralizes ``</script>`` and HTML comments)."""
    return json.dumps(obj, allow_nan=False, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def num(value: Any, nd: int = 4) -> str:
    """Compact, locale-free number formatting; em-dash for ``None``/non-finite; thousands for ints."""
    if isinstance(value, bool) or value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "—"
        if value == int(value) and abs(value) < 1e15:
            return f"{int(value):,}"
        return f"{value:.{nd}g}"
    return esc(value)


def kv_rows(rows: list[tuple[str, Any]]) -> str:
    """Render a 2-column key/value table body, dropping rows whose value is ``None``/empty.

    A value that already starts with ``<`` is treated as trusted pre-rendered HTML (e.g. a link);
    every other value is HTML-escaped.
    """
    out: list[str] = []
    for key, value in rows:
        if value in (None, "", [], {}):
            continue
        out.append(f"<tr><th>{esc(key)}</th><td>{cell(value)}</td></tr>")
    return "".join(out)


def table(caption: str, body: str, *, css_class: str = "kv") -> str:
    """Wrap a key/value (or generic) table body in a captioned ``<table>``; empty body -> ``""``."""
    if not body:
        return ""
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    return f'<table class="{esc(css_class)}">{cap}<tbody>{body}</tbody></table>'


def locator_link(locator: Any) -> Safe:
    """Render a DOI / URL / plain locator as a link (DOI -> doi.org, http(s) as-is, else text).

    Returns :class:`Safe` HTML; only allowlisted URL schemes become links (others render as text).
    """
    loc = str(locator or "").strip()
    if not loc:
        return Safe("")
    if loc.startswith("10."):
        return Safe(f'<a href="https://doi.org/{esc(loc)}" target="_blank" rel="noopener">{esc(loc)}</a>')
    href = safe_url(loc)
    if href:
        return Safe(f'<a href="{href}" target="_blank" rel="noopener">{esc(loc)}</a>')
    return Safe(esc(loc))


def slugify(value: str) -> str:
    """A filesystem/URL-safe slug (lowercase, alnum + single hyphens)."""
    out: list[str] = []
    prev_dash = False
    for ch in str(value).strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "paper"
