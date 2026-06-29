"""Stage 2, noise-robust: regenerate original xN and edited xN, separate
edit-driven changes (in ALL edited, NO original) from random regen churn."""
import difflib, subprocess, sys, os, re, collections, itertools
from pathlib import Path

BASE = Path("runs/drift_1/swe_sympy_contains")
REL = "sympy/sets/contains.py"
S2 = Path("runs/stage2robust")
orig_desc = S2 / "description_original.md"
edit_desc = Path("runs/stage2/description_edited.md")

def regen(desc, outdir):
    env = os.environ.copy()
    env.update(COUNDETRIP_STAGE="regenerate",
               COUNDETRIP_DESCRIPTION=str(desc.resolve()),
               COUNDETRIP_WORKSPACE=str((BASE/"workspace").resolve()),
               COUNDETRIP_GENERATED=str(outdir.resolve()),
               COUNDETRIP_RUN_DIR=str(S2.resolve()))
    subprocess.run([sys.executable,"-m","coundetrip.llm_agent"], env=env, capture_output=True)

def norm(t):
    return [l.rstrip() for l in t.splitlines() if l.strip()]

if sys.argv[1] == "regen":
    N = int(sys.argv[2]); S2.mkdir(parents=True, exist_ok=True)
    if not orig_desc.exists():
        orig_desc.write_text((BASE/"description.md").read_text())
    for i in range(1, N+1):
        print(f">> original run {i}/{N}"); regen(orig_desc, S2/f"orig_{i}")
        print(f">> edited   run {i}/{N}"); regen(edit_desc, S2/f"edit_{i}")
    print("done")

elif sys.argv[1] == "measure":
    N = int(sys.argv[2])
    origs = [set(norm((S2/f"orig_{i}"/REL).read_text())) for i in range(1,N+1)]
    edits = [set(norm((S2/f"edit_{i}"/REL).read_text())) for i in range(1,N+1)]
    edit_driven_add = set.intersection(*edits) - set.union(*origs)
    edit_driven_del = set.intersection(*origs) - set.union(*edits)
    print(f"N={N} runs each side")
    print(f"edit-driven added lines (in all edited, no original): {len(edit_driven_add)}")
    for l in sorted(edit_driven_add): print("   + "+l)
    print(f"edit-driven removed lines (in all original, no edited): {len(edit_driven_del)}")
    for l in sorted(edit_driven_del): print("   - "+l)
    def avg_within(group):
        ds=[len(group[a]^group[b]) for a,b in itertools.combinations(range(len(group)),2)]
        return sum(ds)/len(ds) if ds else 0
    print(f"\nnoise floor (avg line-diff within original runs, same desc): {avg_within(origs):.1f}")
    print(f"noise floor (within edited runs): {avg_within(edits):.1f}")
    tot = len(edit_driven_add)+len(edit_driven_del)
    print(f"\nHONEST amplification: {tot} consistent code-line edits vs 4 description-line edits = {tot/4:.1f}x")
