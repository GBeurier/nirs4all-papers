# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Inline-SVG charts (server-side): a spectra preview of the replay dataset.

The parity / residual plots are drawn *live* by the replay engine (:mod:`assets`) once the pipeline
re-runs in the browser. This module keeps only the static preview, in the same restrained scientific
aesthetic as the ``nirs4all-datasets`` charts (single teal accent, tabular-mono numbers).
"""
from __future__ import annotations

import math
from typing import Any

from .escape import esc

ACCENT = "#0f766e"
ACCENT_SOFT = "#0d9488"
MUTED = "#64748b"
FAINT = "#94a3b8"
GRID = "#dde4ec"
GRID_SOFT = "#eef2f7"
PLOT_BG = "#ffffff"


def _ok(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _svg(w: float, h: float, inner: str, *, title: str) -> str:
    return (
        f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{esc(title)}" '
        f'preserveAspectRatio="xMidYMid meet"><title>{esc(title)}</title>{inner}</svg>'
    )


def _empty(w: float, h: float, title: str, msg: str = "no data") -> str:
    inner = (
        f'<rect x="10" y="10" width="{w - 20:.0f}" height="{h - 20:.0f}" rx="8" fill="{GRID_SOFT}" '
        f'fill-opacity="0.5" stroke="{GRID}" stroke-dasharray="4 4"></rect>'
        f'<text x="{w / 2:.0f}" y="{h / 2 + 4:.0f}" text-anchor="middle" font-size="11.5" fill="{FAINT}">{esc(msg)}</text>'
    )
    return _svg(w, h, inner, title=title)


def spectra_preview(axis: list[float], rows: list[list[float]], *, title: str = "Spectra", unit: str = "", width: float = 520, max_lines: int = 40) -> str:
    """Faint overlay of up to ``max_lines`` spectra + the mean curve, with framed axes."""
    if not rows or not axis or len(axis) < 2:
        return _empty(width, 240, title, "no spectra")
    n_ax = len(axis)
    sample = rows[:: max(1, len(rows) // max_lines)][:max_lines]
    flat = [v for r in sample for v in r if _ok(v)]
    if not flat:
        return _empty(width, 240, title, "no spectra")
    y_lo, y_hi = min(flat), max(flat)
    if y_hi <= y_lo:
        y_hi = y_lo + 1.0
    a_lo, a_hi = float(axis[0]), float(axis[-1])
    if a_hi <= a_lo:
        a_hi = a_lo + 1.0
    height = round(width * 0.5)
    pad_l, pad_r, pad_t, pad_b = 48, 14, 14, 30
    pw, ph = width - pad_l - pad_r, height - pad_t - pad_b

    def px(a: float) -> float:
        return pad_l + (a - a_lo) / (a_hi - a_lo) * pw

    def py(v: float) -> float:
        return pad_t + (1.0 - (v - y_lo) / (y_hi - y_lo)) * ph

    parts: list[str] = [f'<rect x="{pad_l}" y="{pad_t}" width="{pw:.0f}" height="{ph:.0f}" rx="3" fill="{PLOT_BG}" stroke="{GRID}"></rect>']
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = pad_t + frac * ph
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + pw:.0f}" y2="{y:.1f}" stroke="{GRID_SOFT}"></line>')
        val = y_hi - frac * (y_hi - y_lo)
        parts.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="10.5" fill="{MUTED}" class="numt">{val:.3g}</text>')
    mean = [sum(r[i] for r in sample if i < len(r) and _ok(r[i])) / max(1, sum(1 for r in sample if i < len(r) and _ok(r[i]))) for i in range(n_ax)]
    for r in sample:
        pts = " ".join(f"{px(float(axis[i])):.1f},{py(float(r[i])):.1f}" for i in range(min(n_ax, len(r))) if _ok(r[i]))
        if pts:
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{ACCENT_SOFT}" stroke-width="0.7" opacity="0.18"></polyline>')
    mpts = " ".join(f"{px(float(axis[i])):.1f},{py(mean[i]):.1f}" for i in range(n_ax) if _ok(mean[i]))
    parts.append(f'<polyline points="{mpts}" fill="none" stroke="{ACCENT}" stroke-width="1.8"></polyline>')
    for frac in (0.0, 0.5, 1.0):
        a = a_lo + frac * (a_hi - a_lo)
        parts.append(f'<text x="{px(a):.0f}" y="{height - 12:.0f}" text-anchor="middle" font-size="10.5" fill="{MUTED}" class="numt">{a:.4g}</text>')
    parts.append(f'<text x="{pad_l + pw / 2:.0f}" y="{height - 1:.0f}" text-anchor="middle" font-size="11" fill="{FAINT}">{esc(title)}{(" / " + esc(unit)) if unit else ""}</text>')
    return _svg(width, height, "".join(parts), title=title)
