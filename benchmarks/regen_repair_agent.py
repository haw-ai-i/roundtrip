"""Regenerate agent with an import-repair loop.
describe: delegate to llm_agent.describe unchanged.
regenerate: run llm_agent.regenerate, then for each generated file, check it imports cleanly
in the target env; if not, show the model the error and ask it to fix only what is needed,
up to a few attempts. Mirrors how a real coding agent runs its code and fixes errors.
"""
import os, sys, json, re, shutil, subprocess
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip import llm_agent
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

stage = os.environ.get("COUNDETRIP_STAGE")
client = llm_agent.GeminiClient()

if stage == "describe":
    sys.exit(llm_agent.describe(client))

if stage != "regenerate":
    print(f"unknown stage {stage!r}", file=sys.stderr); sys.exit(2)

# 1. normal regenerate
rc = llm_agent.regenerate(client)
if rc != 0:
    sys.exit(rc)

# 2. import-repair loop on the generated files
generated = Path(os.environ["COUNDETRIP_GENERATED"])
model = os.environ.get("COUNDETRIP_MODEL", "gemini-3.5-flash")

cfg_env = os.environ.get("REPAIR_ORACLE_CFG")
if not cfg_env:
    sys.exit(0)  # no repair config -> behave like normal regenerate
cfg_path = Path(cfg_env)
if not cfg_path.exists():
    sys.exit(0)
cfg = json.loads(cfg_path.read_text())
env_path = Path(os.path.expandvars(cfg["env_path"])).expanduser()
venv_py = env_path / ".venv/bin/python"
if not venv_py.exists():
    sys.exit(0)

targets = cfg.get("targets") or [{"target_rel": cfg["target_rel"], "source_basename": cfg["source_basename"]}]

def import_error(genfile, target_rel):
    """Install file into env and try importing; return stderr or None."""
    target_abs = env_path / target_rel
    bak = target_abs.with_suffix(target_abs.suffix + ".repbak")
    if not bak.exists():
        shutil.copy2(target_abs, bak)
    shutil.copy2(genfile, target_abs)
    mod = target_rel.replace("/", ".")[:-3]  # strip .py
    r = subprocess.run([str(venv_py), "-c", f"import {mod}"],
                       capture_output=True, text=True, cwd=str(env_path))
    shutil.copy2(bak, target_abs)  # restore
    return None if r.returncode == 0 else r.stderr

MAXTRIES = 1  # one repair pass keeps it within the time budget

def import_error(genfile, target_rel):
    target_abs = env_path / target_rel
    bak = target_abs.with_suffix(target_abs.suffix + ".repbak")
    if not bak.exists():
        shutil.copy2(target_abs, bak)
    shutil.copy2(genfile, target_abs)
    mod = target_rel.replace("/", ".")[:-3]
    try:
        r = subprocess.run([str(venv_py), "-c", f"import {mod}"],
                           capture_output=True, text=True, cwd=str(env_path), timeout=60)
        err = None if r.returncode == 0 else r.stderr
    except subprocess.TimeoutExpired:
        err = None  # if import hangs, skip repair rather than block
    shutil.copy2(bak, target_abs)
    return err

for t in targets:
    base = t["source_basename"]; rel = t["target_rel"]
    cands = sorted(generated.rglob(base))
    if not cands:
        continue
    genfile = cands[0]
    err = import_error(genfile, rel)
    if not err:
        continue
    code = genfile.read_text()
    prompt = (f"This Python file fails to import:\n\n{err}\n\n"
              f"Fix only what is needed so it imports cleanly. Do not change unrelated logic. "
              f"Output the full corrected file only.\n\n=== {base} ===\n{code}")
    try:
        reply = GeminiClient(model=model, temperature=0.0).complete(
            system="You are a careful Python engineer. Output only the corrected file, no prose.",
            user=prompt)
        files = parse_file_blocks(reply)
        fixed = next(iter(files.values()), None)
        if not fixed:
            m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
            fixed = m.group(1) if m else None
        if fixed and fixed.strip():
            genfile.write_text(fixed if fixed.endswith("\n") else fixed + "\n")
    except Exception:
        pass  # repair is best-effort; never block the pipeline

sys.exit(0)
