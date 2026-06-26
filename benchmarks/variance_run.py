"""Repeat each roundtrip fixture N times; collect pass_fraction spread."""
import json, statistics, subprocess, sys
from pathlib import Path

FIXTURES = [
    ("swe_saferepr",            "benchmarks/fixtures/swe_saferepr"),
    ("swe_sympy_unitsystem",    "benchmarks/fixtures/swe_sympy_unitsystem"),
    ("swe_sympy_prefixes",      "benchmarks/fixtures/swe_sympy_prefixes"),
    ("swe_sympy_tensorproduct", "benchmarks/fixtures/swe_sympy_tensorproduct"),
    ("swe_sympy_ndim_array",    "benchmarks/fixtures/swe_sympy_ndim_array"),
]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
AGENT = "python -m coundetrip.llm_agent"

def score_of(run_id, name):
    rpt = Path("runs") / run_id / name / "report.json"
    if not rpt.exists():
        return None, "no-report"
    d = json.loads(rpt.read_text())
    if "score" not in d:
        return None, "no-score"
    t = d["score"]["tests"]
    return t["pass_fraction"], f"{t['passed']}p/{t['failed']}f/{t['errors']}e"

rows = []
for name, fx in FIXTURES:
    fracs, notes = [], []
    for i in range(1, N + 1):
        rid = f"var_{name}_{i}"
        print(f">> {name} run {i}/{N} ...", flush=True)
        subprocess.run(["python", "-m", "coundetrip.cli", "run",
                        "--fixture", fx, "--agent", AGENT,
                        "--runner", "local", "--run-id", rid],
                       capture_output=True, text=True)
        pf, detail = score_of(rid, name)
        if pf is not None:
            fracs.append(pf)
        notes.append(detail)
        print(f"   -> {pf if pf is not None else detail}")
    if fracs:
        med = statistics.median(fracs); lo, hi = min(fracs), max(fracs)
    else:
        med = lo = hi = None
    errs = sum(1 for n in notes if n in ("no-score","no-report") or n.endswith("1e") or "0p/0f" in n)
    rows.append((name, len(fracs), med, lo, hi, errs, notes))

out = ["# Run-to-run variance (N runs per fixture, gemini-flash)", "",
       f"N = {N} runs each. Scored = runs that produced a report.", "",
       "| fixture | scored/N | median | min | max | errored | raw |",
       "|---|---|---|---|---|---|---|"]
for name, k, med, lo, hi, errs, notes in rows:
    fmt = lambda v: f"{v:.3f}" if v is not None else "—"
    raw = ", ".join(str(n) for n in notes)
    out.append(f"| {name} | {k}/{N} | {fmt(med)} | {fmt(lo)} | {fmt(hi)} | {errs} | {raw} |")
Path("benchmarks/VARIANCE.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
