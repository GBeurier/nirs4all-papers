# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "nirs4all_papers"
ALLOWED_EXTERNAL_IMPORTS = {"yaml"}
ALLOWED_PROJECT_DEPENDENCIES = {"PyYAML"}


def test_runtime_imports_stay_stdlib_pyyaml_or_internal() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module, lineno in _absolute_import_roots(tree):
            if module in {"__future__", "nirs4all_papers"}:
                continue
            if module in sys.stdlib_module_names or module in ALLOWED_EXTERNAL_IMPORTS:
                continue
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}:{lineno}: import {module!r}")

    assert violations == []


def test_runtime_dependencies_are_pyyaml_only() -> None:
    dependencies = _project_dependencies()
    normalized = {_dependency_name(dep) for dep in dependencies}
    assert normalized == ALLOWED_PROJECT_DEPENDENCIES


def _absolute_import_roots(tree: ast.AST) -> list[tuple[str, int]]:
    modules: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((alias.name.split(".", 1)[0], node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append((node.module.split(".", 1)[0], node.lineno))
    return modules


def _project_dependencies() -> list[str]:
    pyproject = REPO_ROOT / "pyproject.toml"
    if tomllib is None:
        return _literal_project_dependencies(pyproject.read_text(encoding="utf-8"))
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    return dependencies if isinstance(dependencies, list) else []


def _literal_project_dependencies(text: str) -> list[str]:
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            break
        if in_project and stripped.startswith("dependencies"):
            _, value = stripped.split("=", 1)
            parsed: Any = ast.literal_eval(value.strip())
            return parsed if isinstance(parsed, list) else []
    return []


def _dependency_name(requirement: str) -> str:
    name = requirement.split(";", 1)[0].strip()
    for marker in ("<", ">", "=", "!", "~", "["):
        name = name.split(marker, 1)[0].strip()
    return name
