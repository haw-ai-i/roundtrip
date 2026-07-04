"""Pipeline design: Pro MATERIALIZES/describes the codebase (real pipeline),
then the weak agent (flash-lite) does a task with vs without Pro's description.
The description is PIPELINE-GENERATED, not hand-written."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/pro1")
FNAME = "taskqueue.py"
CODE = (BASE/FNAME).read_text()
PRO = "gemini-2.5-pro"
WEAK = "gemini-2.5-flash-lite"

# Step 1: Pro DESCRIBES the code (real describe step)
DESCRIBE_SYS = ("Describe this Python module in natural language precisely enough that "
                "an engineer could reimplement it exactly, including any non-obvious "
                "scoring or priority logic. Do not include code.")
print("Step 1: Pro describes the code...")
DESC = GeminiClient(model=PRO, temperature=0.0).complete(system=DESCRIBE_SYS, user=CODE)
(BASE/"pro_description.md").write_text(DESC)
print(f"  generated {len(DESC.split())} words")

# Step 2: quick check the description captured the aging-boost contract
has_contract = ("60" in DESC and "300" in DESC)
print(f"  description mentions aging thresholds (60/300): {has_contract}")

# Step 3: weak agent does a task, A (no desc) vs B (with Pro's desc)
TASK = ("Add a method peek_scores(self) to TaskQueue that returns a list of "
        "(task_name, effective_score) tuples for all tasks, using the SAME scoring "
        "the queue uses to pick the next task.")
ORACLE = '''
import sys; sys.path.insert(0, %r)
from taskqueue import Task, TaskQueue
q = TaskQueue([Task('a',8,0), Task('b',5,120), Task('c',3,400)])
d = dict(q.peek_scores())
assert d['a']==8, d; assert d['b']==10, d; assert d['c']==15, d
print("ORACLE_PASS")
'''
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
    r = subprocess.run([sys.executable, "-c", ORACLE % str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

print("\nStep 3: weak agent with vs without Pro's generated description")
N=3
a = sum(run(False,i) for i in range(N))
b = sum(run(True,i) for i in range(N))
print(f"\nRESULT (Pro-generated desc):  A(no desc): {a}/{N}   B(with desc): {b}/{N}")
print("*** EFFECT WITH PIPELINE DESCRIPTION ***" if (a<b) else "no separation - inspect")
