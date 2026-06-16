<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/horizontal-dark.svg">
    <img alt="nirs4all-papers" src="assets/brand/horizontal.svg" width="440">
  </picture>
</p>

# nirs4all-papers

Public archive for deposited nirs4all papers and reproducible public code
bundles.

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

## License

Reproducibility **code** in this repository is dual-licensed open-source —
**`CeCILL-2.1 OR AGPL-3.0-or-later`** — with an optional **commercial license** (for any commercial use,
contact <nirs4all-admin@cirad.fr>). Repository **content** (notes, figures) is **CC-BY-4.0**; deposited
**manuscripts** carry their publisher's terms where applicable. See [`LICENSING.md`](LICENSING.md) and
[`LICENSES/`](LICENSES/).
