"""Stage 3 with held-out validation. Optimize the describe prompt on a TRAIN set,
then test the discovered prompt on a HELD-OUT set to confirm it generalizes.
Follows the metaharness train/test discipline."""
import json, os, subprocess, sys, statistics
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, _DESCRIBE_SYSTEM

FX = lambda n: Path(f"benchmarks/fixtures/{n}")
TRAIN = [FX("swe_sympy_tensorproduct"), FX("swe_sympy_unitsystem"), FX("swe_sympy_prefixes")]
HELDOUT = [FX("swe_sympy_contains"), FX("swe_sympy_ndim_array")]
AGENT_CMD = "uv run python -m coundetrip.llm_agent"
RUNS = Path("runs/stage3val")
PROPOSER = "gemini-2.5-pro"
N_ITERS = 3
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
    return {"objective":mf-LAMBDA*(mw/300.0),"fidelity":mf,"words":mw,
            "per":list(zip([f.name for f in fixtures],[round(x,3) for x in fids],words))}

def propose(prompt, sc):
    sys_p=("You are improving the system prompt used to DESCRIBE a code file so another "
           "model can regenerate it from the description alone and pass the original tests. "
           "Maximize regeneration fidelity while keeping the description compact. Rewrite the "
           "prompt to score higher. Output ONLY the new prompt text, no preamble.")
    user=(f"Current prompt:\n{prompt}\n\nMean fidelity {sc['fidelity']:.3f}, mean words "
          f"{sc['words']:.0f}. Per fixture: {sc['per']}\n\nRewrite to improve fidelity while "
          "staying compact. Output only the new prompt.")
    return GeminiClient(model=PROPOSER,temperature=0.4).complete(system=sys_p,user=user).strip()

def main():
    RUNS.mkdir(parents=True,exist_ok=True)
    print("=== BASELINE ===")
    base_train = score_set(_DESCRIBE_SYSTEM, TRAIN, "base_tr")
    base_held  = score_set(_DESCRIBE_SYSTEM, HELDOUT, "base_ho")
    print(f"baseline TRAIN:   fid={base_train['fidelity']:.3f} words={base_train['words']:.0f} {base_train['per']}")
    print(f"baseline HELDOUT: fid={base_held['fidelity']:.3f} words={base_held['words']:.0f} {base_held['per']}")

    print("\n=== OPTIMIZE ON TRAIN ===")
    best, best_prompt = base_train, _DESCRIBE_SYSTEM
    for it in range(1, N_ITERS+1):
        cand = propose(best_prompt, best)
        sc = score_set(cand, TRAIN, f"tr{it}")
        kept = sc["objective"] > best["objective"]
        print(f"iter {it}: TRAIN fid={sc['fidelity']:.3f} words={sc['words']:.0f} obj={sc['objective']:.3f} {'KEPT' if kept else 'rej'}")
        if kept: best, best_prompt = sc, cand

    print("\n=== VALIDATE DISCOVERED PROMPT ON HELD-OUT ===")
    disc_held = score_set(best_prompt, HELDOUT, "disc_ho")
    Path("benchmarks/stage3_best_prompt.txt").write_text(best_prompt)
    print(f"discovered HELDOUT: fid={disc_held['fidelity']:.3f} words={disc_held['words']:.0f} {disc_held['per']}")
    print("\n=== GENERALIZATION ===")
    print(f"held-out fidelity: baseline {base_held['fidelity']:.3f} -> discovered {disc_held['fidelity']:.3f}")
    print(f"held-out words:    baseline {base_held['words']:.0f} -> discovered {disc_held['words']:.0f}")
    gen = disc_held['fidelity'] >= base_held['fidelity']
    print("GENERALIZES (discovered >= baseline on unseen fixtures)" if gen else "does not generalize - overfit to train")
    summary = {"baseline_train":base_train,"baseline_heldout":base_held,
               "discovered_heldout":disc_held,"generalizes":gen}
    Path("benchmarks/stage3_validation.json").write_text(json.dumps(summary,indent=2,default=str))

if __name__ == "__main__":
    main()
