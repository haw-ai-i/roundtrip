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

def status(c,f):
    row=data[c].get(f)
    if row is None: return "ABSENT"
    cell=row.get(c)
    if not isinstance(cell,dict): return "MISSING_COND"
    if "mean" in cell: return "OK"
    if "failed" in cell: return "NOEDIT"
    if "skipped" in cell: return "SKIP:"+str(cell.get("skipped",""))[:20]
    return "OTHER:"+",".join(list(cell)[:2])

print(f"{'fixture':<44}" + "".join(f"{c[:9]:>11}" for c in CONDS) + "  drops?")
print("-"*104)
dropcount={c:0 for c in CONDS}
dropped=[]
for f in allf:
    st={c:status(c,f) for c in CONDS}
    if not all(st[c]=="OK" for c in CONDS):
        bad=[c for c in CONDS if st[c]!="OK"]
        for c in bad: dropcount[c]+=1
        dropped.append(f)
        print(f"{f:<44}" + "".join(f"{st[c]:>11}" for c in CONDS) + "  <-- "+",".join(bad))
print("-"*104)
print("total runnable fixtures:",len(allf))
print("fully-paired (all 4 OK):",len(allf)-len(dropped))
print("dropped:",len(dropped))
print("drop reason by condition:",dropcount)
