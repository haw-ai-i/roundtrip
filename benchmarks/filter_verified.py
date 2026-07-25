"""Scan SWE-bench Verified for roundtrip-fixture candidates: instances whose gold
patch modifies exactly one non-test source file and whose test patch names the
oracle tests. Costs nothing (dataset scan only)."""
import json, re, collections
from datasets import load_dataset

FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)
SUPPORTED = ("sympy", "flask", "requests", "pytest", "django", "pylint", "sphinx")

ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
cands = []
for r in ds:
    src = [f for f in FILE_RE.findall(r["patch"]) if "/test" not in f and not f.startswith("test")]
    tst = FILE_RE.findall(r["test_patch"])
    if len(src) == 1 and tst:
        repo = r["repo"].split("/")[-1]
        cands.append({"id": r["instance_id"], "repo": repo, "target": src[0],
                      "tests": tst, "supported": repo.startswith(SUPPORTED)})

by_repo = collections.Counter(c["repo"] for c in cands)
sup = [c for c in cands if c["supported"]]
print(f"single-file candidates in Verified: {len(cands)}  |  in supported repos: {len(sup)}")
print("\nby repo:", dict(by_repo.most_common(12)))
print(f"\nfirst 40 supported candidates:")
for c in sup[:40]:
    print(f"  {c['id']:<34} {c['target']}")
json_path = "benchmarks/verified_candidates.json"
open(json_path, "w").write(json.dumps(cands, indent=1))
print(f"\nsaved all {len(cands)} to {json_path}")
