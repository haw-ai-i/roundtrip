"""Generic scoped oracle for external-env SWE-bench roundtrip fixtures.

Scores the instance's own test selection (FAIL_TO_PASS + PASS_TO_PASS), the way
SWE-bench defines resolution. Handles single- and multi-target fixtures: every
target file is restored from a pristine .orig backup before and after each run,
and every regenerated target is copied into the environment before scoring.
Selections arrive either as pytest node ids or as bare test names (selected
with -k against the instance's test files). Node-id selections are intersected
with what actually collects in this environment; missing FAIL_TO_PASS ids
invalidate the run, missing PASS_TO_PASS ids are dropped and reported.
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
target_rels = cfg.get("target_rels") or [cfg["target_rel"]]
selection = cfg.get("test_selection") or []
oracle_files = cfg.get("oracle_files") or ([cfg["oracle_rel"]] if cfg.get("oracle_rel") else [])

if not venv_py.exists():
    sys.stderr.write(f"run_oracle: env not found at {env} (run setup_swebench_env.py)\n")
    sys.exit(2)

targets = [env / rel for rel in target_rels]

def restore_all():
    for t in targets:
        o = t.with_suffix(t.suffix + ".orig")
        if o.exists():
            shutil.copy2(o, t)

for t in targets:
    o = t.with_suffix(t.suffix + ".orig")
    if not o.exists():
        shutil.copy2(t, o)
restore_all()

missing = []
for rel, t in zip(target_rels, targets):
    exact = HERE / rel
    if exact.exists():
        shutil.copy2(exact, t)
        continue
    by_name = sorted(pth for pth in HERE.rglob(t.name) if "scaffold" not in pth.parts)
    if by_name:
        shutil.copy2(by_name[0], t)
    else:
        missing.append(rel)
if missing:
    sys.stderr.write(f"run_oracle: regenerated file(s) not found: {missing}\n")
    restore_all()
    sys.exit(2)

runner = cfg.get("runner", "pytest")

if runner == "django":
    # django uses its own test runner (tests/runtests.py) and labels of the form
    # "method (module.Class)" -> convert to "module.Class.method". Scope to the
    # instance's own F2P+P2P; drop P2P that fail on gold; F2P must all run.
    import re as _re
    def to_label(t):
        m = _re.match(r"(\w+)\s+\(([\w.]+)\)", t)
        return f"{m.group(2)}.{m.group(1)}" if m else t
    def valid(t):
        # SWE-bench sometimes stores a test's docstring instead of its label;
        # keep only strings matching "method (module.Class)".
        return bool(_re.match(r"\w+\s+\([\w.]+\)$", t))
    labels = [to_label(t) for t in selection if valid(t)]
    f2p_raw = cfg.get("fail_to_pass") or []
    f2p_valid = [t for t in f2p_raw if valid(t)]
    f2p_labels = {to_label(t) for t in f2p_valid}
    # If any F2P entry was a docstring (unmatchable), we cannot verify it -> skip fixture.
    if len(f2p_valid) != len(f2p_raw):
        sys.stderr.write("run_oracle: some FAIL_TO_PASS entries are docstrings, not labels; cannot verify\n")
        restore_all()
        sys.exit(2)
    tests_dir = env / "tests"
    cp = subprocess.run(
        [str(venv_py), "runtests.py", *labels, "--verbosity", "1", "--noinput"],
        cwd=str(tests_dir), capture_output=True, text=True, timeout=1800)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    restore_all()
    sys.exit(cp.returncode)

node_ids = [t for t in selection if "::" in t]
bare = [t for t in selection if "::" not in t]
if node_ids and not bare:
    files = sorted({t.split("::")[0] for t in node_ids})
    col = subprocess.run([str(venv_py), "-m", "pytest", "--collect-only", "-q", *files],
                         cwd=str(env), capture_output=True, text=True, timeout=600)
    existing = {l.strip() for l in col.stdout.splitlines() if "::" in l}
    f2p = set(cfg.get("fail_to_pass") or [])
    missing_f2p = [t for t in node_ids if t in f2p and t not in existing]
    if missing_f2p:
        sys.stderr.write(f"run_oracle: FAIL_TO_PASS test(s) not collectable: {missing_f2p[:5]}\n")
        restore_all()
        sys.exit(2)
    kept = [t for t in node_ids if t in existing]
    dropped = len(node_ids) - len(kept)
    if dropped:
        sys.stderr.write(f"run_oracle: dropped {dropped} PASS_TO_PASS id(s) not present in this env\n")
    args = kept
elif bare:
    # Resolve bare test names to exact node ids: -k matches substrings, which
    # both re-includes dropped names and can over-select. Collection gives the
    # exact ids (with all parametrizations) for precisely the named tests.
    files = [str(env / f) for f in oracle_files]
    col = subprocess.run([str(venv_py), "-m", "pytest", "--collect-only", "-q", *files],
                         cwd=str(env), capture_output=True, text=True, timeout=600)
    ids = [l.strip() for l in col.stdout.splitlines() if "::" in l]
    base = lambda i: i.split("::")[-1].split("[")[0]
    want = set(bare)
    matched = [i for i in ids if base(i) in want]
    found_names = {base(i) for i in matched}
    f2p_names = set(cfg.get("fail_to_pass") or [])
    missing_f2p = sorted(n for n in want & f2p_names if n not in found_names)
    if missing_f2p:
        sys.stderr.write(f"run_oracle: FAIL_TO_PASS test(s) not collectable: {missing_f2p[:5]}\n")
        restore_all()
        sys.exit(2)
    dropped = sorted(want - found_names)
    if dropped:
        sys.stderr.write(f"run_oracle: dropped {len(dropped)} name(s) not present in this env\n")
    args = matched
else:
    args = [str(env / f) for f in oracle_files]

try:
    cp = subprocess.run([str(venv_py), "-m", "pytest", *args, "-q", "--tb=no"],
                        cwd=str(env), capture_output=True, text=True, timeout=900)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    restore_all()
sys.exit(rc)
