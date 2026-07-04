"""Stage 3 reliability: run the optimize-then-validate loop multiple independent
times (different proposer temperatures/seeds) and report whether every run improves
the held-out set. Shows the climb is reliable, not a single lucky trajectory."""
import json, os, subprocess, sys, statistics
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, _DESCRIBE_SYSTEM

FX = lambda n: Path(f"benchmarks/fixtures/{n}")
TRAIN = [FX("swe_sympy_tensorproduct"), FX("swe_sympy_unitsystem"), FX("swe_sympy_prefixes")]
HELDOUT = [FX("swe_sympy_contains"), FX("swe_sympy_ndim_array")]
AGENT_CMD = "uv run python -m coundetrip.llm_agent"
RUNS = Path("runs/stage3multi")
PROPOSER = "gemini-2.5-pro"
N_ITERS = 3
N_RUNS = 3          # independent optimization runs
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

def one_run(run_idx, temp):
    best, best_prompt = score_set(_DESCRIBE_SYSTEM, TRAIN, f"r{run_idx}_tr0"), _DESCRIBE_SYSTEM
    for it in range(1, N_ITERS+1):
        cand = propose(best_prompt, best, temp)
        sc = score_set(cand, TRAIN, f"r{run_idx}_tr{it}")
        if sc["objective"] > best["objective"]:
            best, best_prompt = sc, cand
    held = score_set(best_prompt, HELDOUT, f"r{run_idx}_ho")
    return best, held

def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    base_train = score_set(_DESCRIBE_SYSTEM, TRAIN, "base_tr")
    base_held  = score_set(_DESCRIBE_SYSTEM, HELDOUT, "base_ho")
    print(f"BASELINE  train fid={base_train['fidelity']:.3f}  held-out fid={base_held['fidelity']:.3f} words={base_held['words']:.0f}\n")
    temps = [0.3, 0.5, 0.7][:N_RUNS]
    results = []
    for i, t in enumerate(temps, 1):
        best, held = one_run(i, t)
        improved = held["fidelity"] >= base_held["fidelity"]
        print(f"run {i} (temp {t}): train fid={best['fidelity']:.3f}  ->  HELD-OUT fid={held['fidelity']:.3f} words={held['words']:.0f}  {'generalizes' if improved else 'NO'}")
        results.append({"run":i,"temp":t,"train_fid":best["fidelity"],
                        "heldout_fid":held["fidelity"],"heldout_words":held["words"],"generalizes":improved})
    n_gen = sum(r["generalizes"] for r in results)
    print(f"\n{n_gen}/{len(results)} independent runs improved (or matched) held-out fidelity over baseline.")
    hos = [r["heldout_fid"] for r in results]
    print(f"held-out fidelity across runs: baseline {base_held['fidelity']:.3f} -> runs {hos} (mean {statistics.mean(hos):.3f})")
    Path("benchmarks/stage3_multi.json").write_text(json.dumps(
        {"baseline_heldout":base_held,"runs":results},indent=2,default=str))

if __name__ == "__main__":
    main()
