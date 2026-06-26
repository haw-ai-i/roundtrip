"""Collect roundtrip scores from runs/ into a committed results table."""
import json, sys
from pathlib import Path

RUNS = [
    ("var_swe_saferepr_1",  "swe_saferepr",            103, "lost one exact output literal"),
    ("us_1",      "swe_sympy_unitsystem",    205, "5/33 tests fail"),
    ("sympy_real_2", "swe_sympy_prefixes",   219, "import-time error: regenerated immutability constraint original omits"),
    ("tp_1",      "swe_sympy_tensorproduct", 420, "dropped matrix/trace integration imports"),
    ("nd_1",      "swe_sympy_ndim_array",    592, "importable but behavior off across the board"),
]

runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs")
rows = []
for run_id, fixture, lines, note in RUNS:
    rpt = runs_dir / run_id / fixture / "report.json"
    if not rpt.exists():
        print(f"  MISSING: {rpt}", file=sys.stderr)
        rows.append((fixture, lines, None, None, note, None)); continue
    d = json.loads(rpt.read_text())
    t = d["score"]["tests"]; desc = d["score"].get("description", {})
    detail = f"{t['passed']}p/{t['failed']}f/{t['errors']}e"
    rows.append((fixture, lines, t["pass_fraction"], detail, note, desc.get("word_count")))

out = ["# Roundtrip results (SWE-Bench Lite, gemini-flash)", "",
       "| fixture | lines | pass_fraction | tests (p/f/e) | describe words | failure mode |",
       "|---|---|---|---|---|---|"]
for fixture, lines, pf, detail, note, words in rows:
    pfs = f"{pf:.3f}" if pf is not None else "—"
    out.append(f"| {fixture} | {lines} | {pfs} | {detail or '—'} | {words or '—'} | {note} |")
Path("benchmarks/RESULTS.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
