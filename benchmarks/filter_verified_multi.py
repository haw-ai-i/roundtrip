"""Scan SWE-bench Verified across repos for BOTH single-file and multi-file
candidates (gold patch touching 2-5 non-test source files). Free dataset scan;
feeds the package-level design document."""
import json, re, collections
from pathlib import Path
from datasets import load_dataset

FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)
REPOS = ("sympy", "django", "sphinx", "matplotlib", "scikit-learn", "pytest", "astropy", "xarray")

ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
rows = []
for r in ds:
    src = [f for f in FILE_RE.findall(r["patch"]) if "/test" not in f and not f.startswith("test")]
    tst = FILE_RE.findall(r["test_patch"])
    repo = r["repo"].split("/")[-1]
    if not tst or repo not in REPOS:
        continue
    n = len(src)
    if 1 <= n <= 5:
        # shared top-level package of the touched files (proxy for "same subpackage")
        tops = {f.rsplit("/", 1)[0] for f in src}
        rows.append({"id": r["instance_id"], "repo": repo, "nfiles": n,
                     "same_dir": len(tops) == 1, "files": src, "tests": tst})

by = collections.defaultdict(lambda: collections.Counter())
for c in rows:
    key = "1 file" if c["nfiles"] == 1 else ("2-5 same dir" if c["same_dir"] else "2-5 cross dir")
    by[c["repo"]][key] += 1

print(f"{'repo':<14}{'1 file':>8}{'2-5 same dir':>14}{'2-5 cross dir':>15}{'total':>8}")
for repo in REPOS:
    c = by[repo]
    print(f"{repo:<14}{c['1 file']:>8}{c['2-5 same dir']:>14}{c['2-5 cross dir']:>15}{sum(c.values()):>8}")
tot = collections.Counter()
for c in by.values(): tot.update(c)
print(f"{'TOTAL':<14}{tot['1 file']:>8}{tot['2-5 same dir']:>14}{tot['2-5 cross dir']:>15}{sum(tot.values()):>8}")

Path("benchmarks/verified_candidates_multi.json").write_text(json.dumps(rows, indent=1))
print(f"\nsaved {len(rows)} candidates to benchmarks/verified_candidates_multi.json")
