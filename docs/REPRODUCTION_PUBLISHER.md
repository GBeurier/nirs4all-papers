<!-- SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later -->
# Reproduction Document Publisher — product design (alpha)

> The planned feature named in `CLAUDE.md`: *"automatic per-experiment reproduction-document
> publisher — a methods + bibliography report plus a WASM page that re-runs the pipeline."*
> This document is the design; `src/nirs4all_papers/` is the alpha implementation.

## 1. What it is

A small, dependency-light Python tool (`n4a-papers`) that turns a **finished nirs4all
experiment** — a deposited `.n4a` bundle plus a hand-written `paper.yaml` — into a
**self-contained, publication-grade reproduction document**: one static HTML page per paper that
combines

1. an **auto-generated methods & bibliography report** (the exact pipeline, its protocol and
   scores, a per-step methods narrative, and a citation list cross-referenced to every operator),
   and
2. a **live, in-browser pipeline replay** ("re-run this pipeline") that re-executes the published
   pipeline on an included dataset and recomputes the parity/residual plots and scores — *in the
   same page as the report*,

together with the **machine-readable sidecars** a journal or a reviewer expects
(`CITATION.cff`, `references.bib`, an RO-Crate `ro-crate-metadata.json`, the copied `pipeline.json`
and the `.n4a` itself).

It is a sibling static site to `nirs4all.org` / `datasets.nirs4all.org` / `formats.nirs4all.org`,
intended for **papers.nirs4all.org**, and it deliberately reuses the family's exact visual design.

## 2. Why (use cases)

- **Author** — "I have an accepted paper and the `.n4a` that produced its model. Generate the
  reproduction page, the bibliography, and the citation files for deposit."
- **Reviewer / reader** — "Show me precisely which preprocessing + model + protocol produced this
  number, with the literature for each method, and let me re-run it without installing anything."
- **Ecosystem** — a permanent, browsable, DOI-linked archive of reproducible nirs4all results that
  `nirs4all.org` links to; every page is also a self-contained RO-Crate.

## 3. Boundaries (what it does *not* do)

Per the ecosystem rule *"the lower layer is the single source of truth for its domain"*:

- It **reads** `.n4a` bundles (stdlib `zipfile`+`json`); it does **not** re-implement nirs4all,
  re-parse vendor files, or re-fit models server-side. Pipeline/scores/protocol semantics come from
  the bundle + `paper.yaml`.
- Method citations are a **curated seed** (`data/bibliography.json`) distilled from
  `nirs4all-methods/docs/_extras/methods_bibliography.py` (+ `OPERATOR_BIB`) — not scraped at build
  time. New methods get a new seed entry.
- The replay is a **pure-JS reference engine** (NIPALS PLS + SNV/SavGol/scalers + Kennard–Stone)
  that re-runs the *pipeline definition* and runs anywhere (incl. `file://`). The production target
  is the **libn4m WebAssembly** engine already shipped in `nirs4all-web` (`runPortablePipeline`);
  the page documents and is structured for that upgrade. The alpha never overclaims "WASM".

## 4. Inputs → outputs

```
papers/<slug>/
  paper.yaml        # human metadata the bundle can't carry (title, authors, DOI, scores, protocol…)
  model.n4a         # the deposited bundle: pipeline.json + manifest.json + fold_weights + artifacts
  replay.json       # optional: a small (X, y, axis) dataset to re-run the pipeline live in-browser
        │
        ▼  n4a-papers build .  --out site/
site/
  index.html                         # landing (hero + KPIs + how-it-works)
  catalog.html                       # filter/search/sort over all papers
  paper/<slug>.html                  # THE reproduction document + live replay (one page)
  paper/<slug>/CITATION.cff          # ─┐
  paper/<slug>/references.bib        #  │ machine-readable sidecars,
  paper/<slug>/ro-crate-metadata.json#  │ ready for deposit
  paper/<slug>/pipeline.json         #  │
  paper/<slug>/model.n4a             # ─┘ (the bundle, for download/replay)
  brand/                             # favicon, icon, og (copied)
```

## 5. The per-paper page (sections)

1. **Hero** — title, authors, status/venue/year/DOI badges, abstract, nirs4all version.
2. **KPI strip** — headline metrics (RMSE, R², components, #steps, dataset size).
3. **Pipeline** — the ordered steps as typed cards (preprocessing / target-transform / split /
   model) with params and a citation superscript, plus an inline-SVG flow diagram.
4. **Protocol** — split, CV folds, fold strategy + weights, scoring metric.
5. **Results** — metrics table + parity (predicted vs measured) + residuals plots.
6. **Live replay** — re-runs the published pipeline on the included dataset *in the browser*,
   recomputing parity/residuals and RMSE/R²; honest about being a pure-JS reference engine.
7. **Methods narrative** — auto-generated prose, one paragraph per step, each cited.
8. **Bibliography** — numbered reference list with DOIs/links, only the methods actually used.
9. **Provenance & reproduction** — `pipeline_uid`, per-file SHA-256 fingerprints, bundle inventory,
   reproduction commands, and the sidecar downloads.
10. **Citation** — rendered `CITATION.cff` + BibTeX.

## 6. Architecture (mirrors the `nirs4all-datasets` site generator)

Pure-Python f-string templating, one giant inline `<style>`, inline-SVG charts, self-contained
output that works from `file://` — the same shape as `nirs4all_datasets.site`, so the pages
"claque" identically.

```
src/nirs4all_papers/
  bundle.py        read .n4a (stdlib), per-file checksums, parse + type pipeline steps
  bibliography.py  curated seed → normalize method ids → resolve references → BibTeX
  provenance.py    CITATION.cff, RO-Crate 1.1 (+author/license/citation), reproduction commands
  model.py         PaperView / StepView / ReferenceView; load_paper, load_catalog
  data/bibliography.json   the curated citation seed
  site/{theme,components,charts,pages,escape,assets}.py   the renderer (design lifted from the family)
  cli.py           n4a-papers build / new
```

## 7. Alpha status

Implemented: bundle ingest + fingerprints (with `repr()`-address sanitisation), method→citation
resolution (de-duplicated by citation content), all page types, the live JS replay, and all four
machine-readable sidecars, with one worked demo paper. Publication-readiness layer: Google-Scholar
`citation_*` meta + a schema.org `ScholarlyArticle` JSON-LD per page, canonical/OG/Twitter tags,
`sitemap.xml` + `robots.txt`, a CFF with DOI `identifiers` + dataset citation (no faked version), an
RO-Crate whose `mainEntity` is the real `pipeline.json` with a license URL `@id` + dataset entity,
a per-method **principle** line, an explicit three-layer **licensing** panel, "cite the paper vs the
bundle" guidance, copy-to-clipboard, an in-page TOC, and a print stylesheet. Quality: a `pytest`
suite (`tests/`) + a `ci.yml` that lints, type-checks, tests, builds, and validates the emitted
sidecars; the replay JS is regression-tested against the sklearn reference under Node.

Documented as the production path but **not** in the alpha: the **libn4m WASM** replay engine (the
JS engine is an honest, approximate reference — `replay_panel` is the swap seam) and the optional
ingest of a real `dag-ml` research-provenance package (PROV/RO-Crate) when a run carries one (the
`bundle.has_trace` / `has_chain` flags are the hook).
