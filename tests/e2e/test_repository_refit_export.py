# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from nirs4all_papers.provider import export_sidecars, load_paper_bundle

PAPERS_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PAPERS_ROOT.parent
REPOSITORY_ROOT = WORKSPACE_ROOT / "nirs4all-repository"
REPOSITORY_SRC = REPOSITORY_ROOT / "src"
DEMO_PAPER_DIR = PAPERS_ROOT / "papers" / "2026-pls-nirs-demo"


def test_paper_export_reopens_as_repository_refit_handoff(artifacts_dir: Path) -> None:
    pipeline_id = "paper_pls_nirs_refit"

    paper = load_paper_bundle(DEMO_PAPER_DIR)
    export_root = _fresh_dir(artifacts_dir / "paper-export")
    repo_root = _fresh_dir(artifacts_dir / "repository-catalog")

    crate = export_sidecars(DEMO_PAPER_DIR, export_root)
    zip_path = _zip_tree(export_root, artifacts_dir / "paper-export.zip")

    python_reopen = _load_python_reopen_result(artifacts_dir)
    refit_recipe = _refit_recipe_from_python_reopen(python_reopen) if python_reopen else _refit_recipe_from_paper(paper)
    fingerprints = {
        "paper_bundle_sha256": _sha256(crate / paper.bundle_filename),
        "paper_pipeline_sha256": _sha256(crate / "pipeline.json"),
        "paper_export_zip_sha256": _sha256(zip_path),
    }
    if python_reopen is not None:
        fingerprints["python_reopened_result_sha256"] = _sha256(artifacts_dir / "reopened-result.json")
    request = {
        "pipeline_id": pipeline_id,
        "repo_root": str(repo_root),
        "refit_recipe": refit_recipe,
        "paper": {
            "slug": paper.slug,
            "bundle_filename": paper.bundle_filename,
            "created_at": str(paper.bundle.manifest.get("created_at") or "2026-06-14")[:10],
            "authors": [{"name": author.name, "affiliation": author.affiliation} for author in paper.authors],
        },
        "fingerprints": fingerprints,
        "python_reopen": _python_reopen_summary(python_reopen),
    }
    request_path = artifacts_dir / "repository-handoff-request.json"
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    handoff = _run_repository_handoff(request_path)
    refit_evidence = _refit_evidence_from_python_reopen(python_reopen, selected_pipeline_id=pipeline_id)
    evidence_path = artifacts_dir / "repository-best-pipeline.json"
    evidence = {
        "scenario": "e2e-python-reopen-paper-repository-refit",
        "paper_export": {
            "zip": zip_path.name,
            "zip_sha256": _sha256(zip_path),
            "crate_files": sorted(path.name for path in crate.iterdir() if path.is_file()),
            "source_slug": paper.slug,
        },
        "repository_handoff": handoff,
        "python_reopen": _python_reopen_summary(python_reopen),
        "refit": refit_evidence,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assert zip_path.is_file()
    assert evidence_path.is_file()
    assert handoff["pipeline_id"] == pipeline_id
    assert handoff["reopened_recipe"]["pipeline"] == refit_recipe["pipeline"]
    assert handoff["publication_blockers"] == []
    assert not any("FullTrainFoldSplitter" in json.dumps(step) for step in handoff["reopened_recipe"]["pipeline"])
    if python_reopen is not None:
        descriptor_fingerprints = handoff["descriptor"]["provenance"]["fingerprints"]
        assert descriptor_fingerprints["python_reopened_result_sha256"] == _sha256(artifacts_dir / "reopened-result.json")
        assert evidence["refit"]["executed"] is True
        assert evidence["refit"]["status"] == "passed"
        assert evidence["refit"]["force_best_refit"] is True
        assert evidence["refit"]["selected_pipeline_id"] == pipeline_id
        assert evidence["refit"]["model_hash"] == python_reopen["bundle_reopen"]["sha256"]
        assert evidence["refit"]["data_hash"] == python_reopen["dataset"]["config_sha256"]
        assert evidence["refit"]["prediction_count"] == python_reopen["runs"]["dag_ml"]["num_predictions"]


def _run_repository_handoff(request_path: Path) -> dict[str, Any]:
    if not REPOSITORY_SRC.is_dir():
        raise AssertionError(f"nirs4all-repository source tree not found at {REPOSITORY_SRC}")
    python = _repository_python()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPOSITORY_SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [str(python), "-c", _REPOSITORY_HANDOFF_SCRIPT, str(request_path)],
        cwd=REPOSITORY_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "repository handoff subprocess failed "
            f"({python}, exit {completed.returncode})\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


def _repository_python() -> Path:
    candidates = [
        REPOSITORY_ROOT / ".venv" / "bin" / "python",
        Path("/usr/bin/python3.11"),
        Path(shutil.which("python3.11") or ""),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise AssertionError("no Python 3.11 interpreter found for nirs4all-repository provider APIs")


def _refit_recipe_from_paper(paper: Any) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for step_view in paper.steps:
        info = step_view.info
        if info.kind == "split" or not info.reproducible:
            continue
        key = "y_processing" if info.kind == "target" else "class"
        record: dict[str, Any] = {key: info.raw}
        if info.params:
            record["params"] = dict(info.params)
        steps.append(record)
    if not steps:
        raise AssertionError(f"paper {paper.slug} has no reproducible steps for a repository refit recipe")
    return {"name": f"{paper.slug} refit recipe", "pipeline": steps}


def _load_python_reopen_result(artifacts_dir: Path) -> dict[str, Any] | None:
    path = artifacts_dir / "reopened-result.json"
    if not path.exists():
        return None
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "passed":
        raise AssertionError(f"Python reopen result did not pass: {result.get('status')!r}")
    parity = result.get("parity")
    if not isinstance(parity, dict):
        raise AssertionError("Python reopen result is missing parity evidence")
    tolerance = float(parity.get("tolerance", 0.0))
    for key in ("best_prediction_abs_max", "final_prediction_abs_max", "bundle_reopen_prediction_abs_max"):
        if float(parity.get(key, float("inf"))) > tolerance:
            raise AssertionError(f"Python reopen parity {key} exceeds tolerance: {parity.get(key)!r} > {tolerance!r}")
    _refit_recipe_from_python_reopen(result)
    return result


def _refit_recipe_from_python_reopen(result: dict[str, Any]) -> dict[str, Any]:
    recipe = result.get("repository_refit_recipe")
    if not isinstance(recipe, dict):
        raise AssertionError("Python reopen result is missing repository_refit_recipe")
    pipeline = recipe.get("pipeline")
    if not isinstance(pipeline, list) or not pipeline:
        raise AssertionError("Python reopen repository_refit_recipe.pipeline must be a non-empty list")
    return recipe


def _python_reopen_summary(result: dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {"consumed": False}
    parity = result["parity"]
    return {
        "consumed": True,
        "schema_version": result.get("schema_version"),
        "git_head": result.get("git_head"),
        "bundle_sha256": result.get("bundle_reopen", {}).get("sha256"),
        "best_prediction_abs_max": parity.get("best_prediction_abs_max"),
        "final_prediction_abs_max": parity.get("final_prediction_abs_max"),
        "bundle_reopen_prediction_abs_max": parity.get("bundle_reopen_prediction_abs_max"),
        "tolerance": parity.get("tolerance"),
    }


def _refit_evidence_from_python_reopen(result: dict[str, Any] | None, *, selected_pipeline_id: str) -> dict[str, Any]:
    handoff_call = "nirs4all.run(pipe.to_nirs4all(), dataset, engine='dag-ml', refit=True)"
    if result is None:
        return {
            "mode": "paper_export_only",
            "force_best_refit": True,
            "selected_pipeline_id": selected_pipeline_id,
            "handoff_call": handoff_call,
            "recipe_source": "paper-demo",
            "reason": "Run the paired nirs4all e2e step first to attach runtime refit parity evidence.",
        }

    bundle = result.get("bundle_reopen")
    dataset = result.get("dataset")
    saved_pipeline = result.get("saved_pipeline")
    runs = result.get("runs")
    dagml = runs.get("dag_ml") if isinstance(runs, dict) else None
    if not isinstance(bundle, dict) or not isinstance(dataset, dict) or not isinstance(saved_pipeline, dict) or not isinstance(dagml, dict):
        raise AssertionError("Python reopen ledger is missing bundle/dataset/pipeline/dag-ml refit evidence")

    model_hash = bundle.get("sha256")
    data_hash = dataset.get("config_sha256")
    saved_pipeline_hash = saved_pipeline.get("sha256")
    prediction_count = dagml.get("num_predictions")
    best_rmse = dagml.get("best_rmse")
    if not (model_hash and data_hash and saved_pipeline_hash):
        raise AssertionError("Python reopen ledger is missing one or more required SHA-256 fingerprints")
    if prediction_count is None or best_rmse is None:
        raise AssertionError("Python reopen ledger is missing dag-ml prediction count or best RMSE")

    return {
        "executed": True,
        "status": "passed",
        "force_best_refit": True,
        "selected_pipeline_id": selected_pipeline_id,
        "handoff_call": handoff_call,
        "recipe_source": "python-reopened-result",
        "model_hash": str(model_hash),
        "data_hash": str(data_hash),
        "saved_pipeline_sha256": str(saved_pipeline_hash),
        "prediction_count": int(prediction_count),
        "best_rmse": float(best_rmse),
        "native_results_dir": dagml.get("native_results_dir"),
    }


def _fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _zip_tree(source: Path, target: Path) -> Path:
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(rel)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return target


_REPOSITORY_HANDOFF_SCRIPT = r"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

import nirs4all_repository as n4r
from nirs4all_repository.builder import build_catalog
from nirs4all_repository.recipes import recipe_fingerprints, validate_recipe_structure
from nirs4all_repository.schema import PipelineDescriptor, RecipeFormat
from nirs4all_repository.validate import validate_pipeline


def class_sequence(steps):
    out = []
    for step in steps:
        value = step.get("class") or step.get("y_processing") or step.get("model") or step.get("meta_model")
        if isinstance(value, dict):
            value = value.get("class")
        if value:
            out.append(str(value))
    return out


request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
repo_root = Path(request["repo_root"])
pipeline_id = request["pipeline_id"]
recipe = request["refit_recipe"]

validate_recipe_structure(recipe, RecipeFormat.nirs4all_pipeline_config)

bundle_dir = repo_root / "pipelines" / pipeline_id
bundle_dir.mkdir(parents=True)
(repo_root / "catalog").mkdir(exist_ok=True)
(bundle_dir / "pipeline.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(bundle_dir / "card.md").write_text(
    "# Paper PLS NIRS refit handoff\n\n"
    "Temporary e2e descriptor proving that a reproducible paper export can be handed to "
    "nirs4all-repository as a refit recipe without writing back to either public catalogue.\n",
    encoding="utf-8",
)

fingerprints = recipe_fingerprints(recipe, RecipeFormat.nirs4all_pipeline_config)
fingerprints.update(request["fingerprints"])
paper = request["paper"]
descriptor = PipelineDescriptor.model_validate(
    {
        "schema_version": 1,
        "id": pipeline_id,
        "name": "Paper PLS NIRS refit handoff",
        "summary": "Refit handoff smoke derived from a reproducible paper export.",
        "description": "A temporary descriptor for the ecosystem e2e smoke; not a published catalogue entry.",
        "framework": "nirs4all",
        "kind": "recipe",
        "task": "regression",
        "tags": ["paper", "refit", "pls"],
        "version": "0.0.0+paper-smoke",
        "license": "CeCILL-2.1 OR AGPL-3.0-or-later",
        "created_at": paper["created_at"],
        "authors": paper["authors"],
        "recipe": {"format": "nirs4all/pipeline-config", "path": "pipeline.json"},
        "provenance": {
            "generated_by": "nirs4all-papers e2e repository refit handoff smoke",
            "fingerprints": fingerprints,
            "source": f"nirs4all-papers:{paper['slug']}",
            "notes": "Papers exports archive sidecars; repository owns this descriptor/refit recipe handoff.",
        },
        "governance": {"status": "draft", "visibility": "public", "trust": "experimental"},
    }
)
(bundle_dir / "descriptor.yaml").write_text(
    yaml.safe_dump(descriptor.model_dump(mode="json", exclude_none=True), sort_keys=False),
    encoding="utf-8",
)

build_catalog(repo_root, base_url="https://example.invalid/nirs4all-repository")
report = validate_pipeline(repo_root, pipeline_id)
if not report.ok:
    raise SystemExit(json.dumps({"errors": report.errors, "security_findings": report.security_findings}, indent=2))

pipe = n4r.get_pipeline(pipeline_id, root=repo_root)
reopened = pipe.to_nirs4all()
entries = n4r.get_pipeline_list(root=repo_root, framework="nirs4all", kind="recipe", tag="refit")
if not entries or entries[0]["id"] != pipeline_id:
    raise SystemExit("repository provider list did not return the refit descriptor")

print(
    json.dumps(
        {
            "descriptor": pipe.descriptor.model_dump(mode="json", exclude_none=True),
            "catalog_index": "repository-catalog/catalog/index.json",
            "pipeline_id": pipe.id,
            "publication_blockers": pipe.descriptor.publication_blockers(),
            "recipe_class_sequence": class_sequence(reopened["pipeline"]),
            "recipe_step_count": len(reopened["pipeline"]),
            "reopened_recipe": reopened,
        },
        sort_keys=True,
    )
)
"""
