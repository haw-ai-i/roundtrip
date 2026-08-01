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
}

EXTRA_PINS = {
    # pre-2021 sympy: old conftest uses the removed py library API
    "sympy__sympy-1": ["py<1.9"],
    "pydata__xarray": ["numpy<2", "pandas<2.1"],
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

    ds = load_dataset(args.dataset, split="test")
    r = next((x for x in ds if x["instance_id"] == args.instance_id), None)
    if r is None:
        sys.exit(f"instance {args.instance_id} not found in {args.dataset}")

    target = Path(args.base) / args.instance_id
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    run(["git", "clone", "--quiet", f"https://github.com/{r['repo']}.git", str(target)])
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
    f2p = json.loads(r["FAIL_TO_PASS"])
    p2p = json.loads(r["PASS_TO_PASS"])

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
