# Codex Gate 4 — final release-readiness (nirs4all-papers)

Consolidated into the ecosystem-level **Gate 5**; per-repo Codex effort was on **Gate 3** (see `03_main_diff_review.md`).

**Readiness snapshot:** the public deposited-paper archive + site builder (papers.nirs4all.org). Push-hardening
added the full community-health set (CoC/CITATION/SECURITY/CONTRIBUTING/CHANGELOG/.editorconfig/.pre-commit/
dependabot), SHA-pinned all 17 actions, and a `docs/maintenance/` trail. **No product code changed.**

**Documented (not changed):**
- Deposited manuscripts/datasets keep their own publisher/upstream licenses (scoped in CONTRIBUTING/SECURITY).
- `external/nirs4all-repository` is a floating checkout at build time — pin it to a tag/SHA for hermetic builds before release.
- `site.yml` deploys papers.nirs4all.org on push — gate behind tag/dispatch.
