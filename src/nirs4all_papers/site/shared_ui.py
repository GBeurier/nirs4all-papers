# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Private display projection and prebuilt UI resources; no owner calls or Node."""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .components import metric_value

if TYPE_CHECKING:
    from ..model import PaperView

_READING_EXPLANATIONS = {
    "archive_only": "Archive publication only; current reading has not been evaluated.",
    "dependency_unavailable": "An optional reader dependency is unavailable; this is not a format refusal.",
    "current_reading_refused": "Current reading was refused; the original archive remains downloadable.",
    "documents_readable": "Owner documents are readable. This does not establish executability or scientific validation.",
    "inventory_only": "Container inventory is readable; Papers does not support these owner semantics.",
}


def paper_projection(view: PaperView) -> dict[str, Any]:
    """Select public display strings, without interpreting owner documents or scores."""
    data: dict[str, Any] = {
        "readingStatus": view.reading_status,
        "readingExplanation": _READING_EXPLANATIONS.get(
            view.reading_status, "See the owner documents and reading detail for this reading status.",
        ),
        "rawDownloadSha256": view.raw_download_sha256,
        "metrics": [
            {"name": metric.name, "valueText": metric_value(metric.value),
             "partition": str(metric.partition) if metric.partition is not None else None}
            for metric in view.metrics
        ],
    }
    if view.bundle is not None:
        for key, value in (
            ("coreContainerSha256", view.bundle.container_sha256),
            ("coreManifestSha256", view.bundle.manifest_sha256),
            ("ownerProfile", view.bundle.profile),
        ):
            if value:
                data[key] = value
    return data


def projection_json(view: PaperView) -> str:
    """Valid JSON in an inert script element, including hostile text and non-finite display strings."""
    text = json.dumps(paper_projection(view), allow_nan=False, ensure_ascii=True)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def copy_ui_resources(out: Path) -> bool:
    """Copy staged package assets into marked build output; unstaged source stays static-only."""
    source = resources.files("nirs4all_papers").joinpath("data").joinpath("ui")
    required = ("papers-ui.js", "papers-ui.css", "qualification.css", "manifest.json")
    if not all(source.joinpath(name).is_file() for name in required) or not source.joinpath("licenses").is_dir():
        return False
    destination = out / "assets" / "papers-ui"
    destination.mkdir(parents=True, exist_ok=True)
    for name in required:
        (destination / name).write_bytes(source.joinpath(name).read_bytes())

    def copy_tree(src: Any, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            target = dst / child.name
            if child.is_dir():
                copy_tree(child, target)
            else:
                target.write_bytes(child.read_bytes())

    copy_tree(source.joinpath("licenses"), destination / "licenses")
    return True
