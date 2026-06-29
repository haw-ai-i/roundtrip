"""Stage 2, controlled: regenerate from ORIGINAL and EDITED descriptions in the
same session, diff those two outputs. Isolates the edit from regeneration churn."""
import difflib, subprocess, sys, os, re
from pathlib import Path

BASE = Path("runs/drift_1/swe_sympy_contains")
REL = "sympy/sets/contains.py"
S2 = Path("runs/stage2")
orig_desc = S2 / "description_original.md"
edit_desc = S2 / "description_edited.md"
gen_orig = S2 / "gen_original"
gen_edit = S2 / "gen_edited"

def regen(desc, outdir):
    env = os.environ.copy()
    env["COUNDETRIP_STAGE"] = "regenerate"
    env["COUNDETRIP_DESCRIPTION"] = str(desc.resolve())
    env["COUNDETRIP_WORKSPACE"] = str((BASE / "workspace").resolve())
    env["COUNDETRIP_GENERATED"] = str(outdir.resolve())
    env["COUNDETRIP_RUN_DIR"] = str(S2.resolve())
    return subprocess.run([sys.executable, "-m", "coundetrip.llm_agent"], env=env).returncode

def line_edits(a, b):
    d = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
    return sum(1 for x in d if x and x[0] in "+-" and not x.startswith(("+++","---")))

def token_edits(a, b):
    ta, tb = re.findall(r"\S+", a), re.findall(r"\S+", b)
    sm = difflib.SequenceMatcher(None, ta, tb)
    return sum(max(i2-i1, j2-j1) for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag!="equal")

if sys.argv[1:] == ["regen"]:
    if not orig_desc.exists():
        orig_desc.write_text((BASE / "description.md").read_text())
    print(">> regenerating from ORIGINAL description ..."); regen(orig_desc, gen_orig)
    print(">> regenerating from EDITED description ...");   regen(edit_desc, gen_edit)
    print("done")
elif sys.argv[1:] == ["measure"]:
    od, ed = orig_desc.read_text(), edit_desc.read_text()
    co, ce = (gen_orig/REL).read_text(), (gen_edit/REL).read_text()
    dl, dt = line_edits(od, ed), token_edits(od, ed)
    cl, ct = line_edits(co, ce), token_edits(co, ce)
    print(f"description edits:  {dl} lines, {dt} tokens")
    print(f"code edits (paired):{cl} lines, {ct} tokens")
    if dl and dt:
        print(f"amplification:      {cl/dl:.1f}x lines, {ct/dt:.1f}x tokens")
    print("\n=== paired code diff (original-desc vs edited-desc, same session) ===")
    for l in difflib.unified_diff(co.splitlines(), ce.splitlines(), lineterm="", n=1):
        if l and l[0] in "+-" and not l.startswith(("+++","---")): print(l)
else:
    print("usage: stage2_paired.py [regen|measure]")
