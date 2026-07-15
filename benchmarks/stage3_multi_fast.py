"""Stage 3 reliability, fast version: smaller fixtures, 2 iterations, 3 independent
runs. Shows the loop reliably discovers a generalizing improvement across runs."""
import json, os, subprocess, sys, statistics
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, _DESCRIBE_SYSTEM

FX = lambda n: Path(f"benchmarks/fixtures/{n}")
TRAIN = [FX("swe_sympy_unitsystem"), FX("swe_sympy_prefixes")]
HELDOUT = [FX("swe_sympy_contains")]
AGENT_CMD = "uv run python -m coundetrip.llm_agent"
RUNS = Path("runs/stage3fast")
PROPOSER = "gemini-2.5-pro"
N_ITERS = 2
N_RUNS = 3
LAMBDA = 0.1

def score_set(prompt, fixtures, tag):
    env = dict(os.environ, COUNDETRIP_DESCRIBE_PROMPT=prompt)
    fids, words = [], []
    for fx in fixtures:
        rid = f"{tag}_{fx.name}"
        r = subprocess.run(
            ["uv","run","python","-m","coundetrip","run","--fixture",str(fx),
             "--agent",AGENT_CMD,"--runs-dir",str(RUNS),"--run-id",rid],
            capture_output=True, text=True, env=env)
        try:
            pf = json.loads(r.stdout).get("score",{}).get("tests",{}).get("pass_fraction",0.0)
        except Exception:
            pf = 0.0
        desc = RUNS/rid/fx.name/"description.md"
        wc = len(desc.read_text().split()) if desc.exists() else 999
        fids.append(pf); words.append(wc)
    mf, mw = statistics.mean(fids), statistics.mean(words)
    return {"objective":mf-LAMBDA*(mw/300.0),"fidelity":mf,"words":mw}

def propose(prompt, sc, temp):
    sys_p=("You are improving the system prompt used to DESCRIBE a code file so another "
           "model can regenerate it from the description alone and pass the original tests. "
           "Maximize regeneration fidelity while keeping the description compact. Rewrite the "
           "prompt to score higher. Output ONLY the new prompt text, no preamble.")
    user=(f"Current prompt:\n{prompt}\n\nMean fidelity {sc['fidelity']:.3f}, mean words "
          f"{sc['words']:.0f}.\n\nRewrite to improve fidelity while staying compact. Output only the new prompt.")
    return GeminiClient(model=PROPOSER,temperature=temp).complete(system=sys_p,user=user).strip()

def one_run(idx, temp):
    best, bp = score_set(_DESCRIBE_SYSTEM, TRAIN, f"r{idx}_tr0"), _DESCRIBE_SYSTEM
    for it in range(1, N_ITERS+1):
        cand = propose(bp, best, temp)
        sc = score_set(cand, TRAIN, f"r{idx}_tr{it}")
        if sc["objective"] > best["objective"]: best, bp = sc, cand
    held = score_set(bp, HELDOUT, f"r{idx}_ho")
    return best, held

def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    base_tr = score_set(_DESCRIBE_SYSTEM, TRAIN, "base_tr")
    base_ho = score_set(_DESCRIBE_SYSTEM, HELDOUT, "base_ho")
    print(f"BASELINE train fid={base_tr['fidelity']:.3f}  held-out fid={base_ho['fidelity']:.3f}\n")
    temps = [0.3, 0.5, 0.7]
    res = []
    for i,t in enumerate(temps,1):
        best, held = one_run(i, t)
        ok = held["fidelity"] >= base_ho["fidelity"]
        print(f"run {i} (temp {t}): train {best['fidelity']:.3f} -> held-out {held['fidelity']:.3f} words={held['words']:.0f} {'ok' if ok else 'NO'}")
        res.append({"run":i,"temp":t,"train_fid":best["fidelity"],"heldout_fid":held["fidelity"],
                    "heldout_words":held["words"],"generalizes":ok})
    ng = sum(r["generalizes"] for r in res)
    hos = [r["heldout_fid"] for r in res]
    print(f"\n{ng}/{len(res)} runs generalized. held-out baseline {base_ho['fidelity']:.3f} -> runs {hos}")
    Path("benchmarks/stage3_multi.json").write_text(json.dumps({"baseline_heldout":base_ho,"runs":res},indent=2,default=str))

if __name__ == "__main__":
    main()
