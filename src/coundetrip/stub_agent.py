"""Stub agent for local smoke tests: copies seeded description and snapshot tree.

Regenerate does not read COUNDETRIP_FIXTURE (the pipeline no longer sets it).
Pass the snapshot location explicitly via --snapshot or COUNDETRIP_STUB_SNAPSHOT.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _cmd_describe(args: argparse.Namespace) -> int:
    fixture = Path(args.fixture or os.environ.get("COUNDETRIP_FIXTURE", "")).resolve()
    out = args.out
    if out is None:
        out_s = os.environ.get("COUNDETRIP_DESCRIPTION")
        if not out_s:
            print("Missing --out or COUNDETRIP_DESCRIPTION", file=sys.stderr)
            return 1
        out = Path(out_s)
    seed = fixture / "stub" / "description.md"
    if not seed.is_file():
        print(f"Missing seed description: {seed}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(seed, out)
    return 0


def _cmd_regenerate(args: argparse.Namespace) -> int:
    snap_s = args.snapshot or os.environ.get("COUNDETRIP_STUB_SNAPSHOT", "")
    if not snap_s:
        print("Missing --snapshot or COUNDETRIP_STUB_SNAPSHOT", file=sys.stderr)
        return 1
    snap = Path(snap_s).resolve()
    desc = args.description
    if desc is None:
        d = os.environ.get("COUNDETRIP_DESCRIPTION")
        if not d:
            print("Missing --description or COUNDETRIP_DESCRIPTION", file=sys.stderr)
            return 1
        desc = Path(d)
    gen = args.out
    if gen is None:
        g = os.environ.get("COUNDETRIP_GENERATED")
        if not g:
            print("Missing --out or COUNDETRIP_GENERATED", file=sys.stderr)
            return 1
        gen = Path(g)
    if not desc.is_file():
        print(f"Description not found: {desc}", file=sys.stderr)
        return 1
    if not snap.is_dir():
        print(f"Missing snapshot dir: {snap}", file=sys.stderr)
        return 1
    if gen.exists():
        shutil.rmtree(gen)
    shutil.copytree(snap, gen)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coundetrip stub roundtrip agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("describe", help="Write description.md from fixture stub seed")
    d.add_argument("--fixture", default=None)
    d.add_argument("--out", type=Path, default=None)
    d.set_defaults(func=_cmd_describe)

    r = sub.add_parser("regenerate", help="Copy snapshot dir into output dir")
    r.add_argument("--snapshot", default=None)
    r.add_argument("--description", type=Path, default=None)
    r.add_argument("--out", type=Path, default=None)
    r.set_defaults(func=_cmd_regenerate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())