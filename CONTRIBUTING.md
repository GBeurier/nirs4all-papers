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

## Cross-repository version constraints

Versions are `X.Y.Z`. A patch (`Z`) carries fixes and purely additive,
backward-compatible features: existing outputs, wire formats, schemas and ABI
symbols are unchanged. A minor (`Y`) carries any compatibility break: a changed
or removed API signature, an ABI break or ABI version change, a wire, byte,
schema or fixture change, renamed ids or changed numerical results of existing
operations. The package that bumps classifies its change.

Dependencies on packages from other nirs4all repositories accept every patch of
one tested series, `>=X.Y[.Z],<X.(Y+1)`. A patch floor is allowed when a fix or
feature from that patch is required; moving to a new series is an explicit,
tested decision of the consumer. For 1.x packages the upper bound is the next
minor, never `<2` (npm `~1.4.1`, Cargo `">=1.4.1, <1.5"`, Python
`>=1.4.1,<1.5`).

Current declarations: `nirs4all-core>=0.5,<0.6` and `nirs4all>=1.4,<2`; the
SDK upper bound predates this rule and is aligned at the next release. Exact
versions live in lockfiles and the release order; the qualified reader cohort is
recorded with each bundle, not in these ranges. The full policy is `docs/contracts/release/VERSION_CONSTRAINTS.md` in
`nirs4all-ecosystem`.
