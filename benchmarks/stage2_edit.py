"""Stage 2: edit description -> regenerate -> measure edit amplification.

Counts edits on the description side vs the code side (line- and token-level).
Hypothesis: a meaningful description edit causes a larger code change, i.e.
editing NL is cheaper than editing code.
"""
import difflib, subprocess, sys, os, re
from pathlib import Path

RUN = "drift_1"  # baseline run with the clean 1.0 description + code
NAME = "swe_sympy_contains"
REL = "sympy/sets/contains.py"
base_dir = Path("runs") / RUN / NAME
orig_desc = base_dir / "description.md"
orig_code = base_dir / "generated" / REL

edited_desc = Path("runs/stage2") / "description_edited.md"
gen_dir = Path("runs/stage2/generated")
edited_desc.parent.mkdir(parents=True, exist_ok=True)

def line_edits(a, b):
    d = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
    return sum(1 for x in d if x and x[0] in "+-" and not x.startswith(("+++","---")))

def token_edits(a, b):
    ta, tb = re.findall(r"\S+", a), re.findall(r"\S+", b)
    sm = difflib.SequenceMatcher(None, ta, tb)
    return sum((max(i2-i1, j2-j1)) for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag!="equal")

if sys.argv[1:] == ["regen"]:
    # called after edited_desc is written; run regenerate only
    env = os.environ.copy()
    env["COUNDETRIP_STAGE"] = "regenerate"
    env["COUNDETRIP_DESCRIPTION"] = str(edited_desc.resolve())
    env["COUNDETRIP_WORKSPACE"] = str((base_dir / "workspace").resolve())
    env["COUNDETRIP_GENERATED"] = str(gen_dir.resolve())
    env["COUNDETRIP_RUN_DIR"] = str(Path("runs/stage2").resolve())
    rc = subprocess.run([sys.executable, "-m", "coundetrip.llm_agent"], env=env).returncode
    sys.exit(rc)

if sys.argv[1:] == ["measure"]:
    od, ed = orig_desc.read_text(), edited_desc.read_text()
    oc = orig_code.read_text()
    nc = (gen_dir / REL).read_text()
    dl, dt = line_edits(od, ed), token_edits(od, ed)
    cl, ct = line_edits(oc, nc), token_edits(oc, nc)
    print(f"description edits:  {dl} lines, {dt} tokens")
    print(f"code edits:         {cl} lines, {ct} tokens")
    print(f"amplification:      {cl/dl:.1f}x lines, {ct/dt:.1f}x tokens" if dl and dt else "n/a")
    sys.exit(0)

print("usage: stage2_edit.py [regen|measure]")
