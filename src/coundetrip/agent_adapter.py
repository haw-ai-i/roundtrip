"""Provider-agnostic subprocess adapter for describe / regenerate agents."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Sequence


def run_agent(
    agent_cmd: Sequence[str],
    *,
    stage: str,
    fixture_root: Path,
    run_dir: Path,
    description_path: Path | None = None,
    generated_root: Path | None = None,
    timeout_sec: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Invoke agent with documented environment variables.

    Convention for external agents:
    - COUNDETRIP_STAGE: ``describe`` | ``regenerate``
    - COUNDETRIP_FIXTURE: absolute path to original fixture root
    - COUNDETRIP_RUN_DIR: absolute path to this run directory
    - COUNDETRIP_DESCRIPTION: absolute path to description.md (regenerate only)
    - COUNDETRIP_GENERATED: absolute path to output directory for regenerated tree (regenerate only)

    The command line is ``agent_cmd`` with no extra args from this library; scripts
    should read env vars or document their own flags.
    """
    env = os.environ.copy()
    env["COUNDETRIP_STAGE"] = stage
    env["COUNDETRIP_FIXTURE"] = str(fixture_root.resolve())
    env["COUNDETRIP_RUN_DIR"] = str(run_dir.resolve())
    if description_path is not None:
        env["COUNDETRIP_DESCRIPTION"] = str(description_path.resolve())
    if generated_root is not None:
        env["COUNDETRIP_GENERATED"] = str(generated_root.resolve())

    return subprocess.run(
        list(agent_cmd),
        cwd=str(run_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
