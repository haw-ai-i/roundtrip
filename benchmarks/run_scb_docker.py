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

def _restore_targets(repo_dir, target_rels):
    for rel in target_rels:
        pre = sh(["git","-C",str(repo_dir),"show","HEAD:"+rel]).stdout
        if pre.strip():
            (repo_dir/rel).write_text(pre, encoding="utf-8")

def resolve_one(repo_dir, issue, target_rels, extra=""):
    """Resolve with optional extra documentation prepended. Restores targets to
    pre-fix first, returns (edited, tokens, diff)."""
    _restore_targets(repo_dir, target_rels)
    before = sh(["git","-C",str(repo_dir),"diff"]).stdout
    named = ", ".join(target_rels)
    block = (extra.strip() + "\n\n") if extra and extra.strip() else ""
    user = (block + "# Issue\n" + issue + "\n\nResolve this issue by editing ONLY these file(s): "
            + named + ".\nRead them, then make the smallest change that resolves the issue.")
    frame, err = rk.run_omp(repo_dir, rk.RES_SYS, user)
    if err: sys.stderr.write(f"omp error: {err}\n")
    tok = dict(rk.LAST_USAGE)
    after = sh(["git","-C",str(repo_dir),"diff"]).stdout
    edited = (after.strip() != before.strip()) and bool(after.strip())
    return edited, tok, after

def make_compact(repo_dir, target_rels):
    """Generate a compact static summary of the target file(s) via describe->summarize."""
    srcs = {}
    for rel in target_rels:
        f = repo_dir / rel
        if f.exists():
            srcs[rel] = f.read_text(encoding="utf-8", errors="ignore")
    if not srcs:
        return "", {}
    full = rk.describe(srcs, rk.DESC_SYS_OPTIMIZED)
    comp = rk.summarize(full, budget_words=90)
    tok = dict(rk.LAST_USAGE)
    return comp, tok

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

    conds = os.environ.get("COUNDETRIP_CONDS", "issue_only,context,compact").split(",")
    # context.md for the context arm
    ctx_txt = ""
    ctxf = Path("benchmarks/fixtures_scb") / iid / "context.md"
    if ctxf.exists(): ctx_txt = ctxf.read_text(encoding="utf-8")

    row = {"pull_s": round(pull_s), "targets": targets, "conds": {}}
    # precompute compact summary once (from pre-fix target) if needed
    compact_txt, compact_tok = "", {}
    if "compact" in conds:
        _restore_targets(repo, targets)
        print(f"[{iid}] make compact summary ...", flush=True)
        compact_txt, compact_tok = make_compact(repo, targets)

    for cond in conds:
        extra = {"issue_only":"", "context":ctx_txt, "compact":compact_txt}.get(cond, "")
        print(f"[{iid}] resolve [{cond}] ...", flush=True)
        edited, tok, diff = resolve_one(repo, issue, targets, extra)
        c = {"tokens": tok}
        if cond == "compact":
            c["summary_tokens"] = compact_tok
            c["summary_words"] = len(compact_txt.split())
        if not edited:
            c["resolved"]=None; c["note"]="no edit"
        else:
            resolved, tail = score_with_their_eval(iid, task_json, diff, f"scb_{cond}_{iid.replace('__','_')}")
            c["resolved"]=resolved; c["eval_tail"]=tail
        row["conds"][cond] = c

    shutil.rmtree(scratch, ignore_errors=True)
    return row

def main():
    args = sys.argv[1:]
    ids = [l.strip() for l in Path(args[1]).read_text().splitlines() if l.strip()] if (args and args[0]=="--file") else args
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    conds = os.environ.get("COUNDETRIP_CONDS", "issue_only,context,compact").split(",")
    for iid in ids:
        r0 = results.get(iid, {})
        if r0.get("conds") and all(c in r0["conds"] for c in conds):
            print(f"[{iid}] already done, skip"); continue
        try: results[iid] = process(iid)
        except Exception as e: results[iid] = {"error": str(e)}
        OUT.write_text(json.dumps(results, indent=1))
        r=results[iid]
        summ=" ".join(f"{c}={r.get('conds',{}).get(c,{}).get('resolved')}" for c in conds)
        print(f"[{iid}] {summ} err={r.get('error','')}", flush=True)
    # summary per condition
    print("\n=== SUMMARY ===")
    for c in conds:
        scored=[v['conds'][c] for v in results.values() if v.get('conds',{}).get(c,{}).get('resolved') is not None]
        res=sum(1 for x in scored if x.get('resolved'))
        print(f"  {c:<11}: {res}/{len(scored)} resolved")
    tot=sum(cc.get('tokens',{}).get('total',0) for v in results.values() for cc in v.get('conds',{}).values())
    tot+=sum(v['conds'].get('compact',{}).get('summary_tokens',{}).get('total',0) for v in results.values() if v.get('conds',{}).get('compact'))
    print(f"  total tokens (all conds+summaries): {tot:,}")

if __name__ == "__main__":
    main()
