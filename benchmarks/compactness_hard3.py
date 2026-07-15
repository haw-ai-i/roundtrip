"""Three-way context-rot test to remove the missing-keys confound.
- compact:       keys listed verbatim, tight
- verbose_unfair: keys only DESCRIBED in prose (no literal key strings)
- verbose_fair:   literal key strings PRESENT but buried in long prose with filler
If verbose_fair fails too, that is genuine burial-induced degradation (real context rot).
If verbose_fair passes but verbose_unfair fails, the earlier collapse was the missing-keys
confound, not context length."""
import sys, subprocess, re, shutil, json, urllib.request
from pathlib import Path

BASE = Path("benchmarks/settings_hard")
FNAME = "settings.py"
CODE = (BASE/FNAME).read_text()
COMPACT = (BASE/"desc_compact.md").read_text()
UNFAIR = (BASE/"desc_verbose.md").read_text()
FAIR = (BASE/"desc_verbose_fair.md").read_text()

MODE = sys.argv[1] if len(sys.argv) > 1 else "ollama"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemma3:4b"

TASK = ("Implement the _default(self, key) method of Settings so that get(key) returns the "
        "documented default value for that key, and None for keys with no documented default.")
SYS = (f"You are a coding agent. Implement the change. Output the COMPLETE file including the "
       f"full class. Output ONLY valid Python:\n=== {FNAME} ===\n<contents>\n")

def call_ollama(system, user):
    body = json.dumps({"model": MODEL, "prompt": f"{system}\n\n{user}", "stream": False,
                       "options": {"temperature": 0.0, "num_predict": 3072}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1200) as r:
        return json.loads(r.read())["response"]

def call_api(system, user):
    sys.path.insert(0, "src")
    from coundetrip.llm_agent import GeminiClient
    return GeminiClient(model=MODEL, temperature=0.0).complete(system=system, user=user)

def gen(system, user):
    return call_ollama(system, user) if MODE == "ollama" else call_api(system, user)

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
        if st.startswith(("Documentation for","```","Here is","Of course","The settings")): break
        out.append(l)
    return "\n".join(out).rstrip()+"\n"

def run(desc, tag, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(gen(SYS, ctx))
    d = BASE/f"h3_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if "class Settings" not in src: return False
    r = subprocess.run([sys.executable, str(BASE/"oracle.py"), str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

N = int(sys.argv[3]) if len(sys.argv) > 3 else 8
print(f"mode={MODE} model={MODEL} N={N}")
print(f"compact {len(COMPACT.split())}w | unfair {len(UNFAIR.split())}w | fair {len(FAIR.split())}w\n")
comp = sum(run(COMPACT, "compact", i) for i in range(N))
unf  = sum(run(UNFAIR, "unfair", i) for i in range(N))
fair = sum(run(FAIR, "fair", i) for i in range(N))
print(f"COMPACT:        {comp}/{N}")
print(f"VERBOSE unfair: {unf}/{N}   (keys only described)")
print(f"VERBOSE fair:   {fair}/{N}   (keys present but buried)")
print()
if fair < comp and unf < comp:
    print(">>> Even the FAIR verbose fails: genuine burial-induced context rot")
elif fair >= comp and unf < comp:
    print(">>> Fair passes, unfair fails: earlier collapse was the missing-keys confound")
else:
    print(">>> mixed / no clear gap")
