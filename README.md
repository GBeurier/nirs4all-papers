<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/horizontal-dark.svg">
    <img alt="nirs4all-papers" src="assets/brand/horizontal.svg" width="440">
  </picture>
</p>

# nirs4all-papers

Public archive for deposited nirs4all papers and reproducible public code
bundles.

Part of the [open-source NIRS tools](https://nirs4all.org/open-source-nirs-tools.html)
ecosystem: file readers, datasets, methods, browser modelling, reproducible pipelines,
papers, benchmarks, and release dashboards for near-infrared spectroscopy.

This repository is for material that can be public and permanent:

- accepted/deposited paper PDFs;
- reproducibility kits;
- public data references and download scripts;
- frozen code used for a paper result;
- WASM/static builds linked from `nirs4all.org`;
- DOI, tag, release, and provenance metadata.

Drafts, reviewer-private material, journal scouting, private datasets, and
in-progress manuscripts belong in the private `nirs4all-drafts` repository.

## Lifecycle

1. Work happens privately in `nirs4all-drafts` and experimentally in
   `nirs4all-lab`.
2. Once the draft and lab work are ready for public release, move only the
   deposited PDF and reproducible public code here.
3. Build a stable WASM/static artifact when the paper needs an interactive
   public companion.
4. Link the released paper bundle from `nirs4all.org`.

## Layout

```text
papers/
  README.md
templates/
  reproducibility-kit/
    README.md
```

Each paper should use a stable slug, for example:

```text
papers/2026-aom-transfer/
  README.md
  paper.pdf
  CITATION.cff
  code/
  data/
  wasm/
```

Do not commit generated caches, private review files, unpublished drafts, or
data that cannot be redistributed.

## Reproduction-document publisher

`n4a-papers` publishes public archive metadata and byte-identical downloads. Optional current
reading delegates V1 transport/inventory and native Package2/3 admission to Core; SDK-host serialized
JSON inspection belongs to the SDK. Complete owner documents are published as escaped text and exact
bytes, including distinct original training declarations and cosmetic prediction configurations.
No fitted objects are loaded and no metric, pipeline or scientific identity is reconstructed.

The Python 3.10 base requires PyYAML only and can publish historical raw downloads without admitting
them to the current reader. The optional `current-reader` (Core) and `sdk-host-reader` (SDK) extras
require Python 3.11 through their owners. Candidate floors Core >=0.5.0,<0.6 and SDK >=1.4.16,<2 must
be used with the matching qualified native wheel/SDK source cohort; they are not claims about every
published artifact with those labels.

```bash
n4a-papers build . --out <dedicated-output>                 # archive-only
n4a-papers build . --out <dedicated-output> --read-current  # optional current inspection
n4a-papers check <public-paper-directory> --read-current
```

Missing optional readers and unsupported/corrupt transport have distinct visible statuses and do not
remove catalog entries. Downloads preserve original bytes and URLs. Raw historical copies are not
current admission. Native/SDK documents retain their own identities and complete available score
context; depositor metrics are separately labelled **as published**. Missing training recipes or
scores remain absent. Unknown foreign content stays inventory-only. Readability is not executability.

Historical approximate-JS companions retain their separate labels and frozen bytes. Current read
views do not execute that replay or claim native parity. No source archive or generated `site/` is
rewritten by reading. Builds retain the output marker and refuse to wipe unmarked directories.

## Shared UI presentation

Paper pages use the actual UI.2 `StatTile` export for a compact reading/identity summary and
**as published** result cards. A partition filter changes only the displayed cards; it does not
select, rank or recompute scores. Reading and execution remain distinct, with execution explicitly
**Not evaluated**. Original downloads, full owner documents and complete static results remain
accessible without JavaScript. All enhancement assets are local; the existing site chrome is separate.

The Python package ships prebuilt resources under `data/ui/`. The installed builder does not call or
look for Node, and an unstaged source checkout retains static-only publication. Maintainer-only
staging uses `ui/build.mjs`, the exact accepted UI archive and an explicit existing Web dependency
cohort, without an npm install or UI rebuild. See the
[presentation staging instructions](docs/REPRODUCTION_PUBLISHER.md#shared-ui-presentation-staging).

## Provider/plugin facade

`nirs4all_papers.provider` exposes `list_papers`, `load_paper`, `load_paper_bundle`, `inspect_bundle`,
`build_methods_section`, `citation` and `bibtex`, plus explicit local `build_repro_page`/`export_sidecars`.
Catalog/view/build/export calls accept `read_current=False`; `inspect_bundle` always uses the actual
current owner reader. The facade does not execute, upload or write back to other stores.

See [publisher contract](docs/REPRODUCTION_PUBLISHER.md) and the existing contributor/quality-gate
commands. The narrow publisher checks and CI-equivalent provider/coverage gate remain distinct.

## License

This repository — reproducibility **code** and accompanying **content** alike — is dual-licensed
open-source — **`CeCILL-2.1 OR AGPL-3.0-or-later`** — with an optional **commercial license** (for any
commercial use, contact <nirs4all-admin@cirad.fr>), matching the rest of the nirs4all ecosystem.
Deposited **manuscripts** carry their publisher's terms, and datasets / third-party assets keep their
upstream terms. See [`LICENSING.md`](LICENSING.md) and [`LICENSES/`](LICENSES/).
