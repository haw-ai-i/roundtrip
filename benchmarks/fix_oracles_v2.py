"""Env-safe oracle: snapshot the gold-patched target once (now, while envs are
verified good), and always restore it after the test run in a finally block.
Patches the single-file oracles in place."""
import sys
from pathlib import Path

OLD = """orig = target.with_suffix(target.suffix + ".orig")
if not orig.exists():
    shutil.copy2(target, orig)
shutil.copy2(orig, target)"""

NEW = """orig = target.with_suffix(target.suffix + ".orig")
if not orig.exists():
    shutil.copy2(target, orig)
shutil.copy2(orig, target)"""

OLD_TAIL = """cp = subprocess.run([str(venv_py), "-m", "pytest", str(oracle), "-q"],
                    capture_output=True, text=True)
sys.stdout.write(cp.stdout)
sys.stderr.write(cp.stderr)
sys.exit(cp.returncode)"""

NEW_TAIL = """try:
    cp = subprocess.run([str(venv_py), "-m", "pytest", str(oracle), "-q"],
                        capture_output=True, text=True)
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    shutil.copy2(orig, target)
sys.exit(rc)"""

for f in sorted(Path("benchmarks/fixtures").glob("*/run_oracle.py")):
    s = f.read_text()
    if "targets" in s or OLD_TAIL not in s:
        print(f"skip    {f.parent.name}")
        continue
    f.write_text(s.replace(OLD_TAIL, NEW_TAIL))
    print(f"patched {f.parent.name}")
