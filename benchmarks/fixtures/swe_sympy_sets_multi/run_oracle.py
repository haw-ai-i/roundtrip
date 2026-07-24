"""Multi-file oracle wrapper for repo-wide roundtrip fixtures.
Snapshots each target once (guarded so a dirty target can never become the
reference), installs each regenerated file, runs the union of the target test
files, and always restores every target afterward."""
import json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "oracle_env.json").read_text(encoding="utf-8"))
env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
venv_py = env / ".venv/bin/python"
targets = cfg["targets"]
if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env}\n"); sys.exit(2)


def _git_clean(rel):
    r = subprocess.run(["git", "-C", str(env), "diff", "--quiet", "--", rel],
                       capture_output=True)
    return r.returncode == 0


origs = {}
for t in targets:
    target = env / t["target_rel"]
    orig = target.with_suffix(target.suffix + ".orig")
    if not orig.exists():
        if not _git_clean(t["target_rel"]):
            gold = env / "_gold.patch"
            applied_gold = gold.exists() and subprocess.run(
                ["git", "-C", str(env), "apply", "--reverse", "--check",
                 str(gold)], capture_output=True).returncode == 0
            if not applied_gold:
                sys.stderr.write(
                    f"run_oracle: {t['target_rel']} is modified but does not "
                    f"match the gold-patched state; refusing to snapshot. "
                    f"Rebuild the env before running.\n")
                sys.exit(2)
        shutil.copy2(target, orig)
    origs[t["target_rel"]] = orig

rc = 2
try:
    oracles = []
    for t in targets:
        target = env / t["target_rel"]
        shutil.copy2(origs[t["target_rel"]], target)
        cands = sorted(HERE.rglob(t["source_basename"]))
        if not cands:
            sys.stderr.write(f"run_oracle: no regenerated "
                             f"{t['source_basename']} found\n")
            sys.exit(2)
        shutil.copy2(cands[0], target)
        oracles.append(str(env / t["oracle_rel"]))
    cp = subprocess.run([str(venv_py), "-m", "pytest", *oracles, "-q"],
                        capture_output=True, text=True)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    for rel, orig in origs.items():
        shutil.copy2(orig, env / rel)
sys.exit(rc)
