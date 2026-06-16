# Papers

One directory per deposited paper, `papers/<slug>/` (slug = `YYYY-short-title`). The
[reproduction-document publisher](../docs/REPRODUCTION_PUBLISHER.md) turns each one into a
self-contained page — methods + bibliography, the protocol and scores, a **live in-browser pipeline
replay**, and machine-readable deposit sidecars.

## A paper bundle

```text
papers/<slug>/
  paper.yaml     # title, authors, DOI, scores, protocol, dataset reference (see ../templates/paper.yaml)
  model.n4a      # the deposited nirs4all bundle (pipeline + fitted artifacts)
  replay.json    # optional: a small {axis, X, y, target} dataset for the live replay
```

Only add content that is safe for a public repository. The `.n4a` carries the pipeline and
fingerprints; `paper.yaml` carries everything it cannot.

## Build the site

```bash
pip install -e .          # or: pip install PyYAML
n4a-papers new 2026-my-paper       # scaffold papers/2026-my-paper/ from the template
n4a-papers check papers/2026-my-paper   # sanity-check one bundle
n4a-papers build --out site        # build the whole site into ./site
```

Open `site/index.html`. The output is self-contained (inline SVG charts, an inline JS replay
engine) and works from `file://`.

## Example

`2026-pls-nirs-demo/` is a worked demonstration built around a real deposited `.n4a` (a PLS protein
calibration) plus a synthetic dataset, so the pipeline can be re-run live in the browser.
