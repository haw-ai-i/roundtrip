"""Integration tests for roundtrip pipeline and command resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from coundetrip.pipeline import _resolve_stage_command, run_roundtrip

FIXTURES = Path(__file__).resolve().parent.parent / "benchmarks" / "fixtures"


def _set_stub_snapshot(monkeypatch: pytest.MonkeyPatch, fixture: str) -> None:
    snap = FIXTURES / fixture / "stub" / "generated_snapshot"
    monkeypatch.setenv("COUNDETRIP_STUB_SNAPSHOT", str(snap))


def test_resolve_stage_command_stub() -> None:
    base = [sys.executable, "-m", "coundetrip.stub_agent"]
    assert _resolve_stage_command(base, "describe")[-1] == "describe"
    assert _resolve_stage_command(base, "regenerate")[-1] == "regenerate"


def test_resolve_stage_command_replace_last() -> None:
    cmd = [sys.executable, "-m", "coundetrip.stub_agent", "describe"]
    assert _resolve_stage_command(cmd, "regenerate")[-1] == "regenerate"


def test_run_roundtrip_calc_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _set_stub_snapshot(monkeypatch, "calc")
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
    # Oracle integrity: tests in the generated tree are the fixture originals.
    original = (FIXTURES / "calc" / "tests" / "test_calc.py").read_text(encoding="utf-8")
    evaluated = (run_dir / "generated" / "tests" / "test_calc.py").read_text(encoding="utf-8")
    assert evaluated == original


def test_run_roundtrip_reverse_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _set_stub_snapshot(monkeypatch, "reverse")
    report = run_roundtrip(
        fixture_path=FIXTURES / "reverse",
        agent_cmd=[sys.executable, "-m", "coundetrip.stub_agent"],
        runs_dir=tmp_path / "runs2",
        run_id="pytest_rev",
    )
    assert report["success"] is True


ENV_DUMP_AGENT = """
import json, os
from pathlib import Path

stage = os.environ["COUNDETRIP_STAGE"]
run_dir = Path(os.environ["COUNDETRIP_RUN_DIR"])
dump = {k: v for k, v in os.environ.items() if k.startswith("COUNDETRIP_")}
(run_dir / f"env_{stage}.json").write_text(json.dumps(dump), encoding="utf-8")
if stage == "describe":
    Path(os.environ["COUNDETRIP_DESCRIPTION"]).write_text("probe", encoding="utf-8")
"""


def test_regenerate_is_isolated_from_fixture(tmp_path: Path) -> None:
    """The regenerate stage must never receive the original fixture path."""
    agent = tmp_path / "env_dump_agent.py"
    agent.write_text(ENV_DUMP_AGENT, encoding="utf-8")
    report = run_roundtrip(
        fixture_path=FIXTURES / "calc",
        agent_cmd=[sys.executable, str(agent)],
        runs_dir=tmp_path / "runs",
        run_id="pytest_isolation",
    )
    run_dir = Path(report["run_dir"])

    env_desc = json.loads((run_dir / "env_describe.json").read_text(encoding="utf-8"))
    env_reg = json.loads((run_dir / "env_regenerate.json").read_text(encoding="utf-8"))

    # Describe legitimately sees the fixture.
    assert "COUNDETRIP_FIXTURE" in env_desc
    # Regenerate must not: no fixture path, workspace instead.
    assert "COUNDETRIP_FIXTURE" not in env_reg
    assert "COUNDETRIP_WORKSPACE" in env_reg

    # Workspace contains only scaffold content: pyproject.toml, no source.
    workspace = Path(env_reg["COUNDETRIP_WORKSPACE"])
    assert (workspace / "pyproject.toml").is_file()
    assert not (workspace / "src").exists()
    assert not (workspace / "tests").exists()

HOSTILE_AGENT = """
import os, shutil
from pathlib import Path

stage = os.environ["COUNDETRIP_STAGE"]
if stage == "describe":
    Path(os.environ["COUNDETRIP_DESCRIPTION"]).write_text("probe", encoding="utf-8")
else:
    gen = Path(os.environ["COUNDETRIP_GENERATED"])
    snap = Path(os.environ["COUNDETRIP_STUB_SNAPSHOT"])
    if gen.exists():
        shutil.rmtree(gen)
    shutil.copytree(snap, gen)
    # Attack 1: plant an extra auto-passing test.
    (gen / "tests" / "test_evil.py").write_text(
        "def test_always_passes():\\n    assert True\\n", encoding="utf-8"
    )
    # Attack 2: replace an original test file with a directory.
    target = gen / "tests" / "test_calc.py"
    target.unlink()
    target.mkdir()
"""


def test_agent_cannot_hijack_test_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Agent-written files in test paths must not survive into evaluation."""
    _set_stub_snapshot(monkeypatch, "calc")
    agent = tmp_path / "hostile_agent.py"
    agent.write_text(HOSTILE_AGENT, encoding="utf-8")
    report = run_roundtrip(
        fixture_path=FIXTURES / "calc",
        agent_cmd=[sys.executable, str(agent)],
        runs_dir=tmp_path / "runs",
        run_id="pytest_hijack",
    )
    assert report["success"] is True
    run_dir = Path(report["run_dir"])
    tests_dir = run_dir / "generated" / "tests"
    # The planted test is gone; the original is back as a real file.
    assert not (tests_dir / "test_evil.py").exists()
    assert (tests_dir / "test_calc.py").is_file()
    original = (FIXTURES / "calc" / "tests" / "test_calc.py").read_text(encoding="utf-8")
    assert (tests_dir / "test_calc.py").read_text(encoding="utf-8") == original
    # Only the original tests were counted.
    assert report["score"]["tests"]["passed"] == 2  