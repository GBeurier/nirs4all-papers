# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Reproduction-document publisher for the nirs4all ecosystem.

Turns a deposited ``.n4a`` bundle plus a hand-written ``paper.yaml`` into a self-contained,
publication-grade reproduction page (methods + bibliography report **and** a live in-browser pipeline
replay) plus machine-readable deposit sidecars (CITATION.cff, BibTeX, RO-Crate, pipeline.json).

See ``docs/REPRODUCTION_PUBLISHER.md`` for the product design.
"""
from __future__ import annotations

__version__ = "0.2.0"
