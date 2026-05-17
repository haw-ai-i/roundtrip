"""Command-line interface for coundetrip benchmark runs."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from coundetrip.pipeline import run_roundtrip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="coundetrip",
        description="Run a roundtrip benchmark: describe → regenerate → evaluate → score",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run full roundtrip for one fixture")
    run_p.add_argument(
        "--fixture",
        type=Path,
        required=True,
        help="Path to fixture directory containing coundetrip.yaml",
    )
    run_p.add_argument(
        "--agent",
        required=True,
        help=(
            "Shell-style agent command (quoted), e.g. "
            "'python -m coundetrip.stub_agent'. Parsed with shlex.split."
        ),
    )
    run_p.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Base directory for run artifacts (default: ./runs)",
    )
    run_p.add_argument(
        "--run-id",
        default=None,
        help="Optional run id subdirectory name (default: auto timestamp)",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        agent_cmd = shlex.split(args.agent)
        if not agent_cmd:
            print("error: --agent must expand to a non-empty command", file=sys.stderr)
            return 2
        report = run_roundtrip(
            fixture_path=args.fixture.resolve(),
            agent_cmd=agent_cmd,
            runs_dir=args.runs_dir.resolve(),
            run_id=args.run_id,
        )
        print(json.dumps(report, indent=2))
        return 0 if report.get("success") else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
