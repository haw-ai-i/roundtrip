"""Fidelity x3 per Verified fixture: mean, SD, and token density from the same runs."""
import json, os, statistics, subprocess
from pathlib import Path
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
new = json.loads(Path("benchmarks/verified_fixtures.json").read_text())
FIX = ["swe_sympy_contains", "swe_sympy_unitsystem", "swe_sympy_unitsystem_v2"] + new
N = 3
print(f"{'fixture':<30}{'runs':<20}{'mean':>6}{'sd':>6}{'tok_ratio':>10}")
out = {}
for f in FIX:
    scores, ratios = [], []
    for i in range(N):
        rid = f"vfid_{f}_{i}"
        env = dict(os.environ); env["COUNDETRIP_MODEL"] = "gemini-3.5-flash"
        subprocess.run(["uv","run","python","-m","coundetrip.cli","run",
                        "--fixture", f"benchmarks/fixtures/{f}",
                        "--agent", "python -m coundetrip.llm_agent",
                        "--run-id", rid], env=env, capture_output=True, text=True)
        rdir = Path("runs")/rid/f
        rep = rdir/"report.json"
        s = json.loads(rep.read_text()).get("score",{}).get("tests",{}).get("pass_fraction") if rep.exists() else None
        scores.append(s if s is not None else -1.0)
        desc = rdir/"description.md"
        yaml = (Path("benchmarks/fixtures")/f/"coundetrip.yaml").read_text()
        src_rel = [l.split("- ",1)[1].strip() for l in yaml.splitlines() if l.strip().startswith("- ") and l.strip().endswith(".py") and "run_oracle" not in l][0]
        src = (Path("benchmarks/fixtures")/f/src_rel).read_text()
        if desc.exists():
            ratios.append(len(ENC.encode(desc.read_text()))/max(1,len(ENC.encode(src))))
    ok = [s for s in scores if s >= 0]
    m = statistics.mean(ok) if ok else float("nan")
    sd = statistics.stdev(ok) if len(ok) > 1 else 0.0
    tr = statistics.mean(ratios) if ratios else float("nan")
    out[f] = {"scores": scores, "mean": m, "sd": sd, "tok_ratio": tr}
    print(f"{f:<30}{str([round(s,2) for s in scores]):<20}{m:>6.2f}{sd:>6.2f}{tr:>10.2f}", flush=True)
Path("benchmarks/VERIFIED_FIDELITY.json").write_text(json.dumps(out, indent=1))
print("\nsaved benchmarks/VERIFIED_FIDELITY.json")
