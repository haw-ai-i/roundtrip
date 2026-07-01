"""Pro-pipeline, task forces REPRODUCING the formula (no self._score reuse).
Faithful Pro description of correct code. Honest test of whether description helps."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/pro2")
FNAME = "taskqueue.py"
CODE = (BASE/FNAME).read_text()
PRO, WEAK = "gemini-2.5-pro", "gemini-2.5-flash-lite"

print("Pro describes the code...")
DESC = GeminiClient(model=PRO, temperature=0.0).complete(
    system=("Describe this Python module in natural language precisely enough that an "
            "engineer could reimplement it exactly, including any non-obvious scoring "
            "or priority logic and exact thresholds. No code."), user=CODE)
(BASE/"pro_description.md").write_text(DESC)
print(f"  {len(DESC.split())} words; mentions 60/300: {'60' in DESC and '300' in DESC}")

TASK = ("Add a module-level function score_task(urgency, age) to taskqueue.py that "
        "returns the effective score for a task with the given urgency and age, using "
        "the SAME scoring rule the TaskQueue uses internally. It takes two integers "
        "and must not depend on the Task or TaskQueue classes.")
ORACLE = (BASE/"oracle.py").read_text()
SYS = (f"You are a coding agent. Implement the change. Output ONLY valid Python:\n=== {FNAME} ===\n<contents>\n")

def extract(reply):
    files = parse_file_blocks(reply)
    body = next(iter(files.values())) if files else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    out, started = [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith(("from ","import ","class ","def ")): started = True
        if started and (s.startswith("## ") or s.startswith("Describe ") or re.match(r"# \w+ module", s)): break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"

def run(with_desc, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if with_desc: ctx += f"Documentation:\n{DESC}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=WEAK, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"run_{'B' if with_desc else 'A'}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(BASE/"oracle.py"), str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

N=3
a = sum(run(False,i) for i in range(N))
b = sum(run(True,i) for i in range(N))
print(f"\nRESULT (reproduce-formula task):  A(no desc): {a}/{N}   B(with desc): {b}/{N}")
print("*** EFFECT ***" if a<b else ("both perfect - task still too easy" if a==b==N else "inspect runs"))
