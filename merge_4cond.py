import json, os
from pathlib import Path
from math import comb

BASE = Path("benchmarks/baseline_results")
DCACHE = Path("benchmarks/descriptions")
SRC = {
    "issue_only": BASE / "transfer_kindb_omp.json",
    "optimized":  BASE / "transfer_kindb_omp.json",
    "ast":        BASE / "transfer_kindb_ast.json",
    "compact":    BASE / "transfer_kindb_compact.json",
}
CONDS = ["issue_only", "optimized", "compact", "ast"]
EXCLUDED = {
    "swe_pytest_dev___init___xdir_5840", "swe_pytest_dev_python_multi_8399",
    "swe_sympy_basic_xdir_13091", "swe_sympy_matrices_xdir_13877",
}
def load(p): return json.loads(Path(p).read_text()) if Path(p).exists() else {}
data = {c: load(SRC[c]) for c in CONDS}

# real full-description word counts from the cache (optimized data predates desc logging)
def full_words(fix):
    f = DCACHE / (fix + ".md")
    return len(f.read_text().split()) if f.exists() else 0

def cell(cond, fix):
    c = data[cond].get(fix, {}).get(cond)
    return c if isinstance(c, dict) and "mean" in c else None

fixtures = sorted((set().union(*[set(d) for d in data.values()])) - EXCLUDED)

def fully_resolved(c):
    r = c.get("resolved")
    if not r: return None
    g, _, t = r.partition("/")
    try: return int(t) > 0 and int(g) == int(t)
    except ValueError: return None

def dwords(cond, fix, c):
    # use logged desc_words if present; else fall back to cache for optimized
    w = c.get("desc_words", 0)
    if w == 0 and cond == "optimized":
        w = full_words(fix)
    return w

print("=" * 92)
print("FOUR-CONDITION SUMMARY  (issue_only | optimized | compact | ast)")
print("=" * 92)
print(f"{'condition':<12}{'scored':>8}{'resolved':>10}{'mean_frac':>11}{'desc_words':>12}{'in_tok':>9}{'out_tok':>9}")
print("-" * 92)
agg = {}
for cond in CONDS:
    rows = [(f, cell(cond, f)) for f in fixtures]
    rows = [(f, c) for f, c in rows if c is not None]
    n = len(rows)
    if not n:
        print(f"{cond:<12}{0:>8}   (no data yet)"); continue
    res = sum(1 for _, c in rows if fully_resolved(c))
    mf = sum(c["mean"] for _, c in rows) / n
    dw = sum(dwords(cond, f, c) for f, c in rows) / n
    it = sum(c.get("tokens", {}).get("input", 0) for _, c in rows) / n
    ot = sum(c.get("tokens", {}).get("output", 0) for _, c in rows) / n
    agg[cond] = dict(n=n, res=res, mf=mf, dw=dw, it=it, ot=ot)
    print(f"{cond:<12}{n:>8}{res:>10}{mf:>11.3f}{dw:>12.0f}{it:>9.0f}{ot:>9.0f}")

def mcnemar(a, b):
    b01 = b10 = 0
    for f in fixtures:
        ca, cb = cell(a, f), cell(b, f)
        if ca is None or cb is None: continue
        ra, rb = fully_resolved(ca), fully_resolved(cb)
        if ra is None or rb is None: continue
        if ra and not rb: b01 += 1
        elif rb and not ra: b10 += 1
    disc = b01 + b10
    if disc == 0: return b01, b10, 1.0
    k = min(b01, b10)
    return b01, b10, min(1.0, 2*sum(comb(disc,i) for i in range(k+1))/(2**disc))

print("\n" + "=" * 92)
print("PAIRED McNEMAR vs issue_only (resolved)")
print("=" * 92)
for cond in ["optimized", "compact", "ast"]:
    if cond not in agg: continue
    b01, b10, p = mcnemar("issue_only", cond)
    print(f"issue_only vs {cond:<10} {cond} better:{b10:>3}  issue_only better:{b01:>3}  exact p={p:.4f}")

print("\n" + "=" * 92)
print("EFFICIENCY / AMORTIZATION")
print("=" * 92)
if "optimized" in agg and "compact" in agg:
    fdw, cdw = agg["optimized"]["dw"], agg["compact"]["dw"]
    ratio = fdw / cdw if cdw else float("nan")
    print(f"full description : {fdw:>7.0f} words/fixture, resolved {agg['optimized']['res']}/{agg['optimized']['n']}, mean {agg['optimized']['mf']:.3f}")
    print(f"compact summary  : {cdw:>7.0f} words/fixture, resolved {agg['compact']['res']}/{agg['compact']['n']}, mean {agg['compact']['mf']:.3f}")
    if "ast" in agg:
        print(f"ast (free)       : {agg['ast']['dw']:>7.0f} words/fixture, resolved {agg['ast']['res']}/{agg['ast']['n']}, mean {agg['ast']['mf']:.3f}")
    print(f"issue_only base  : resolved {agg['issue_only']['res']}/{agg['issue_only']['n']}, mean {agg['issue_only']['mf']:.3f}")
    print(f"compression      : compact ~{ratio:.0f}x smaller than full description")

print("\ncoverage:", {c: agg.get(c, {}).get("n", 0) for c in CONDS}, "of", len(fixtures))
