"""Multi-file oracle wrapper for repo-wide roundtrip fixtures.
Restores each target file from a pristine .orig backup, copies in each regenerated
file, then runs the union of the target test files. Extends the single-file oracle
to several interdependent modules without modifying it.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "oracle_env.json").read_text(encoding="utf-8"))
env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
venv_py = env / ".venv/bin/python"
targets = cfg["targets"]  # list of {target_rel, oracle_rel, source_basename}

if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env}\n"); sys.exit(2)

# restore originals and copy in each regenerated file
oracles = []
for t in targets:
    target = env / t["target_rel"]
    oracle = env / t["oracle_rel"]
    basename = t["source_basename"]
    orig = target.with_suffix(target.suffix + ".orig")
    if not orig.exists():
        shutil.copy2(target, orig)
    shutil.copy2(orig, target)  # restore pristine
    cands = sorted(HERE.rglob(basename))
    if not cands:
        sys.stderr.write(f"run_oracle: no regenerated {basename} found\n"); sys.exit(2)
    shutil.copy2(cands[0], target)  # install regenerated
    oracles.append(str(oracle))

# run the union of all target test files
cp = subprocess.run([str(venv_py), "-m", "pytest", *oracles, "-q"],
                    capture_output=True, text=True)
sys.stdout.write(cp.stdout)
sys.stderr.write(cp.stderr)
sys.exit(cp.returncode)
