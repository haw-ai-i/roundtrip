"""Completeness experiment: does agent uplift track description completeness?
Per-value score (how many of 5 defaults the agent gets right) reveals the gradient.
Same comprehension-only settings task, so success = did the description convey the facts."""
import sys, subprocess, re, shutil
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("benchmarks/settings_exp")
FNAME = "settings.py"
CODE = (BASE/FNAME).read_text()
AGENT = "gemini-2.5-flash-lite"

LEVELS = [
    ("none",    None),
    ("minimal", BASE/"desc_minimal.md"),   # 1 of 5 values
    ("partial", BASE/"desc_partial.md"),   # 3 of 5
    ("full",    BASE/"desc_full.md"),      # 5 of 5
]
EXPECTED = {"timeout":30, "retries":5, "cache_size":256, "log_level":"warning", "batch_size":64}

# per-value scorer: how many of the 5 defaults does the agent's code return correctly?
SCORER = '''
import sys; sys.path.insert(0, %r)
from settings import Settings
s = Settings()
exp = {"timeout":30,"retries":5,"cache_size":256,"log_level":"warning","batch_size":64}
correct = 0
for k,v in exp.items():
    try:
        if s.get(k) == v: correct += 1
    except Exception: pass
print("SCORE", correct)
'''

TASK = ("Implement the _default(self, key) method of Settings so that get(key) returns "
        "the project's documented default value for that key, and None for keys with no "
        "documented default.")
SYS = (f"You are a coding agent. Implement the change. Output ONLY valid Python:\n=== {FNAME} ===\n<contents>\n")

def extract(reply):
    fm = re.search(r"=== .*? ===\n(.*)", reply, re.DOTALL)
    body = fm.group(1) if fm else None
    if body is None:
        m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL); body = m.group(1) if m else reply
    lines = body.splitlines()
    start = next((i for i,l in enumerate(lines) if l.strip().startswith(("from ","import ","class "))), 0)
    out = []
    for l in lines[start:]:
        st = l.strip()
        if st.startswith(("Documentation for","```","## ","Here is","Of course")): break
        out.append(l)
    return "\n".join(out).rstrip()+"\n"

def run(descpath, tag, i):
    desc = descpath.read_text() if descpath else ""
    ctx = f"=== {FNAME} ===\n{CODE}\n\n"
    if desc: ctx += f"Documentation for this module:\n{desc}\n\n"
    ctx += f"Task: {TASK}\n"
    src = extract(GeminiClient(model=AGENT, temperature=0.0).complete(system=SYS, user=ctx))
    d = BASE/f"comp_{tag}_{i}"
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); (d/FNAME).write_text(src)
    if not src.strip(): return 0
    r = subprocess.run([sys.executable, "-c", SCORER % str(d)], capture_output=True, text=True)
    m = re.search(r"SCORE (\d+)", r.stdout)
    return int(m.group(1)) if m else 0

N=5
print(f"Per-value score (out of 5 defaults correct), N={N} avg\n")
for tag, path in LEVELS:
    scores = [run(path, tag, i) for i in range(N)]
    avg = sum(scores)/len(scores)
    words = len(path.read_text().split()) if path else 0
    print(f"{tag:9s} ({words:3d} words):  avg {avg:.1f}/5   runs={scores}")
