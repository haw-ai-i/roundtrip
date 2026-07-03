"""Stage 3: minimal meta-harness loop. Optimizes the DESCRIBE prompt (the harness)
against the roundtrip benchmark, hill-climbing with a candidate ledger. Objective
rewards complete AND compact descriptions."""
import json, os, subprocess, sys, statistics
from pathlib import Path
sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, _DESCRIBE_SYSTEM

FIXTURES = [
    Path("benchmarks/fixtures/swe_sympy_tensorproduct"),
    Path("benchmarks/fixtures/swe_sympy_unitsystem"),
]
AGENT_CMD = "uv run python -m coundetrip.llm_agent"
RUNS = Path("runs/stage3")
PROPOSER = "gemini-2.5-pro"
N_ITERS = 3
LAMBDA = 0.1

def score(prompt, tag):
    env = dict(os.environ, COUNDETRIP_DESCRIBE_PROMPT=prompt)
    fids, words = [], []
    for fx in FIXTURES:
        rid = f"{tag}_{fx.name}"
        r = subprocess.run(
            ["uv","run","python","-m","coundetrip","run","--fixture",str(fx),
             "--agent",AGENT_CMD,"--runs-dir",str(RUNS),"--run-id",rid],
            capture_output=True, text=True, env=env)
        try:
            report = json.loads(r.stdout)
            pf = report.get("score",{}).get("tests",{}).get("pass_fraction", 0.0)
        except Exception:
            pf = 0.0
        desc = RUNS/rid/fx.name/"description.md"
        wc = len(desc.read_text().split()) if desc.exists() else 999
        fids.append(pf); words.append(wc)
    mean_fid = statistics.mean(fids); mean_wc = statistics.mean(words)
    obj = mean_fid - LAMBDA*(mean_wc/300.0)
    return {"objective":obj,"fidelity":mean_fid,"words":mean_wc,
            "per_fixture":list(zip([f.name for f in FIXTURES],fids,words))}

def propose(current_prompt, sc):
    sys_p = ("You are improving the system prompt used to DESCRIBE a code file in natural "
             "language, so another model can regenerate the code from the description alone "
             "and pass the original tests. Goal: maximize regeneration fidelity while keeping "
             "the description compact. Given the current prompt and its measured fidelity and "
             "length, rewrite it to score higher. Output ONLY the new prompt text, no preamble.")
    user = (f"Current describe prompt:\n{current_prompt}\n\n"
            f"Measured: mean fidelity {sc['fidelity']:.3f}, mean words {sc['words']:.0f}.\n"
            f"Per fixture (name, fidelity, words): {sc['per_fixture']}\n\n"
            "Rewrite to improve fidelity while staying compact. Output only the new prompt.")
    return GeminiClient(model=PROPOSER, temperature=0.4).complete(system=sys_p, user=user).strip()

def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    ledger = []
    best_prompt = _DESCRIBE_SYSTEM
    best = score(best_prompt, "iter0")
    ledger.append((0, best["objective"], best["fidelity"], best["words"]))
    print(f"iter 0 (baseline): obj={best['objective']:.3f} fid={best['fidelity']:.3f} words={best['words']:.0f}")
    print(f"  per-fixture: {best['per_fixture']}")
    for it in range(1, N_ITERS+1):
        cand = propose(best_prompt, best)
        sc = score(cand, f"iter{it}")
        kept = sc["objective"] > best["objective"]
        print(f"iter {it}: obj={sc['objective']:.3f} fid={sc['fidelity']:.3f} words={sc['words']:.0f}  {'KEPT' if kept else 'rejected'}")
        print(f"  per-fixture: {sc['per_fixture']}")
        ledger.append((it, sc["objective"], sc["fidelity"], sc["words"]))
        if kept:
            best, best_prompt = sc, cand
            Path("benchmarks/stage3_best_prompt.txt").write_text(cand)
    print("\nLedger (iter, objective, fidelity, words):")
    for row in ledger: print(" ", row)
    Path("benchmarks/stage3_ledger.json").write_text(json.dumps(ledger, indent=2))
    print(f"\nBest: obj={best['objective']:.3f} fid={best['fidelity']:.3f} words={best['words']:.0f}")

if __name__ == "__main__":
    main()
