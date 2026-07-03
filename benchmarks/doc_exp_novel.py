"""Point-2 on a NOVEL codebase flash-lite has never seen.
Task requires the non-obvious deny-override + priority contract.
A: code+task. B: code+task+description. Effect = A fails, B passes."""
import sys, os, subprocess, re
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

NOVEL = Path("benchmarks/novel")
CODE = (NOVEL/"policyengine.py").read_text()
DESC = (NOVEL/"description.md").read_text()
AGENT = "gemini-2.5-flash-lite"

TASK = ("Add a method explain(self, principal, action) to PolicyEngine that returns "
        "the single Rule object that DECIDES the request (the first matching rule "
        "under the engine's evaluation order), or None if no rule matches and the "
        "default-deny applies.")

ORACLE = '''
import sys; sys.path.insert(0, %r)
from policyengine import Rule, PolicyEngine
rules = [Rule(10,'allow','alice','*'), Rule(10,'deny','alice','delete'), Rule(5,'allow','*','read')]
e = PolicyEngine(rules)
d = e.explain('alice','delete');  assert d is not None and d.effect=='deny' and d.priority==10, f"got {d}"
d2 = e.explain('bob','read');     assert d2 is not None and d2.effect=='allow' and d2.priority==5, f"got {d2}"
d3 = e.explain('bob','delete');   assert d3 is None, f"expected None, got {d3}"
print("ORACLE_PASS")
'''

SYS = ("You are a coding agent. Implement the requested change. Output the full "
       "updated file:\n=== policyengine.py ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    if files: return next(iter(files.values()))
    m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
    if m: return m.group(1).strip()+"\n"
    s = reply.strip()
    return (s+"\n") if s.startswith(("from ","import ","class ",'"""',"#")) else ""

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

print("Novel codebase: policyengine (deny-override, priority-order, default-deny)")
print("Agent:", AGENT, "\n")
a = run(False, "A_no_desc")
b = run(True, "B_with_desc")
print(f"\nRESULT: A(no desc)={a}  B(with desc)={b}")
print("*** EFFECT DEMONSTRATED ***" if (a is False and b is True) else "no clean separation - inspect benchmarks/novel/out_*/")
