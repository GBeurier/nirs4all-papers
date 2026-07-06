# Release checklist — nirs4all-papers

Publishing is via `publish.yml` (release / dispatch, PyPI Trusted Publishing). Branch pushes to `main`
never publish to PyPI, **but do deploy the site to papers.nirs4all.org**.

## Pre-release

- [ ] Green gate + CI green (see `quality_gates.md`); `n4a-papers build` produces the intended site.
- [ ] `CHANGELOG.md` `[Unreleased]` → a dated version; `VERSION` / manifest agree.
- [ ] `version-guard` green; tag `vX.Y.Z` points at the exact release commit.
- [ ] `external/nirs4all-repository` resolves to a published/pinned version (not a floating checkout).

## Release

- [ ] Tag `vX.Y.Z` on the release commit; publish the GitHub Release (triggers `publish.yml`).
- [ ] Confirm the run is green and (if published) the version is on PyPI.

## Post-release

- [ ] `pip install nirs4all-papers==X.Y.Z` in a clean venv; smoke `n4a-papers --help`.
- [ ] Verify papers.nirs4all.org reflects the intended deposited set.

## Notes

- The site publishes to the shared `*.nirs4all.org` domain on push — review content changes before merging.
- Deposit only artifacts you have the right to publish; respect each paper's/dataset's license.
