"""Stage 2, minimal-edit regeneration: original code + edited spec -> smallest change."""
import difflib, os, re, sys
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("runs/drift_1/swe_sympy_contains")
REL = "sympy/sets/contains.py"
orig_code = (BASE / "generated" / REL).read_text()
orig_desc = (BASE / "description.md").read_text()
edit_desc = Path("runs/stage2/description_edited.md").read_text()

SYS = (
    "You are given the CURRENT contents of a source file and an UPDATED specification. "
    "Modify the file to satisfy the updated specification, changing as LITTLE as possible. "
    "Preserve all existing code, names, structure, and formatting that the change does not "
    "require touching. Output the full updated file in this format:\n"
    "=== <relative/path> ===\n<full file contents>\n"
)

def minimal_regen(desc, label):
    client = GeminiClient(model=os.environ.get("COUNDETRIP_MODEL","gemini-3.5-flash"), temperature=0.0)
    user = (f"Updated specification:\n\n{desc}\n\n"
            f"Current file (=== {REL} ===):\n\n=== {REL} ===\n{orig_code}\n")
    reply = client.complete(system=SYS, user=user)
    files = parse_file_blocks(reply)
    code = files.get(REL) or next(iter(files.values()), "")
    Path(f"runs/stage2min_{label}.py").write_text(code)
    return code

def ledits(a,b):
    d=list(difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm=""))
    return sum(1 for x in d if x and x[0] in "+-" and not x.startswith(("+++","---")))

if sys.argv[1:] == ["run"]:
    print(">> minimal-regen from ORIGINAL description (control: should be ~no change)")
    co = minimal_regen(orig_desc, "orig")
    print(">> minimal-regen from EDITED description")
    ce = minimal_regen(edit_desc, "edit")
    print(f"\ncontrol drift (orig-desc minimal vs original code): {ledits(orig_code, co)} lines")
    print(f"edit effect (edit-desc minimal vs original code):   {ledits(orig_code, ce)} lines")
    print(f"edit vs control (the clean signal):                 {ledits(co, ce)} lines")
    print("\n=== edit-desc minimal diff vs original code ===")
    for l in difflib.unified_diff(orig_code.splitlines(), ce.splitlines(), lineterm="", n=0):
        if l and l[0] in "+-" and not l.startswith(("+++","---")): print(l)
