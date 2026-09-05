#!/usr/bin/env python3
"""Run issue-only resolution on SWE-ContextBench tasks using their Docker images
for the environment and their run_evaluation.py for scoring."""
import json, os, re, subprocess, sys, tempfile, shutil, time
from pathlib import Path

sys.path.insert(0, "benchmarks")
import importlib.util
spec = importlib.util.spec_from_file_location("rk", "benchmarks/resolution_kindb_omp.py")
rk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rk)

SCB = Path(os.environ.get("SCB_DIR", "/tmp/scb"))
LITE = SCB / "cases" / "SWEContextBench Lite"
OUT = Path(os.environ.get("OUT", "benchmarks/baseline_results/scb_docker_issue.json"))
IMG_REPO = "jiayuanz3/swecontextbench"
FILE_RE = re.compile(r'^\+\+\+ b/(.+)$', re.M)

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)
def img_tag(iid):
    return f"{IMG_REPO}:{iid.replace('__','.').lower()}"
def code_files(patch):
    return [f for f in sorted(set(FILE_RE.findall(patch or ""))) if f.endswith((".py",".pyx",".pyi"))]

def resolve_issue_only(repo_dir, issue, target_rels):
    for rel in target_rels:
        pre = sh(["git","-C",str(repo_dir),"show","HEAD:"+rel]).stdout
        if pre.strip():
            (repo_dir/rel).write_text(pre, encoding="utf-8")
    before = sh(["git","-C",str(repo_dir),"diff"]).stdout
    named = ", ".join(target_rels)
    user = ("# Issue\n" + issue + "\n\nResolve this issue by editing ONLY these file(s): "
            + named + ".\nRead them, then make the smallest change that resolves the issue.")
    frame, err = rk.run_omp(repo_dir, rk.RES_SYS, user)
    if err: sys.stderr.write(f"omp error: {err}\n")
    tok = dict(rk.LAST_USAGE)
    after = sh(["git","-C",str(repo_dir),"diff"]).stdout
    edited = (after.strip() != before.strip()) and bool(after.strip())
    return edited, tok, after

def score_with_their_eval(iid, task_json, model_patch, run_id):
    pred = [{"instance_id": iid, "model_name_or_path": "coundetrip-issue-only", "model_patch": model_patch}]
    pf = Path(f"/tmp/pred_{iid.replace('__','_')}.json")
    pf.write_text(json.dumps(pred), encoding="utf-8")
    cp = subprocess.run(
        ["python3","-m","swebench_memory.harness.run_evaluation",
         "--dataset_name", str(task_json), "--predictions_path", str(pf), "--run_id", run_id],
        cwd=str(SCB), capture_output=True, text=True, timeout=2400)
    out = cp.stdout + cp.stderr
    m = re.search(r"Resolved:\s*(True|False)", out)
    resolved = (m.group(1)=="True") if m else None
    return resolved, out[-500:]

def process(iid):
    task_json = LITE / f"{iid}.json"
    if not task_json.exists(): return {"error": "no task json"}
    d = json.loads(task_json.read_text())
    issue = d["problem_statement"]; targets = code_files(d["patch"])
    if not targets: return {"error": "no code target"}
    tag = img_tag(iid)
    print(f"[{iid}] pull {tag} ...", flush=True); t0=time.time()
    pl = sh(["docker","pull",tag])
    if pl.returncode != 0: return {"error": "pull failed: "+pl.stderr[-200:]}
    pull_s = time.time()-t0
    scratch = Path(tempfile.mkdtemp(prefix=f"scb_{iid.replace('__','_')}_"))
    cid = sh(["docker","create",tag]).stdout.strip()
    sh(["docker","cp",f"{cid}:/testbed", str(scratch/"repo")]); sh(["docker","rm",cid])
    repo = scratch/"repo"
    if not repo.exists():
        shutil.rmtree(scratch, ignore_errors=True); return {"error": "extract failed"}
    sh(["sudo","chown","-R",f"{os.getuid()}:{os.getgid()}", str(repo)])
    print(f"[{iid}] resolve (targets: {targets}) ...", flush=True)
    edited, tok, diff = resolve_issue_only(repo, issue, targets)
    row = {"tokens": tok, "pull_s": round(pull_s), "targets": targets}
    if not edited:
        row["resolved"]=None; row["note"]="no edit"
        shutil.rmtree(scratch, ignore_errors=True); return row
    resolved, tail = score_with_their_eval(iid, task_json, diff, f"scb_{iid.replace('__','_')}")
    row["resolved"]=resolved; row["eval_tail"]=tail
    shutil.rmtree(scratch, ignore_errors=True); return row

def main():
    args = sys.argv[1:]
    ids = [l.strip() for l in Path(args[1]).read_text().splitlines() if l.strip()] if (args and args[0]=="--file") else args
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for iid in ids:
        if iid in results and results[iid].get("resolved") is not None:
            print(f"[{iid}] already done, skip"); continue
        try: results[iid] = process(iid)
        except Exception as e: results[iid] = {"error": str(e)}
        OUT.write_text(json.dumps(results, indent=1))
        r=results[iid]; print(f"[{iid}] resolved={r.get('resolved')} tok={r.get('tokens',{}).get('total')} err={r.get('error','')}", flush=True)
    done=[v for v in results.values() if v.get('resolved') is not None]
    res=sum(1 for v in done if v.get('resolved'))
    tin=sum(v.get('tokens',{}).get('input',0) for v in results.values())
    tout=sum(v.get('tokens',{}).get('output',0) for v in results.values())
    print(f"\n=== SUMMARY: {res}/{len(done)} resolved | tokens in={tin} out={tout} total={tin+tout} ===")

if __name__ == "__main__":
    main()
