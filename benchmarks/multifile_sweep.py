"""Multi-file roundtrip: repeated runs across models to characterize feasibility and variance."""
import os, subprocess, json, statistics
from pathlib import Path

FIXTURE = "benchmarks/fixtures/swe_sympy_sets_multi"
MODELS = ["gemini-3.5-flash", "gemini-2.5-flash-lite"]
N = 3
RUNS = Path("runs")

def one_run(model, i):
    rid = f"msweep_{model.replace('.','_').replace('-','_')}_{i}"
    env = dict(os.environ); env["COUNDETRIP_MODEL"] = model
    subprocess.run(["uv","run","python","-m","coundetrip.cli","run",
                    "--fixture",FIXTURE,"--agent","python -m coundetrip.llm_agent",
                    "--run-id",rid], env=env, capture_output=True, text=True)
    rep = RUNS/rid/"swe_sympy_sets_multi"/"report.json"
    if rep.exists():
        d = json.loads(rep.read_text())
        t = d.get("score",{}).get("tests",{})
        return t.get("pass_fraction",0.0), t.get("passed",0), t.get("failed",0), t.get("errors",0)
    return 0.0,0,0,1

print(f"Multi-file roundtrip sweep ({N} runs/model)\n")
for model in MODELS:
    fracs=[]
    print(f"=== {model} ===")
    for i in range(N):
        pf,p,f,e = one_run(model,i)
        fracs.append(pf)
        print(f"  run {i}: pass_fraction={pf:.2f}  (passed={p} failed={f} errors={e})")
    print(f"  mean={statistics.mean(fracs):.2f}  min={min(fracs):.2f}  max={max(fracs):.2f}\n")
