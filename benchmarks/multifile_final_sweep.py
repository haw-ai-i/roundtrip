"""Multi-file roundtrip: characterization run (cost-optimized).
Cheap models at 10 runs, pricier 2.5-pro at 6 runs. Repair vs plain.
Reports mean, min, max, std, and error-run count per cell.
"""
import os, subprocess, json, statistics
from pathlib import Path

FIXTURE = "benchmarks/fixtures/swe_sympy_sets_multi"
ORACLE_CFG = str(Path(FIXTURE, "oracle_env.json").resolve())
PLAIN = "python -m coundetrip.llm_agent"
REPAIR = f"python {Path('benchmarks/regen_repair_agent.py').resolve()}"
# (model, n_runs) - fewer runs for the pricier model
PLAN = [("gemini-2.5-flash-lite", 10), ("gemini-3.5-flash", 10), ("gemini-2.5-pro", 6)]
RUNS = Path("runs")

def one(model, agent, repair, i):
    tag = f"fin_{model.replace('.','_').replace('-','_')}_{'rep' if repair else 'pln'}_{i}"
    env = dict(os.environ); env["COUNDETRIP_MODEL"] = model
    if repair: env["REPAIR_ORACLE_CFG"] = ORACLE_CFG
    subprocess.run(["uv","run","python","-m","coundetrip.cli","run",
                    "--fixture",FIXTURE,"--agent",agent,"--run-id",tag],
                   env=env, capture_output=True, text=True)
    rep = RUNS/tag/"swe_sympy_sets_multi"/"report.json"
    if rep.exists():
        t = json.loads(rep.read_text()).get("score",{}).get("tests",{})
        return t.get("pass_fraction",0.0), t.get("errors",0)
    return 0.0, 1

print(f"{'model':<24}{'cond':<8}{'n':<4}{'mean':<7}{'min':<6}{'max':<6}{'std':<7}{'errs'}")
results = {}
for model, n in PLAN:
    for repair, agent, label in [(False,PLAIN,"plain"),(True,REPAIR,"repair")]:
        fr, errs = [], 0
        for i in range(n):
            pf,e = one(model,agent,repair,i)
            fr.append(pf)
            if e>0: errs+=1
        std = statistics.stdev(fr) if len(fr)>1 else 0.0
        print(f"{model:<24}{label:<8}{n:<4}{statistics.mean(fr):<7.2f}{min(fr):<6.2f}{max(fr):<6.2f}{std:<7.2f}{errs}")
        results[f"{model}_{label}"] = fr
Path("benchmarks/fixtures/swe_sympy_sets_multi/final_sweep.json").write_text(json.dumps(results, indent=2))
print("\nsaved final_sweep.json")
