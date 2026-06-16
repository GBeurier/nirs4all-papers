# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Read a deposited ``.n4a`` bundle with the stdlib only (no nirs4all import required).

A ``.n4a`` is a ZIP archive. ``manifest.json`` and ``pipeline.json`` are always present;
``fold_weights.json`` / ``trace.json`` / ``chain.json`` are optional. The bundle carries the
**pipeline definition + fitted artifacts**, but *not* scores/protocol/dataset identity — those are
supplied by the paper's ``paper.yaml`` (see :mod:`nirs4all_papers.model`).

This module deliberately mirrors only the *reading* contract of
``nirs4all.pipeline.bundle.BundleLoader`` (manifest/pipeline/fold_weights) so the publisher stays
dependency-light and never re-implements nirs4all logic.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A live-object ``repr()`` (e.g. an internal splitter) embeds a volatile memory address; strip it so
# it never lands in the permanent, fingerprinted deposit (pipeline.json / RO-Crate / page).
_ADDR_RE = re.compile(r" (?:object )?at 0x[0-9A-Fa-f]+")

# Step-dict keys, in the order the writer uses them (see nirs4all generator.py / pipeline.json).
_STEP_KEYS = ("step", "class", "model", "meta_model", "y_processing")

# Heuristics for the one pipeline step that is a live-object ``repr()`` (a splitter) rather than a
# clean class path — it carries a volatile memory address and produces no fitted artifact.
_SPLITTER_HINTS = ("Splitter", "split", "Fold", "KFold", "ShuffleSplit")


@dataclass
class StepInfo:
    """One ordered pipeline step, typed for rendering and citation lookup."""

    index: int  # 1-based position in pipeline.json["steps"]
    kind: str  # preprocessing | target | model | split | other
    raw: str  # the verbatim class path / repr from pipeline.json
    short_name: str  # last dotted component, repr wrapper stripped
    params: dict[str, Any] = field(default_factory=dict)
    reproducible: bool = True  # False for repr-only steps (e.g. an internal splitter)


@dataclass
class BundleFile:
    """An entry inside the .n4a archive with its size and content fingerprint."""

    name: str
    size: int
    sha256: str


@dataclass
class Bundle:
    """A parsed ``.n4a`` bundle: manifest + pipeline + fold weights + a fingerprinted file inventory."""

    path: Path
    manifest: dict[str, Any]
    pipeline: dict[str, Any]
    fold_weights: dict[int, float]
    files: list[BundleFile]
    has_trace: bool
    has_chain: bool

    @property
    def model_step_index(self) -> int | None:
        idx = self.pipeline.get("model_step_index", self.manifest.get("model_step_index"))
        return int(idx) if isinstance(idx, (int, float)) else None

    @property
    def nirs4all_version(self) -> str:
        return str(self.manifest.get("nirs4all_version") or "—")

    @property
    def pipeline_uid(self) -> str:
        return str(self.manifest.get("pipeline_uid") or "")

    @property
    def fingerprint(self) -> str:
        """A stable bundle fingerprint: SHA-256 over the sorted ``name:sha256`` of every file."""
        joined = "\n".join(f"{f.name}:{f.sha256}" for f in sorted(self.files, key=lambda f: f.name))
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def steps(self) -> list[StepInfo]:
        """Ordered, typed pipeline steps (1-based), resolved from ``pipeline.json``."""
        out: list[StepInfo] = []
        raw_steps = self.pipeline.get("steps") or []
        model_idx = self.model_step_index
        for i, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue
            key = next((k for k in _STEP_KEYS if k in step), None)
            if key is None:
                continue
            raw = str(step.get(key))
            short, is_repr = _short_name(raw)
            params = step.get("params") if isinstance(step.get("params"), dict) else {}
            kind = _classify(key, short, is_repr, index=i, model_idx=model_idx)
            out.append(
                StepInfo(
                    index=i,
                    kind=kind,
                    raw=raw,
                    short_name=short,
                    params=dict(params or {}),
                    reproducible=not is_repr,
                )
            )
        return out


def _short_name(raw: str) -> tuple[str, bool]:
    """Return ``(short_class_name, is_repr)``; strips ``<… object at 0x…>`` reprs and module paths."""
    s = raw.strip()
    is_repr = s.startswith("<")
    if is_repr:
        s = s[1:]
        s = s.split(" object at", 1)[0]
        s = s.split(" at 0x", 1)[0]
    s = s.strip().strip("<>").strip()
    short = s.rsplit(".", 1)[-1] if "." in s else s
    return short.lstrip("_") or s, is_repr


def _classify(key: str, short: str, is_repr: bool, *, index: int, model_idx: int | None) -> str:
    """Bucket a step into preprocessing / target / model / split / other."""
    if key == "y_processing":
        return "target"
    if key in ("model", "meta_model"):
        return "model"
    if is_repr or any(h.lower() in short.lower() for h in _SPLITTER_HINTS):
        return "split"
    if key == "class":
        return "model" if (model_idx is not None and index == model_idx) else "preprocessing"
    return "preprocessing"


def _sanitize_pipeline(pipeline: dict[str, Any]) -> None:
    """Strip volatile ``repr()`` memory addresses from every step's string values, in place."""
    for step in pipeline.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for key, value in list(step.items()):
            if isinstance(value, str):
                step[key] = _ADDR_RE.sub("", value)


def _read_json_member(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        with zf.open(name) as fh:
            data = json.loads(fh.read().decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def read_bundle(path: str | Path) -> Bundle:
    """Open and parse a ``.n4a`` bundle. Raises ``ValueError`` if it is not a valid bundle ZIP."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if not zipfile.is_zipfile(path):
        raise ValueError(f"{path} is not a valid .n4a bundle (not a ZIP archive)")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if "manifest.json" not in names or "pipeline.json" not in names:
            raise ValueError(f"{path} is missing manifest.json/pipeline.json — not a nirs4all bundle")
        manifest = _read_json_member(zf, "manifest.json")
        pipeline = _read_json_member(zf, "pipeline.json")
        _sanitize_pipeline(pipeline)
        raw_weights = _read_json_member(zf, "fold_weights.json") if "fold_weights.json" in names else {}
        fold_weights: dict[int, float] = {}
        for k, v in raw_weights.items():
            try:
                fold_weights[int(k)] = float(v)
            except (TypeError, ValueError):
                continue

        files: list[BundleFile] = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            with zf.open(info) as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            files.append(BundleFile(name=info.filename, size=info.file_size, sha256=digest))

    return Bundle(
        path=path,
        manifest=manifest,
        pipeline=pipeline,
        fold_weights=fold_weights,
        files=files,
        has_trace="trace.json" in names,
        has_chain="chain.json" in names,
    )
