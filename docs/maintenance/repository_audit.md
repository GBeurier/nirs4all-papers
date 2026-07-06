# Repository audit — nirs4all-papers

> **Point-in-time audit — Phase-1 scan, 2026-07-04, PRE-hardening.** This snapshot reflects the repository
> *before* the hardening pass. Items it lists as missing (CODE_OF_CONDUCT / CITATION / SECURITY /
> .editorconfig / .pre-commit / Dependabot) or as floating action tags are **remediated by the same commit
> that adds this file**; the version and CI/packaging surface may have advanced since. The **Deepest
> hardening roadmap** section below is the forward-looking list. Reviewed at Codex Gate 1.

- **Mode:** IN SCOPE — reconciled to origin/main; hardened + pushed (this commit). *(Was audit-only/diverged at the 2026-07-04 scan; the divergence has since been reconciled.)*
- **Baseline HEAD:** `f7ee141 (DIVERGED — audit only)`
- **Role:** Senior release/CI/packaging/security engineer — read-only pre-release hardening audit
- **Stack:** Python >=3.10 (CI on 3.11). setuptools>=64 + wheel build backend. Runtime dep: PyYAML>=5.4 only (stdlib-first design). Dev: pytest>=7, ruff>=0.5, mypy>=1.8, build, pytest-cov. Console script n4a-papers. Pure-Python f-string site generator + inline-JS replay engine; no compiled/Rust/JS-package components.

## Release-readiness verdict
nirs4all-papers is a small, well-tended public archive + a pure-Python (PyYAML-only) reproduction-document publisher; CI is fully green across all five workflows, tests are healthy (~44 across 9 files with lint+type+build+sidecar validation), and PyPI release uses OIDC Trusted Publishing — a solid baseline. The main hardening gaps are governance/security hygiene rather than code: ci.yml and content-check.yml lack least-privilege token permissions, actions float on mutable tags with no Dependabot, and standard community files (SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, root CITATION.cff, dependabot, editorconfig, pre-commit, PR/issue templates) are absent. Packaging duplicates the version across pyproject and VERSION with only VERSION guarded, so the two can drift. Push risk is real but well-fenced: site.yml redeploys the live papers.nirs4all.org on any push to main and version-guard hard-fails if VERSION runs ahead of its tag — and this checkout has diverged (ahead 1/behind 5) and per scope must not be pushed. No secrets were found in tracked source.

## Gate commands (detected)
| key | value |
|---|---|
| `install` | pip install -e ".[dev]" |
| `test` | pytest -q --cov=nirs4all_papers --cov-report=xml |
| `lint` | ruff check src tests |
| `typecheck` | mypy src/nirs4all_papers |
| `format` | — |
| `docs_build` | — |
| `package_build` | python -m build |

## CI
- **Latest status:** All green. Latest 8 runs (Content Check, CI, version-guard, Site) all [ok]. No failing runs to triage.
- **Workflows:**
- ci.yml (push + PR): install .[dev]+pytest-cov, ruff check, mypy, pytest --cov, upload coverage.xml artifact, n4a-papers build, sidecar CFF/RO-Crate validation
- publish.yml (release published + workflow_dispatch dry_run): build sdist+wheel, smoke n4a-papers --version, PyPI Trusted-Publishing OIDC (environment pypi)
- site.yml (push to main + dispatch): build site, write CNAME papers.nirs4all.org, deploy to GitHub Pages
- version-guard.yml (push/PR to main): VERSION must not be ahead of latest v* tag
- content-check.yml (push + PR): assert README.md, papers/README.md, templates/reproducibility-kit/README.md exist
- **Gaps:**
- ci.yml and content-check.yml have NO top-level permissions: block -> workflow token defaults to broad scope (should be contents: read)
- No Dependabot/Renovate: all actions float on major tags (actions/checkout@v4, setup-python@v5, upload-artifact@v4, pypa/gh-action-pypi-publish@release/v1) and are never bump-audited
- Actions pinned to mutable tags, not commit SHAs (supply-chain exposure)
- No coverage threshold / --cov-fail-under; coverage.xml emitted but never gates
- CI runs a single Python 3.11 (no matrix) though requires-python >=3.10
- ci.yml triggers on every push (all branches), not just main/PR — wastes minutes on feature branches

## Standard files
- **Present:** readme, license, gitignore
- **Missing:** changelog, contributing, security, code_of_conduct, citation, editorconfig, precommit, pr_template, issue_template, dependabot

## Packaging
- **name:** `nirs4all-papers` — **version:** `0.2.0`
- **issues:**
- Version is duplicated in two places — pyproject.toml [project].version=0.2.0 AND the VERSION file=0.2.0 — with no single source of truth; version-guard only validates VERSION, so pyproject can drift out of sync silently
- setuptools build backend with static version (no dynamic wiring to VERSION); a bump must be edited in both files
- package-data declares nirs4all_papers = ["data/*.json","data/*.yaml"]; actual data dir holds bibliography.json + paper_template.yaml (covered) — OK, but the glob is the only guard
- Minimal project metadata: no classifiers, no project.license-files entry, no Documentation URL; keywords present but Trove classifiers absent (weakens PyPI discoverability)
- Single hard runtime dep PyYAML>=5.4 with no upper bound (acceptable for a leaf tool, but unpinned)
- src/nirs4all_papers.egg-info/ exists on disk (build residue); gitignored so not tracked — verify it never gets force-added

## Tests
- **framework:** pytest (with pytest-cov)
- **estimate:** ~44 test functions across 9 files (test_model, test_assets, test_bibliography, test_provider_api, test_replay_js, test_provenance, test_build, test_escape, test_bundle) + conftest.py
- **coverage:** Measured in CI (--cov=nirs4all_papers, coverage.xml artifact) but NO threshold enforced and no [tool.coverage] config; no fail-under gate.

## Docs
- **system:** Plain Markdown only: docs/REPRODUCTION_PUBLISHER.md (design) + docs/backlog.md. No Sphinx/MkDocs/RTD config (no mkdocs.yml, docs/conf.py, or .readthedocs.yaml). The `n4a-papers build` step generates the public reproduction SITE (papers.nirs4all.org), which is a product artifact, not API docs.
- **status:** No renderable docs site; README + two design/backlog markdown files are the documentation. Buildable as-is (nothing to compile); adding RTD/MkDocs would be net-new.

## Risks
| severity | area | detail |
|---|---|---|
| high | ci-permissions | .github/workflows/ci.yml and .github/workflows/content-check.yml declare no top-level permissions block, so the GITHUB_TOKEN gets the repo/org default scope (often read-write). publish.yml, site.yml, version-guard.yml correctly set least privilege — the two unhardened ones are the gap. |
| medium | pages-deploy-on-push | site.yml deploys the live public site papers.nirs4all.org (pages: write, id-token: write) on every push to main with no path filter. Any commit to main redeploys the production domain, including rewriting CNAME. |
| medium | supply-chain | All actions float on mutable major tags (checkout@v4, setup-python@v5, upload/download-artifact@v4, configure/deploy-pages, pypa/gh-action-pypi-publish@release/v1) with no Dependabot and no SHA pinning; a compromised tag would run in a workflow that can publish to PyPI via OIDC. |
| medium | version-source-of-truth | pyproject.toml version (0.2.0) and VERSION (0.2.0) are independent; version-guard only checks VERSION. A release that bumps one but not the other ships a mismatched wheel version vs. the guarded manifest. |
| low | coverage | CI emits coverage.xml but enforces no threshold (no --cov-fail-under, no [tool.coverage] config); coverage can silently regress. |
| low | ci-trigger-scope | ci.yml and content-check.yml trigger on unrestricted `push:` (all branches) plus pull_request, doubling runs on PR branches and burning minutes. |
| low | local-divergence | Local main is ahead 1 / behind 5 of origin/main (unpushed `feat(provider): add papers export facade`). Audit-only per instructions; must be reconciled before any push or the local commit will not fast-forward. |

## Security
- **info** — Light secret scan over src/, site/, templates/ found no private keys, AWS secrets, api_key/token assignments — clean.
- **info** — PyPI publishing uses Trusted Publishing (OIDC, environment pypi) with no stored API token — good practice; publish.yml scopes id-token: write only to the publish job.
- **low** — No detect-private-key / secret-scanning pre-commit hook or gitleaks CI step; relies on manual review to keep the public archive clean of accidental secrets.

## Quick wins (pragmatic scope — safe to apply now)
- Add `permissions:\n  contents: read` at the top of .github/workflows/ci.yml and .github/workflows/content-check.yml (the only two workflows missing least-privilege; the other three already scope it).
- Add SECURITY.md pointing to nirs4all-admin@cirad.fr (matches ecosystem policy) — the public archive has no disclosure policy.
- Add .github/dependabot.yml for the github-actions ecosystem (weekly) so the floating action tags get audited bumps.
- Add .editorconfig and a .pre-commit-config.yaml (ruff, ruff-format, mypy, detect-private-key, check-yaml) — mirrors the ecosystem convention and the existing lint/type gate.
- Scaffold CHANGELOG.md (Keep-a-Changelog) seeded from the existing tags (v0.2.0 publisher MVP, etc.).
- Add a root CITATION.cff for the tool itself (the publisher emits per-paper CFFs but the repo has none).
- Add .github/PULL_REQUEST_TEMPLATE.md and a paper-deposit ISSUE_TEMPLATE.
- Add `--cov-fail-under=80` to the CI pytest invocation (or a [tool.coverage.report] fail_under) to lock in current coverage — coverage.xml is already produced.
- Narrow ci.yml/content-check.yml `push:` triggers to `branches: [main]` (plus existing pull_request) to stop redundant feature-branch runs.
- Add `ruff format --check src tests` as a CI step (formatter is available via the ruff dev dep but never invoked).

## Deepest hardening roadmap (fullest realistic hardening)
- Add least-privilege permissions: {contents: read} at top of ci.yml and content-check.yml; keep the scoped id-token/pages blocks already present in site.yml and publish.yml
- Pin every GitHub Action to a full commit SHA (with a version comment) and add .github/dependabot.yml with the github-actions ecosystem (weekly) + pip ecosystem for the dev extras
- Add SECURITY.md (contact nirs4all-admin@cirad.fr per ecosystem policy), CONTRIBUTING.md, CODE_OF_CONDUCT.md, .github/PULL_REQUEST_TEMPLATE.md, and .github/ISSUE_TEMPLATE/ (bug + paper-deposit request)
- Add a root CITATION.cff for the tool/repo (distinct from the per-paper CITATION.cff the publisher emits) so the archive itself is citable
- Add CHANGELOG.md (Keep-a-Changelog) and wire release notes; the repo already does tagged releases (v0.2.0) so a changelog closes the loop
- Introduce a coverage floor: --cov-fail-under (e.g. 80) in CI, and a [tool.coverage.run] source=nirs4all_papers section in pyproject; 44 tests across 9 files is a solid base to lock in
- Expand CI to a Python matrix (3.10/3.11/3.12/3.13) matching requires-python>=3.10; the pure-stdlib+PyYAML footprint makes this cheap
- Add .pre-commit-config.yaml (ruff, ruff-format, mypy, end-of-file-fixer, check-yaml, detect-private-key) and a .editorconfig; document `pre-commit run --all-files` in the green gate
- Adopt `ruff format --check` as an explicit format gate in CI (currently only ruff lint runs; formatter is unused)
- Single-source the version: VERSION file and pyproject [project].version both say 0.2.0 — derive one from the other (e.g. dynamic version from VERSION, or have version-guard also check pyproject) so a bump can't half-land
- Scope ci.yml push trigger to branches:[main] + PR to stop running full lint/type/test on every feature-branch push
- Harden the Pages deploy: gate site.yml on paths (papers/**, src/**, assets/**) so unrelated commits to main don't redeploy the live domain; consider a build-artifact preview on PRs
- Publisher docs: the design lives in docs/REPRODUCTION_PUBLISHER.md but there is no rendered docs site — either add an mkdocs/Sphinx build or explicitly declare docs out of scope (README-only) to set expectations
- Add SBOM / provenance attestation to publish.yml (actions/attest-build-provenance) since it publishes to PyPI via OIDC
- Reconcile the diverged local main (ahead 1 / behind 5 of origin/main) before any future push — the local `feat(provider): add papers export facade` commit is not on the remote lineage

## Push-safety notes
- site.yml deploys the live production domain papers.nirs4all.org on every push to main (permissions pages: write + id-token: write, concurrency group pages, no path filter) — pushing main triggers an immediate public-site redeploy and rewrites site/CNAME.
- version-guard.yml runs on push/PR to main and FAILS the build if VERSION (0.2.0) is ahead of the latest v* git tag. A commit to main that bumps VERSION without also pushing the matching tag will red-gate main. Bumps must ship as `git tag vX.Y.Z`, never a lone commit.
- publish.yml is release-triggered (types: [published]) — comparatively safe (tag/release-gated, not push-gated) — but it publishes to PyPI via OIDC, so a mis-tagged GitHub Release fires a real publish; workflow_dispatch defaults dry_run=true which is the safe default.
- Version coupling: pyproject.toml version and VERSION are separate; a push that updates only one leaves the wheel and the guarded manifest inconsistent.
- Cross-repo coupling: version-guard is described as the ecosystem-wide version-sync guardrail and the site links into nirs4all.org — changes here can affect the published ecosystem surface.
- Local main has diverged (ahead 1 / behind 5 of origin/main); per audit scope this repo will NOT be pushed. A push now would require reconciling the 5 remote commits first — do not force-push.
