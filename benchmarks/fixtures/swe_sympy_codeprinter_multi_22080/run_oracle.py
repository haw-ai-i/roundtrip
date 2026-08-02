"""Generic scoped oracle for external-env SWE-bench roundtrip fixtures.

Scores the instance's own test selection (FAIL_TO_PASS + PASS_TO_PASS) rather
than whole test files, which is how SWE-bench itself defines resolution. This
keeps a fixture valid when unrelated neighbour tests in the same file drift with
the interpreter or dependency versions.

Restores the env's target file from a pristine .orig backup before and after each
run, so a previous roundtrip can never leave the env dirty.
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
basename = cfg["source_basename"]
selection = cfg.get("test_selection") or []
oracle_files = cfg.get("oracle_files") or ([cfg["oracle_rel"]] if cfg.get("oracle_rel") else [])

orig = target.with_suffix(target.suffix + ".orig")
if not orig.exists():
    shutil.copy2(target, orig)
shutil.copy2(orig, target)

cands = sorted(HERE.rglob(basename))
if not cands:
    sys.stderr.write(f"run_oracle: no regenerated {basename} found in generated tree\n")
    sys.exit(2)
if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env} (run setup_swebench_env.py)\n")
    sys.exit(2)

shutil.copy2(cands[0], target)

# SWE-bench stores selections either as pytest node ids
# ("tests/test_x.py::test_y") or, for some projects, as bare test function
# names. Node ids are passed straight through; bare names are selected with -k
# against the instance's own test files.
node_ids = [t for t in selection if "::" in t]
bare = [t for t in selection if "::" not in t]
if node_ids and not bare:
    # SWE-bench selections were generated under the reference harness; some
    # parametrized ids may not exist in this environment (optional dependencies
    # change parametrization). pytest aborts the whole run on a single missing
    # id, so pre-collect what exists and intersect. FAIL_TO_PASS ids must all
    # exist; missing PASS_TO_PASS ids are dropped and reported.
    files = sorted({t.split("::")[0] for t in node_ids})
    col = subprocess.run([str(venv_py), "-m", "pytest", "--collect-only", "-q", *files],
                         cwd=str(env), capture_output=True, text=True, timeout=600)
    existing = {l.strip() for l in col.stdout.splitlines() if "::" in l}
    f2p = set(cfg.get("fail_to_pass") or [])
    missing_f2p = [t for t in node_ids if t in f2p and t not in existing]
    if missing_f2p:
        sys.stderr.write(f"run_oracle: FAIL_TO_PASS test(s) not collectable in this env: {missing_f2p[:5]}\n")
        for t in targets:
            shutil.copy2(t.with_suffix(t.suffix + ".orig"), t)
        sys.exit(2)
    kept = [t for t in node_ids if t in existing]
    dropped = len(node_ids) - len(kept)
    if dropped:
        sys.stderr.write(f"run_oracle: dropped {dropped} PASS_TO_PASS id(s) not present in this env\n")
    args = kept
elif bare:
    files = [str(env / f) for f in oracle_files]
    expr = " or ".join(sorted(set(bare)))
    args = files + ["-k", expr]
else:
    args = [str(env / f) for f in oracle_files]
try:
    cp = subprocess.run([str(venv_py), "-m", "pytest", *args, "-q", "--tb=no"],
                        cwd=str(env), capture_output=True, text=True, timeout=900)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    shutil.copy2(orig, target)
sys.exit(rc)
