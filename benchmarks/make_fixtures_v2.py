"""Cut fixtures from every built SWE-bench environment, across repos.

Upgrades over the first generator:
  1. Scoped oracle: each fixture scores the instance's own FAIL_TO_PASS +
     PASS_TO_PASS selection, which is how SWE-bench defines resolution, instead
     of whole test files.
  2. Multi-repo: scans the environments directory directly, so sympy, sphinx,
     xarray and anything built later are handled by the same pass.

Every fixture is self-checked: its own gold-patched copy must pass its own
scoped oracle before the fixture is kept.
"""
import ast, json, re, shutil, subprocess, sys
from pathlib import Path

ENVS = Path.home() / "Desktop/coundetrip/swebench_envs"
FIXTURES = Path("benchmarks/fixtures")
ORACLE_TEMPLATE = Path("benchmarks/run_oracle_scoped.py")
FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)


def load_rows():
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    return {r["instance_id"]: r for r in ds}


def contract_names(target, env, modpath):
    tree = ast.parse(target.read_text(errors="ignore"))
    defined = {n.name for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assigned = {t.id for n in tree.body if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)}
    all_defined = defined | assigned
    pub = {n for n in all_defined if not n.startswith("_")}
    mod = modpath[:-3].replace("/", ".")
    pat = re.compile(rf"from\s+{re.escape(mod)}\s+import\s+([^\n(]+|\([^)]*\))")
    imported = set()
    scan_root = env / modpath.split("/")[0]
    if scan_root.is_dir():
        for py in scan_root.rglob("*.py"):
            try:
                txt = py.read_text(errors="ignore")
            except Exception:
                continue
            for m in pat.finditer(txt):
                for name in re.split(r"[,\s()]+", m.group(1)):
                    name = name.strip()
                    if name and name != "import" and name in all_defined:
                        imported.add(name)
    return sorted(pub | imported)


def short_name(iid, target_rel, nfiles=1):
    repo = iid.split("__")[0].replace("-", "_")
    num = iid.split("-")[-1]
    mod = target_rel.split("/")[-1].removesuffix(".py")
    tag = "_multi" if nfiles > 1 else ""
    return f"swe_{repo}_{mod}{tag}_{num}"


def main():
    rows = load_rows()
    made, skipped = [], []
    env_dirs = sorted(d for d in ENVS.iterdir()
                      if d.is_dir() and (d / ".venv/bin/python").exists())
    print(f"scanning {len(env_dirs)} built environments\n")

    for env in env_dirs:
        iid = env.name
        r = rows.get(iid)
        if r is None:
            skipped.append((iid, "not in Verified")); continue
        src = [f for f in FILE_RE.findall(r["patch"])
               if "/test" not in f and not f.startswith("test")]
        if not 1 <= len(src) <= 5:
            skipped.append((iid, f"{len(src)} source files")); continue
        cross_dir = len({f.rsplit("/", 1)[0] for f in src}) > 1
        targets = [(rel, env / rel) for rel in src]
        missing = [rel for rel, t in targets if not t.exists()]
        if missing:
            skipped.append((iid, f"target missing: {missing[0]}")); continue
        target_rel = src[0]  # primary, used for naming
        test_files = FILE_RE.findall(r["test_patch"])
        f2p = json.loads(r["FAIL_TO_PASS"]); p2p = json.loads(r["PASS_TO_PASS"])
        selection = f2p + p2p
        if not selection:
            skipped.append((iid, "empty selection")); continue

        fname = short_name(iid, target_rel, len(targets))
        if len(targets) > 1 and cross_dir:
            fname = fname.replace("_multi_", "_xdir_")
        fdir = FIXTURES / fname
        if fdir.exists():
            shutil.rmtree(fdir)
        (fdir / "scaffold").mkdir(parents=True)
        all_names = {}
        for rel, t in targets:
            spec = fdir / rel
            spec.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(t, spec)
            all_names[rel] = contract_names(t, env, rel)
        names = [n for ns in all_names.values() for n in ns]

        contract = ["# Implementation target\n"]
        if len(targets) == 1:
            contract.append(f"Write the module at `{target_rel}`.\n")
        else:
            contract.append(f"Write the following {len(targets)} modules. They live in the same package and may import each other.\n")
        for rel, ns in all_names.items():
            contract.append(f"\n## `{rel}`\n")
            contract.append("Other modules import these names from it, so they MUST exist with these exact names:\n")
            contract.extend(f"- `{n}`\n" for n in ns)
        contract.append("\nImplement them to satisfy the specification. Do not write tests.\n")
        (fdir / "scaffold" / "CONTRACT.md").write_text("".join(contract))
        (fdir / "oracle_env.json").write_text(json.dumps({
            "env_path": f"~/Desktop/coundetrip/swebench_envs/{iid}",
            "target_rel": target_rel,
            "target_rels": [rel for rel, _ in targets],
            "source_basename": target_rel.split("/")[-1],
            "test_selection": selection,
            "oracle_files": test_files,
            "fail_to_pass": f2p,
            "pass_to_pass": p2p,
        }, indent=2))
        shutil.copy2(ORACLE_TEMPLATE, fdir / "run_oracle.py")
        (fdir / "coundetrip.yaml").write_text(
            f"name: {fname}\ntest_command:\n  - python\n  - run_oracle.py\n"
            "source_paths:\n" + "".join(f"  - {rel}\n" for rel, _ in targets) + "scaffold_paths:\n  - scaffold\n"
            f"test_paths:\n  - run_oracle.py\n  - oracle_env.json\n")
        (fdir / "issue.md").write_text(r["problem_statement"])

        check = subprocess.run([sys.executable, "run_oracle.py"], cwd=fdir,
                               capture_output=True, text=True)
        if check.returncode != 0:
            # Baseline calibration: a PASS_TO_PASS test that fails on the gold
            # code is environment drift and cannot inform regeneration scoring.
            # Drop such tests with a logged record. A FAIL_TO_PASS failure on
            # gold invalidates the fixture.
            out = check.stdout + check.stderr
            failed = [l.split()[1] for l in out.splitlines()
                      if l.startswith("FAILED ") and len(l.split()) > 1]
            # sympy-style selections carry bare test names; normalize failed
            # node ids to base function names so removal and the F2P guard
            # compare like with like.
            if selection and "::" not in selection[0]:
                failed = [f.split("::")[-1].split("[")[0] for f in failed]
            f2p_set = set(f2p)
            if failed and not (set(failed) & f2p_set):
                new_sel = [t for t in selection if t not in set(failed)]
                cfgp = fdir / "oracle_env.json"
                cfg = json.loads(cfgp.read_text())
                cfg["test_selection"] = new_sel
                cfg["dropped_p2p_on_gold"] = sorted(set(failed))
                cfgp.write_text(json.dumps(cfg, indent=2))
                check = subprocess.run([sys.executable, "run_oracle.py"], cwd=fdir,
                                       capture_output=True, text=True)
                if check.returncode == 0:
                    print(f"CAL  {fname:<44} dropped {len(set(failed))} drifted P2P on gold")
        if check.returncode == 0:
            made.append(fname)
            print(f"OK   {fname:<44} ({len(names)} names, {len(selection)} tests)")
        else:
            tail = (check.stdout.strip().splitlines()
                    or check.stderr.strip().splitlines() or ["?"])[-1]
            skipped.append((iid, f"self-check exit {check.returncode}: {tail[:90]}"))
            print(f"FAIL {fname:<44} {tail[:70]}")
            shutil.rmtree(fdir)

    print(f"\n{len(made)} fixtures made and self-checked; {len(skipped)} skipped")
    for iid, why in skipped:
        print(f"  skipped {iid}: {why}")
    Path("benchmarks/fixtures_v2.json").write_text(json.dumps(
        {"made": made, "skipped": [{"id": i, "reason": w} for i, w in skipped]}, indent=1))


if __name__ == "__main__":
    main()
