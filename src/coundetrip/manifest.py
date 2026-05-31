"""Load and validate coundetrip.yaml fixture manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

MANIFEST_NAME = "coundetrip.yaml"


@dataclass(frozen=True)
class FixtureManifest:
    """Parsed fixture configuration."""

    name: str
    test_command: list[str]
    source_paths: list[str]
    fixture_root: Path
    scaffold_paths: list[str] = field(default_factory=list)
    test_paths: list[str] = field(default_factory=list)
    


    @property
    def manifest_path(self) -> Path:
        return self.fixture_root / MANIFEST_NAME


def _as_str_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        return list(value)
    raise ValueError(f"{field} must be a string or list of strings")


def load_manifest(fixture_root: Path) -> FixtureManifest:
    """Load coundetrip.yaml from fixture_root."""
    root = fixture_root.resolve()
    path = root / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(f"Missing manifest: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Manifest must be a YAML mapping")

    name = raw.get("name")
    if not name or not isinstance(name, str):
        name = root.name

    test_cmd = _as_str_list(raw.get("test_command"), "test_command")
    if not test_cmd:
        raise ValueError("test_command is required")

    source_paths = _as_str_list(raw.get("source_paths"), "source_paths")
    if not source_paths:
        raise ValueError("source_paths is required (non-empty)")

    scaffold_paths = _as_str_list(raw.get("scaffold_paths"), "scaffold_paths")
    test_paths = _as_str_list(raw.get("test_paths"), "test_paths")

    return FixtureManifest(
        name=name,
        test_command=test_cmd,
        source_paths=source_paths,
        fixture_root=root,
        scaffold_paths=scaffold_paths,
        test_paths=test_paths,
    )


def _list_files(manifest: FixtureManifest, rel_paths: list[str], field: str) -> list[Path]:
    """Resolve rel_paths under fixture_root; files only, sorted, de-duped."""
    root = manifest.fixture_root.resolve()
    files: list[Path] = []
    for rel in rel_paths:
        p = (manifest.fixture_root / rel).resolve()
        if not str(p).startswith(str(root)):
            raise ValueError(f"{field} entry escapes fixture: {rel}")
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    files.append(f)
        else:
            raise FileNotFoundError(f"{field} not found: {rel}")
    # de-dupe preserving order
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        rp = f.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def list_source_files(manifest: FixtureManifest) -> list[Path]:
    """Resolve source_paths under fixture_root; files only, sorted."""
    return _list_files(manifest, manifest.source_paths, "source_paths")


def list_test_files(manifest: FixtureManifest) -> list[Path]:
    """Resolve test_paths under fixture_root; files only, sorted."""
    return _list_files(manifest, manifest.test_paths, "test_paths")


def list_scaffold_files(manifest: FixtureManifest) -> list[Path]:
    """Resolve scaffold_paths under fixture_root; files only, sorted."""
    return _list_files(manifest, manifest.scaffold_paths, "scaffold_paths")
