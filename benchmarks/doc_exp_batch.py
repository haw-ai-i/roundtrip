"""Point-2 stability + generality: novel codebases, N repeats, A vs B.
Fixed extractor: cut only on real description headers, never code comments."""
import sys, subprocess, re
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

AGENT = "gemini-2.5-flash-lite"
N = 3

CASES = [
    ("policyengine", "novel2", "policyengine.py",
     "Add a method resolve(self, principal, action) to PolicyEngine that returns the "
     "deciding Rule object (or None). It must apply the module's decision contract "
     "regardless of the order rules were passed in."),
    ("scheduler", "cb2", "scheduler.py",
     "Add a method schedule(self) to RetryPolicy returning the list of delays for "
     "attempts 1 through max_attempts, applying the module's delay contract."),
    ("ledger", "cb3", "ledger.py",
     "Add a method balance(self) to Ledger that computes the correct balance per the "
     "module's balance contract."),
]

SYS = ("You are a coding agent. Implement the requested change. Output ONLY valid "
       "Python (no markdown, no prose after code). Format:\n=== {fname} ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    body = next(iter(files.values())) if files else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
        body = m.group(1) if m else reply
    out, started = [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith(("from ","import ","class ","def ")): started = True
        # cut ONLY on real description markdown headers, never code comments
        if started and (s.startswith("## ") or s.startswith("Documentation for") or
                        s.startswith("# ledger module") or s.startswith("# scheduler module") or
                        s.startswith("# policyengine module")):
            break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"

def one(folder, fname, task, code, desc, with_desc):
    ctx = f"=== {fname} ===\n{code}\n\n"
    if with_desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {task}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS.format(fname=fname), user=ctx))
    d = Path("benchmarks")/folder/("out_"+("B" if with_desc else "A"))
    d.mkdir(exist_ok=True); (d/fname).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(Path("benchmarks")/folder/"oracle.py"), str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

print(f"Agent: {AGENT}, N={N} per condition\n")
for name, folder, fname, task in CASES:
    base = Path("benchmarks")/folder
    code = (base/fname).read_text(); desc = (base/"description.md").read_text()
    aP = sum(one(folder,fname,task,code,desc,False) for _ in range(N))
    bP = sum(one(folder,fname,task,code,desc,True) for _ in range(N))
    print(f"{name:14s}  A(no desc): {aP}/{N}   B(with desc): {bP}/{N}")
