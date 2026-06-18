"""Unit tests for DockerRunner's command construction (no daemon required)."""

from __future__ import annotations

from pathlib import Path

from coundetrip.runner import Mount, build_docker_command


def _flags(cmd: list[str], flag: str) -> list[str]:
    """Return the values that follow each occurrence of ``flag``."""
    return [cmd[i + 1] for i, tok in enumerate(cmd) if tok == flag]


def test_evaluate_offline_mounts_only_generated(tmp_path: Path) -> None:
    gen = tmp_path / "run" / "generated"
    gen.mkdir(parents=True)
    cmd = build_docker_command(
        ["python", "-m", "pytest", "-q", "tests"],
        cwd=gen,
        image="coundetrip-sandbox",
        env=None,
        mounts=[Mount(gen, "rw")],
        network="none",
    )
    assert f"{gen}:/coundetrip/run:rw" in _flags(cmd, "-v")
    assert len(_flags(cmd, "-v")) == 1
    assert _flags(cmd, "--network") == ["none"]
    assert cmd[-5:] == ["python", "-m", "pytest", "-q", "tests"]
    assert "-e" not in cmd


def test_regenerate_does_not_mount_fixture(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    workspace = run_dir / "workspace"
    generated = run_dir / "generated"
    description = run_dir / "description.md"
    fixture = tmp_path / "fixtures" / "calc"
    for p in (workspace, generated):
        p.mkdir(parents=True)
    description.write_text("x", encoding="utf-8")

    env = {
        "COUNDETRIP_STAGE": "regenerate",
        "COUNDETRIP_RUN_DIR": str(run_dir),
        "COUNDETRIP_WORKSPACE": str(workspace),
        "COUNDETRIP_DESCRIPTION": str(description),
        "COUNDETRIP_GENERATED": str(generated),
    }
    cmd = build_docker_command(
        ["python", "/coundetrip/run/agent.py"],
        cwd=run_dir,
        image="coundetrip-sandbox",
        env=env,
        mounts=[Mount(workspace, "rw"), Mount(description, "ro"), Mount(generated, "rw")],
        network="inherit",
    )
    mounts = _flags(cmd, "-v")
    assert mounts == [f"{run_dir}:/coundetrip/run:rw"]
    assert all(str(fixture) not in tok for tok in cmd)
    envs = _flags(cmd, "-e")
    assert "COUNDETRIP_WORKSPACE=/coundetrip/run/workspace" in envs
    assert "COUNDETRIP_GENERATED=/coundetrip/run/generated" in envs
    assert "COUNDETRIP_DESCRIPTION=/coundetrip/run/description.md" in envs
    assert "COUNDETRIP_RUN_DIR=/coundetrip/run" in envs
    assert "COUNDETRIP_STAGE=regenerate" in envs


def test_describe_mounts_fixture_externally(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    description = run_dir / "description.md"
    fixture = tmp_path / "fixtures" / "calc"
    fixture.mkdir(parents=True)

    env = {
        "COUNDETRIP_STAGE": "describe",
        "COUNDETRIP_RUN_DIR": str(run_dir),
        "COUNDETRIP_FIXTURE": str(fixture),
        "COUNDETRIP_DESCRIPTION": str(description),
    }
    cmd = build_docker_command(
        ["python", "/coundetrip/run/agent.py"],
        cwd=run_dir,
        image="coundetrip-sandbox",
        env=env,
        mounts=[Mount(fixture, "ro"), Mount(description, "ro")],
        network="inherit",
    )
    mounts = _flags(cmd, "-v")
    assert f"{run_dir}:/coundetrip/run:rw" in mounts
    assert f"{fixture}:/coundetrip/extern0:ro" in mounts
    envs = _flags(cmd, "-e")
    assert "COUNDETRIP_FIXTURE=/coundetrip/extern0" in envs
    assert "COUNDETRIP_DESCRIPTION=/coundetrip/run/description.md" in envs


def test_non_coundetrip_env_is_dropped(tmp_path: Path) -> None:
    cwd = tmp_path
    cmd = build_docker_command(
        ["true"],
        cwd=cwd,
        image="img",
        env={"COUNDETRIP_STAGE": "describe", "SECRET_TOKEN": "abc", "HOME": "/Users/x"},
        mounts=[],
        network="inherit",
    )
    envs = _flags(cmd, "-e")
    assert "COUNDETRIP_STAGE=describe" in envs
    assert all("SECRET_TOKEN" not in e and "HOME" not in e for e in envs)