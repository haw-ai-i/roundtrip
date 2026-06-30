"""Stage 2 workflow comparison: same change, two workflows, size + output."""
import sys
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

REL = "sympy/sets/contains.py"
FIX = Path("benchmarks/fixtures/swe_sympy_contains")
orig_code = (FIX / REL).read_text()
orig_desc = Path("runs/drift_1/swe_sympy_contains/description.md").read_text()

REQUEST = ("Make Contains handle tuple inputs component-wise: if x is a tuple or "
           "Tuple, Contains(x, s) should return the And of Contains(elem, s) for "
           "each element.")

SYS_CODE = ("You are a coding agent. You are given a source file and a change request. "
            "Apply the requested change, modifying as little as possible. Output the full "
            "updated file as:\n=== <path> ===\n<contents>\n")
SYS_DESC = ("You are given the CURRENT contents of a source file and an UPDATED specification. "
            "Modify the file to satisfy the updated specification, changing as little as possible. "
            "Output the full updated file as:\n=== <path> ===\n<contents>\n")

def call(system, user):
    return GeminiClient(temperature=0.0).complete(system=system, user=user)
def extract(reply):
    f = parse_file_blocks(reply); return f.get(REL) or (next(iter(f.values())) if f else "")

# Workflow 1: code agent on raw code + concise request
w1_user = f"=== {REL} ===\n{orig_code}\n\nChange request: {REQUEST}\n"
w1 = extract(call(SYS_CODE, w1_user))
Path("runs/wf1_code.py").write_text(w1)

# Workflow 2: description edit -> materialize
edited_desc = orig_desc + "\n### Tuple membership\n" + REQUEST + "\n"
w2_user = f"Updated specification:\n\n{edited_desc}\n\nCurrent file (=== {REL} ===):\n\n=== {REL} ===\n{orig_code}\n"
w2 = extract(call(SYS_DESC, w2_user))
Path("runs/wf2_desc.py").write_text(w2)

print("=== INPUT SIZE (what the human wrote) ===")
print(f"Workflow 1 (prompt to code agent): {len(REQUEST)} chars")
print(f"Workflow 2 (description edit):     {len('### Tuple membership\\n'+REQUEST)} chars")
print("\n=== WORKFLOW 1 output: tuple handling present? ===")
print("\n".join(l for l in w1.splitlines() if "tuple" in l.lower() or "And" in l))
print("\n=== WORKFLOW 2 output: tuple handling present? ===")
print("\n".join(l for l in w2.splitlines() if "tuple" in l.lower() or "And" in l))
print("\n(full outputs saved: runs/wf1_code.py, runs/wf2_desc.py)")
