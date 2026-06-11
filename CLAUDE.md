# CLAUDE.md

This file provides guidance to Claude Code when working in `nirs4all-papers`.

## Role

This repository is public. It stores deposited nirs4all papers and reproducible
public code bundles after the corresponding private draft and lab work are ready
for release.

## Do not add

- in-progress manuscript drafts;
- reviewer-private material;
- journal scouting notes;
- private or license-restricted datasets;
- lab notebooks that have not been sanitized for public release.

Those belong in `nirs4all-drafts` or `nirs4all-lab`.

## Expected bundle

A paper directory should include a README, citation metadata, reproduction
commands, public code, public data references, and any stable WASM/static build
that `nirs4all.org` links to.

## Cross-project updates

When adding a released paper:

1. record the source draft/lab commit or tag;
2. tag the reproducibility bundle;
3. update `nirs4all.org` with the permanent link;
4. note any upstream package versions needed by the bundle.
