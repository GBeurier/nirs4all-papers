# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Detached current-container evidence over public Core and SDK owner APIs.

This module contains no physical parser, converter or fitted-object loader.
Archive publication can copy historical bytes independently of this reader.
"""
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ReaderDependencyError(RuntimeError):
    """The optional current reader or its matching native bridge is unavailable."""


@dataclass
class StepInfo:
    """Presentation input for isolated historical approximate-JS references only.

    Current V1 documents are never projected into this shape.
    """

    index: int
    kind: str
    raw: str
    short_name: str
    params: dict[str, Any] = field(default_factory=dict)
    reproducible: bool = True


@dataclass(frozen=True)
class BundleFile:
    """A payload member from Core's verified inventory."""

    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class OwnerDocument:
    """Exact owner-selected JSON and its semantic role; no fitted object."""

    role: str
    member: str | None
    raw: bytes
    value: Any
    artifact_id: str | None = None
    content_type: dict[str, Any] | None = None
    inventory_sha256: str | None = None


@dataclass
class Bundle:
    """One detached Core V1 inspection; readability is separate from support."""

    path: Path
    manifest_bytes: bytes
    manifest: dict[str, Any]
    view: dict[str, Any]
    profile: str = "foreign"
    support: str = "inventory_only"
    detail: str = "Owner semantics are not supported by Papers; execution is unavailable."
    documents: list[OwnerDocument] = field(default_factory=list)
    owner_view: dict[str, Any] = field(default_factory=dict)
    opaque_artifacts: list[dict[str, Any]] = field(default_factory=list)

    @property
    def container_sha256(self) -> str:
        return str(self.view["readability"]["container_sha256"])

    @property
    def manifest_sha256(self) -> str:
        return str(self.view["readability"]["manifest_sha256"])

    @property
    def files(self) -> list[BundleFile]:
        return [BundleFile(item["path"], item["byte_length"], item["sha256"]) for item in self.manifest["members"]]

    def document(self, role: str) -> OwnerDocument | None:
        matches = [doc for doc in self.documents if doc.role == role]
        if len(matches) > 1:
            raise ValueError(f"ambiguous owner document role: {role}")
        return matches[0] if matches else None


def _core() -> Any:
    try:
        core = importlib.import_module("nirs4all_core")
    except ImportError as error:
        raise ReaderDependencyError("Current reading requires the optional current-reader extra and matching Core native wheel.") from error
    if not callable(getattr(core, "open_n4a_file", None)):
        raise ReaderDependencyError("The installed Core lacks the public file-backed V1 reader.")
    return core


def read_bundle(
    path: str | Path, *, entrypoint: str | None = None, operation: str | None = None,
    memory_budget_bytes: int | None = None,
) -> Bundle:
    """Read genuine current V1 bytes through their owners, without execution.

    Unsupported physical transport and invalid owner admission raise ValueError.
    Unknown foreign content is inventory-only. SDK dependency absence is retained
    as a dependency status alongside the already verified container inventory.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    core = _core()
    try:
        with core.open_n4a_file(path, memory_budget_bytes=memory_budget_bytes) as source:
            raw_manifest = source.manifest_bytes()
            view = source.view()
            manifest = view["readability"]["manifest"]
            bundle = Bundle(path, raw_manifest, manifest, view)
            objects = [*manifest["artifacts"], *manifest["entrypoints"], *manifest["links"]]
            host = "nirs4all-python-host@1" in manifest["required_features"] or any(
                item["owner"] == "nirs4all.python-host" for item in objects
            )
            native = any(entry["owner"] == "dag-ml" and (
                "native-methods-package@1" in manifest["required_features"]
                or "native-methods-package@1" in entry["required_features"]
            ) for entry in manifest["entrypoints"])
            if host:
                # SDK owns the complete host shape/refusal, including mixed owners.
                _read_sdk(bundle, source, entrypoint, operation)
            elif native:
                if operation not in (None, "predict-external"):
                    raise ValueError("Papers supports native document reading through predict-external only")
                _read_native(bundle, core, source, entrypoint, memory_budget_bytes)
            elif entrypoint is not None or operation is not None:
                raise ValueError("the requested owner operation is unsupported by Papers")
            return bundle
    except core.NativeArchiveUnavailableError as error:
        raise ReaderDependencyError(str(error)) from error


def _read_native(bundle: Bundle, core: Any, source: Any, entrypoint: str | None, budget: int | None) -> None:
    if not callable(getattr(core, "open_native_package", None)):
        raise ReaderDependencyError("The installed Core lacks retained native package admission.")
    proof = core.open_native_package(source, entrypoint=entrypoint, operation="predict-external", memory_budget_bytes=budget)
    try:
        selected = proof.view()
        version = selected["package_schema_version"]
        if version == 2:
            package = core.read_portable_predictor_package_v2(proof)
            outcome = proof.training_outcome_bytes()
            bundle.documents.append(OwnerDocument("training_outcome", None, outcome, json.loads(outcome)))
        elif version == 3:
            package = core.read_portable_refit_package_v3(proof)
        else:
            raise ValueError(f"unsupported owner-selected native package version: {version}")
        bundle.documents.insert(0, OwnerDocument(
            "native_package", selected["package_member"], package, json.loads(package), selected["root_artifact"],
        ))
        bundle.profile = "native-methods-package"
        bundle.support = "documents_readable"
        bundle.detail = "Owner-admitted native documents; execution is not evaluated by Papers."
        bundle.owner_view = selected
    finally:
        # Core's proof owns its verified snapshot; it has no separate close API.
        del proof


def _read_sdk(bundle: Bundle, source: Any, entrypoint: str | None, operation: str | None) -> None:
    try:
        sdk = importlib.import_module("nirs4all")
        host = importlib.import_module("nirs4all.pipeline.dagml.host_container")
        inspect_host = sdk.inspect_n4a
    except (ImportError, AttributeError) as error:
        bundle.profile = "nirs4all.python-host"
        bundle.support = "dependency_unavailable"
        bundle.detail = f"SDK-host JSON inspection requires the optional sdk-host-reader extra: {error}"
        return
    if entrypoint not in (None, host.HOST_ENTRYPOINT_ID) or operation not in (None, host.HOST_OPERATION):
        raise ValueError("unsupported SDK-host inspection entrypoint/operation")
    if ("core_file" not in inspect.signature(host.open_n4a_source).parameters
            or not {"source", "include_host_json"} <= inspect.signature(inspect_host).parameters.keys()):
        raise ReaderDependencyError("The installed SDK lacks the matching safe-inspection/borrowed-source API.")
    with host.open_n4a_source(bundle.path, core_file=source) as opened:
        inspected = inspect_host(bundle.path, source=opened, include_host_json=True)
    bundle.profile = inspected["profile"]
    bundle.support = "documents_readable"
    bundle.detail = "SDK serialized JSON inspected; scientific scoring and execution are not evaluated."
    bundle.owner_view = {key: value for key, value in inspected.items() if key not in ("documents", "bundle_manifest_bytes", "view")}
    bundle.opaque_artifacts = inspected["opaque_artifacts"]
    bundle.documents = [OwnerDocument(
        item["role"], item["member"], item["bytes"], item["json"], item["artifact_id"], item["content_type"], item["inventory_sha256"],
    ) for item in inspected["documents"]]


def raw_file_identity(path: Path) -> tuple[str, int]:
    """Raw file-copy identity only; this grants no current-container admission."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def copy_download(path: Path, destination: Path, expected_sha256: str, *, current: Bundle | None = None) -> None:
    """Stage exact bytes, verify displayed identity, then atomically publish.

    Current containers use Core's verified copy. Historical raw copies never open
    members and are not labelled as current admission. Partial copies are removed.
    """
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".n4a-copy-", delete=False) as staged:
        temporary = Path(staged.name)
        try:
            if current is not None:
                core = _core()
                with core.open_n4a_file(path) as source:
                    report = source.view()["readability"]
                    if (report["container_sha256"] != current.container_sha256
                            or report["manifest_sha256"] != current.manifest_sha256
                            or report["container_sha256"] != expected_sha256):
                        raise ValueError("download source identity differs from displayed Core receipt")
                    source.copy_archive_to(staged)
            else:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                        staged.write(chunk)
                if digest.hexdigest() != expected_sha256:
                    raise ValueError("raw download source identity changed")
            staged.flush()
            staged.close()
            os.replace(temporary, destination)
        finally:
            staged.close()
            temporary.unlink(missing_ok=True)
