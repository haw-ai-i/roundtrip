"""Tests for fixture manifest loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from coundetrip.manifest import load_manifest, list_source_files

FIXTURES = Path(__file__).resolve().parent.parent / "benchmarks" / "fixtures"


def test_load_calc_manifest() -> None:
    m = load_manifest(FIXTURES / "calc")
    assert m.name == "calc"
    assert m.test_command[:4] == ["python", "-m", "pytest", "-q"]
    assert "src" in m.source_paths


def test_list_source_files_calc() -> None:
    m = load_manifest(FIXTURES / "calc")
    files = list_source_files(m)
    rels = {f.relative_to(m.fixture_root) for f in files}
    assert Path("src/calc/__init__.py") in rels
    assert Path("tests/test_calc.py") not in rels
    assert Path("pyproject.toml") in rels


def test_manifest_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path)


def test_manifest_invalid_empty_test_command(tmp_path: Path) -> None:
    (tmp_path / "coundetrip.yaml").write_text(
        "name: x\nsource_paths: [src]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="test_command"):
        load_manifest(tmp_path)
