"""Isolation tests driven by a probe agent that tries to read the original
fixture source during regenerate.

The probe is given the fixture source's absolute host path -- modeling a
determined agent that already knows the host layout. Under LocalRunner that
path is on the same filesystem and is readable (the threat). Under DockerRunner
the fixture is never mounted, so the same read fails: the bytes are simply not
present in the container. Together the two tests show the flip.

The probe is passed inline via ``python -c`` so nothing needs to be mounted for
the agent script itself. In describe it writes the description; in regenerate it
records how many bytes of source it could read into COUNDETRIP_GENERATED, which
the host reads afterward.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from coundetrip.pipeline import run_roundtrip
from coundetrip.runner import DockerRunner, LocalRunner

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "benchmarks" / "fixtures"
_TARGET = FIXTURES / "calc" / "src" / "calc" / "__init__.py"

PROBE = f"""
import json, os
from pathlib import Path

stage = os.environ["COUNDETRIP_STAGE"]
if stage == "describe":
    Path(os.environ["COUNDETRIP_DESCRIPTION"]).write_text("probe", encoding="utf-8")
else:
    try:
        bytes_read = len(Path(r"{_TARGET}").read_text(encoding="utf-8"))
    except OSError:
        bytes_read = None
    gen = Path(os.environ["COUNDETRIP_GENERATED"])
    gen.mkdir(parents=True, exist_ok=True)
    (gen / "FINDINGS.json").write_text(
        json.dumps({{"bytes_read": bytes_read}}), encoding="utf-8"
    )
"""


def _bytes_read(report: dict) -> int | None:
    run_dir = Path(report["run_dir"])
    data = json.loads((run_dir / "generated" / "FINDINGS.json").read_text(encoding="utf-8"))
    return data["bytes_read"]


def _docker_ok() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=15
        ).returncode == 0
    except Exception:
        return False


def test_local_probe_reaches_source(tmp_path: Path) -> None:
    """Without a sandbox, the regenerate agent reads the original source."""
    report = run_roundtrip(
        fixture_path=FIXTURES / "calc",
        agent_cmd=[sys.executable, "-c", PROBE],
        runs_dir=tmp_path / "runs",
        run_id="local_probe",
        runner=LocalRunner(),
    )
    assert _bytes_read(report) is not None and _bytes_read(report) > 0


@pytest.mark.skipif(not _docker_ok(), reason="docker engine not available")
def test_docker_probe_cannot_reach_source() -> None:
    """Inside the container the fixture is not mounted, so the read fails.

    The run directory must live under the user's home directory: Colima (and
    Docker Desktop) only bind-mount paths under home into the VM, so a run dir
    in the system temp area would not propagate back to the host. We create it
    under the repo, which is under home.
    """
    runs_root = REPO / "runs"
    runs_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="docker_iso_", dir=runs_root))
    try:
        report = run_roundtrip(
            fixture_path=FIXTURES / "calc",
            agent_cmd=["python", "-c", PROBE],
            runs_dir=work,
            run_id="docker_probe",
            runner=DockerRunner(image="coundetrip-sandbox"),
        )
        assert _bytes_read(report) is None
    finally:
        shutil.rmtree(work, ignore_errors=True)