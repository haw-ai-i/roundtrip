"""Stage 2 structural edit: measure code cost of a cascading description edit."""
import difflib, os, sys
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("runs/drift_1/swe_sympy_contains")
REL = "sympy/sets/contains.py"
orig_code = (BASE / "generated" / REL).read_text()
orig_desc = (BASE / "description.md").read_text()
struct_desc = Path("runs/stage2/description_structural.md").read_text()

SYS = (
    "You are given the CURRENT contents of a source file and an UPDATED specification. "
    "Modify the file to satisfy the updated specification, changing as LITTLE as possible. "
    "Preserve all existing code, names, structure, and formatting that the change does not "
    "require touching. Output the full updated file in this format:\n"
    "=== <relative/path> ===\n<full file contents>\n"
)

def minimal_regen(desc):
    client = GeminiClient(model=os.environ.get("COUNDETRIP_MODEL","gemini-3.5-flash"), temperature=0.0)
    user = f"Updated specification:\n\n{desc}\n\nCurrent file (=== {REL} ===):\n\n=== {REL} ===\n{orig_code}\n"
    files = parse_file_blocks(client.complete(system=SYS, user=user))
    return files.get(REL) or next(iter(files.values()), "")

def ledits(a,b):
    d=list(difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm=""))
    return sum(1 for x in d if x and x[0] in "+-" and not x.startswith(("+++","---")))

def desc_ledits():
    return ledits(orig_desc, struct_desc)

print(">> control: minimal-regen from ORIGINAL desc"); co = minimal_regen(orig_desc)
print(">> structural: minimal-regen from edited desc"); cs = minimal_regen(struct_desc)
print(f"\ndescription edit:   {desc_ledits()} lines")
print(f"control drift:      {ledits(orig_code, co)} lines")
print(f"code edit (struct): {ledits(orig_code, cs)} lines")
print(f"amplification:      {ledits(orig_code, cs)/max(desc_ledits(),1):.1f}x")
print("\n=== structural code diff ===")
for l in difflib.unified_diff(orig_code.splitlines(), cs.splitlines(), lineterm="", n=0):
    if l and l[0] in "+-" and not l.startswith(("+++","---")): print(l)
