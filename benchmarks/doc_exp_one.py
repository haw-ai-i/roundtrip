"""Run ONE codebase cleanly: wipes output dirs, N repeats, A vs B. Usage:
   uv run python benchmarks/doc_exp_one.py <folder> <fname> <N>"""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

folder, fname, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
AGENT = "gemini-2.5-flash-lite"
base = Path("benchmarks")/folder
code = (base/fname).read_text(); desc = (base/"description.md").read_text()
TASK = (base/"task.txt").read_text().strip()

SYS = (f"You are a coding agent. Implement the requested change. Output ONLY valid "
       f"Python (no markdown, no prose after code). Format:\n=== {fname} ===\n<contents>\n")

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
        if started and (s.startswith("## ") or s.startswith("Documentation for") or
                        re.match(r"# \w+ module", s)):
            break
        out.append(ln)
    return "\n".join(out).rstrip()+"\n"

def one(with_desc, i):
    ctx = f"=== {fname} ===\n{code}\n\n"
    if with_desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    d = base/f"run_{'B' if with_desc else 'A'}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/fname).write_text(src)
    # copy oracle deps: none needed, oracle imports from d via sys.path
    if not src.strip(): return False
    r = subprocess.run([sys.executable, str(base/"oracle.py"), str(d)], capture_output=True, text=True)
    return "ORACLE_PASS" in r.stdout

# clean old runs
for old in base.glob("run_*"): shutil.rmtree(old)
for old in base.glob("out_*"): shutil.rmtree(old)
aP = sum(one(False,i) for i in range(N))
bP = sum(one(True,i) for i in range(N))
print(f"{folder:14s}  A(no desc): {aP}/{N}   B(with desc): {bP}/{N}")
