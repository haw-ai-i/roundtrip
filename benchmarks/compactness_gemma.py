"""Context-rot test: does the verbose description hurt on a weaker model (Gemma)?
Same comprehension task and descriptions as the flash-lite compactness run, but the
agent is Gemma. Prediction: verbose falls behind compact (facts buried in filler),
whereas on flash-lite they were equal."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient

BASE = Path("benchmarks/settings_exp")
FNAME = "settings.py"
CODE = (BASE/FNAME).read_text()
COMPACT = (BASE/"desc_compact.md").read_text()
VERBOSE = (BASE/"desc_verbose.md").read_text()
AGENT = "gemma-3-4b-it"

TASK = ("Implement the _default(self, key) method of Settings so that get(key) returns "
        "the project's documented default value for that key, and None for keys with no "
        "documented default.")
SYS = (f"You are a coding agent. Implement the change. Output ONLY valid Python:\n=== {FNAME} ===\n<contents>\n")

def extract(reply):
    fm = re.search(r"=== .*? ===\n(.*)", reply, re.DOTALL)
    body = fm.group(1) if fm else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    lines = body.splitlines()
    start = next((i for i,l in enumerate(lines) if l.strip().startswith(("from ","import ","class "))), 0)
    out = []
    for l in lines[start:]:
        st = l.strip()
        if st.startswith(("Documentation for","```","## ","Here is","Of course")): break
        out.append(l)
    return "\n".join(out).rstrip()+"\n"

def run(desc, tag, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"gemma_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(BASE/"oracle.py"), str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

N=8
print(f"agent: {AGENT}  |  compact {len(COMPACT.split())}w  verbose {len(VERBOSE.split())}w\n")
none_ = sum(run("", "none", i) for i in range(N))
comp = sum(run(COMPACT, "compact", i) for i in range(N))
verb = sum(run(VERBOSE, "verbose", i) for i in range(N))
print(f"no desc:   {none_}/{N}")
print(f"COMPACT:   {comp}/{N}")
print(f"VERBOSE:   {verb}/{N}")
print()
if verb < comp: print(">>> CONTEXT ROT: verbose underperforms compact on the weaker model")
elif comp == verb: print(">>> no gap: verbose = compact even on Gemma")
else: print(">>> verbose >= compact (unexpected)")
