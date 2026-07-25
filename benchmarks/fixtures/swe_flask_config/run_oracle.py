"""Oracle wrapper for the flask-4992 roundtrip fixture (env-safe)."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _flask_env():
    p = HERE / "flask_env_path.txt"
    if p.is_file():
        raw = p.read_text(encoding="utf-8").strip()
        if raw:
            return Path(os.path.expandvars(raw)).expanduser()
    return Path(os.environ["HOME"]) / "Desktop/coundetrip/swebench_envs/flask-4992"


FLASK_ENV = _flask_env()
VENV_PY = FLASK_ENV / ".venv/bin/python"
TARGET = FLASK_ENV / "src/flask/config.py"
ORACLE = FLASK_ENV / "tests/test_config.py"
candidates = sorted(HERE.rglob("config.py"))
if not candidates:
    sys.stderr.write("run_oracle: no regenerated config.py found in generated tree\n")
    sys.exit(2)
generated_cfg = candidates[0]
if not VENV_PY.exists():
    sys.stderr.write(f"run_oracle: flask env not found at {FLASK_ENV} (run the setup script)\n")
    sys.exit(2)
ORIG = TARGET.with_suffix(TARGET.suffix + ".orig")
if not ORIG.exists():
    shutil.copy2(TARGET, ORIG)
shutil.copy2(ORIG, TARGET)
shutil.copy2(generated_cfg, TARGET)
try:
    cp = subprocess.run(
        [str(VENV_PY), "-m", "pytest", str(ORACLE), "-q"],
        capture_output=True, text=True,
    )
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc = cp.returncode
finally:
    shutil.copy2(ORIG, TARGET)
sys.exit(rc)
