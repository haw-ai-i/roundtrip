"""Generate a coundetrip roundtrip fixture from a prepared SWE-Bench env.

Given an instance_id whose env was built by setup_swebench_env.py, this locates
the env, auto-detects the names other modules import from the target module (the
contract regenerate must satisfy), and writes the fixture (coundetrip.yaml,
scaffold/CONTRACT.md, the generic self-restoring wrapper, oracle_env.json, and
the gold-patched source). Refuses multi-file gold patches.

Usage:
    uv run python benchmarks/make_fixture.py sympy__sympy-24909
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

_FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)

_WRAPPER = '''\
"""Generic oracle wrapper for external-env SWE-Bench roundtrip fixtures.

Restores the env's target file from a pristine .orig backup before each run, so
a previous roundtrip can never leave the env dirty and corrupt the next score.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "oracle_env.json").read_text(encoding="utf-8"))
env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
venv_py = env / ".venv/bin/python"
target = env / cfg["target_rel"]
oracle = env / cfg["oracle_rel"]
basename = cfg["source_basename"]

orig = target.with_suffix(target.suffix + ".orig")
if not orig.exists():
    shutil.copy2(target, orig)
shutil.copy2(orig, target)

cands = sorted(HERE.rglob(basename))
if not cands:
    sys.stderr.write(f"run_oracle: no regenerated {basename} found in generated tree\\n")
    sys.exit(2)
if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env} (run setup_swebench_env.py)\\n")
    sys.exit(2)

shutil.copy2(cands[0], target)
cp = subprocess.run([str(venv_py), "-m", "pytest", str(oracle), "-q"],
                    capture_output=True, text=True)
sys.stdout.write(cp.stdout)
sys.stderr.write(cp.stderr)
sys.exit(cp.returncode)
'''


def module_path(rel: str) -> str:
    return rel[:-3].replace("/", ".")


def detect_import_surface(repo: Path, target_rel: str) -> list[str]:
    mod = module_path(target_rel)
    base = mod.split(".")[-1]
    target_abs = (repo / target_rel).resolve()
    names: set[str] = set()
    for py in repo.rglob("*.py"):
        if py.resolve() == target_abs:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            absolute = node.module == mod
            relative = node.level > 0 and node.module and node.module.split(".")[-1] == base
            if absolute or relative:
                for alias in node.names:
                    if alias.name != "*":
                        names.add(alias.name)
    return sorted(names)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--name", default="")
    ap.add_argument("--base", default=str(Path.home() / "Desktop/coundetrip/swebench_envs"))
    ap.add_argument("--fixtures", default="benchmarks/fixtures")
    ap.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite")
    args = ap.parse_args()

    env = Path(args.base) / args.instance_id
    if not (env / ".venv").exists():
        sys.exit(f"env not found at {env}; run setup_swebench_env.py {args.instance_id} first")

    from datasets import load_dataset
    ds = load_dataset(args.dataset, split="test")
    r = next((x for x in ds if x["instance_id"] == args.instance_id), None)
    if r is None:
        sys.exit(f"instance {args.instance_id} not found")

    gold_files = _FILE_RE.findall(r["patch"])
    test_files = _FILE_RE.findall(r["test_patch"])
    if len(gold_files) != 1:
        sys.exit(f"refusing: gold patch touches {len(gold_files)} files {gold_files}; "
                 "single-file roundtrips need single-file tasks")
    if len(test_files) != 1:
        print(f"note: {len(test_files)} test files; using first in oracle")

    target_rel = gold_files[0]
    oracle_rel = test_files[0]
    basename = Path(target_rel).name
    surface = detect_import_surface(env, target_rel)

    repo_short = r["repo"].split("/")[-1]
    name = args.name or f"swe_{repo_short}_{Path(target_rel).stem}"
    fx = Path(args.fixtures) / name
    (fx / "scaffold").mkdir(parents=True, exist_ok=True)
    (fx / Path(target_rel).parent).mkdir(parents=True, exist_ok=True)

    (fx / target_rel).write_text((env / target_rel).read_text(encoding="utf-8"), encoding="utf-8")
    (fx / "run_oracle.py").write_text(_WRAPPER, encoding="utf-8")
    (fx / "oracle_env.json").write_text(json.dumps({
        "env_path": str(Path("~/Desktop/coundetrip/swebench_envs") / args.instance_id),
        "target_rel": target_rel,
        "oracle_rel": oracle_rel,
        "source_basename": basename,
    }, indent=2), encoding="utf-8")
    (fx / "coundetrip.yaml").write_text(
        f"name: {name}\n"
        "test_command:\n  - python\n  - run_oracle.py\n"
        f"source_paths:\n  - {target_rel}\n"
        "scaffold_paths:\n  - scaffold\n"
        "test_paths:\n  - run_oracle.py\n  - oracle_env.json\n",
        encoding="utf-8")
    surface_md = "\n".join(f"- `{n}`" for n in surface) or "- (none auto-detected)"
    (fx / "scaffold" / "CONTRACT.md").write_text(
        f"# Implementation target\n\nWrite the module at `{target_rel}`.\n\n"
        f"Other modules import these public names from it, so they MUST exist "
        f"with these exact names:\n\n{surface_md}\n\n"
        "Implement them to satisfy the specification. Do not write tests.\n",
        encoding="utf-8")

    print(f"created fixture: {fx}")
    print(f"  target:  {target_rel}")
    print(f"  oracle:  {oracle_rel}")
    print(f"  surface: {len(surface)} names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
