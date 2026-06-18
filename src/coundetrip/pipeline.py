"""Run directory layout and full roundtrip pipeline."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from coundetrip.agent_adapter import run_agent
from coundetrip.manifest import list_scaffold_files, list_test_files, load_manifest
from coundetrip.runner import LocalRunner, Mount, Runner
from coundetrip.scoring import describe_text_metrics, parse_pytest_summary


def _safe_run_id(run_id: str | None) -> str:
    if run_id:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", run_id).strip("._-")
        return cleaned or "run"
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_roundtrip(
    *,
    fixture_path: Path,
    agent_cmd: list[str],
    runs_dir: Path,
    run_id: str | None = None,
    agent_timeout_sec: int | None = 600,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """
    Execute describe → regenerate → evaluate → score.

    ``agent_cmd`` is the command to run for both stages; the stage is passed via env
    (see agent_adapter). For ``python -m coundetrip.stub_agent``, pass e.g.::

        ["python", "-m", "coundetrip.stub_agent", "describe"]

    That would only run describe — so we need TWO invocations with different subcommands.

    The plan's ``--agent`` is a prefix; we append the subcommand name for stub_agent.
    Convention:
    - If the last element is ``describe`` or ``regenerate``, use agent_cmd as-is for that stage only.
    - Otherwise, if ``stub_agent`` in cmd, append ``describe`` / ``regenerate`` for each stage.
    - Otherwise, run the same agent_cmd for both stages (env-only contract).
    """
    manifest = load_manifest(fixture_path)
    runner = runner or LocalRunner()
    rid = _safe_run_id(run_id)
    run_dir = (runs_dir / rid / manifest.name).resolve()
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    description_path = run_dir / "description.md"
    generated_root = run_dir / "generated"
    workspace_root = run_dir / "workspace"

    report: dict[str, Any] = {
        "fixture": str(manifest.fixture_root),
        "manifest_name": manifest.name,
        "run_dir": str(run_dir),
        "workspace": str(workspace_root),
        "success": False,
    }

    describe_cmd = _resolve_stage_command(agent_cmd, "describe")
    regen_cmd = _resolve_stage_command(agent_cmd, "regenerate")

    # --- describe ---
    cp_desc = run_agent(
        describe_cmd,
        stage="describe",
        fixture_root=manifest.fixture_root,
        run_dir=run_dir,
        description_path=description_path,
        generated_root=None,
        timeout_sec=agent_timeout_sec,
        runner=runner,
    )
    
    (logs_dir / "describe.stdout.txt").write_text(cp_desc.stdout or "", encoding="utf-8")
    (logs_dir / "describe.stderr.txt").write_text(cp_desc.stderr or "", encoding="utf-8")
    report["describe"] = {"returncode": cp_desc.returncode}
    if cp_desc.returncode != 0 or not description_path.is_file():
        report["error"] = "describe_failed"
        _write_report(run_dir, report)
        return report

    # --- regenerate (isolated: scaffold workspace only, never fixture source) ---
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True)
    for scaffold_file in list_scaffold_files(manifest):
        rel = scaffold_file.relative_to(manifest.fixture_root)
        dest = workspace_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scaffold_file, dest)

    if generated_root.exists():
        shutil.rmtree(generated_root)
    generated_root.mkdir(parents=True)
    cp_reg = run_agent(
        regen_cmd,
        stage="regenerate",
        workspace=workspace_root,
        run_dir=run_dir,
        description_path=description_path,
        generated_root=generated_root,
        timeout_sec=agent_timeout_sec,
        runner=runner,
    )
    (logs_dir / "regenerate.stdout.txt").write_text(cp_reg.stdout or "", encoding="utf-8")
    (logs_dir / "regenerate.stderr.txt").write_text(cp_reg.stderr or "", encoding="utf-8")
    report["regenerate"] = {"returncode": cp_reg.returncode}
    if cp_reg.returncode != 0:
        report["error"] = "regenerate_failed"
        _write_report(run_dir, report)
        return report

    # evaluate (original tests are the oracle: copy them into generated tree) 
    # Clear destination test paths first so nothing agent-written survives there
    # (extra auto-passing tests, or directories planted at test file paths).
    for rel_path in manifest.test_paths:
        dest = generated_root / rel_path
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        elif dest.exists() or dest.is_symlink():
            dest.unlink()
    for test_file in list_test_files(manifest):
        rel = test_file.relative_to(manifest.fixture_root)
        dest = generated_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(test_file, dest)

    test_cp = runner.execute(
        manifest.test_command,
        cwd=generated_root,
        env=None,
        mounts=[Mount(generated_root, "rw")],
        network="none",
        timeout=agent_timeout_sec,
    )
    (logs_dir / "test.stdout.txt").write_text(test_cp.stdout or "", encoding="utf-8")
    (logs_dir / "test.stderr.txt").write_text(test_cp.stderr or "", encoding="utf-8")
    summary = parse_pytest_summary(test_cp.stderr, test_cp.stdout)
    metrics = describe_text_metrics(description_path)
    # Normalize readability placeholder for JSON
    desc_metrics: dict[str, Any] = {
        "word_count": metrics["word_count"],
        "byte_size_utf8": metrics["byte_size_utf8"],
        "readability_rubric": None,
    }

    report["evaluate"] = {
        "returncode": test_cp.returncode,
        "test_command": list(manifest.test_command),
        "cwd": str(generated_root),
    }
    report["score"] = {
        "description": desc_metrics,
        "tests": {
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "skipped": summary.skipped,
            "pass_fraction": summary.pass_fraction,
        },
    }
    tests_ok = summary.failed == 0 and summary.errors == 0 and summary.passed > 0
    report["success"] = bool(tests_ok and test_cp.returncode == 0)
    _write_report(run_dir, report)
    return report


def _resolve_stage_command(agent_cmd: list[str], stage: str) -> list[str]:
    if not agent_cmd:
        raise ValueError("agent_cmd must be non-empty")
    cmd = list(agent_cmd)
    joined = " ".join(cmd)
    if cmd[-1] in ("describe", "regenerate"):
        cmd[-1] = stage
        return cmd
    if "stub_agent" in joined:
        return [*cmd, stage]
    return cmd


def _write_report(run_dir: Path, report: dict[str, Any]) -> None:
    (run_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")