import json
from pathlib import Path
from math import comb
BASE = Path("benchmarks/baseline_results")
DCACHE = Path("benchmarks/descriptions")
SRC = {"issue_only":BASE/"transfer_kindb_omp.json","optimized":BASE/"transfer_kindb_omp.json",
       "ast":BASE/"transfer_kindb_ast.json","compact":BASE/"transfer_kindb_compact.json"}
CONDS=["issue_only","optimized","compact","ast"]
EXCL={"swe_pytest_dev___init___xdir_5840","swe_pytest_dev_python_multi_8399",
      "swe_sympy_basic_xdir_13091","swe_sympy_matrices_xdir_13877"}
data={c:(json.loads(Path(SRC[c]).read_text()) if Path(SRC[c]).exists() else {}) for c in CONDS}
def cell(c,f):
    x=data[c].get(f,{}).get(c); return x if isinstance(x,dict) and "mean" in x else None
def resolved(x):
    r=x.get("resolved");
    if not r: return None
    g,_,t=r.partition("/")
    try: return int(t)>0 and int(g)==int(t)
    except: return None
allf=sorted((set().union(*[set(d) for d in data.values()]))-EXCL)
# strict: fixtures where ALL FOUR scored
paired=[f for f in allf if all(cell(c,f) is not None for c in CONDS)]
print("STRICT PAIRED SET (all 4 conditions scored):", len(paired), "fixtures\n")
print(f"{'condition':<12}{'resolved':>10}{'mean_frac':>11}{'desc_words':>12}")
print("-"*45)
for c in CONDS:
    cells=[cell(c,f) for f in paired]
    res=sum(1 for x in cells if resolved(x))
    mf=sum(x['mean'] for x in cells)/len(cells)
    if c=="optimized":
        dw=sum(len((DCACHE/(f+'.md')).read_text().split()) if (DCACHE/(f+'.md')).exists() else 0 for f in paired)/len(paired)
    else:
        dw=sum(x.get('desc_words',0) for x in cells)/len(cells)
    print(f"{c:<12}{res:>10}{mf:>11.3f}{dw:>12.0f}")
print("\nPAIRED McNEMAR vs issue_only (same",len(paired),"fixtures):")
for c in ["optimized","compact","ast"]:
    b01=b10=0
    for f in paired:
        ra,rb=resolved(cell("issue_only",f)),resolved(cell(c,f))
        if ra and not rb:b01+=1
        elif rb and not ra:b10+=1
    d=b01+b10
    p=1.0 if d==0 else min(1.0,2*sum(comb(d,i) for i in range(min(b01,b10)+1))/(2**d))
    print(f"  {c:<10} {c} better:{b10}  issue_only better:{b01}  p={p:.4f}")
