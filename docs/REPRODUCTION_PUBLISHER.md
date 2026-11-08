<!-- SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later -->
# Reproduction document publisher: current reader contract

The active publisher keeps archive publication independent of optional current `.n4a` inspection.
Core owns V1 physical storage, inventory, integrity, native Package2/3 selection and admission. SDK
owns `nirs4all.python-host` metadata and JSON selection/validation over that same verified Core file.
Calling SDK for its profile is an owner route, never a fallback after native refusal.

## Supported reading

- Native Package2/3: Core selects `predict-external`; exact package and available training outcome
  documents are detached. A standalone Package3 has no invented complete parent outcome or scores.
- SDK-host: SDK validates `host-predict` / `host.predict` and returns exact bundle metadata and full
  JSON documents with semantic roles, inventory identities and declared content types. Original
  `training_declaration` and cosmetic `prediction_config` remain distinct. Additional owner JSON,
  branches, options, targets, results, scoring context and identity arrays are preserved whole.
- Foreign V1: readable inventory, unsupported owner semantics. No references are fetched.
- Historical physical layouts: Core refuses current reading. Raw archive downloads remain unchanged;
  no old ZIP parser, converter, fitted-object loader or inferred pipeline is provided.

Readability, SDK pre-model checks, scientific scoring validation and execution are distinct. Reports
state what was evaluated; no JSON readability claim implies valid DAG scoring or native parity.

## Publication and identity

`paper.yaml` supplies human public metadata. Scores/protocol from it are labelled **as published**,
separate from complete owner evidence. Missing owner documents, recipes or scores are explicitly
absent. Papers never flattens V1 recipes into a step/model heuristic or substitutes prediction labels
for a training recipe. Bibliography comes from explicitly supplied `method_ids` and the curated seed.

Current exports copy exact owner document bytes to numbered `owner-document-*.json` files, with the
member/role displayed in the page, plus the exact `container-manifest.json`. No synthetic
`pipeline.json` or Python computational workflow is generated. RO-Crate describes actual files; its
main entity is the archive. Current Core container/manifest hashes, owner fingerprints and raw file
SHA are separate. Supplied historical `provenance.bundle_fingerprint` retains its old namespace.

Optional `archive_sidecars` is a list of explicitly supplied released files confined to the paper
directory. They are copied verbatim, including supplied CFF/RO-Crate, rather than recreated from an
unsupported container. Their basenames must not collide. Derived sidecars available only in a frozen
published site must be supplied explicitly; the publisher does not mine generated output. Metadata
links retain historical companions and their approximation labels. Current reader pages do not run
approximate-JS replay or produce automatic `.predict` reproduction instructions.

Downloads keep their basename/URL. Current copies use Core verified copying into a staged file and
compare the receipt to displayed identities before atomic publication; partial failures are discarded.
Historical raw copies use a separate raw hash and make no current-admission claim. Output keeps
`.n4a-papers-build` and refuses to wipe unmarked nonempty directories. Never hand-edit generated site.

## Dependencies and local use

The archive-only Python 3.10 base uses PyYAML. Optional `current-reader` supplies Core and optional
`sdk-host-reader` supplies SDK, lazily used for its profile; owners require Python >=3.11. Candidate
floors Core >=0.5.0,<0.6 and SDK >=1.4.16,<2 require the matching qualified wheel/source cohort, not
merely a release label. No package version, lock, schema epoch or release tag is changed here.

```bash
n4a-papers build . --out <dedicated-output>
n4a-papers build . --out <dedicated-output> --read-current
n4a-papers check <paper-directory> --read-current
```

Archive-only is the default; it cannot qualify current reading. Missing Core/SDK is a dependency
status, not an invalid/historical classification. A refused read does not delete a catalog entry.
Direct provider `inspect_bundle` requests current reading; catalog/build/export wrappers accept
`read_current=True`. The facade writes only caller-selected local output, never uploads or writes
other stores. Existing narrow publisher and full provider/coverage CI-equivalent gates remain
separate, including the latter's separately authorized external Repository setup.

## Boundaries

No server refit, vendor parser, model deserialization, execution, score recomputation or source archive
mutation. Frozen scientific kits, models, locks, manuscripts and provenance remain upstream evidence.
Historical JS replay remains an approximate independent reference, not production WASM parity.
The optional local presentation island changes display only; owner reading and scientific behavior are unchanged.


## Shared UI presentation staging

The publisher consumes the actual UI.2 `StatTile` component for neutral reading/identity and
as-published result cards. Its partition selector preserves supplied labels, order and duplicates.
A missing partition is distinct from a supplied partition named “All”. Values use the same display
strings as the existing static results, including `nan`, `inf`, `-inf` and `—`; no numerical value is
calculated or substituted. A fixed JSON whitelist excludes metadata dumps, local paths, reading
exceptions, recipes and owner documents. React renders the projected strings as text.

The island starts hidden and becomes visible after a successful mount. Complete static results remain
in a native disclosure (initially open), with provenance, exact downloads and full owner documents
unchanged. No JavaScript is needed to access them. Missing or blocked enhancement assets retain
static publication. The island makes no network/storage/owner calls and adds no external assets;
existing font/analytics declarations in the host chrome are outside this presentation change.

Node is needed only for explicitly requested maintainer staging, never by `build_site`, the installed
CLI, install hooks or wheel creation. Use an existing offline Web dependency cohort. The accepted
archive SHA-256 is `237a3bf306bdb6fec5088783c425381bcf125540ba7ad25e1aec0604198d7728`.
The supplied local tooling cohort has React/ReactDOM 18.3.1, scheduler 0.23.2, and esbuild 0.25.12.

```bash
node ui/build.mjs \
  --archive /path/to/nirs4all-ui-0.2.2-local.20261107.2.tgz \
  --modules /path/to/nirs4all-web/web-app/node_modules \
  --stage /path/to/empty-private-stage \
  --out src/nirs4all_papers/data/ui
```

The script refuses an unrecognized archive and nonempty stage/output directories. It extracts the
accepted archive directly, uses its public qualification export and Web's explicit React/DOM cohort,
and emits one classic IIFE plus unchanged upstream qualification CSS and a small Papers stylesheet.
It does not use Web's installed UI copy, run npm lifecycle hooks or rebuild UI/Core/SDK/Methods.
The resource manifest records actual dependency/tool versions, archive/source hashes and output
hashes. UI licences/notices and the actual bundled React/DOM/scheduler MIT texts accompany the files;
the UI upstream notice's separate browser-bundle versions do not describe this Papers bundle.

Stage once before making the consumer wheel. Package-data includes nested notices; the Python builder
copies resources via `importlib.resources` to `assets/papers-ui/`. An unstaged source checkout stays
static-only. A current-reader gate and a shared-UI gate must exercise their actual respective paths;
static-only success is not shared-UI qualification. The affected shared-UI gate is the focused
projection tests plus existing build tests, one filter/reset browser path and one no-JS or blocked
bundle fallback, followed by one candidate-wheel resource/Node-free builder check. No owner suite,
fit, model deserialization, real archive regeneration or deployment is implied.
