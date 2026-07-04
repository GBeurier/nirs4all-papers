# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--artifacts-dir",
        action="store",
        default=None,
        help="Directory where e2e evidence artifacts are written.",
    )


@pytest.fixture
def artifacts_dir(pytestconfig: pytest.Config, tmp_path: Path) -> Path:
    raw = pytestconfig.getoption("--artifacts-dir")
    path = Path(raw) if raw else tmp_path / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path
