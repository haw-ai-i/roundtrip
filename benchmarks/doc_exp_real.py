"""Real-code point-2: tensorproduct (423 lines, real sympy). Task leans on the
non-obvious scalar-extraction contract in flatten/__new__. Reuses existing Pro
description. A: code+task. B: code+task+description. N=2."""
import sys, subprocess, re, shutil, os
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

REL = "sympy/physics/quantum/tensorproduct.py"
FIX = Path("benchmarks/fixtures/swe_sympy_tensorproduct")
CODE = (FIX/REL).read_text()
DESC = Path("runs/tp_1/swe_sympy_tensorproduct/description.md").read_text()
WEAK = "gemini-2.5-flash-lite"

TASK = ("Add a module-level function scalar_factor(tp) that, given a TensorProduct "
        "(or the result of constructing one), returns a tuple (scalar, core) where "
        "scalar is the commutative coefficient factored out of the tensor product and "
        "core is the remaining TensorProduct (or scalar 1 if none was factored). It "
        "must match how TensorProduct itself separates scalar and tensor parts.")

ORACLE = '''
import sys; sys.path.insert(0, %r)
from sympy.physics.quantum.tensorproduct import TensorProduct, scalar_factor
from sympy.physics.quantum import Operator
A, B = Operator('A'), Operator('B')
sc, core = scalar_factor(TensorProduct(2*A, B))
assert sc == 2, f"scalar: {sc}"
assert core == TensorProduct(A, B), f"core: {core}"
sc2, core2 = scalar_factor(TensorProduct(A, B))
assert sc2 == 1, f"scalar2: {sc2}"
print("ORACLE_PASS")
'''

SYS = (f"You are a coding agent. Implement the change to the file. Output ONLY valid "
       f"Python:\n=== {REL} ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    body = next(iter(files.values())) if files else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    return body.rstrip()+"\n" if body else ""

def run(with_desc, i, env):
    ctx = f"=== {REL} ===\n{CODE}\n\n"
    if with_desc: ctx += f"Documentation for this module:\n{DESC}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=WEAK, temperature=0.0).complete(system=SYS, user=ctx))
    Path(f"runs/realexp_{'B' if with_desc else 'A'}_{i}.py").write_text(src)
    if not src.strip(): return False
    target = env/REL
    bak = target.with_suffix(".py.realbak")
    if not bak.exists(): shutil.copy2(target, bak)
    target.write_text(src)
    r = subprocess.run([str(env/".venv/bin/python"), "-c", ORACLE % str(env)], capture_output=True, text=True)
    shutil.copy2(bak, target)
    if "ORACLE_PASS" not in r.stdout:
        Path(f"runs/realexp_{'B' if with_desc else 'A'}_{i}.err").write_text((r.stdout+r.stderr)[-500:])
    return "ORACLE_PASS" in r.stdout

ENV_ID = os.environ.get("TP_ENV","sympy__sympy-24152")
env = Path.home()/"Desktop/coundetrip/swebench_envs"/ENV_ID
print(f"env: {env} (exists: {(env/REL).exists()})")
if not (env/REL).exists():
    print("bad TP_ENV"); sys.exit(1)
N=2
a = sum(run(False,i,env) for i in range(N))
b = sum(run(True,i,env) for i in range(N))
print(f"\nREAL-CODE RESULT (tensorproduct):  A(no desc): {a}/{N}   B(with desc): {b}/{N}")
print("*** DESCRIPTION HELPS ON REAL CODE ***" if a<b else ("both pass - flash-lite copes" if a==b==N else "inspect runs/realexp_*.err"))
