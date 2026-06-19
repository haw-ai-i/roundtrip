"""Execution backends for agent stages and evaluation.

A ``Runner`` executes a command and returns its result. Two backends are
planned:

- ``LocalRunner`` runs on the host with no isolation. This is the current
  default and reproduces the pre-container behavior exactly.
- ``DockerRunner`` (added in a later change) runs the command inside a
  container, exposing only the declared ``mounts`` and honoring ``network``.

``mounts`` and ``network`` declare what a sandboxed runner should expose to the
process. ``LocalRunner`` runs directly on the host and therefore does not
enforce them; they are honored only by container-based runners.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class Mount:
    """A host path the process may access, with the given mode.

    ``mode`` is ``"ro"`` (read-only) or ``"rw"`` (read-write). A sandboxed
    runner exposes only the listed mounts; anything not mounted is absent from
    the process's filesystem.
    """

    host: Path
    mode: str = "ro"


@dataclass(frozen=True)
class RunResult:
    """Outcome of a command execution.

    A small subset of :class:`subprocess.CompletedProcess` carrying only the
    fields callers use, so callers do not depend on how the command was run.
    """

    returncode: int
    stdout: str
    stderr: str


class Runner(Protocol):
    """Executes a command, optionally sandboxed."""

    def execute(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        mounts: Sequence[Mount] = (),
        network: str = "inherit",
        timeout: int | None = None,
    ) -> RunResult:
        ...


class LocalRunner:
    """Run the command on the host with no isolation.

    Reproduces the pre-container behavior. ``mounts`` and ``network`` are
    accepted for interface compatibility but not enforced: the host already has
    full access to its own filesystem and network. Enforcement is the job of a
    container-based runner.
    """

    def execute(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        mounts: Sequence[Mount] = (),
        network: str = "inherit",
        timeout: int | None = None,
    ) -> RunResult:
        cp = subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=dict(env) if env is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return RunResult(
            returncode=cp.returncode,
            stdout=cp.stdout or "",
            stderr=cp.stderr or "",
        )


# --- Container backend -------------------------------------------------------

_WORK = "/coundetrip/run"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _to_container_path(
    value: str, cwd: Path, externs: list[tuple[Path, str]]
) -> str:
    """Rewrite an absolute host path to its location inside the container.

    Non-paths and paths that are neither under ``cwd`` nor under an external
    mount are returned unchanged (e.g. ``COUNDETRIP_STAGE=regenerate``).
    """
    if not value.startswith("/"):
        return value
    cwd_s = str(cwd)
    if value == cwd_s:
        return _WORK
    if value.startswith(cwd_s + os.sep):
        return _WORK + value[len(cwd_s):]
    for host, cpath in externs:
        host_s = str(host)
        if value == host_s:
            return cpath
        if value.startswith(host_s + os.sep):
            return cpath + value[len(host_s):]
    return value


def build_docker_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    image: str,
    env: Mapping[str, str] | None = None,
    mounts: Sequence[Mount] = (),
    network: str = "inherit",
    forward_env: Sequence[str] = (),
) -> list[str]:
    """Construct the ``docker run`` argv for one stage.

    The working directory ``cwd`` (the run directory for agents, the generated
    tree for evaluate) is bind-mounted read-write at ``/coundetrip/run``. Every
    path the stage legitimately needs lives under it, so it is reachable without
    a separate mount. Any declared mount that lies *outside* ``cwd`` (the fixture
    during describe) is mounted separately. Anything not mounted is absent from
    the container filesystem -- that absence is the isolation guarantee.

    Only ``COUNDETRIP_*`` environment variables are forwarded, with their path
    values rewritten to container paths. The host's own environment is not
    leaked into the container.
    """
    cwd = Path(cwd).resolve()
    cmd: list[str] = ["docker", "run", "--rm"]
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        cmd += ["--user", f"{os.getuid()}:{os.getgid()}"]
    cmd += ["-w", _WORK, "-v", f"{cwd}:{_WORK}:rw"]

    externs: list[tuple[Path, str]] = []
    for i, m in enumerate(mounts):
        host = Path(m.host).resolve()
        if host == cwd or _is_relative_to(host, cwd):
            # Reachable through the work mount. If declared read-only, overlay a
            # read-only bind so it stays read-only despite the writable parent.
            if m.mode == "ro" and host != cwd:
                rel = host.relative_to(cwd)
                cmd += ["-v", f"{host}:{_WORK}/{rel}:ro"]
            continue
        cpath = f"/coundetrip/extern{i}"
        cmd += ["-v", f"{host}:{cpath}:{m.mode}"]
        externs.append((host, cpath))

    if network == "none":
        cmd += ["--network", "none"]

    forward = tuple(forward_env)
    for key, value in (env or {}).items():
        if key.startswith("COUNDETRIP_") or key in forward:
            cmd += ["-e", f"{key}={_to_container_path(value, cwd, externs)}"]

    cmd.append(image)
    cmd += list(argv)
    return cmd


class DockerRunner:
    """Run the command inside a container.

    Exposes only the declared mounts; the fixture is never mounted during
    regenerate or evaluate, so filesystem traversal cannot reach the original
    source. ``network="none"`` is honored for offline evaluation.
    """

    def __init__(self, image: str = "coundetrip-sandbox", forward_env: Sequence[str] = ()) -> None:
        self.image = image
        self.forward_env = tuple(forward_env)

    def execute(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        mounts: Sequence[Mount] = (),
        network: str = "inherit",
        timeout: int | None = None,
    ) -> RunResult:
        cmd = build_docker_command(
            argv,
            cwd=cwd,
            image=self.image,
            env=env,
            mounts=mounts,
            network=network,
            forward_env=self.forward_env,
        )
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return RunResult(
            returncode=cp.returncode,
            stdout=cp.stdout or "",
            stderr=cp.stderr or "",
        )