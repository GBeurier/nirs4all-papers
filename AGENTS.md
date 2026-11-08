# Papers contributor instructions

## Archive and publisher

Papers archives public PDFs/kits/frozen code/static-WASM companions and has a publisher package/tests. Frozen kits pin dependencies; they are not production numerics.
No drafts, reviewer-private material, journal notes, unsanitized notebooks, private/restricted data, caches or nonredistributable output. Private manuscript/lab references grant no access; deposit only released public-safe material.
Keep YYYY-short-title slugs, citation/status/reproduction commands, permitted PDF/CITATION, exact locks, public data refs and necessary permanent artifacts. Follow [kit template](templates/reproducibility-kit/README.md)/[layout](papers/README.md#a-paper-bundle); verify redistribution/publisher rights and fixture/tag/upstream provenance.
The [publisher](docs/REPRODUCTION_PUBLISHER.md#3-boundaries-what-it-does-not-do) keeps stdlib reads/curated citations, no server refit/vendor parser. The [facade](README.md#providerplugin-facade) is archive-local/read-side, explicit local outputs only, no upload/other-store writes.
Keep approximate JS replay distinct from the production WASM seam; no inferred parity/implementation. Never hand-edit `site/`; retain `.n4a-papers-build` and refusal to wipe unmarked output.

## Commands and release conditions

From this checkout/package environment retain the original narrower publisher commands; they are not the CI-equivalent provider/coverage gate:

```bash
pip install -e ".[dev]"  # runtime PyYAML; dev pytest/ruff/mypy
n4a-papers build --out site
ruff check src tests && mypy src/nirs4all_papers && pytest -q
```

The [full gate](docs/maintenance/quality_gates.md#local-green-gate-matches-ci) needs pytest-cov, the external/nirs4all-repository clone/install and XML coverage; the clone is a network/Git step requiring separate authority. [CONTRIBUTING](CONTRIBUTING.md#green-gate-matches-ci) retains its non-XML coverage form and optional hooks. Keep both conditions.
Before authorized commits README.md, papers/README.md and templates/reproducibility-kit/README.md must exist. VERSION cannot lead latest v* tag; release-in-flight tags may lead VERSION. Bumps ship as tag/release (`git tag vX.Y.Z`), not lone main commits.
For authorized deposits, `cp templates/reproducibility-kit/README.md papers/<slug>/README.md`; fill source commit/tag, package versions and dataset DOIs/checksums, tag the bundle, then arrange the stable public link. site.yml, tags and the nirs4all.org link duty grant no publication/deployment or Org edit.

## Licensing and security

Project-authored code AND content use `CeCILL-2.1 OR AGPL-3.0-or-later` plus optional commercial terms/contact. Preserve SPDX; manuscript copyright/redistribution and dataset/asset licence/DOI terms remain upstream. Follow [LICENSING](LICENSING.md#4-deposited-manuscripts-and-datasets), [notices](THIRD_PARTY_NOTICES.md) and [SECURITY](SECURITY.md), including safe content failures and private reporting; no secrets/user data.

## Working rules

Read applicable instructions first and preserve dirty work. If `../AGENTS.md` exists, read it within the current user scope; this file also works alone.
Use CodeGraph FIRST only with this checkout's own `.codegraph/` (exact projectPath or local CLI); never auto-index or use an ancestor index. Source, tests and builds are final authority.
Record actual commands, exits and skips. Keep secrets, private data and build output out of Git. Examples grant no install, network, science, publication, hosting, frontend or Git authority.
All project content, including UI text, docs, tests, reports, PRs and commits, is English; conversation may be French. Preserve names, identifiers, quotations and provenance.
