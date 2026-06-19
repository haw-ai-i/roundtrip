"""Provider-agnostic adapter for describe / regenerate agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from coundetrip.runner import LocalRunner, Mount, RunResult, Runner


def run_agent(
    agent_cmd: Sequence[str],
    *,
    stage: str,
    run_dir: Path,
    fixture_root: Path | None = None,
    workspace: Path | None = None,
    description_path: Path | None = None,
    generated_root: Path | None = None,
    timeout_sec: int | None = None,
    runner: Runner | None = None,
) -> RunResult:
    """
    Invoke an agent for one stage with documented environment variables.

    Convention for external agents:
    - COUNDETRIP_STAGE: ``describe`` | ``regenerate``
    - COUNDETRIP_FIXTURE: absolute path to original fixture root (describe only)
    - COUNDETRIP_WORKSPACE: absolute path to isolated scaffold workspace (regenerate only)
    - COUNDETRIP_RUN_DIR: absolute path to this run directory
    - COUNDETRIP_DESCRIPTION: absolute path to description.md (regenerate only)
    - COUNDETRIP_GENERATED: absolute path to output directory for regenerated tree (regenerate only)

    Isolation contract: during regenerate, the original fixture path is never
    exposed; the agent sees only the description, the scaffold workspace, and
    the output directory.

    The command is executed by ``runner`` (default :class:`LocalRunner`, i.e. on
    the host). Each path the agent legitimately needs is also declared as a
    :class:`Mount`, so a container-based runner can expose exactly those paths
    and nothing else. The mounts mirror the environment variables above.
    """
    runner = runner or LocalRunner()

    env = os.environ.copy()
    env["COUNDETRIP_STAGE"] = stage
    env["COUNDETRIP_RUN_DIR"] = str(run_dir.resolve())

    mounts: list[Mount] = []
    if fixture_root is not None:
        p = fixture_root.resolve()
        env["COUNDETRIP_FIXTURE"] = str(p)
        mounts.append(Mount(p, "ro"))
    if workspace is not None:
        p = workspace.resolve()
        env["COUNDETRIP_WORKSPACE"] = str(p)
        mounts.append(Mount(p, "rw"))
    if description_path is not None:
        p = description_path.resolve()
        env["COUNDETRIP_DESCRIPTION"] = str(p)
        # The description is the output of describe (writable) but a read-only
        # input to regenerate.
        mounts.append(Mount(p, "ro" if stage == "regenerate" else "rw"))
    if generated_root is not None:
        p = generated_root.resolve()
        env["COUNDETRIP_GENERATED"] = str(p)
        mounts.append(Mount(p, "rw"))

    return runner.execute(
        list(agent_cmd),
        cwd=run_dir,
        env=env,
        mounts=mounts,
        network="inherit",
        timeout=timeout_sec,
    )