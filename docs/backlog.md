<!-- SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later -->
# Backlog — reproduction-document publisher

Ideas not in the alpha. Nothing here is committed work; it's a parking lot.

## 1. Push further toward fully-automatic generation

Today the *methods + bibliography report* is fully auto-generated from the `.n4a`
(pipeline, step params, principles, citations, provenance, sidecars, replay). The
**`paper.yaml`** still carries hand-authored fields — some of which actually exist
elsewhere and could be pulled in instead of typed:

- **Scores & protocol** → read from the nirs4all **WorkspaceStore** (SQLite): the
  `predictions` table (`val_score`/`test_score`/`partition`/`metric`) and the
  `chains` table (`cv_val_score`/`final_test_score`). The `.n4a` deliberately does
  not carry these, but the workspace that produced it does. Optional input:
  `paper.yaml: workspace: <path>` → auto-fill the Results + Protocol panels.
- **Dataset card** → resolve from **nirs4all-io** / **nirs4all-datasets** instead of
  the hand-written `dataset:` block: name, DOI, target, n_samples/n_features,
  even a spectra preview, from a dataset id or a `nio.load(...)` source.
- **Replay dataset** → materialize via the optional `nirs4all-io` import (build-time)
  from a folder/glob/config, instead of a hand-made `replay.json`.

Net effect: the only genuinely human input becomes the **identity** that cannot be
auto-derived — authors (+ORCID), venue, **DOI**, and the abstract. Everything about
the science stays auto-generated. Keep all of this *optional* (graceful fallback to
`paper.yaml`) so the publisher never hard-depends on the workspace/io being present.

## 2. Replay engine: libn4m WASM

The in-browser replay is an honest pure-JS NIPALS reference engine. The production
target is the **libn4m WebAssembly** engine already shipped in `nirs4all-web`
(`runPortablePipeline`). `site/assets.py::replay_panel` is the swap seam; the
`--io-wasm` plumbing for "run on your own data" is the same shape.

## 3. Ingest a real dag-ml provenance package

When a run was executed through **dag-ml**, it can emit a W3C PROV / RO-Crate /
OpenLineage package. Detect a bundled `ro-crate-metadata.json` / PROV next to the
`.n4a` and *merge* it into the page's provenance section + the emitted RO-Crate,
rather than always synthesizing. The `bundle.has_trace` / `has_chain` flags are the
hook.

## 4. Smaller items

- Vendor-format "run on your own data" enabled by default (bundle the
  `nirs4all-formats` + `nirs4all-io` WASM, or host it) instead of opt-in `--io-wasm`.
- A `--primary` flag on metrics so the catalog card / KPIs pick the headline score
  deterministically instead of `metrics[0]`.
- DOI enrichment for `data/bibliography.json` (most seed entries lack a DOI; Crossref
  lookup at curation time).
- Per-paper Zenodo deposit hook (mint a DOI for the reproduction bundle itself).
