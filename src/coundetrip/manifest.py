"""Load and validate coundetrip.yaml fixture manifests."""

from __future__ import annotations

from dataclasses import dataclass
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

    return FixtureManifest(
        name=name,
        test_command=test_cmd,
        source_paths=source_paths,
        fixture_root=root,
    )


def list_source_files(manifest: FixtureManifest) -> list[Path]:
    """Resolve source_paths under fixture_root; files only, sorted."""
    files: list[Path] = []
    for rel in manifest.source_paths:
        p = (manifest.fixture_root / rel).resolve()
        if not str(p).startswith(str(manifest.fixture_root.resolve())):
            raise ValueError(f"source_paths entry escapes fixture: {rel}")
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    files.append(f)
        else:
            raise FileNotFoundError(f"source_paths not found: {rel}")
    # de-dupe preserving order
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        rp = f.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out
