"""Cut fixtures from verified-good Verified envs, matching the committed fixture
format. Self-checks each fixture by running its oracle on its own gold-patched
spec copy, which must pass by construction."""
import ast, json, re, shutil, subprocess, sys
from pathlib import Path

ENVS = Path.home() / "Desktop/coundetrip/swebench_envs"
FIXTURES = Path("benchmarks/fixtures")
TEMPLATE_ORACLE = FIXTURES / "swe_sympy_contains/run_oracle.py"

log2 = json.loads(Path("benchmarks/verified_build_log2.json").read_text())
good = [l for l in log2 if l["ok"]]
cands = {c["id"]: c for c in json.loads(Path("benchmarks/verified_candidates.json").read_text())}

def public_names(target, env, modpath):
    tree = ast.parse(target.read_text())
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
    for py in scan_root.rglob("*.py"):
        try:
            txt = py.read_text()
        except Exception:
            continue
        for m in pat.finditer(txt):
            for name in re.split(r"[,\s()]+", m.group(1)):
                name = name.strip()
                if name and name != "import" and name in all_defined:
                    imported.add(name)
    return sorted(pub | imported)

made, failed = [], []
for l in good:
    iid, tgt = l["id"], l["target"]
    c = cands[iid]
    if len(c["tests"]) != 1:
        failed.append((iid, f"needs 1 oracle test file, has {len(c['tests'])}")); continue
    env = ENVS / iid
    target = env / tgt
    if not target.exists():
        failed.append((iid, "target missing in env")); continue
    short = tgt.split("/")[-1].removesuffix(".py")
    fname = f"swe_v_{short}_{iid.split('-')[-1]}"
    fdir = FIXTURES / fname
    if fdir.exists():
        shutil.rmtree(fdir)
    (fdir / "scaffold").mkdir(parents=True)
    spec_copy = fdir / tgt
    spec_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, spec_copy)
    names = public_names(target, env, tgt)
    (fdir / "scaffold" / "CONTRACT.md").write_text(
        "# Implementation target\n"
        f"Write the module at `{tgt}`.\n"
        "Other modules import these names from it, so they MUST exist with these exact names:\n"
        + "".join(f"- `{n}`\n" for n in names)
        + "Implement them to satisfy the specification. Do not write tests.\n")
    (fdir / "oracle_env.json").write_text(json.dumps({
        "env_path": f"~/Desktop/coundetrip/swebench_envs/{iid}",
        "target_rel": tgt,
        "oracle_rel": c["tests"][0],
        "source_basename": tgt.split("/")[-1]}, indent=2))
    shutil.copy2(TEMPLATE_ORACLE, fdir / "run_oracle.py")
    (fdir / "coundetrip.yaml").write_text(
        f"name: {fname}\ntest_command:\n  - python\n  - run_oracle.py\n"
        f"source_paths:\n  - {tgt}\nscaffold_paths:\n  - scaffold\n"
        f"test_paths:\n  - run_oracle.py\n  - oracle_env.json\n")
    r = subprocess.run([sys.executable, "run_oracle.py"], cwd=fdir,
                       capture_output=True, text=True)
    if r.returncode == 0:
        made.append(fname)
        print(f"OK   {fname}  ({len(names)} contract names)")
    else:
        tail = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["?"])[-1]
        failed.append((iid, f"self-check exit {r.returncode}: {tail}"))
        print(f"FAIL {fname}: {tail}")
        shutil.rmtree(fdir)

print(f"\n{len(made)} fixtures made and self-checked")
for iid, why in failed:
    print(f"  excluded {iid}: {why}")
Path("benchmarks/verified_fixtures.json").write_text(json.dumps(made, indent=1))
