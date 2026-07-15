"""Stage 2 comparison with OpenWiki as a third condition.
A: weak agent, no description
B: weak agent + our Pro-generated description
C: weak agent + OpenWiki's documentation"""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/pro1")
OW = Path("benchmarks/pro1_openwiki/openwiki")
FNAME = "taskqueue.py"
CODE = (BASE/FNAME).read_text()
WEAK = "gemini-2.5-flash-lite"

DESC = (BASE/"pro_description.md").read_text()
OW_DOCS = "\n\n".join(p.read_text() for p in sorted(OW.glob("*.md")))
print(f"our desc: {len(DESC.split())}w | openwiki: {len(OW_DOCS.split())}w")
print(f"our desc has 60/300: {'60' in DESC and '300' in DESC}")
print(f"openwiki has 60/300: {'60' in OW_DOCS and '300' in OW_DOCS}")

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

def run(doc, tag, i):
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if doc: ctx += f"Documentation:\n{doc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=WEAK, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"owexp_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return False
    r = subprocess.run([sys.executable, "-c", ORACLE % str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

N=4
a = sum(run("", "A", i) for i in range(N))
b = sum(run(DESC, "B", i) for i in range(N))
c = sum(run(OW_DOCS, "C", i) for i in range(N))
print(f"\nA (no desc):          {a}/{N}")
print(f"B (our description):  {b}/{N}")
print(f"C (OpenWiki docs):    {c}/{N}")
