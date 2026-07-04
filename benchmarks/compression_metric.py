"""Compression ratio per fixture: NL description size vs original code size.
Stage 1 metric: how much description suffices to regenerate the code."""
import json
from pathlib import Path

# (run_id, fixture, original source rel-path inside the env or fixture)
ROWS = [
    ("var_swe_saferepr_1",            "swe_saferepr",            "src/saferepr.py"),
    ("var_swe_sympy_unitsystem_1",    "swe_sympy_unitsystem",    "sympy/physics/units/unitsystem.py"),
    ("var_swe_sympy_prefixes_1",      "swe_sympy_prefixes",      "sympy/physics/units/prefixes.py"),
    ("var_swe_sympy_tensorproduct_1", "swe_sympy_tensorproduct", "sympy/physics/quantum/tensorproduct.py"),
    ("var_swe_sympy_ndim_array_1",    "swe_sympy_ndim_array",    "sympy/tensor/array/ndim_array.py"),
    ("ver_23950",                     "swe_sympy_contains",      "sympy/sets/contains.py"),
]

def find_src(fixture, rel):
    p = Path("benchmarks/fixtures") / fixture / rel
    if p.exists(): return p
    cands = list((Path("benchmarks/fixtures")/fixture).rglob(Path(rel).name))
    return cands[0] if cands else None

print(f"{'fixture':28s} {'code_lines':>10} {'code_chars':>10} {'desc_words':>10} {'words/line':>10} {'pass':>6}")
out = ["# Compression ratio (description size vs code size)","",
       "| fixture | code lines | code chars | desc words | words/line | pass |","|---|---|---|---|---|---|"]
for run_id, fixture, rel in ROWS:
    rpt = Path("runs")/run_id/fixture/"report.json"
    desc = Path("runs")/run_id/fixture/"description.md"
    src = find_src(fixture, rel)
    if not (rpt.exists() and src):
        print(f"{fixture:28s}  MISSING (run_id={run_id})"); continue
    d = json.loads(rpt.read_text())
    words = d["score"]["description"].get("word_count") or (len(desc.read_text().split()) if desc.exists() else 0)
    pf = d["score"]["tests"]["pass_fraction"]
    code = src.read_text()
    lines = len([l for l in code.splitlines() if l.strip()])
    chars = len(code)
    wpl = words/lines if lines else 0
    print(f"{fixture:28s} {lines:10d} {chars:10d} {words:10d} {wpl:10.2f} {pf:6.2f}")
    out.append(f"| {fixture} | {lines} | {chars} | {words} | {wpl:.2f} | {pf:.2f} |")
Path("benchmarks/COMPRESSION.md").write_text("\n".join(out)+"\n")
