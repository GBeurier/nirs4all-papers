# Security policy

`nirs4all-papers` is the **public deposited paper archive** for the nirs4all ecosystem: accepted/deposited
PDFs, public reproducibility code (RO-Crate), and stable WASM/static companions, built into a site published
at **papers.nirs4all.org** (via `n4a-papers build`).

Security-relevant surface:

- **Content it builds** — paper metadata, reproducibility kits, and static/WASM companions are compiled into
  a public site. The build (`n4a-papers build`) parses repository content; malformed content should fail the
  build cleanly rather than emit an unsafe page.
- **WASM companions** run client-side in the visitor's browser sandbox.
- **No secrets, no user data.** PyPI publishing uses OIDC Trusted Publishing.

Only deposit artifacts you have the right to publish; respect each paper's/dataset's license.

## Reporting a vulnerability

Please report security issues **privately** — do not open a public GitHub issue. Email
**nirs4all-admin@cirad.fr** with the affected version, a description, and reproduction steps.
