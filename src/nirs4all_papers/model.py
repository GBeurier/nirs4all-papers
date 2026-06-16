# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""View models: assemble a ``.n4a`` bundle + ``paper.yaml`` + resolved citations into a ``PaperView``.

``paper.yaml`` carries the human metadata the bundle cannot (title, authors, DOI, scores, protocol,
dataset reference); the bundle carries the pipeline + fingerprints. The two are merged here so
:mod:`nirs4all_papers.site.pages` is pure rendering.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .bibliography import Reference, build_bibliography, reference_for, resolve_method
from .bundle import Bundle, StepInfo, read_bundle
from .site.escape import slugify


@dataclass
class Author:
    name: str
    orcid: str | None = None
    affiliation: str | None = None


@dataclass
class Metric:
    name: str
    value: Any
    partition: str | None = None


@dataclass
class StepView:
    """A pipeline step plus its resolved citation, ready to render.

    ``reference`` is the *shared* citation (its number may be reused by other methods that cite the
    same paper), while ``principle`` is this operator's own one-line description — they differ when
    two operators (e.g. MinMaxScaler and StandardScaler) cite the same library.
    """

    info: StepInfo
    method_id: str | None
    reference: Reference | None
    principle: str | None = None

    @property
    def citation_number(self) -> int:
        return self.reference.number if self.reference else 0


@dataclass
class PaperView:
    """Everything one reproduction page needs."""

    slug: str
    meta: dict[str, Any]
    bundle: Bundle
    steps: list[StepView]
    references: list[Reference]
    replay: dict[str, Any] | None
    bundle_filename: str
    paper_dir: Path

    # ── flat metadata accessors ──────────────────────────────────────────
    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.slug)

    @property
    def authors(self) -> list[Author]:
        out: list[Author] = []
        for a in _as_list(self.meta.get("authors")):
            if isinstance(a, dict):
                out.append(Author(name=str(a.get("name") or ""), orcid=a.get("orcid"), affiliation=a.get("affiliation")))
            elif isinstance(a, str):
                out.append(Author(name=a))
        return [a for a in out if a.name]

    @property
    def authors_line(self) -> str:
        return ", ".join(a.name for a in self.authors)

    @property
    def abstract(self) -> str:
        return str(self.meta.get("abstract") or "")

    @property
    def venue(self) -> str | None:
        return self.meta.get("venue")

    @property
    def year(self) -> Any:
        return self.meta.get("year")

    @property
    def doi(self) -> str | None:
        return self.meta.get("doi")

    @property
    def status(self) -> str:
        return str(self.meta.get("status") or "preprint")

    @property
    def manuscript_license(self) -> str | None:
        return self.meta.get("license")

    @property
    def keywords(self) -> list[str]:
        return [str(k) for k in _as_list(self.meta.get("keywords"))]

    @property
    def dataset(self) -> dict[str, Any]:
        return _as_dict(self.meta.get("dataset"))

    @property
    def protocol(self) -> dict[str, Any]:
        return _as_dict(self.meta.get("protocol"))

    @property
    def links(self) -> list[dict[str, Any]]:
        return [link for link in _as_list(self.meta.get("links")) if isinstance(link, dict)]

    @property
    def provenance(self) -> dict[str, Any]:
        return _as_dict(self.meta.get("provenance"))

    @property
    def metrics(self) -> list[Metric]:
        out: list[Metric] = []
        for m in _as_list(self.meta.get("metrics")):
            if isinstance(m, dict) and m.get("name") is not None:
                out.append(Metric(name=str(m["name"]), value=m.get("value"), partition=m.get("partition")))
        return out

    # ── derived ──────────────────────────────────────────────────────────
    @property
    def n_steps(self) -> int:
        """Pipeline steps excluding internal split/cv steps (the scientifically meaningful count)."""
        return len([s for s in self.steps if s.info.kind != "split"])

    @property
    def model_step(self) -> StepView | None:
        return next((s for s in self.steps if s.info.kind == "model"), None)

    def headline_metrics(self) -> list[tuple[str, str]]:
        """KPI strip pairs (value, label): the published scores, then pipeline shape."""
        pairs: list[tuple[str, str]] = []
        for m in self.metrics[:3]:
            val = m.value
            label = m.name + (f" ({m.partition})" if m.partition else "")
            pairs.append((_fmt(val), label))
        model = self.model_step
        if model is not None:
            ncomp = model.info.params.get("n_components")
            if ncomp is not None:
                pairs.append((str(ncomp), "components"))
        pairs.append((str(self.n_steps), "pipeline steps"))
        ds = self.dataset
        if ds.get("n_samples"):
            pairs.append((_fmt(ds.get("n_samples")), "samples"))
        if ds.get("n_features"):
            pairs.append((_fmt(ds.get("n_features")), "wavelengths"))
        return pairs[:6]


@dataclass
class Catalog:
    root: Path
    papers: list[PaperView] = field(default_factory=list)


def _as_list(value: Any) -> list:
    """Tolerate malformed paper.yaml: return the value only if it is a list, else ``[]``."""
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict:
    """Tolerate malformed paper.yaml: return the value only if it is a dict, else ``{}``."""
    return value if isinstance(value, dict) else {}


def _fmt(val: Any) -> str:
    if isinstance(val, bool) or val is None:
        return "—"
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float):
        return f"{val:.4g}"
    return str(val)


def _load_metadata(paper_dir: Path) -> dict[str, Any]:
    for name in ("paper.yaml", "paper.yml", "paper.json"):
        path = paper_dir / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            data = json.loads(text) if name.endswith(".json") else yaml.safe_load(text)
            if isinstance(data, dict):
                return data
    raise FileNotFoundError(f"no paper.yaml / paper.json in {paper_dir}")


def _finite_rows(rows: Any, *, width: int | None = None) -> list[list[float]] | None:
    """Coerce a list of equal-length numeric rows to finite floats, or ``None`` if malformed."""
    if not isinstance(rows, list) or not rows:
        return None
    out: list[list[float]] = []
    for r in rows:
        if not isinstance(r, list):
            return None
        if width is None:
            width = len(r)
        if len(r) != width:  # reject ragged matrices
            return None
        fr: list[float] = []
        for v in r:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                return None
            fr.append(float(v))
        out.append(fr)
    return out


def _finite_vec(seq: Any) -> list[float] | None:
    if not isinstance(seq, list) or not seq:
        return None
    out: list[float] = []
    for v in seq:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            return None
        out.append(float(v))
    return out


def _load_replay(paper_dir: Path, meta: dict[str, Any]) -> dict[str, Any] | None:
    """Load + sanitize the optional replay dataset; a malformed sidecar degrades to ``None``.

    Validation is strict on purpose: a non-finite value or ragged shape would otherwise crash the
    JSON embedding (``allow_nan=False``) or the SVG preview for the *whole* site build.
    """
    ref = meta.get("replay") or "replay.json"
    path = paper_dir / ref if not Path(ref).is_absolute() else Path(ref)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    x = _finite_rows(data.get("X"))
    if x is None:
        return None
    y = _finite_vec(data.get("y"))
    if y is None or len(y) != len(x):
        return None
    axis = data.get("axis")
    axis_clean = _finite_vec(axis) if axis is not None else None
    if axis is not None and (axis_clean is None or len(axis_clean) != len(x[0])):
        return None
    clean = dict(data)
    clean["X"], clean["y"] = x, y
    if axis_clean is not None:
        clean["axis"] = axis_clean
    return clean


def load_paper(paper_dir: str | Path) -> PaperView:
    """Build a :class:`PaperView` from a ``papers/<slug>/`` directory."""
    paper_dir = Path(paper_dir)
    meta = _load_metadata(paper_dir)
    slug = slugify(str(meta.get("slug") or paper_dir.name))

    bundle_name = str(meta.get("bundle") or "model.n4a")
    bundle_path = (paper_dir / bundle_name).resolve()
    if not bundle_path.is_relative_to(paper_dir.resolve()):
        raise ValueError(f"{paper_dir.name}: bundle path '{bundle_name}' escapes the paper directory")
    bundle = read_bundle(bundle_path)
    # The crate/download always use a flat basename, never a sub-path.
    bundle_filename = Path(bundle_name).name

    steps: list[StepView] = []
    used_ids: list[str] = []
    for info in bundle.steps():
        method_id = resolve_method(info.short_name, info.raw)
        if method_id:
            used_ids.append(method_id)
        steps.append(StepView(info=info, method_id=method_id, reference=None))

    references, id_to_ref = build_bibliography(used_ids)
    for sv in steps:
        if sv.method_id:
            sv.reference = id_to_ref.get(sv.method_id)
            own = reference_for(sv.method_id)  # this operator's own entry (for its specific principle)
            sv.principle = own.principle if own else None

    return PaperView(
        slug=slug,
        meta=meta,
        bundle=bundle,
        steps=steps,
        references=references,
        replay=_load_replay(paper_dir, meta),
        bundle_filename=bundle_filename,
        paper_dir=paper_dir,
    )


def load_catalog(root: str | Path) -> Catalog:
    """Discover every ``papers/<slug>/paper.yaml`` under ``root`` and build its view."""
    root = Path(root)
    papers_dir = root / "papers"
    papers: list[PaperView] = []
    seen: dict[str, str] = {}
    if papers_dir.is_dir():
        for child in sorted(papers_dir.iterdir()):
            if child.is_dir() and any((child / n).exists() for n in ("paper.yaml", "paper.yml", "paper.json")):
                view = load_paper(child)
                if view.slug in seen:
                    raise ValueError(
                        f"slug collision: '{child.name}' and '{seen[view.slug]}' both resolve to slug "
                        f"'{view.slug}' — they would overwrite each other's page and bundle. Set a distinct `slug:`."
                    )
                seen[view.slug] = child.name
                papers.append(view)
    return Catalog(root=root, papers=papers)
