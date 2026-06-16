# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role

`nirs4all-papers` is the **public, permanent archive** of the nirs4all ecosystem:
deposited paper PDFs, per-paper reproducibility kits, public data references, frozen
code used for a paper result, and the stable WASM/static companions linked from
`nirs4all.org`. See the ecosystem map in the parent [`../CLAUDE.md`](../CLAUDE.md).

This is an **archive, not a development tree** — there is no application code, package,
or test suite to build. Everything here is published material plus the metadata and CI
that keep it safe to publish. Reproducible *code* lives inside each `papers/<slug>/code/`
bundle and pins its own dependencies; this repo does not.

## Do not add

- in-progress manuscript drafts;
- reviewer-private material;
- journal scouting notes;
- private or license-restricted datasets;
- lab notebooks not sanitized for public release;
- generated caches, build output, or anything that cannot be redistributed.

Those belong in the private `nirs4all-drafts` (manuscripts/review) or `nirs4all-lab`
(experiments). Content arrives here **only after** the draft and lab work are released.

## Layout

```text
papers/<YYYY-short-title>/   one directory per deposited paper (slug = YYYY-short-title)
templates/reproducibility-kit/README.md   copy this into papers/<slug>/README.md
LICENSES/                    license-family texts (AGPL, CeCILL, commercial)
assets/brand/                shared nirs4all brand kit (logos, icons, OG image)
VERSION                      single-line repo version, gated against git tags (see below)
```

A complete paper bundle (`papers/<slug>/`) contains: `README.md` (built from the
reproducibility-kit template — citation, provenance, reproduction commands), `paper.pdf`,
`CITATION.cff`, `code/` (with exact dependency locks), `data/` (public references only),
and `wasm/` when an interactive companion exists.

## Reproduction-document publisher (`src/nirs4all_papers/`)

The tool the repo was planned around: `n4a-papers` turns a deposited `.n4a` + a hand-written
`paper.yaml` into a self-contained reproduction page — methods + bibliography, protocol/scores, a
**live in-browser pipeline replay**, and deposit sidecars (CITATION.cff, BibTeX, RO-Crate). Design:
[`docs/REPRODUCTION_PUBLISHER.md`](docs/REPRODUCTION_PUBLISHER.md).

```bash
pip install -e ".[dev]"                # runtime dep: PyYAML only; dev adds pytest/ruff/mypy
n4a-papers build --out site            # papers/*/ → ./site
ruff check src tests && mypy src/nirs4all_papers && pytest -q   # the package green gate
```

Architecture mirrors the `nirs4all-datasets` site generator (pure-Python f-string templating, inline
SVG, self-contained output): `bundle.py` reads the `.n4a` with the **stdlib only** (no nirs4all
import); `bibliography.py` resolves operators to a curated seed (`data/bibliography.json`, distilled
from `nirs4all-methods`); `provenance.py` emits CITATION.cff + RO-Crate + BibTeX; `site/` renders the
pages; the replay engine (`site/assets.py`, inline JS) is a pure-JS NIPALS PLS + preprocessing +
k-fold-OOF engine that runs anywhere (incl. `file://`) — honestly labelled an *approximate* reference
engine (the **libn4m WASM** engine in `nirs4all-web` is the production swap seam). Design tokens are
lifted from the family so the site matches `datasets.nirs4all.org`. Tests live in `tests/`; CI is
`.github/workflows/ci.yml` (lint + types + tests + build + sidecar validation). Deploys to
**papers.nirs4all.org** via `.github/workflows/site.yml`. `site/` is a build artifact (git-ignored),
regenerated wholesale — never hand-edit it; the publisher writes a `.n4a-papers-build` marker and
refuses to wipe any output dir lacking it.

## Gates (run before every commit — this repo's "green gate")

Two GitHub Actions enforce the invariants; reproduce them locally before pushing:

- **Content check** (`.github/workflows/content-check.yml`) — `README.md`,
  `papers/README.md`, and `templates/reproducibility-kit/README.md` must all exist.
- **Version guard** (`.github/workflows/version-guard.yml`) — `VERSION` must **never be
  ahead** of the latest `v*` git tag. A tag ahead of `VERSION` (release in flight) is fine;
  a bumped `VERSION` merged to `main` without its tag is rejected. **A version bump ships
  as a tag/release (`git tag vX.Y.Z`), never as a lone commit to `main`.** This is the
  ecosystem-wide version-sync guardrail.

## Licensing (load-bearing — get this right)

The repo is dual open-source `CeCILL-2.1 OR AGPL-3.0-or-later`, plus an optional commercial
license (`nirs4all-admin@cirad.fr`). The dual license covers project-authored code **and
content** alike. Two carve-outs keep their own terms and must be respected when adding files:

- **Deposited manuscripts** (paper PDFs) stay under the **publisher's copyright** —
  redistribute only as the publisher's terms allow.
- **Datasets / third-party assets** keep their **upstream license or DOI terms**.

Source files use SPDX header `# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later`.
See [`LICENSING.md`](LICENSING.md) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Adding a released paper

1. Confirm publish-safety: no draft-only / reviewer-only / private files; data
   redistribution rights verified; manuscript publisher terms allow deposit.
2. `cp templates/reproducibility-kit/README.md papers/<slug>/README.md` and fill in the
   **Provenance** block — record the source `nirs4all-drafts` / `nirs4all-lab` commit or
   tag, the nirs4all package versions, and dataset DOIs/checksums.
3. Tag the reproducibility bundle.
4. Update `nirs4all.org` with the permanent public link once the artifact is stable.
