import json
f = "benchmarks/baseline_results/transfer_kindb_omp.json"
d = json.load(open(f))
bad = [k for k, v in d.items()
       if not (set(v.keys()) >= {"issue_only", "optimized"}
               and all(isinstance(c, dict) and "mean" in c for c in v.values()))]
for k in bad:
    d.pop(k)
open(f, "w").write(json.dumps(d, indent=1))
print("purged:", len(bad), "| kept:", len(d))
