"""Phase 0 of the package-level design: find self-contained subpackage candidates
(Kind A) in a built environment. A candidate is a package directory of 3-15 source
files inside the project itself (not site-packages) with its own tests directory,
or with test files in a project tests directory that name-match its modules."""
import json, sys
from pathlib import Path

SKIP = (".venv", "site-packages", "build", "dist", "doc", "docs", "examples", ".git")

def own_tests(d: Path, root: Path):
    """Tests that belong to this subpackage: an inner tests/ dir, else project
    tests whose filenames match this subpackage's module names."""
    inner = d / "tests"
    if inner.is_dir():
        files = sorted(inner.glob("test_*.py"))
        if files:
            return inner, files
    mods = {f.stem for f in d.glob("*.py") if f.name != "__init__.py"}
    for cand in (d.parent / "tests", root / "tests"):
        if cand.is_dir():
            matched = sorted(f for f in cand.glob("test_*.py")
                             if f.stem[len("test_"):] in mods)
            if matched:
                return cand, matched
    return None, []

def scan(root: Path):
    rows = []
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        rel = d.relative_to(root).as_posix()
        if any(s in rel.split("/") or s in rel for s in SKIP):
            continue
        if d.name.startswith((".", "__")) or "test" in d.name:
            continue
        if not (d / "__init__.py").exists():
            continue
        srcs = [f for f in d.glob("*.py")
                if not f.name.startswith("test") and f.name != "__init__.py"]
        if not (3 <= len(srcs) <= 15):
            continue
        tdir, tfiles = own_tests(d, root)
        if not tfiles:
            continue
        rows.append({
            "subpackage": rel,
            "source_files": len(srcs),
            "source_lines": sum(len(f.read_text(errors="ignore").splitlines()) for f in srcs),
            "tests_dir": tdir.relative_to(root).as_posix(),
            "test_files": [f.name for f in tfiles],
        })
    return rows

if len(sys.argv) < 2:
    sys.exit("usage: filter_subpackages.py <env_path> [more envs...]")

all_rows = {}
for arg in sys.argv[1:]:
    root = Path(arg).expanduser()
    rows = scan(root)
    all_rows[root.name] = rows
    print(f"\n=== {root.name}: {len(rows)} candidate subpackages ===")
    print(f"{'subpackage':<40}{'files':>6}{'lines':>8}{'tests':>7}")
    for r in sorted(rows, key=lambda x: -x["source_lines"])[:20]:
        print(f"{r['subpackage']:<40}{r['source_files']:>6}{r['source_lines']:>8}{len(r['test_files']):>7}")
    if len(rows) > 20:
        print(f"... and {len(rows)-20} more")

Path("benchmarks/subpackage_candidates.json").write_text(json.dumps(all_rows, indent=1))
print(f"\ntotal: {sum(len(v) for v in all_rows.values())} candidates")
print("saved benchmarks/subpackage_candidates.json")
