"""Stage 2 OpenWiki comparison on novel2 (contract only in description).
A: no doc | B: our description | C: OpenWiki docs"""
import sys, subprocess, re
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks
NOVEL = Path("benchmarks/novel2")
OW = Path("benchmarks/novel2_openwiki/openwiki")
CODE = (NOVEL/"policyengine.py").read_text()
DESC = (NOVEL/"description.md").read_text()
OW_DOCS = "\n\n".join(p.read_text() for p in sorted(OW.glob("*.md")))
AGENT = "gemini-2.5-flash-lite"
print(f"our desc has deny-override: {'deny-override' in DESC.lower() or 'deny is evaluated before' in DESC.lower()}")
print(f"openwiki has deny-override: {'deny-override' in OW_DOCS.lower() or 'deny is evaluated before' in OW_DOCS.lower()}")
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
    out, started = [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith(("from ","import ","class ","def ")): started = True
        if started and (s.startswith(("Documentation for","## ","# policyengine")) or
                        s == "Resolves access-control decisions from rules."):
            break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"
def run(doc, tag):
    ctx = f"=== policyengine.py ===\n{CODE}\n\n"
    if doc: ctx += f"Documentation for this module:\n{doc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    outdir = NOVEL/f"owc_{tag}"; outdir.mkdir(exist_ok=True)
    (outdir/"policyengine.py").write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, "-c", ORACLE % str(outdir)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout
N=4
a = sum(run("", f"A{i}") for i in range(N))
b = sum(run(DESC, f"B{i}") for i in range(N))
c = sum(run(OW_DOCS, f"C{i}") for i in range(N))
print(f"\nA (no doc):          {a}/{N}")
print(f"B (our description): {b}/{N}")
print(f"C (OpenWiki docs):   {c}/{N}")
