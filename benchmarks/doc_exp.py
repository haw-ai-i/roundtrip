"""Documentation experiment: does the NL description help a WEAK agent (flash-lite)?
A: code+task. B: code+task+description. Behavioral oracle. Effect = A fails, B passes.
Robust extraction: handles both === path === and ```python fences (weak models
often ignore the format instruction)."""
import sys, os, subprocess, shutil, re
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

REL = "sympy/sets/contains.py"
ENV = Path.home()/"Desktop/coundetrip/swebench_envs/sympy__sympy-23950"
CODE = Path(f"benchmarks/fixtures/swe_sympy_contains/{REL}").read_text()
DESC = Path("runs/drift_1/swe_sympy_contains/description.md").read_text()
AGENT = "gemini-2.5-flash-lite"

TASK = ("Add a classmethod `simplify_result(cls, x, s)` to Contains that returns "
        "the string 'member' if x is definitely in s, 'not-member' if definitely "
        "not, and 'unknown' if membership cannot be determined. Reuse the same "
        "decision logic that Contains.eval uses (which returns S.true, S.false, or "
        "None respectively).")

ORACLE = '''
from sympy import S, Integer, Symbol, Contains
i = Symbol('i', integer=True)
assert Contains.simplify_result(Integer(2), S.Integers) == 'member', 'definite member'
assert Contains.simplify_result(Integer(2), S.Naturals) == 'member', 'nat member'
r = Contains.simplify_result(i, S.Naturals)
assert r == 'unknown', f'expected unknown, got {r!r}'
print("ORACLE_PASS")
'''

SYS = ("You are a coding agent. Implement the requested change. Output the full "
       "updated file:\n=== <path> ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    if files:
        return files.get(REL) or next(iter(files.values()))
    m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
    if m: return m.group(1).strip() + "\n"
    s = reply.strip()
    return (s + "\n") if s.startswith(("from ","import ","class ",'"""',"#")) else ""

def run(with_desc, tag):
    ctx = f"=== {REL} ===\n{CODE}\n\n"
    if with_desc: ctx += f"Documentation for this module:\n{DESC}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    Path(f"runs/docexp_{tag}.py").write_text(src)
    if not src.strip():
        print(f"  {tag}: EMPTY output"); return None
    target = ENV/REL
    bak = target.with_suffix(".py.docbak")
    if not bak.exists(): shutil.copy2(target, bak)
    target.write_text(src)
    r = subprocess.run([str(ENV/".venv/bin/python"), "-c", ORACLE], capture_output=True, text=True)
    shutil.copy2(bak, target)
    ok = "ORACLE_PASS" in r.stdout
    err = (r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "")[:75]
    print(f"  {tag}: {'PASS' if ok else 'FAIL'}  {err}")
    return ok

print("Task: simplify_result (leans on eval true/false/None contract)")
print("Agent:", AGENT, "\n")
a = run(False, "A_no_desc")
b = run(True, "B_with_desc")
print(f"\nRESULT: A(no desc)={a}  B(with desc)={b}")
print("*** EFFECT DEMONSTRATED ***" if (a is False and b is True) else "no clean separation - inspect runs/docexp_*.py")
