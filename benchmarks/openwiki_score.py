"""Score OpenWiki's documentation for a fixture through the roundtrip benchmark.
Usage: uv run python benchmarks/openwiki_score.py <fixture_dir> <agent_score>"""
import os, sys, shutil, subprocess, re
from pathlib import Path

FIXTURE = Path(sys.argv[1])
AGENT_SCORE = sys.argv[2] if len(sys.argv) > 2 else "?"
MODEL = os.environ.get("COUNDETRIP_MODEL", "gemini-3.5-flash")

ow_dir = FIXTURE / "openwiki"
docs = sorted(ow_dir.rglob("*.md"))
description = "\n\n".join(d.read_text(encoding="utf-8") for d in docs if d.is_file())
if not description.strip():
    print("ERROR: no OpenWiki docs under", ow_dir); sys.exit(1)
print(f"[{FIXTURE.name}] OpenWiki desc: {len(description.split())} words, {len(docs)} file(s)")

RUN_DIR = Path(f"runs/openwiki_{FIXTURE.name}")
if RUN_DIR.exists(): shutil.rmtree(RUN_DIR)
RUN_DIR.mkdir(parents=True)
desc_path = RUN_DIR / "description.md"; desc_path.write_text(description, encoding="utf-8")
workspace = RUN_DIR / "workspace"; generated = RUN_DIR / "generated"

SRC_DIRS = {"src", "sympy"}
TEST_MARKERS = {"tests", "test"}
workspace.mkdir(parents=True)
for f in FIXTURE.rglob("*"):
    if not f.is_file(): continue
    if "openwiki" in f.parts: continue
    rel = f.relative_to(FIXTURE); parts = rel.parts
    if parts and parts[0] in SRC_DIRS: continue
    if any(p in TEST_MARKERS for p in parts): continue
    dest = workspace / rel; dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, dest)
generated.mkdir(parents=True)

env = dict(os.environ)
env.update({"COUNDETRIP_STAGE":"regenerate","COUNDETRIP_DESCRIPTION":str(desc_path),
            "COUNDETRIP_WORKSPACE":str(workspace),"COUNDETRIP_GENERATED":str(generated),
            "COUNDETRIP_MODEL":MODEL})
print(f"regenerating with {MODEL}...")
r = subprocess.run([sys.executable,"-m","coundetrip.llm_agent"], env=env, capture_output=True, text=True)
print("regenerate rc:", r.returncode)
if r.returncode != 0:
    print(r.stderr[-800:]); sys.exit(1)

for t in FIXTURE.rglob("test_*.py"):
    if "openwiki" in t.parts: continue
    rel = t.relative_to(FIXTURE); dest = generated / rel
    dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(t, dest)

test_r = subprocess.run([sys.executable,"-m","pytest","-q"], cwd=generated, capture_output=True, text=True)
out = test_r.stdout + test_r.stderr
print(out[-1200:])
def grab(pat):
    m = re.search(pat, out); return int(m.group(1)) if m else 0
passed, failed, errors = grab(r"(\d+) passed"), grab(r"(\d+) failed"), grab(r"(\d+) error")
total = passed + failed + errors
line = f"=== {FIXTURE.name}: OpenWiki {passed}/{total}"
if total: line += f" = {passed/total:.2f}"
line += f"  vs agent {AGENT_SCORE} ==="
print("\n" + line)
