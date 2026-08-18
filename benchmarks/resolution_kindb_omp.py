"""Section 7 transfer experiment over multi-file Kind-B instances, omp as agent.

For each fixture the agent resolves the issue with the repository PRESENT in its
working directory (standard issue-resolution). Two conditions: issue only; issue
+ optimized-prompt description. Descriptions come from the PRE-FIX target files
(via git HEAD) so the fix cannot leak. Scoring reuses run_oracle_scoped.py.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

from coundetrip.scoring import parse_pytest_summary

N = 1
DISCOVERED = Path("benchmarks/stage3_best_prompt.txt").read_text(encoding="utf-8")
OMP = os.environ.get("COUNDETRIP_OMP_BIN", "omp")
PROVIDER = "local-qwen"
MODEL = "hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_M"

RES_SYS = ("You are a coding agent resolving a repository issue. The repository "
           "is in your working directory. Read ONLY the file(s) named in the "
           "prompt - do NOT search or grep the rest of the repository. As soon "
           "as you have read them, immediately call your edit tool to apply the "
           "fix to those file(s). Your task is not complete until you have made "
           "an edit. Do not explain the fix instead of making it. Make the "
           "smallest change that resolves the issue.")

DESC_SYS_OPTIMIZED = DISCOVERED

out_path = Path("benchmarks/baseline_results/transfer_kindb_omp.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
results = json.loads(out_path.read_text()) if out_path.exists() else {}


LAST_USAGE = {}


def run_omp(cwd, system_prompt, user_prompt, timeout=2400, tries=4):
    """Call omp once and return (agent_end_frame, error). Retries when omp
    returns no agent_end frame: on a single-slot model node, a call fired
    right after another can come back empty while the node releases the
    prior request. A short, growing settle between tries lets the node idle."""
    # The prompt can exceed the OS argv limit (the optimized condition carries
    # an ~9k-char description), so hand it to omp as an @file reference.
    _pf = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                      encoding="utf-8")
    _pf.write(user_prompt)
    _pf.close()
    cmd = [OMP, "--provider", PROVIDER, "--model", MODEL,
           "--no-session", "--no-lsp", "--mode", "json", "--thinking", "off",
           "--max-time", "20m",
           "--system-prompt", system_prompt, "-p", "@" + _pf.name]
    last_err = None
    _tok = {"input": 0, "output": 0, "total": 0}
    for attempt in range(tries):
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        final = None
        err = None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "agent_end":
                final = obj
            msg = obj.get("message")
            if isinstance(msg, dict):
                if msg.get("stopReason") == "error":
                    err = msg.get("errorMessage")
                _u = msg.get("usage")
                if isinstance(_u, dict) and _u.get("totalTokens"):
                    _tok["input"] = _u.get("input") or 0
                    _tok["output"] = _u.get("output") or 0
                    _tok["total"] = _u.get("totalTokens") or 0
        if final is not None:
            LAST_USAGE.update(_tok)
            os.unlink(_pf.name)
            return final, err
        last_err = err
        time.sleep(2 * (attempt + 1))
    LAST_USAGE.update(_tok)
    os.unlink(_pf.name)
    return None, last_err


def final_text(frame):
    """Return the last assistant message's written text. Accept any content
    block that carries a non-empty `text` field (some blocks are typed
    'text', others carry text alongside a 'thinking' block); skip empties."""
    if not frame:
        return ""
    msgs = frame.get("messages") or []
    for msg in reversed(msgs):
        if msg.get("role") != "assistant":
            continue
        parts = []
        for b in msg.get("content", []):
            if b.get("type") == "thinking":
                continue
            txt = b.get("text", "")
            if txt and txt.strip():
                parts.append(txt)
        t = chr(10).join(parts).strip()
        if t:
            return t
    return ""


def describe(prefix_srcs, system_prompt):
    """Describe the pre-fix source per file, then merge. Each target file is
    described in its own omp turn so a large multi-file target never exhausts
    the context window. Source-only, isolated so no tests leak."""
    parts = []
    for rel, src in prefix_srcs.items():
        with tempfile.TemporaryDirectory(prefix="omp_desc_") as td:
            stage = Path(td)
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src, encoding="utf-8")
            user = ("Read this source file in full using your read tool: " + rel
                    + ". Then write a complete natural-language specification of "
                    "this file as your final message. Read the file before writing.")
            got = ""
            for _ in range(4):
                frame, err = run_omp(stage, system_prompt, user)
                if err:
                    sys.stderr.write("describe omp error: " + str(err) + chr(10))
                got = final_text(frame)
                if got.strip():
                    break
        if not got.strip():
            return ""
        parts.append("## " + rel + chr(10) + got.strip())
    return (chr(10) + chr(10)).join(parts)


def resolve_once(env, issue, desc, target_rels):
    """One resolve attempt with the repo present. Copy the env repo (minus
    .git/.venv) into a scratch dir, let omp edit the target file(s) in place,
    return the repo dir (caller scores its target files)."""
    scratch = Path(tempfile.mkdtemp(prefix="omp_resolve_"))
    repo = scratch / "repo"
    shutil.copytree(env, repo,
                    ignore=shutil.ignore_patterns(".git", ".venv"),
                    symlinks=True)
    # setup_swebench_env applies the gold patch to the env so the roundtrip
    # source passes by construction. For issue resolution the agent must face
    # the PRE-FIX code, so restore each target file from the HEAD blob. Test
    # files keep their test patch so the FAIL_TO_PASS tests exist.
    for _rel in target_rels:
        _pre = subprocess.run(["git", "-C", str(env), "show", "HEAD:" + _rel],
                              capture_output=True, text=True).stdout
        if _pre.strip():
            (repo / _rel).write_text(_pre, encoding="utf-8")
    files_line = ", ".join(target_rels)
    user = "# Issue" + chr(10) + issue + chr(10) + chr(10)
    if desc is not None:
        user += "# Module documentation" + chr(10) + desc + chr(10) + chr(10)
    user += ("# Files to edit: " + files_line + chr(10) +
             "Read these files, then edit them in place at exactly these paths "
             "so the issue is resolved.")

    def digests():
        out = {}
        for rel in target_rels:
            f = repo / rel
            if f.exists():
                out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
        return out

    before = digests()
    for _ in range(4):
        frame, err = run_omp(repo, RES_SYS, user)
        if err:
            sys.stderr.write("resolve omp error: " + str(err) + chr(10))
        after = digests()
        if any(after.get(rel) != before.get(rel) for rel in target_rels):
            return repo, True
    return repo, False


def parse_django_summary(stderr, stdout):
    """Django's runtests.py does not print pytest's summary line. It prints
    "Ran N tests in Xs" then "OK" or "FAILED (failures=A, errors=B, ...)".
    Returns (passed, failed)."""
    blob = (stderr or "") + chr(10) + (stdout or "")
    ran = re.search(r"Ran (\d+) tests?", blob)
    total = int(ran.group(1)) if ran else 0
    bad = 0
    fail_line = re.search(r"FAILED \(([^)]*)\)", blob)
    if fail_line:
        for key in ("failures", "errors"):
            mm = re.search(key + r"=(\d+)", fail_line.group(1))
            if mm:
                bad += int(mm.group(1))
        if bad == 0:
            bad = total
    return total - bad, bad


def score(fix, fdir, repo):
    """Copy oracle + oracle_env.json + the agent's edited target files into a
    scoring dir, run the oracle, parse pass/fail counts."""
    with tempfile.TemporaryDirectory(prefix="omp_score_") as td:
        sdir = Path(td)
        shutil.copy2("benchmarks/run_oracle_scoped.py", sdir / "run_oracle_scoped.py")
        shutil.copy2(fdir / "oracle_env.json", sdir / "oracle_env.json")
        cfg = json.loads((fdir / "oracle_env.json").read_text())
        target_rels = cfg.get("target_rels") or [cfg["target_rel"]]
        for rel in target_rels:
            src = repo / rel
            if src.exists():
                dest = sdir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        cp = subprocess.run([sys.executable, "run_oracle_scoped.py"],
                            cwd=str(sdir), capture_output=True, text=True, timeout=1200)
        if cfg.get("runner") == "django":
            return parse_django_summary(cp.stderr, cp.stdout)
        summ = parse_pytest_summary(cp.stderr, cp.stdout)
        return summ.passed, summ.failed


def wait_for_endpoint(tries=30, delay=20):
    """Block until the model endpoint answers. The ssh tunnel drops; without
    this a dead endpoint silently produces unedited repos that still score."""
    import urllib.request
    for _ in range(tries):
        try:
            urllib.request.urlopen("http://127.0.0.1:11434/v1/models", timeout=5)
            return True
        except Exception:
            sys.stderr.write("endpoint down, waiting..." + chr(10))
            time.sleep(delay)
    return False


def main():
    made = json.load(open("benchmarks/fixtures_v2.json"))["made"]
    kindb = [m for m in made if "multi" in m or "xdir" in m]
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    if only:
        kindb = [m for m in kindb if m in only]
    for fix in kindb:
        if fix in results:
            print(fix, "already done, skipping"); continue
        if not wait_for_endpoint():
            print("endpoint unreachable, stopping before recording bad data", flush=True)
            break
        fdir = Path("benchmarks/fixtures") / fix
        cfg = json.loads((fdir / "oracle_env.json").read_text())
        _envs_base = os.environ.get("COUNDETRIP_ENVS_BASE")
        if _envs_base:
            env = Path(_envs_base).expanduser() / Path(cfg["env_path"]).name
        else:
            env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
        target_rels = cfg.get("target_rels") or [cfg["target_rel"]]
        issue = (fdir / "issue.md").read_text(encoding="utf-8")
        prefix_srcs = {}
        for rel in target_rels:
            src = subprocess.run(["git", "-C", str(env), "show", "HEAD:" + rel],
                                 capture_output=True, text=True).stdout
            if src.strip():
                prefix_srcs[rel] = src
        if not prefix_srcs:
            print(fix, "no pre-fix source, skipping"); continue
        descs = {"issue_only": None,
                 "optimized": describe(prefix_srcs, DESC_SYS_OPTIMIZED)}
        row = {}
        for cond in ["issue_only", "optimized"]:
            if cond != "issue_only" and not descs[cond]:
                row[cond] = {"skipped": "describe empty"}; continue
            fracs, resolved = [], 0
            for _ in range(N):
                repo, edited = resolve_once(env, issue, descs[cond], target_rels)
                _used = dict(LAST_USAGE)
                if not edited:
                    shutil.rmtree(repo.parent, ignore_errors=True)
                    row[cond] = {"failed": "agent made no edit (check connection)"}
                    print(fix.ljust(34) + cond.ljust(12) + "NO EDIT - not scored", flush=True)
                    break
                try:
                    p, f = score(fix, fdir, repo)
                finally:
                    shutil.rmtree(repo.parent, ignore_errors=True)
                tot = p + f
                fracs.append(round(p / tot if tot else 0.0, 3))
                if f == 0 and p > 0:
                    resolved += 1
            if not fracs:
                continue
            row[cond] = {"tokens": _used,
                         "fracs": fracs, "mean": round(sum(fracs) / len(fracs), 3),
                         "resolved": str(resolved) + "/" + str(N)}
            print(fix.ljust(34) + cond.ljust(12) + str(fracs) + " resolved=" + str(resolved) + "/" + str(N), flush=True)
        results[fix] = row
        out_path.write_text(json.dumps(results, indent=1))
    print("saved", out_path)


if __name__ == "__main__":
    main()
