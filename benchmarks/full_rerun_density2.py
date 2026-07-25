"""One full roundtrip per fixture: fidelity + token density from the SAME descriptions."""
import os, subprocess, json
from pathlib import Path
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
FIX = [
    ("swe_sympy_contains",      "sympy/sets/contains.py",              1.00),
    ("swe_sympy_unitsystem",    "sympy/physics/units/unitsystem.py",   0.85),
    ("swe_saferepr",            None,                                  0.73),
    ("swe_sympy_tensorproduct", "sympy/physics/quantum/tensorproduct.py", 0.62),
    ("swe_sympy_prefixes",      "sympy/physics/units/prefixes.py",     0.00),
    ("swe_sympy_ndim_array",    "sympy/tensor/array/ndim_array.py",    0.00),
]
RUNS = Path("runs")
print(f"{'fixture':<24}{'old_fid':>8}{'new_fid':>8}{'tok_ratio':>10}")
for name, src_rel, old_fid in FIX:
    rid = f"dens2_{name}"
    env = dict(os.environ); env["COUNDETRIP_MODEL"] = "gemini-3.5-flash"
    subprocess.run(["uv","run","python","-m","coundetrip.cli","run",
                    "--fixture", f"benchmarks/fixtures/{name}",
                    "--agent", "python -m coundetrip.llm_agent",
                    "--run-id", rid], env=env, capture_output=True, text=True)
    rdir = RUNS/rid/name
    rep = rdir/"report.json"
    fid = json.loads(rep.read_text()).get("score",{}).get("tests",{}).get("pass_fraction") if rep.exists() else None
    # find the description this run produced
    descs = list(rdir.rglob("description*")) + list(rdir.rglob("*.txt"))
    desc_file = next((d for d in descs if "descri" in d.name and "std" not in d.name), None)
    fixture = Path("benchmarks/fixtures")/name
    srcs = [fixture/src_rel] if src_rel else sorted((fixture/"src").rglob("*.py"))
    src_tok = len(ENC.encode("\n".join(p.read_text() for p in srcs if p.exists())))
    ratio = len(ENC.encode(desc_file.read_text()))/src_tok if desc_file and src_tok else None
    fid_s = f"{fid:.2f}" if fid is not None else "ERR"
    rat_s = f"{ratio:.2f}" if ratio else "no-desc-file"
    print(f"{name:<24}{old_fid:>8.2f}{fid_s:>8}{rat_s:>10}")
