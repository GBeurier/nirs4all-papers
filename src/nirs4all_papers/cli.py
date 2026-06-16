# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""``n4a-papers`` — build the reproduction-document site, or scaffold a new paper bundle."""
from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .model import load_paper
from .site import build_site


def _template_text() -> str:
    """The paper.yaml scaffold, loaded from packaged data (works in a wheel install)."""
    return resources.files("nirs4all_papers").joinpath("data/paper_template.yaml").read_text(encoding="utf-8")


def _cmd_build(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not (root / "papers").is_dir():
        print(f"error: no papers/ directory under {root.resolve()} — is this the repository root?", file=sys.stderr)
        return 1
    out = build_site(root, args.out)
    papers = list((out / "paper").glob("*.html"))
    print(f"Built {len(papers)} paper page(s) → {out}")
    print(f"  open {out / 'index.html'}")
    return 0


def _cmd_new(args: argparse.Namespace) -> int:
    root = Path(args.root)
    dest = root / "papers" / args.slug
    if dest.exists():
        print(f"error: {dest} already exists", file=sys.stderr)
        return 1
    dest.mkdir(parents=True)
    (dest / "paper.yaml").write_text(_template_text(), encoding="utf-8")
    print(f"Scaffolded {dest}/paper.yaml")
    print("  next: drop your model.n4a (and an optional replay.json) here, fill in paper.yaml, then:")
    print("  n4a-papers build --out site")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    """Load one paper bundle and print a quick summary (a fast sanity check on inputs)."""
    view = load_paper(args.paper_dir)
    print(f"{view.title}")
    print(f"  slug:     {view.slug}")
    print(f"  nirs4all: {view.bundle.nirs4all_version}")
    print(f"  steps:    {len(view.steps)} ({view.n_steps} excl. split)")
    print(f"  cited:    {len(view.references)} reference(s)")
    print(f"  replay:   {'yes' if view.replay else 'no'}")
    uncited = [s.info.short_name for s in view.steps if s.info.kind in ("preprocessing", "model", "target") and not s.reference]
    if uncited:
        print(f"  uncited:  {', '.join(uncited)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="n4a-papers", description="nirs4all reproduction-document publisher")
    parser.add_argument("--version", action="version", version=f"n4a-papers {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build the static site from papers/*/")
    p_build.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    p_build.add_argument("--out", default="site", help="output directory (default: site)")
    p_build.set_defaults(func=_cmd_build)

    p_new = sub.add_parser("new", help="scaffold a new papers/<slug>/ bundle")
    p_new.add_argument("slug", help="paper slug, e.g. 2026-pls-nirs")
    p_new.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    p_new.set_defaults(func=_cmd_new)

    p_check = sub.add_parser("check", help="summarize one papers/<slug>/ bundle")
    p_check.add_argument("paper_dir", help="path to a papers/<slug>/ directory")
    p_check.set_defaults(func=_cmd_check)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError) as exc:
        # Boundary errors (bad paths, malformed bundles, slug collisions) -> a clean message, not a traceback.
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
