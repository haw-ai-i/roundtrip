"""Stand up a SWE-Bench task's environment for a coundetrip roundtrip fixture.

Clone the repo at base_commit, editable-install with an era-pinned pytest, apply
the gold + test patches (so the original passes the oracle by construction), and
run the task's tests to confirm the known-good baseline. Works for pure-Python
repos (sympy, flask, requests, pytest, django, pylint, sphinx).

Usage:
    uv run python benchmarks/setup_swebench_env.py sympy__sympy-24909
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

_FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)


def run(cmd, cwd=None, check=True):
    print(">>", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), check=check)



PYTHON_FOR_REPO = {
    # django 2.x-3.x era: distutils (removed 3.12), older stdlib
    "django__django-1": "3.9",
    "django__django-2": "3.9",
    "django__django-3": "3.10",
    "django__django-4": "3.10",
    "django__django-5": "3.11",
    # pytest tests itself; 5.x-6.x source uses ast.Str (removed 3.12)
    "pytest-dev__pytest": "3.9",
    # sphinx 4.1 era: version-guarded "from types import Union" (3.10-alpha name)
    "sphinx-doc__sphinx-9": "3.9",
    "sphinx-doc__sphinx-93": "3.9",
    "sphinx-doc__sphinx-94": "3.9",
    # sphinx 2.x-3.x era (7xxx-8xxx ids)
    "sphinx-doc__sphinx-7": "3.9",
    "sphinx-doc__sphinx-8": "3.9",
    # this instance's test_rewriting imports sympy._compilation -> distutils
    "sympy__sympy-22080": "3.10",
    # sphinx 3.x era (85xx ids): types.Union-era code, needs a pre-3.10 stdlib
    "sphinx-doc__sphinx-85": "3.9",
    # pre-2021 sympy (1xxxx ids) predates the distutils removal; use its era Python
    # 2017-2018 sympy (11xxx-14xxx): collections ABC aliases removed in 3.10
    "sympy__sympy-11": "3.9",
    "sympy__sympy-12": "3.9",
    "sympy__sympy-13": "3.9",
    "sympy__sympy-14": "3.9",
    # 2021 sympy (21xxx): still needs distutils
    "sympy__sympy-21": "3.10",
    # 2020 sympy (20xxx): distutils still required, removed in 3.12
    "sympy__sympy-20": "3.10",
    # 2019-2020 sympy (15xxx-19xxx): fine on 3.10
    "sympy__sympy-1": "3.10",
    # Era-appropriate interpreters. Some repos' pinned dependency stacks have no
    # wheels for the current Python (e.g. numpy<2 stops at 3.12), so the venv is
    # created with an interpreter of the instance's era, resolved via uv.
    "pydata__xarray": "3.10",
    # pylint: pre-3.11 wrapt uses inspect.formatargspec (removed in 3.11)
    "pylint-dev__pylint-4": "3.9",
    "pylint-dev__pylint-6": "3.10",
    "pylint-dev__pylint-8": "3.10",
    "mwaskom__seaborn-3": "3.10",
}

EXTRA_PINS = {
    "sphinx-doc__sphinx-7": [
        "setuptools<81", "standard-imghdr", "jinja2<3.0", "markupsafe<2.1", "docutils<0.17",
        "sphinxcontrib-applehelp==1.0.2", "sphinxcontrib-devhelp==1.0.2",
        "sphinxcontrib-htmlhelp==2.0.0", "sphinxcontrib-serializinghtml==1.1.5",
        "sphinxcontrib-qthelp==1.0.3", "sphinxcontrib-jsmath==1.0.1",
        "alabaster==0.7.12",
    ],
    "sphinx-doc__sphinx-8": [
        "setuptools<81", "standard-imghdr", "jinja2<3.0", "markupsafe<2.1", "docutils<0.17",
        "sphinxcontrib-applehelp==1.0.2", "sphinxcontrib-devhelp==1.0.2",
        "sphinxcontrib-htmlhelp==2.0.0", "sphinxcontrib-serializinghtml==1.1.5",
        "sphinxcontrib-qthelp==1.0.3", "sphinxcontrib-jsmath==1.0.1",
        "alabaster==0.7.12",
    ],
    # sphinx 3.x era: jinja2 3 removed environmentfilter; docutils 0.17 moved roman
    "sphinx-doc__sphinx-85": [
        "setuptools<81", "standard-imghdr", "jinja2<3.0", "markupsafe<2.1", "docutils<0.17",
        "sphinxcontrib-applehelp==1.0.2", "sphinxcontrib-devhelp==1.0.2",
        "sphinxcontrib-htmlhelp==2.0.0", "sphinxcontrib-serializinghtml==1.1.5",
        "sphinxcontrib-qthelp==1.0.3", "sphinxcontrib-jsmath==1.0.1",
        "alabaster==0.7.12",
    ],
    # pre-2021 sympy: old conftest uses the removed py library API
    "sympy__sympy-1": ["py<1.9"],
    "pydata__xarray": ["numpy<2", "pandas<2.1", "dask[array]<2023", "scipy<1.11", "bottleneck"],
    # Per-repo dependency pins discovered by probing (see verified_build_log*).
    # sphinx 4.x era on Python 3.14: pkg_resources removal, imghdr removal,
    # and unpinned sphinxcontrib helpers drifting to Sphinx>=5 requirements.
    "sphinx-doc__sphinx": [
        "setuptools<81", "standard-imghdr",
        "sphinxcontrib-applehelp==1.0.2", "sphinxcontrib-devhelp==1.0.2",
        "sphinxcontrib-htmlhelp==2.0.0", "sphinxcontrib-serializinghtml==1.1.5",
        "sphinxcontrib-qthelp==1.0.3", "sphinxcontrib-jsmath==1.0.1",
        "alabaster==0.7.12",
    ],
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--base", default=str(Path.home() / "Desktop/coundetrip/swebench_envs"))
    ap.add_argument("--pytest", default="7.4.4", help="pytest version to pin (era-dependent)")
    ap.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("Need `datasets`: run `uv pip install datasets`.")

    if args.dataset.endswith(".json") and Path(args.dataset).exists():
        ds = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    else:
        ds = load_dataset(args.dataset, split="test")
    r = next((x for x in ds if x["instance_id"] == args.instance_id), None)
    if r is None:
        sys.exit(f"instance {args.instance_id} not found in {args.dataset}")

    target = Path(args.base) / args.instance_id
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{r['repo']}.git"
    cache = Path.home() / (r["repo"].split("/")[-1] + "_cache.git")
    if target.exists():
        shutil.rmtree(target)
    if cache.exists():
        # Local cache clone: instant, offline, full history so any commit checks out.
        run(["git", "clone", "--quiet", "--local", str(cache), str(target)])
        run(["git", "checkout", "--quiet", r["base_commit"]], cwd=target)
    else:
        # No cache for this repo yet: fall back to a network fetch of the commit.
        target.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "--quiet"], cwd=target)
        run(["git", "remote", "add", "origin", url], cwd=target)
        try:
            run(["git", "fetch", "--quiet", "--depth", "1", "origin", r["base_commit"]], cwd=target)
            run(["git", "checkout", "--quiet", "FETCH_HEAD"], cwd=target)
        except Exception:
            try:
                run(["git", "fetch", "--quiet", "--filter=blob:none", "origin", r["base_commit"]], cwd=target)
                run(["git", "checkout", "--quiet", "FETCH_HEAD"], cwd=target)
            except Exception as e2:
                print(f">> partial fetch failed ({e2}); full blobless clone", file=sys.stderr)
                shutil.rmtree(target)
                run(["git", "clone", "--quiet", "--filter=blob:none", url, str(target)])
                run(["git", "checkout", "--quiet", r["base_commit"]], cwd=target)

    venv = target / ".venv"
    base_python = sys.executable
    for prefix, pyver in PYTHON_FOR_REPO.items():
        if args.instance_id.startswith(prefix):
            found = subprocess.run(["uv", "python", "find", pyver],
                                   capture_output=True, text=True)
            if found.returncode == 0 and found.stdout.strip():
                base_python = found.stdout.strip()
                print(f">> era interpreter for {prefix}: Python {pyver} at {base_python}")
            else:
                print(f">> WARNING: Python {pyver} not found via uv; "
                      f"falling back to {sys.executable}. Run: uv python install {pyver}")
            break
    run([base_python, "-m", "venv", str(venv)])
    py = venv / "bin" / "python"
    run([str(py), "-m", "pip", "install", "-q", "-U", "pip"])
    run([str(py), "-m", "pip", "install", "-q", "-e", "."], cwd=target)
    # When the repo under test IS pytest, its own editable-installed source is the
    # pytest being exercised; installing a released pytest would clobber it.
    if not args.instance_id.startswith("pytest-dev__pytest"):
        run([str(py), "-m", "pip", "install", "-q", f"pytest=={args.pytest}"])
    for prefix, pins in EXTRA_PINS.items():
        if args.instance_id.startswith(prefix):
            run([str(py), "-m", "pip", "install", "-q", *pins])


    (target / "_gold.patch").write_text(r["patch"], encoding="utf-8")
    (target / "_test.patch").write_text(r["test_patch"], encoding="utf-8")
    run(["git", "apply", "_gold.patch"], cwd=target)
    run(["git", "apply", "_test.patch"], cwd=target)

    test_files = _FILE_RE.findall(r["test_patch"])
    gold_files = _FILE_RE.findall(r["patch"])
    f2p = r["FAIL_TO_PASS"] if isinstance(r["FAIL_TO_PASS"], list) else json.loads(r["FAIL_TO_PASS"])
    p2p = r["PASS_TO_PASS"] if isinstance(r["PASS_TO_PASS"], list) else json.loads(r["PASS_TO_PASS"])

    print(f"\n>> oracle: {len(f2p)} FAIL_TO_PASS + {len(p2p)} PASS_TO_PASS in {test_files}")
    cp = run([str(py), "-m", "pytest", "-q", *test_files], cwd=target, check=False)

    print("\n" + "=" * 60)
    print(f"env ready:        {target}")
    print(f"venv python:      {py}")
    print(f"roundtrip target: {gold_files}")
    print(f"oracle tests:     {test_files}")
    print(f"baseline exit:    {cp.returncode}  (0 = all oracle tests pass)")
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
