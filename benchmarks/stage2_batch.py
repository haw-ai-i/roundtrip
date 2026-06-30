"""Stage 2 edit-distribution: several description edits through the minimal-edit
instrument, measuring description-edit vs code-edit per edit across scopes."""
import difflib, os, sys
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

BASE = Path("runs/drift_1/swe_sympy_contains")
REL = "sympy/sets/contains.py"
orig_code = (BASE/"generated"/REL).read_text()
orig_desc = (BASE/"description.md").read_text()

SYS = (
    "You are given the CURRENT contents of a source file and an UPDATED specification. "
    "Modify the file to satisfy the updated specification, changing as LITTLE as possible. "
    "Preserve all existing code, names, structure, and formatting that the change does not "
    "require touching. Output the full updated file in this format:\n"
    "=== <relative/path> ===\n<full file contents>\n"
)

EDITS = [
  ("validation", "single-site",
   "\n### Input validation\nIn `eval`, if `x` is not a SymPy expression (use `sympify`), convert it; if conversion fails, raise `TypeError` with message `\"element must be a SymPy expression\"`.\n"),
  ("doit", "new-method",
   "\n### Method: `doit`\nAdd a `doit(**hints)` method that re-evaluates membership by calling `self.func(*self.args)` and returns the simplified result.\n"),
  ("multi-method", "multi-site",
   "\n### Combined change\nAdd a `negate()` method returning `Not(Contains(x, s))`, AND change `as_set` to return `s.complement(S.UniversalSet)` when the contains is negated.\n"),
]

def ledits(a,b):
    d=list(difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm=""))
    return sum(1 for x in d if x and x[0] in "+-" and not x.startswith(("+++","---")))

def minimal_regen(desc):
    client = GeminiClient(temperature=0.0)
    user=f"Updated specification:\n\n{desc}\n\nCurrent file (=== {REL} ===):\n\n=== {REL} ===\n{orig_code}\n"
    files=parse_file_blocks(client.complete(system=SYS,user=user))
    return files.get(REL) or next(iter(files.values()),"")

print(f"{'edit':14s} {'scope':12s} {'desc_lines':>10} {'code_lines':>10} {'amp':>6}")
for label, scope, addition in EDITS:
    new_desc = orig_desc + addition
    dl = ledits(orig_desc, new_desc)
    code = minimal_regen(new_desc)
    cl = ledits(orig_code, code)
    print(f"{label:14s} {scope:12s} {dl:10d} {cl:10d} {cl/max(dl,1):6.1f}")
    Path(f"runs/stage2batch_{label}.py").write_text(code)
