"""Issue-resolution v3: documentation as durable source. The agent does NOT see
the current file. Conditions: issue only; issue + baseline-prompt description;
issue + optimized-prompt description. Descriptions are generated from the
PRE-FIX file. Ceiling for comparison = v2's issue+file condition."""
import json, os, re, statistics, subprocess, sys
from pathlib import Path

sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient, _DESCRIBE_SYSTEM, parse_file_blocks

MODEL = "gemini-3.5-flash"
N = 3
DISCOVERED = Path("benchmarks/stage3_best_prompt.txt").read_text()
FIXES = ["swe_sympy_contains", "swe_sympy_unitsystem", "swe_sympy_unitsystem_v2"] + \
        json.loads(Path("benchmarks/verified_fixtures.json").read_text())

RES_SYS = ("You are a coding agent resolving a repository issue. You are given the "
           "issue and, possibly, documentation of the module to modify. You do NOT "
           "have the module's source. Write the COMPLETE Python file at the stated "
           "path so that it satisfies the documentation and resolves the issue. "
           "Output ONLY the file contents, no explanations, no markdown fences.")


def extract_code(reply):
    files = parse_file_blocks(reply)
    if files:
        return next(iter(files.values()))
    m = re.search(r"```(?:python)?\s*\n(.*?)```", reply, re.DOTALL)
    return m.group(1) if m else reply


def run_tests(env, target_rel, oracle_rel, code):
    import shutil
    target = env / target_rel
    orig = target.with_suffix(target.suffix + ".orig")
    venv_py = env / ".venv/bin/python"
    try:
        target.write_text(code)
        cp = subprocess.run([str(venv_py), "-m", "pytest",
                             str(env / oracle_rel), "-q", "--tb=no"],
                            capture_output=True, text=True, timeout=600)
        out = cp.stdout
        p = sum(int(x) for x in re.findall(r"(\d+) passed", out))
        f = sum(int(x) for x in re.findall(r"(\d+) failed", out))
        e = sum(int(x) for x in re.findall(r"(\d+) error", out))
        return p, f + e
    except Exception:
        return 0, 1
    finally:
        if orig.exists():
            shutil.copy2(orig, target)


results = {}
out_path = Path("benchmarks/RESOLUTION_V3.json")
if out_path.exists():
    results = json.loads(out_path.read_text())

for fix in FIXES:
    if fix in results:
        print(f"{fix}: already done, skipping"); continue
    fdir = Path("benchmarks/fixtures") / fix
    cfg = json.loads((fdir / "oracle_env.json").read_text())
    env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
    target_rel, oracle_rel = cfg["target_rel"], cfg["oracle_rel"]
    issue = (fdir / "issue.md").read_text()
    prefix_src = subprocess.run(["git", "-C", str(env), "show", f"HEAD:{target_rel}"],
                                capture_output=True, text=True).stdout
    if not prefix_src.strip():
        print(f"{fix}: could not read pre-fix source, skipping"); continue

    client = GeminiClient(model=MODEL)
    descs = {"issue_only": None}
    for label, prompt in [("baseline", _DESCRIBE_SYSTEM), ("optimized", DISCOVERED)]:
        try:
            descs[label] = client.complete(system=prompt, user=prefix_src)
        except Exception as ex:
            descs[label] = None
            print(f"{fix}: describe {label} failed: {str(ex)[:60]}")

    row = {}
    for cond in ["issue_only", "baseline", "optimized"]:
        if cond != "issue_only" and descs[cond] is None:
            row[cond] = {"skipped": "describe failed"}; continue
        fracs, resolved = [], 0
        for i in range(N):
            user = f"# Issue\n{issue}\n\n"
            if cond != "issue_only":
                user += f"# Module documentation\n{descs[cond]}\n\n"
            user += f"# File to write: {target_rel}\n"
            try:
                reply = client.complete(system=RES_SYS, user=user)
                p, f_ = run_tests(env, target_rel, oracle_rel, extract_code(reply))
            except Exception:
                p, f_ = 0, 1
            tot = p + f_
            fracs.append(round(p / tot if tot else 0.0, 3))
            if f_ == 0 and p > 0:
                resolved += 1
        row[cond] = {"fracs": fracs, "mean": round(statistics.mean(fracs), 3),
                     "resolved": f"{resolved}/{N}"}
        print(f"{fix:<28}{cond:<12}fracs={fracs}  resolved={resolved}/{N}", flush=True)
    results[fix] = row
    out_path.write_text(json.dumps(results, indent=1))

print("\nsaved", out_path)
