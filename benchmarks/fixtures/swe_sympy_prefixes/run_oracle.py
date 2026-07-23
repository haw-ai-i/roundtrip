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

# Pristine backup: first run captures the known-good (gold-patched) target.
orig = target.with_suffix(target.suffix + ".orig")
if not orig.exists():
    shutil.copy2(target, orig)
# Always restore from pristine before swapping in the regenerated file.
shutil.copy2(orig, target)

cands = sorted(HERE.rglob(basename))
if not cands:
    sys.stderr.write(f"run_oracle: no regenerated {basename} found in generated tree\n")
    sys.exit(2)
if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env} (run setup_swebench_env.py)\n")
    sys.exit(2)

shutil.copy2(cands[0], target)
try:
    cp = subprocess.run([str(venv_py), "-m", "pytest", str(oracle), "-q"],
                        capture_output=True, text=True)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    shutil.copy2(orig, target)
sys.exit(rc)
