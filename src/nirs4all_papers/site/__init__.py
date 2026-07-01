# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Build the static reproduction-document site: load -> render -> write ``out/``.

Pure rendering over the committed inputs (``papers/<slug>/paper.yaml`` + ``model.n4a``): one HTML page
per paper plus its deposit sidecars (the bundle, ``pipeline.json``, ``CITATION.cff``,
``references.bib``, ``ro-crate-metadata.json``), the landing page, the catalog, and the brand chrome.
All charts are inline SVG; the replay engine is inline JS; the output is self-contained.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..model import Catalog, PaperView

_ENCODING = {
    ".n4a": "application/zip",
    ".json": "application/json",
    ".bib": "application/x-bibtex",
    ".cff": "application/x-yaml",
    ".html": "text/html",
}


def _file_meta(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "name": path.name,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "encodingFormat": _ENCODING.get(path.suffix, "application/octet-stream"),
    }


def write_paper_sidecars(view: PaperView, out: str | Path) -> Path:
    """Write the per-paper deposit bundle: .n4a + pipeline.json + CITATION.cff + references.bib + RO-Crate."""
    from .. import provenance
    from ..bibliography import references_to_bibtex

    out = Path(out)
    crate = out / "paper" / view.slug
    crate.mkdir(parents=True, exist_ok=True)

    # The deposited bundle (for download + replay), copied verbatim.
    bundle_dst = crate / view.bundle_filename
    shutil.copy2(view.bundle.path, bundle_dst)
    # The pipeline definition, lifted out for easy inspection.
    (crate / "pipeline.json").write_text(json.dumps(view.bundle.pipeline, indent=2, ensure_ascii=False), encoding="utf-8")
    # Citation metadata.
    (crate / "CITATION.cff").write_text(provenance.citation_cff(view), encoding="utf-8")
    (crate / "references.bib").write_text(references_to_bibtex(view.references), encoding="utf-8")

    crate_files = [_file_meta(crate / name) for name in (view.bundle_filename, "pipeline.json", "CITATION.cff", "references.bib")]
    crate_meta = provenance.ro_crate(view, crate_files)
    (crate / "ro-crate-metadata.json").write_text(json.dumps(crate_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return crate


_write_paper_sidecars = write_paper_sidecars


def _copy_io_wasm(io_wasm: str | Path, out: Path) -> str:
    """Copy the nirs4all-formats + nirs4all-io WASM bundles into ``out/wasm/``; return the page-relative base.

    Expects ``io_wasm`` to contain ``formats/`` and ``io/`` subdirectories of wasm-bindgen output.
    The returned base (``../wasm``) is relative to a ``paper/<slug>.html`` page.
    """
    src = Path(io_wasm)
    if not (src / "formats").is_dir():
        raise ValueError(f"--io-wasm {src} has no formats/ subdirectory of nirs4all-formats WASM output")
    dst = out / "wasm"
    for sub in ("formats", "io"):
        if (src / sub).is_dir():
            shutil.copytree(src / sub, dst / sub)
    return "../wasm"


def _copy_brand(root: Path, out: Path) -> None:
    """Ship the site chrome (favicon, app icon, social card) under ``out/brand/``."""
    brand_src = root / "assets" / "brand"
    if not brand_src.is_dir():
        return
    brand_out = out / "brand"
    brand_out.mkdir(parents=True, exist_ok=True)
    for name in ("favicon.ico", "icon.svg", "icon-180.png", "og.png", "horizontal.svg", "horizontal-dark.svg"):
        src = brand_src / name
        if src.exists():
            shutil.copy2(src, brand_out / name)


def build_site(root: str | Path, out: str | Path, io_wasm: str | Path | None = None) -> Path:
    """Build the reproduction-document site from ``root`` into ``out`` (regenerated wholesale).

    ``io_wasm`` (optional) is a directory holding ``formats/`` and ``io/`` nirs4all-formats /
    nirs4all-io WASM bundles (e.g. ``nirs4all-web/studio-lite/src/engine/wasm``). When given, it is
    copied into ``out/wasm/`` so the replay's "run on your own data" can decode vendor spectra files
    in-browser; otherwise only the CSV upload path is available.
    """
    from ..model import load_catalog
    from . import pages

    root = Path(root)
    out = Path(out)
    # Guard the wholesale rmtree: only ever delete a directory this tool created (it carries the
    # marker). This refuses `--out .`, `--out src`, `--out papers`, etc. — any pre-existing,
    # non-empty directory we did not build — instead of silently destroying the source tree.
    marker = ".n4a-papers-build"
    if out.exists():
        if not out.is_dir():
            raise ValueError(f"refusing to build: --out {out} is a file, not a directory")
        if any(out.iterdir()) and not (out / marker).exists():
            raise ValueError(
                f"refusing to wipe {out}: it is a non-empty directory not created by n4a-papers "
                f"(no {marker} marker). Choose an empty or dedicated output directory."
            )
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / marker).write_text("nirs4all-papers build output — safe to delete.\n", encoding="utf-8")
    (out / "paper").mkdir()

    io_base = _copy_io_wasm(io_wasm, out) if io_wasm else ""

    catalog = load_catalog(root)

    (out / "index.html").write_text(pages.render_index(catalog), encoding="utf-8")
    (out / "catalog.html").write_text(pages.render_catalog(catalog), encoding="utf-8")
    for view in catalog.papers:
        (out / "paper" / f"{view.slug}.html").write_text(pages.render_paper(view, io_base), encoding="utf-8")
        write_paper_sidecars(view, out)

    _write_seo(out, catalog)
    _copy_brand(root, out)
    return out


def _write_seo(out: Path, catalog: Catalog) -> None:
    """Emit robots.txt + sitemap.xml for the public, indexed archive."""
    from .theme import SITE_URL

    paths = ["", "catalog.html"] + [f"paper/{p.slug}.html" for p in catalog.papers]
    urls = "".join(f"  <url><loc>{SITE_URL}/{p}</loc></url>\n" for p in paths)
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    (out / "sitemap.xml").write_text(head + urls + "</urlset>\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
