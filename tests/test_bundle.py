# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from nirs4all_papers.bundle import ReaderDependencyError, copy_download, read_bundle
from tests.conftest import make_n4a


def test_native_owner_documents_are_exact_and_child_has_no_invented_parent(native_files):
    parent, child, package, outcome, child_package = native_files
    result = read_bundle(parent)
    assert result.profile == "native-methods-package"
    assert result.support == "documents_readable"
    assert result.document("native_package").raw == package
    assert result.document("training_outcome").raw == outcome
    assert result.document("training_outcome").member is None
    assert result.document("native_package").member == result.owner_view["package_member"]
    assert result.owner_view["receipt"]["container_sha256"] == hashlib.sha256(parent.read_bytes()).hexdigest()
    assert result.owner_view["manifest"] == result.manifest
    assert result.document("training_outcome").value == json.loads(outcome)
    result_child = read_bundle(child)
    assert result_child.owner_view["package_schema_version"] == 3
    assert result_child.document("native_package").raw == child_package
    assert result_child.document("training_outcome") is None
    assert not any(link["relation"] == "refit_of" for link in result_child.manifest["links"])


def test_sdk_documents_preserve_full_recipe_scores_and_raw_strings(current_view):
    result = current_view.bundle
    train = result.document("training_declaration")
    predict = result.document("prediction_config")
    assert train.value["steps"][1]["branch"][1][0]["model"] == "sklearn.linear_model.Ridge"
    assert train.value["options"]["search"] == {"n_components": [1, 2]}
    assert train.value["targets"] == ["target:b", "target:a"]
    assert predict.value != train.value
    assert result.document("bundle_manifest").value["extra"]["owner_string"] == "<Opaque object at 0x123abc>"
    scores = next(doc.value for doc in result.documents if doc.member == "scores.json")
    assert scores["score"] == {"value": 1.25, "metric": "rmse", "partition": "validation", "target": "t:2",
                               "level": "sample", "selection": "owner-declared", "aggregation": "mean"}
    assert result.document("relation_replay_manifest").value["sample_ids"] == ["s:2", "s:1"]
    assert result.opaque_artifacts and all("bytes" not in item for item in result.opaque_artifacts)
    assert current_view.steps == [] and current_view.n_steps is None
    for document in result.documents:
        assert hashlib.sha256(document.raw).hexdigest() == document.inventory_sha256
        assert json.loads(document.raw) == document.value


def test_rejects_old_physical_and_corruption(tmp_path, native_files):
    historical = make_n4a(tmp_path / "old.n4a", [{"class": "x.Model"}])
    with pytest.raises(ValueError):
        read_bundle(historical)
    plain = tmp_path / "plain.n4a"
    plain.write_bytes(b'{"manifest":{}}')
    with pytest.raises(ValueError):
        read_bundle(plain)
    parent = native_files[0]
    damaged = bytearray(parent.read_bytes())
    damaged[0] ^= 1
    plain.write_bytes(damaged)
    with pytest.raises(ValueError):
        read_bundle(plain)
    with pytest.raises(FileNotFoundError):
        read_bundle(tmp_path / "missing.n4a")


def _foreign_manifest():
    return {"schema": "nirs4all.n4a.container.v1", "schema_version": 1, "minimum_reader_version": 1,
            "container_id": "papers:foreign", "required_features": [], "physical_profile": "zip-stored.v1",
            "members": [{"path": "pipeline.json", "byte_length": 0, "sha256": "0" * 64}],
            "artifacts": [{"id": "foreign", "kind": "attachment", "owner": "foreign.example",
                           "content_type": {"id": "foreign.opaque", "version": 1},
                           "identity": {"owner": "foreign.example", "schema": "foreign.identity", "schema_version": 1,
                                        "fingerprint_profile": "opaque", "fingerprint": "foreign:value"},
                           "storage": {"kind": "embedded", "root_member": "pipeline.json", "member_paths": ["pipeline.json"]},
                           "requirements": None}], "links": [], "entrypoints": []}


def test_unknown_foreign_stays_inventory_only_despite_filename(tmp_path):
    import nirs4all_core as core

    path = tmp_path / "unknown.bin"
    core.write_n4a_file(path, json.dumps(_foreign_manifest()), [("pipeline.json", b"opaque: not JSON")])
    result = read_bundle(path)
    assert result.support == "inventory_only"
    assert result.documents == []
    assert result.files[0].name == "pipeline.json"


def test_ambiguous_native_and_explicit_binding_refuse(tmp_path, native_files):
    import nirs4all_core as core

    parent = native_files[0]
    with core.open_n4a_file(parent) as source:
        manifest = source.view()["readability"]["manifest"]
        entry = next(item for item in manifest["entrypoints"] if item["operation"] == "predict-external")
        manifest["entrypoints"].append({**entry, "id": "duplicate-predict"})
        path = tmp_path / "ambiguous.n4a"
        core.write_n4a_file(path, json.dumps(manifest), [], base=source)
    with pytest.raises(ValueError, match="ambiguous"):
        read_bundle(path)
    assert read_bundle(path, entrypoint=entry["id"]).support == "documents_readable"
    with pytest.raises(ValueError):
        read_bundle(parent, entrypoint="missing")
    with pytest.raises(ValueError):
        read_bundle(parent, operation="retrain")


def test_mixed_sdk_owner_refuses_without_native_retry(tmp_path, sdk_paper, monkeypatch):
    import nirs4all_core as core

    with core.open_n4a_file(sdk_paper / "model.n4a") as source:
        manifest = source.view()["readability"]["manifest"]
        manifest["artifacts"][1]["owner"] = "foreign.example"
        manifest["artifacts"][1]["identity"]["owner"] = "foreign.example"
        path = tmp_path / "mixed.n4a"
        core.write_n4a_file(path, json.dumps(manifest), [], base=source)
    monkeypatch.setattr(core, "open_native_package", lambda *a, **k: pytest.fail("native retry"))
    with pytest.raises(ValueError, match="mix"):
        read_bundle(path)


def test_verified_copy_identity_and_partial_discard(tmp_path, native_files, monkeypatch):
    import nirs4all_core as core

    from nirs4all_papers import bundle as module

    parent = native_files[0]
    result = read_bundle(parent)
    destination = tmp_path / "download.n4a"
    copy_download(parent, destination, result.container_sha256, current=result)
    assert destination.read_bytes() == parent.read_bytes()
    destination.write_bytes(b"existing")

    class Partial:
        def __enter__(self):
            self.source = core.open_n4a_file(parent)
            return self

        def __exit__(self, *exc):
            self.source.close()

        def view(self):
            return self.source.view()

        def copy_archive_to(self, stream):
            stream.write(b"unverified")
            raise ValueError("synthetic copy failure")

    monkeypatch.setattr(module, "_core", lambda: SimpleNamespace(open_n4a_file=lambda *a, **k: Partial()))
    with pytest.raises(ValueError, match="copy failure"):
        copy_download(parent, destination, result.container_sha256, current=result)
    assert destination.read_bytes() == b"existing"
    assert list(tmp_path.glob(".n4a-copy-*")) == []


def test_changed_download_cannot_replace_snapshot(tmp_path, native_files):
    parent = native_files[0]
    result = read_bundle(parent)
    parent.write_bytes(b"changed after inspection")
    destination = tmp_path / "unchanged.n4a"
    destination.write_bytes(b"old output")
    with pytest.raises(ValueError):
        copy_download(parent, destination, result.container_sha256, current=result)
    assert destination.read_bytes() == b"old output"


def test_missing_optional_core_is_a_dependency_error(tmp_path, monkeypatch):
    from nirs4all_papers import bundle as module

    path = tmp_path / "opaque.n4a"
    path.write_bytes(b"historical")
    def unavailable(name):
        raise ImportError("not installed")
    monkeypatch.setattr(module.importlib, "import_module", unavailable)
    with pytest.raises(ReaderDependencyError):
        read_bundle(path)


def test_missing_sdk_retains_verified_inventory_as_dependency_status(sdk_paper, monkeypatch):
    from nirs4all_papers import bundle as module

    original = module.importlib.import_module
    def missing_sdk(name):
        if name == "nirs4all" or name.startswith("nirs4all."):
            raise ImportError("SDK deliberately absent")
        return original(name)
    monkeypatch.setattr(module.importlib, "import_module", missing_sdk)
    result = read_bundle(sdk_paper / "model.n4a")
    assert result.support == "dependency_unavailable"
    assert result.profile == "nirs4all.python-host"
    assert result.manifest_bytes and result.files and result.container_sha256
    assert result.documents == []
    assert "SDK" in result.detail


def test_sdk_signature_check_does_not_mask_nested_owner_typeerror(sdk_paper, monkeypatch):
    import nirs4all as sdk

    failure = TypeError("unexpected keyword argument from a nested owner callback")
    def owner_failure(path, *, source=None, include_host_json=False):
        raise failure
    monkeypatch.setattr(sdk, "inspect_n4a", owner_failure)
    with pytest.raises(TypeError) as raised:
        read_bundle(sdk_paper / "model.n4a")
    assert raised.value is failure


def test_missing_sdk_public_keywords_is_dependency_error(sdk_paper, monkeypatch):
    import nirs4all as sdk

    def older_inspect(path):
        pytest.fail("incompatible public signature was called")
    monkeypatch.setattr(sdk, "inspect_n4a", older_inspect)
    with pytest.raises(ReaderDependencyError, match="safe-inspection/borrowed-source API"):
        read_bundle(sdk_paper / "model.n4a")
