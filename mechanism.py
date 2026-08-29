import json
from pathlib import Path
BASE = Path("benchmarks/baseline_results")
DCACHE = Path("benchmarks/descriptions")
FIXDIR = Path("benchmarks/fixtures")
compact = json.loads((BASE/"transfer_kindb_compact.json").read_text())

# the 8 compact-specific failures + 1 catastrophic, from deepdive
compact_fail = ["swe_django_compiler_multi_15563","swe_django_utils_xdir_11885",
    "swe_django_operations_xdir_13121","swe_sympy_codeprinter_multi_22080",
    "swe_sympy_latex_xdir_14248","swe_django_related_lookups_xdir_16032",
    "swe_django_compiler_multi_10554","swe_django_expressions_xdir_16263"]
catastrophic = ["swe_sympy_relational_xdir_20438"]

def props(fix):
    fdir = FIXDIR/fix
    cfg = {}
    for j in fdir.glob("*.json"):
        try: cfg = json.loads(j.read_text()); break
        except: pass
    trs = cfg.get("target_rels") or ([cfg["target_rel"]] if cfg.get("target_rel") else [])
    nfiles = len(trs)
    # full description size (proxy for how much had to be compressed)
    dfile = DCACHE/(fix+".md")
    full_words = len(dfile.read_text().split()) if dfile.exists() else 0
    return nfiles, full_words

print("="*84)
print("MECHANISM: do compact failures cluster on #target-files or description size?")
print("="*84)
print(f"{'fixture':<42}{'#files':>7}{'full_words':>12}  category")
print("-"*84)

import statistics
def show(fixes, label):
    nf=[]; fw=[]
    for f in fixes:
        n,w = props(f); nf.append(n); fw.append(w)
        print(f"{f.split('swe_')[-1]:<42}{n:>7}{w:>12}  {label}")
    return nf, fw

nf_fail, fw_fail = show(compact_fail, "COMPACT-FAIL")
nf_cat, fw_cat = show(catastrophic, "WRONG-EDIT")

# baseline: fixtures where compact SUCCEEDED
succ = [f for f,v in compact.items() if 'mean' in v.get('compact',{})]
nf_ok=[]; fw_ok=[]
for f in succ:
    n,w=props(f); nf_ok.append(n); fw_ok.append(w)

print("-"*84)
def summ(name,nf,fw):
    if not nf: print(f"{name}: none"); return
    print(f"{name:<16} n={len(nf):<3} avg #files={statistics.mean(nf):.2f}  "
          f"multi-file(>1)={sum(1 for x in nf if x>1)}/{len(nf)}  "
          f"avg full_words={statistics.mean(fw):.0f}")
summ("compact-FAIL", nf_fail, fw_fail)
summ("compact-OK", nf_ok, fw_ok)
print()
print("READ: if FAIL avg #files >> OK avg #files, the 70-word summary can't cover")
print("      multiple target files -> that's the mechanism of the robustness tax.")
