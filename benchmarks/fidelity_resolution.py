"""Does description fidelity predict a description's contribution to issue resolution?

For each fixture (known roundtrip description fidelity), a mid-tier agent (gemini-3.5-flash)
implements the target file from the scaffold, once WITHOUT the description and once WITH it.
The fixture's real tests are the acceptance criteria. We measure mean test-pass fraction in each
condition over N attempts; the description's contribution is the uplift (with minus without).
We correlate uplift with description fidelity.
"""
import sys, os, subprocess, json, statistics
from pathlib import Path

FIX = [
    ("swe_sympy_contains",      1.00),
    ("swe_sympy_unitsystem",    0.85),
    ("swe_saferepr",            0.73),
    ("swe_sympy_tensorproduct", 0.62),
    ("swe_sympy_prefixes",      0.00),
    ("swe_sympy_ndim_array",    0.00),
]
AGENT = "gemini-3.5-flash"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
RUNS = Path("runs")

def one(fixture, rid, agent_cmd):
    env = dict(os.environ); env["COUNDETRIP_MODEL"] = AGENT
    subprocess.run([sys.executable, "-m", "coundetrip.cli", "run",
                    "--fixture", f"benchmarks/fixtures/{fixture}",
                    "--agent", agent_cmd, "--run-id", rid],
                   env=env, capture_output=True, text=True)
    rep = RUNS / rid / fixture / "report.json"
    if rep.exists():
        return json.loads(rep.read_text()).get("score",{}).get("tests",{}).get("pass_fraction",0.0)
    return 0.0

def mean_frac(fixture, agent_cmd, tag):
    return statistics.mean(one(fixture, f"{tag}_{fixture}_{i}", agent_cmd) for i in range(N))

WITH = "python -m coundetrip.llm_agent"
WITHOUT = "python benchmarks/nodesc_agent.py"

print(f"Description fidelity vs uplift on issue resolution (agent={AGENT}, N={N})\n")
print(f"{'fixture':<26}{'fidelity':>9}{'no_desc':>9}{'with_desc':>11}{'uplift':>9}")
fids, uplifts = [], []
for fixture, fid in FIX:
    without = mean_frac(fixture, WITHOUT, "fr_no")
    withd   = mean_frac(fixture, WITH,    "fr_yes")
    up = withd - without
    fids.append(fid); uplifts.append(up)
    print(f"{fixture:<26}{fid:>9.2f}{without:>9.2f}{withd:>11.2f}{up:>9.2f}")

if len(set(fids))>1 and len(set(uplifts))>1:
    print(f"\nPearson correlation (fidelity vs uplift): {statistics.correlation(fids,uplifts):.3f}")
else:
    print("\n(insufficient variation)")

out = {"agent":AGENT,"N":N,"measure":"resolution_uplift",
       "data":[{"fixture":f,"fidelity":fi,"uplift":u} for (f,fi),u in zip(FIX,uplifts)]}
Path("benchmarks/FIDELITY_RESOLUTION.json").write_text(json.dumps(out,indent=2))
print("\nsaved")
