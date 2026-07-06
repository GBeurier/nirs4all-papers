# Final hardening report — nirs4all-papers

**Date:** 2026-07-06 · **Branch:** `main` · **Operator:** Claude (Opus 4.8) · **Reviewer:** Codex CLI 0.142.5

## Summary
Pragmatic hardening of the public deposited-paper archive: added the **full** community-health set and
SHA-pinned all workflow actions. **No product code changed.** (Audit-only in the earlier sprint because it was
diverged; since reconciled to `origin/main`, so now hardened + pushed.)

## Baseline / commit
- **Baseline HEAD:** `878e597` (origin/main, CI-green, in-sync).
- **Commit:** *(this commit)* — community-health + 17 SHA-pins + docs/maintenance.

## Files
Added: `CODE_OF_CONDUCT.md`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.editorconfig`,
`.pre-commit-config.yaml`, `.github/dependabot.yml` (github-actions + pip),
`docs/maintenance/{repository_audit,quality_gates,release_checklist,final_report}.md` + `codex_reviews/{03,04}`.
Modified: `.github/workflows/{ci,content-check,publish,site,version-guard}.yml` (17 SHA-pins).

## Checks
- YAML/CFF validated. Non-code change; ruff+mypy+pytest+`n4a-papers build` run in CI. Baseline branch-push CI green at `878e597`.
- **Codex Gate 3** — pins valid; fixed contributor-license scoping (deposited artifacts keep own terms), the
  `external/nirs4all-repository` clone step, and the stale audit mode line. **Gate 4** — consolidated into ecosystem Gate 5.

## GitHub Actions (this push)
Branch-push gating runs (no PyPI publish): `CI`, `Content Check`, `Site (GitHub Pages)` (papers.nirs4all.org),
`version-guard`. Verified green post-push.

## Residual risks
- Deposited manuscripts/datasets keep their own licenses (not CeCILL/AGPL).
- `external/nirs4all-repository` is a floating build-time checkout — pin before release. Pages-on-push. No coverage floor.

## 12-month maintenance
- Merge weekly Dependabot PRs after CI-green. Date `CHANGELOG.md` `[Unreleased]` at each tag.
- Before release: pin the external provider checkout; verify Trusted Publisher; tag the exact release commit.
