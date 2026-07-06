# Contributing to nirs4all-papers

`nirs4all-papers` is the **public deposited paper archive**: accepted PDFs, public reproducibility code
(RO-Crate), and stable WASM/static companions built into the site at papers.nirs4all.org. Active drafting
lives in `nirs4all-drafts` — this repo is for **deposited / public** artifacts only.

## Green gate (matches CI)

```bash
python -m pip install -e ".[dev]" pytest-cov
git clone https://github.com/GBeurier/nirs4all-repository external/nirs4all-repository   # provider handoff (CI checks this out separately)
python -m pip install -e external/nirs4all-repository
ruff check src tests
mypy src/nirs4all_papers
pytest -q --cov=nirs4all_papers
n4a-papers build . --out site                           # build the site locally
```

Optional local hooks: `uvx pre-commit run --all-files`.

- Add a deposited paper with its metadata + reproducibility kit; keep companions self-contained and licensed.
- Do not commit large binaries beyond what the archive requires; prefer stable, citable artifacts.

By contributing **project-authored code/content** you agree to the `CeCILL-2.1 OR AGPL-3.0-or-later`
license and `CODE_OF_CONDUCT.md`. **Deposited artifacts keep their own terms** — published/accepted
manuscript PDFs remain under the publisher's copyright, and datasets/third-party assets are governed by
their own license/DOI terms; only deposit what you can redistribute under those terms.
