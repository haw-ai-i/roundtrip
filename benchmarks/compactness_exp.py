"""Compactness experiment: compact vs verbose complete description.
Robust extractor strips prose flash-lite pastes into the code file."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/novel2")
FNAME = "policyengine.py"
CODE = (BASE/FNAME).read_text()
WEAK = "gemini-2.5-flash"
PRO = "gemini-2.5-pro"
COMPACT = (BASE/"description.md").read_text()

# reuse verbose if already generated, else make it
vpath = BASE/"description_verbose.md"
if vpath.exists():
    VERBOSE = vpath.read_text()
    print("reusing existing verbose description")
else:
    print("Generating verbose description via Pro...")
    VERBOSE = GeminiClient(model=PRO, temperature=0.0).complete(
        system=("Rewrite this module as an exhaustive natural-language description. Describe "
                "every function and effectively every line in prose. Include the full decision "
                "contract: highest-priority first, at equal priority deny before allow, first "
                "match decides, no match means deny. Verbose and complete. No code."),
        user=CODE)
    vpath.write_text(VERBOSE)

print(f"COMPACT: {len(COMPACT.split())} words | VERBOSE: {len(VERBOSE.split())} words | {len(VERBOSE.split())/len(COMPACT.split()):.1f}x\n")

TASK = ("Add a method resolve(self, principal, action) to PolicyEngine that returns "
        "the deciding Rule object (or None). It must apply the module's decision "
        "contract regardless of the order rules were passed in.")
ORACLE = (BASE/"oracle.py")
SYS = (f"You are a coding agent. Implement the change. Output ONLY valid Python, no prose:\n=== {FNAME} ===\n<contents>\n")

def extract(reply):
    fm = re.search(r"=== .*? ===\n(.*)", reply, re.DOTALL)
    body = fm.group(1) if fm else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    out, started = [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith(("from ","import ","class ","def ","@")): started = True
        if started:
            is_prose = bool(re.match(r"^[A-Z][a-z]+ [a-z].*\.$", s)) and not ln.startswith((" ","\t"))
            is_md = s.startswith(("## ","# ","Documentation","Here is","Of course"))
            if is_prose or is_md: break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"

def run(desc, tag, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=WEAK, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"cmp_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(ORACLE), str(d)], capture_output=True, text=True)
    if "ORACLE_PASS" not in r.stdout:
        (d/"err.txt").write_text((r.stdout+r.stderr)[-300:])
    return "ORACLE_PASS" in r.stdout

N=8
none_ = sum(run("", "none", i) for i in range(N))
comp = sum(run(COMPACT, "compact", i) for i in range(N))
verb = sum(run(VERBOSE, "verbose", i) for i in range(N))
print(f"no desc:      {none_}/{N}")
print(f"COMPACT:      {comp}/{N}  ({len(COMPACT.split())} words)")
print(f"VERBOSE:      {verb}/{N}  ({len(VERBOSE.split())} words)")
