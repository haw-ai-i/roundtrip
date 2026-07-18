"""Multi-file roundtrip: repair vs no-repair across models.
Shows whether the import-repair step helps across model strengths, on the three-file
sympy sets fixture. Reports mean pass_fraction and error-run count per cell.
"""
import os, subprocess, json, statistics
from pathlib import Path

FIXTURE = "benchmarks/fixtures/swe_sympy_sets_multi"
ORACLE_CFG = str(Path(FIXTURE, "oracle_env.json").resolve())
PLAIN = "python -m coundetrip.llm_agent"
REPAIR = f"python {Path('benchmarks/regen_repair_agent.py').resolve()}"
MODELS = ["gemini-2.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-pro"]
N = 3
RUNS = Path("runs")

def run(model, agent, repair, i):
    tag = f"sw_{model.replace('.','_').replace('-','_')}_{'rep' if repair else 'plain'}_{i}"
    env = dict(os.environ)
    env["COUNDETRIP_MODEL"] = model
    if repair:
        env["REPAIR_ORACLE_CFG"] = ORACLE_CFG
    subprocess.run(["uv","run","python","-m","coundetrip.cli","run",
                    "--fixture",FIXTURE,"--agent",agent,"--run-id",tag],
                   env=env, capture_output=True, text=True)
    rep = RUNS/tag/"swe_sympy_sets_multi"/"report.json"
    if rep.exists():
        t = json.loads(rep.read_text()).get("score",{}).get("tests",{})
        return t.get("pass_fraction",0.0), t.get("errors",0)
    return 0.0, 1

print(f"{'model':<24}{'condition':<10}{'runs':<22}{'mean':<7}{'err_runs'}")
for model in MODELS:
    for repair, agent, label in [(False, PLAIN, "plain"), (True, REPAIR, "repair")]:
        fracs, errs = [], 0
        for i in range(N):
            pf, e = run(model, agent, repair, i)
            fracs.append(pf)
            if e > 0: errs += 1
        runs_str = ", ".join(f"{f:.2f}" for f in fracs)
        print(f"{model:<24}{label:<10}{runs_str:<22}{statistics.mean(fracs):<7.2f}{errs}")
