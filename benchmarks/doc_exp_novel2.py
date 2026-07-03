"""Point-2, contract only in description. Robust extraction strips trailing
markdown that weak models paste into the file."""
import sys, subprocess, re
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

NOVEL = Path("benchmarks/novel2")
CODE = (NOVEL/"policyengine.py").read_text()
DESC = (NOVEL/"description.md").read_text()
AGENT = "gemini-2.5-flash-lite"

TASK = ("Add a method resolve(self, principal, action) to PolicyEngine that returns "
        "the deciding Rule object (or None if none matches). It must apply the "
        "module's decision contract regardless of the order rules were passed in.")

ORACLE = '''
import sys; sys.path.insert(0, %r)
from policyengine import Rule, PolicyEngine
rules = [Rule(5,'allow','*','read'), Rule(10,'allow','alice','*'), Rule(10,'deny','alice','delete')]
e = PolicyEngine(rules)
d = e.resolve('alice','delete');  assert d is not None and d.effect=='deny' and d.priority==10, f"deny-override failed: {d}"
d2 = e.resolve('bob','read');     assert d2 is not None and d2.effect=='allow' and d2.priority==5, f"got {d2}"
d3 = e.resolve('bob','delete');   assert d3 is None, f"expected None, got {d3}"
print("ORACLE_PASS")
'''

SYS = ("You are a coding agent. Implement the requested change. Output ONLY valid "
       "Python (no markdown, no prose after the code). Format:\n=== policyengine.py ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    body = next(iter(files.values())) if files else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
        body = m.group(1) if m else reply
    # strip trailing pasted markdown/docs after code starts
    out, started = [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith(("from ","import ","class ","def ")): started = True
        if started and (s.startswith(("Documentation for","## ","# policyengine")) or
                        s == "Resolves access-control decisions from rules."):
            break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"

def run(with_desc, tag):
    ctx = f"=== policyengine.py ===\n{CODE}\n\n"
    if with_desc: ctx += f"Documentation for this module:\n{DESC}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    outdir = NOVEL/f"out_{tag}"; outdir.mkdir(exist_ok=True)
    (outdir/"policyengine.py").write_text(src)
    if not src.strip(): print(f"  {tag}: EMPTY"); return None
    r = subprocess.run([sys.executable, "-c", ORACLE % str(outdir)], capture_output=True, text=True)
    ok = "ORACLE_PASS" in r.stdout
    print(f"  {tag}: {'PASS' if ok else 'FAIL'}  {(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '')[:75]}")
    return ok

print("novel2: contract only in description; robust extraction")
print("Agent:", AGENT, "\n")
a = run(False, "A_no_desc")
b = run(True, "B_with_desc")
print(f"\nRESULT: A(no desc)={a}  B(with desc)={b}")
print("*** EFFECT DEMONSTRATED ***" if (a is False and b is True) else "no clean separation - inspect benchmarks/novel2/out_*/")
