"""Score OpenWiki's documentation through the roundtrip benchmark, to compare against
the agent's own descriptions. We take the documentation OpenWiki generated for a fixture,
use it as the description, run the normal regenerate + evaluate stages, and report fidelity."""
import os, sys, shutil, subprocess
from pathlib import Path

# --- config ---
FIXTURE = Path("benchmarks/fixtures/swe_saferepr")
OPENWIKI_DOCS = [
    FIXTURE / "openwiki" / "quickstart.md",
    FIXTURE / "openwiki" / "saferepr-module.md",
]
RUN_DIR = Path("runs/openwiki_saferepr")
MODEL = os.environ.get("COUNDETRIP_MODEL", "gemini-3.5-flash")

# --- build the OpenWiki description (concatenate its docs) ---
desc_parts = []
for d in OPENWIKI_DOCS:
    if d.exists():
        desc_parts.append(d.read_text(encoding="utf-8"))
description = "\n\n".join(desc_parts)
if not description.strip():
    print("ERROR: no OpenWiki docs found at", [str(d) for d in OPENWIKI_DOCS]); sys.exit(1)
print(f"OpenWiki description: {len(description.split())} words from {len(desc_parts)} file(s)")

# --- set up run dir, description, workspace (scaffold only), generated ---
if RUN_DIR.exists(): shutil.rmtree(RUN_DIR)
RUN_DIR.mkdir(parents=True)
desc_path = RUN_DIR / "description.md"
desc_path.write_text(description, encoding="utf-8")
workspace = RUN_DIR / "workspace"
generated = RUN_DIR / "generated"

# scaffold: copy the fixture's non-source, non-test files (pyproject, etc.) as the empty scaffold
# We copy pyproject/config but NOT src (that's what must be regenerated) and NOT tests.
workspace.mkdir(parents=True)
for f in FIXTURE.rglob("*"):
    if f.is_file() and "openwiki" not in f.parts:
        rel = f.relative_to(FIXTURE)
        parts = rel.parts
        # skip the source file(s) under src/ and the tests/ (these are the oracle / to-be-regenerated)
        if parts and parts[0] in ("src", "tests"): 
            continue
        dest = workspace / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)

generated.mkdir(parents=True)

# --- run regenerate using your real llm_agent ---
env = dict(os.environ)
env["COUNDETRIP_STAGE"] = "regenerate"
env["COUNDETRIP_DESCRIPTION"] = str(desc_path)
env["COUNDETRIP_WORKSPACE"] = str(workspace)
env["COUNDETRIP_GENERATED"] = str(generated)
env["COUNDETRIP_MODEL"] = MODEL

print(f"regenerating with {MODEL} from OpenWiki description...")
r = subprocess.run([sys.executable, "-m", "coundetrip.llm_agent"],
                   env=env, cwd=".", capture_output=True, text=True)
print("regenerate rc:", r.returncode)
if r.returncode != 0:
    print("STDERR:", r.stderr[-1000:]); sys.exit(1)

# --- copy the original tests into generated (they are the oracle) ---
for t in (FIXTURE / "tests").rglob("*.py"):
    rel = t.relative_to(FIXTURE)
    dest = generated / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(t, dest)

# --- run the tests ---
print("running tests on regenerated code...")
test_r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/"],
                        cwd=generated, capture_output=True, text=True)
out = test_r.stdout + test_r.stderr
print(out[-1500:])

# --- parse fidelity ---
import re
m = re.search(r"(\d+) passed", out)
passed = int(m.group(1)) if m else 0
mf = re.search(r"(\d+) failed", out)
failed = int(mf.group(1)) if mf else 0
me = re.search(r"(\d+) error", out)
errors = int(me.group(1)) if me else 0
total = passed + failed + errors
print(f"\n=== OPENWIKI BASELINE (saferepr) ===")
print(f"passed: {passed} / {total}")
if total: print(f"fidelity: {passed/total:.2f}")
print(f"(compare to agent's 0.73 on saferepr)")
