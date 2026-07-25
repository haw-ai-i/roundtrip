"""Build envs for the newest sympy Verified candidates (modern era), skipping the
three already built. Log outcomes to verified_build_log2.json."""
import json, subprocess
from pathlib import Path

EXISTING = {"sympy__sympy-24213", "sympy__sympy-24066", "sympy__sympy-23950"}
cands = json.loads(Path("benchmarks/verified_candidates.json").read_text())
sympy = sorted((c for c in cands if c["repo"]=="sympy"),
               key=lambda c: int(c["id"].split("-")[-1]), reverse=True)
todo = [c for c in sympy if c["id"] not in EXISTING][:21]
print(f"building {len(todo)} envs\n")
log = []
for i, c in enumerate(todo, 1):
    iid = c["id"]
    print(f"[{i:02d}/{len(todo)}] {iid} ({c['target']})", flush=True)
    r = subprocess.run(["uv","run","python","benchmarks/setup_swebench_env.py", iid,
                        "--dataset","princeton-nlp/SWE-bench_Verified"],
                       capture_output=True, text=True)
    ok = "baseline exit:    0" in r.stdout
    tail = (r.stdout.strip().splitlines() or ["?"])[-1]
    log.append({"id": iid, "target": c["target"], "ok": ok, "tail": tail})
    print(f"        {'OK' if ok else 'FAILED'}: {tail}", flush=True)
Path("benchmarks/verified_build_log2.json").write_text(json.dumps(log, indent=1))
good = [l["id"] for l in log if l["ok"]]
print(f"\n{len(good)}/{len(log)} verified good: {good}")
