"""Integration tests for roundtrip pipeline and command resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from coundetrip.pipeline import _resolve_stage_command, run_roundtrip

FIXTURES = Path(__file__).resolve().parent.parent / "benchmarks" / "fixtures"


def test_resolve_stage_command_stub() -> None:
    base = [sys.executable, "-m", "coundetrip.stub_agent"]
    assert _resolve_stage_command(base, "describe")[-1] == "describe"
    assert _resolve_stage_command(base, "regenerate")[-1] == "regenerate"


def test_resolve_stage_command_replace_last() -> None:
    cmd = [sys.executable, "-m", "coundetrip.stub_agent", "describe"]
    assert _resolve_stage_command(cmd, "regenerate")[-1] == "regenerate"


def test_run_roundtrip_calc_stub(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    report = run_roundtrip(
        fixture_path=FIXTURES / "calc",
        agent_cmd=[sys.executable, "-m", "coundetrip.stub_agent"],
        runs_dir=runs,
        run_id="pytest_calc",
    )
    assert report["success"] is True
    run_dir = Path(report["run_dir"])
    assert (run_dir / "description.md").is_file()
    assert (run_dir / "generated" / "src" / "calc" / "__init__.py").is_file()
    assert (run_dir / "report.json").is_file()
    loaded = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert loaded["score"]["tests"]["passed"] >= 2


def test_run_roundtrip_reverse_stub(tmp_path: Path) -> None:
    report = run_roundtrip(
        fixture_path=FIXTURES / "reverse",
        agent_cmd=[sys.executable, "-m", "coundetrip.stub_agent"],
        runs_dir=tmp_path / "runs2",
        run_id="pytest_rev",
    )
    assert report["success"] is True
