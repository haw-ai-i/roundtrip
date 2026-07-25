"""Recompute description density as a token ratio (tokens in description / tokens in source).
Re-runs only the describe stage at temperature zero, which reproduces the original
descriptions deterministically. Tokenizer: tiktoken cl100k_base."""
import os, sys, subprocess, tempfile
from pathlib import Path
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
FIX = [
    ("swe_sympy_contains",      "sympy/sets/contains.py"),
    ("swe_sympy_unitsystem",    "sympy/physics/units/unitsystem.py"),
    ("swe_saferepr",            None),
    ("swe_sympy_tensorproduct", "sympy/physics/quantum/tensorproduct.py"),
    ("swe_sympy_prefixes",      "sympy/physics/units/prefixes.py"),
    ("swe_sympy_ndim_array",    "sympy/tensor/array/ndim_array.py"),
]

print(f"{'fixture':<24}{'src_tok':>9}{'desc_tok':>10}{'ratio':>8}{'words':>8}{'w/line':>8}")
for name, src_rel in FIX:
    fixture = Path("benchmarks/fixtures")/name
    # source: single file, or all .py under source_paths for saferepr
    if src_rel:
        srcs = [fixture/src_rel]
    else:
        srcs = sorted((fixture/"src").rglob("*.py"))
    src_text = "\n".join(p.read_text() for p in srcs if p.exists())
    src_lines = sum(1 for _ in src_text.splitlines())
    with tempfile.TemporaryDirectory() as td:
        desc = Path(td)/"description.txt"
        env = dict(os.environ)
        env.update({"COUNDETRIP_STAGE":"describe",
                    "COUNDETRIP_FIXTURE":str(fixture.resolve()),
                    "COUNDETRIP_DESCRIPTION":str(desc),
                    "COUNDETRIP_MODEL":"gemini-3.5-flash"})
        r = subprocess.run(["uv","run","python","-m","coundetrip.llm_agent"],
                           env=env, capture_output=True, text=True, cwd=".")
        if r.returncode != 0 or not desc.exists():
            print(f"{name:<24}  DESCRIBE FAILED: {r.stderr.strip()[:60]}")
            continue
        d = desc.read_text()
    st, dt = len(ENC.encode(src_text)), len(ENC.encode(d))
    w = len(d.split())
    print(f"{name:<24}{st:>9}{dt:>10}{dt/st:>8.2f}{w:>8}{w/src_lines:>8.1f}")
