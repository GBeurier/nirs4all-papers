# Repository Guidelines

## Scope

`nirs4all-papers` is the public repository for deposited papers and reproducible
public code bundles. It is not a drafting area.

Use `nirs4all-drafts` for active manuscripts, private review material, journal
selection, and notes. Move content here only when it is safe to publish.

## Paper Bundle Rules

Each public paper bundle should include:

- a `README.md` with the paper citation, status, and reproduction commands;
- the deposited PDF when redistribution is allowed;
- a `CITATION.cff` or equivalent citation metadata;
- public code and exact dependency locks;
- public data references, not private datasets;
- generated artifacts only when they are needed for permanent public access.

## Safety Checks

Before committing:

- confirm the bundle contains no draft-only, reviewer-only, or private files;
- confirm data redistribution rights;
- record provenance for fixtures, tags, and upstream versions;
- update `nirs4all.org` links after the public artifact is stable.
