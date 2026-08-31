"""Turn SWE-ContextBench Lite task JSONs into coundetrip fixture dirs
(issue.md + oracle_env.json) so the existing resolve+score harness runs on them.
Also emits a local dataset json for setup_swebench_env.py.
Does NOT build envs or run anything — pure file prep."""
import json, re, sys
from pathlib import Path

SCB = Path("/tmp/scb/cases/SWEContextBench Lite")
FIXROOT = Path("benchmarks/fixtures_scb")
DATASET = Path("benchmarks/scb_lite_dataset.json")
ENVBASE = "~/coundetrip/swebench_envs"
FILE_RE = re.compile(r'^\+\+\+ b/(.+)$', re.M)  # files touched by a diff

CODE_EXT = (".py", ".pyx", ".pyi")
def files_in_patch(patch, code_only=False):
    fs = sorted(set(FILE_RE.findall(patch or "")))
    if code_only:
        fs = [f for f in fs if f.endswith(CODE_EXT)]
    return fs

def runner_for(repo):
    return "django" if "django" in repo.lower() else "pytest"

def to_django_name(nodeid):
    """tests/forms_tests/tests/test_formsets.py::Cls::method
       -> forms_tests.tests.test_formsets.Cls.method
       (django's runtests.py expects dotted labels, not pytest node-ids)."""
    parts = nodeid.split("::")
    filepath = parts[0]
    # strip leading tests/ and .py, dot the path
    mod = filepath[:-3] if filepath.endswith(".py") else filepath
    if mod.startswith("tests/"):
        mod = mod[len("tests/"):]
    mod = mod.replace("/", ".")
    rest = parts[1:]  # class, method (parametrization already excluded for django)
    # drop any pytest parametrization [..] on the last segment
    rest = [seg.split("[")[0] for seg in rest]
    return ".".join([mod] + rest)

def main():
    tasks = sorted(SCB.glob("*.json"))
    print(f"{len(tasks)} SCB Lite tasks")
    FIXROOT.mkdir(parents=True, exist_ok=True)
    dataset = []
    built = 0
    for tf in tasks:
        d = json.loads(tf.read_text())
        iid = d["instance_id"]
        target_rels = files_in_patch(d["patch"], code_only=True)
        oracle_files = files_in_patch(d.get("test_patch", ""))
        if not target_rels:
            print(f"  SKIP {iid}: no files in patch"); continue
        f2p = json.loads(d["FAIL_TO_PASS"]) if isinstance(d["FAIL_TO_PASS"], str) else d["FAIL_TO_PASS"]
        p2p = json.loads(d["PASS_TO_PASS"]) if isinstance(d["PASS_TO_PASS"], str) else d["PASS_TO_PASS"]
        fdir = FIXROOT / iid
        fdir.mkdir(exist_ok=True)
        (fdir / "issue.md").write_text(d["problem_statement"], encoding="utf-8")
        _is_dj = runner_for(d["repo"]) == "django"
        if _is_dj:
            f2p_sel = [to_django_name(x) for x in f2p]
            p2p_sel = [to_django_name(x) for x in p2p]
        else:
            f2p_sel, p2p_sel = f2p, p2p
        oracle_env = {
            "env_path": f"{ENVBASE}/{iid}",
            "target_rel": target_rels[0],
            "target_rels": target_rels,
            "source_basename": Path(target_rels[0]).name,
            "test_selection": f2p_sel + p2p_sel,
            "oracle_files": oracle_files,
            "fail_to_pass": f2p_sel,
            "pass_to_pass": p2p_sel,
            "runner": runner_for(d["repo"]),
        }
        (fdir / "oracle_env.json").write_text(json.dumps(oracle_env, indent=1), encoding="utf-8")
        dataset.append(d)
        built += 1
    DATASET.write_text(json.dumps(dataset, indent=1), encoding="utf-8")
    print(f"built {built} fixtures in {FIXROOT}")
    print(f"dataset written to {DATASET}")
    # quick sanity on one
    if dataset:
        ex = dataset[0]["instance_id"]
        print(f"\nexample {ex}:")
        print((FIXROOT/ex/"oracle_env.json").read_text()[:400])


if __name__ == "__main__":
    main()
