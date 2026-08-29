import json
from pathlib import Path
BASE = Path("benchmarks/baseline_results")
SRC = {"issue_only":BASE/"transfer_kindb_omp.json","optimized":BASE/"transfer_kindb_omp.json",
       "ast":BASE/"transfer_kindb_ast.json","compact":BASE/"transfer_kindb_compact.json"}
CONDS=["issue_only","optimized","compact","ast"]
EXCL={"swe_pytest_dev___init___xdir_5840","swe_pytest_dev_python_multi_8399",
      "swe_sympy_basic_xdir_13091","swe_sympy_matrices_xdir_13877"}
data={c:(json.loads(Path(SRC[c]).read_text()) if Path(SRC[c]).exists() else {}) for c in CONDS}
allf=sorted((set().union(*[set(d) for d in data.values()]))-EXCL)

def st(c,f):
    row=data[c].get(f)
    if row is None: return None,"absent"
    cell=row.get(c)
    if not isinstance(cell,dict): return None,"absent"
    if "mean" in cell: return cell["mean"],"ok"
    if "failed" in cell: return None,"noedit"
    return None,"other"

# ---- PART 2: per-fixture 4-way table ----
print("="*104)
print("PER-FIXTURE 4-WAY (score, or NE=no-edit)")
print("="*104)
print(f"{'fixture':<44}{'issue':>9}{'optim':>9}{'compact':>9}{'ast':>9}   note")
print("-"*104)
for f in allf:
    vals={}; notes=[]
    for c in CONDS:
        m,s=st(c,f)
        vals[c]= f"{m:.3f}" if m is not None else ("NE" if s=="noedit" else "-")
    # flag interesting rows
    scored={c:st(c,f)[0] for c in CONDS if st(c,f)[0] is not None}
    if "compact" in scored and "issue_only" in scored:
        d=scored["compact"]-scored["issue_only"]
        if abs(d)>=0.1: notes.append(f"compact-issue={d:+.2f}")
    if st("compact",f)[1]=="noedit" and st("issue_only",f)[1]=="ok":
        notes.append("COMPACT-ONLY-FAIL")
    print(f"{f:<44}{vals['issue_only']:>9}{vals['optimized']:>9}{vals['compact']:>9}{vals['ast']:>9}   {' '.join(notes)}")

# ---- PART 1: robustness — is compact's no-edit a real compression cost? ----
print()
print("="*104)
print("ROBUSTNESS: no-edit overlap analysis")
print("="*104)
ne={c:set(f for f in allf if st(c,f)[1]=="noedit") for c in CONDS}
for c in CONDS:
    print(f"{c:<12} no-edits: {len(ne[c])}  -> {sorted(x.split('swe_')[-1] for x in ne[c])}")
print()
# compact no-edits: how many did OTHER conds handle fine?
comp_only=[f for f in ne["compact"] if any(st(c,f)[1]=="ok" for c in ["issue_only","optimized","ast"])]
comp_shared=[f for f in ne["compact"] if f not in comp_only]
print(f"compact no-edits where >=1 other condition SUCCEEDED (real compression cost): {len(comp_only)}")
for f in comp_only:
    others=[c for c in ["issue_only","optimized","ast"] if st(c,f)[1]=="ok"]
    print(f"   {f.split('swe_')[-1]:<40} succeeded in: {','.join(others)}")
print(f"compact no-edits also failing everywhere (hard fixture, not compact-specific): {len(comp_shared)}")
for f in comp_shared:
    print(f"   {f.split('swe_')[-1]}")
