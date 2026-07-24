"""Take the first 30 sympy candidates from verified_candidates.json (dataset order),
build each env with setup_swebench_env.py, and log outcomes to verified_build_log.json."""
import json, subprocess, sys
from pathlib import Path

cands = json.loads(Path("benchmarks/verified_candidates.json").read_text())
sympy = [c for c in cands if c["repo"] == "sympy"][:30]
print(f"building {len(sympy)} sympy Verified envs\n")
log = []
for i, c in enumerate(sympy, 1):
    iid = c["id"]
    print(f"[{i:02d}/30] {iid} ({c['target']})", flush=True)
    r = subprocess.run(["uv","run","python","benchmarks/setup_swebench_env.py", iid,
                        "--dataset","princeton-nlp/SWE-bench_Verified"],
                       capture_output=True, text=True)
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip().splitlines()[-1:] and r.stderr.strip().splitlines()[-1]
    ok = "baseline exit:    0" in r.stdout
    log.append({"id": iid, "target": c["target"], "ok": ok, "tail": tail})
    print(f"        {'OK' if ok else 'FAILED'}: {tail}")
Path("benchmarks/verified_build_log.json").write_text(json.dumps(log, indent=1))
good = sum(1 for l in log if l["ok"])
print(f"\n{good}/{len(log)} envs verified good; log saved")
