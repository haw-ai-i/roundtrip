"""Compactness, comprehension-only task: implementation is trivial (dict lookup),
so success depends purely on whether the description conveyed the default values.
Compares no-desc / compact / verbose. Isolates description quality from coding skill."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/settings_exp")
FNAME = "settings.py"
CODE = (BASE/FNAME).read_text()
AGENT = "gemini-2.5-flash-lite"   # weak agent; task is trivial to implement
PRO = "gemini-2.5-pro"
COMPACT = (BASE/"desc_compact.md").read_text()

vpath = BASE/"desc_verbose.md"
if vpath.exists():
    VERBOSE = vpath.read_text()
else:
    print("Generating verbose description via Pro...")
    VERBOSE = GeminiClient(model=PRO, temperature=0.0).complete(
        system=("Rewrite the following documentation as an exhaustive, verbose natural-language "
                "description. Explain the settings module at length, narrating the purpose of each "
                "default value in full sentences. You MUST preserve every exact default value: "
                "timeout 30, retries 5, cache_size 256, log_level warning, batch_size 64, and that "
                "unlisted keys default to None. Be wordy but keep all values exact. No code."),
        user=COMPACT)
    vpath.write_text(VERBOSE)

print(f"COMPACT: {len(COMPACT.split())} words | VERBOSE: {len(VERBOSE.split())} words | {len(VERBOSE.split())/len(COMPACT.split()):.1f}x\n")

TASK = ("Implement the _default(self, key) method of Settings so that get(key) returns "
        "the project's documented default value for that key (and None for keys with no "
        "documented default).")
ORACLE = (BASE/"oracle.py")
SYS = (f"You are a coding agent. Implement the change. Output ONLY valid Python:\n=== {FNAME} ===\n<contents>\n")

def extract(reply):
    fm = re.search(r"=== .*? ===\n(.*)", reply, re.DOTALL)
    body = fm.group(1) if fm else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    # keep from first code line; drop trailing fenced junk
    lines = body.splitlines()
    start = next((i for i,l in enumerate(lines) if l.strip().startswith(("from ","import ","class "))), 0)
    code = "\n".join(lines[start:])
    code = code.split("```")[0]  # cut any trailing fence
    return code.rstrip()+"\n"

def run(desc, tag, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"run_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(ORACLE), str(d)], capture_output=True, text=True)
    if "ORACLE_PASS" not in r.stdout: (d/"err.txt").write_text((r.stdout+r.stderr)[-250:])
    return "ORACLE_PASS" in r.stdout

N=8
none_ = sum(run("", "none", i) for i in range(N))
comp = sum(run(COMPACT, "compact", i) for i in range(N))
verb = sum(run(VERBOSE, "verbose", i) for i in range(N))
print(f"no desc:    {none_}/{N}")
print(f"COMPACT:    {comp}/{N}  ({len(COMPACT.split())} words)")
print(f"VERBOSE:    {verb}/{N}  ({len(VERBOSE.split())} words)")
