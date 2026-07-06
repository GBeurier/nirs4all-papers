# Codex Gate 3 — main diff review (nirs4all-papers)

**Reviewer:** Codex CLI 0.142.5 — `codex exec review --uncommitted`, 2026-07-06 (background).

## Verdict
> "The workflow pinning itself looks structurally fine" — 3 findings in the added docs, all fixed.

| # | sev | finding | disposition |
|---|---|---|---|
| P2 | important | CONTRIBUTING's blanket "you agree to CeCILL/AGPL" conflicts with the repo's policy that **deposited manuscripts/datasets keep their own publisher/upstream terms** — contributors can't relicense those. | **Fixed** — scoped to *project-authored* code/content; deposited artifacts keep their own terms. |
| P2 | important | Green gate's `pip install -e external/nirs4all-repository` fails on a fresh clone (CI checks that path out separately). | **Fixed** — added the `git clone … external/nirs4all-repository` step before the install (CONTRIBUTING + quality_gates). |
| P3 | minor | `repository_audit.md` said "AUDIT-ONLY (diverged; will NOT be pushed)" while being committed to the public repo. | **Fixed** — mode updated to "IN SCOPE — reconciled + hardened + pushed"; header already marked point-in-time. |

## Verified
- 17 action pins across 5 workflows; 0 floating tags remain. `publish.yml` is release/dispatch-gated
  (no PyPI publish on branch push); `site.yml` deploys papers.nirs4all.org on push. Gate 4 → ecosystem Gate 5.
