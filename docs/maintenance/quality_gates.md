# Quality gates — nirs4all-papers

The public deposited-paper archive + site builder (published to papers.nirs4all.org via `n4a-papers build`).

## Local green gate (matches CI)

```bash
python -m pip install -e ".[dev]" pytest-cov
git clone https://github.com/GBeurier/nirs4all-repository external/nirs4all-repository   # provider handoff (CI checks this out separately)
python -m pip install -e external/nirs4all-repository
ruff check src tests
mypy src/nirs4all_papers
pytest -q --cov=nirs4all_papers --cov-report=xml
n4a-papers build . --out site
```

Optional local hooks: `uvx pre-commit run --all-files`.

## CI gates (`.github/workflows/`)

| workflow | trigger | gate |
|---|---|---|
| `ci.yml` | push/PR | ruff + mypy + pytest (coverage) + `n4a-papers build` |
| `content-check.yml` | push/PR | deposited-content validation |
| `site.yml` | push `main` | build + **deploy GitHub Pages → papers.nirs4all.org** |
| `version-guard.yml` | push/PR | manifest not ahead of latest `v*` tag |
| `publish.yml` | **release / dispatch** | PyPI Trusted Publishing — **not** on branch push |

All third-party actions are **SHA-pinned** (17 across 5 workflows), Dependabot-tracked (github-actions + pip).

## Deepest-hardening roadmap

- Gate the Pages deploy behind tag/dispatch so routine `main` commits don't republish the public site.
- Pin the `external/nirs4all-repository` path dependency to a tag/SHA for hermetic builds.
- Coverage floor; wider Python matrix.
