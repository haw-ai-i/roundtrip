"""Targeted-edit resolution: agent never loads the whole file. Step 1: from the
issue (+ optionally the description) it names the symbols it needs. Step 2: it
gets only those symbols' source and returns replacements, spliced in and tested.
Conditions: guided (optimized description) vs unguided. Metrics: resolved rate,
pass fraction, tokens; full-file prompt cost recorded as ceiling reference."""
import ast, json, os, re, statistics, subprocess, sys
from pathlib import Path

sys.path.insert(0, "src")
from coundetrip.llm_agent import GeminiClient
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
MODEL = "gemini-3.5-flash"
N = 3
DISCOVERED = Path("benchmarks/stage3_best_prompt.txt").read_text()
FIXES = ["swe_sympy_contains", "swe_sympy_unitsystem", "swe_sympy_unitsystem_v2"] + \
        json.loads(Path("benchmarks/verified_fixtures.json").read_text())

PLAN_SYS = ("You plan a minimal code edit. Given a repository issue and possibly "
            "module documentation, name the top-level functions or classes of the "
            "module that must be inspected and modified to resolve the issue. "
            "Reply with ONLY a JSON list of symbol names from the provided list.")
EDIT_SYS = ("You are resolving a repository issue by editing only the shown "
            "symbols. Return each symbol you modify as a block:\n"
            "=== <symbol name> ===\n<complete replacement source for that symbol>\n"
            "You may add one block '=== imports ===' with new import lines. "
            "Do not return symbols you leave unchanged. No markdown fences.")


def toks(*texts):
    return sum(len(ENC.encode(t)) for t in texts)


def symbol_spans(src):
    tree = ast.parse(src)
    spans = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = n.lineno
            if n.decorator_list:
                start = min([n.lineno] + [d.lineno for d in n.decorator_list])
            spans[n.name] = (start, n.end_lineno)
    return spans


def splice(src, spans, blocks):
    lines = src.splitlines()
    repl = sorted(((spans[k], v) for k, v in blocks.items() if k in spans),
                  key=lambda x: -x[0][0])
    for (s, e), code in repl:
        lines[s - 1:e] = code.splitlines()
    if "imports" in blocks:
        last_imp = 0
        for i, l in enumerate(lines[:80]):
            if l.startswith(("import ", "from ")):
                last_imp = i
        lines[last_imp + 1:last_imp + 1] = blocks["imports"].splitlines()
    return "\n".join(lines) + "\n"


def parse_blocks(reply):
    out = {}
    for m in re.finditer(r"^=== (.+?) ===\n(.*?)(?=^=== |\Z)", reply, re.M | re.S):
        out[m.group(1).strip()] = m.group(2).rstrip("\n")
    return out


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
        p = sum(int(x) for x in re.findall(r"(\d+) passed", cp.stdout))
        f = sum(int(x) for x in re.findall(r"(\d+) failed", cp.stdout))
        e = sum(int(x) for x in re.findall(r"(\d+) error", cp.stdout))
        return p, f + e
    except Exception:
        return 0, 1
    finally:
        if orig.exists():
            shutil.copy2(orig, target)


results = {}
out_path = Path("benchmarks/RESOLUTION_V4.json")
if out_path.exists():
    results = json.loads(out_path.read_text())

for fix in FIXES:
    if fix in results:
        print(f"{fix}: done, skipping"); continue
    fdir = Path("benchmarks/fixtures") / fix
    cfg = json.loads((fdir / "oracle_env.json").read_text())
    env = Path(os.path.expandvars(cfg["env_path"])).expanduser()
    target_rel, oracle_rel = cfg["target_rel"], cfg["oracle_rel"]
    issue = (fdir / "issue.md").read_text()
    src = subprocess.run(["git", "-C", str(env), "show", f"HEAD:{target_rel}"],
                         capture_output=True, text=True).stdout
    if not src.strip():
        print(f"{fix}: no pre-fix source, skipping"); continue
    spans = symbol_spans(src)
    names = sorted(spans)
    client = GeminiClient(model=MODEL)
    try:
        desc = client.complete(system=DISCOVERED, user=src)
    except Exception as ex:
        print(f"{fix}: describe failed: {str(ex)[:60]}"); continue
    fullfile_tokens = toks(issue, src)

    row = {"fullfile_prompt_tokens": fullfile_tokens}
    for cond in ["guided", "unguided"]:
        fracs, resolved, tok_in, tok_out = [], 0, [], []
        for i in range(N):
            plan_user = f"# Issue\n{issue}\n\n"
            if cond == "guided":
                plan_user += f"# Module documentation\n{desc}\n\n"
            plan_user += f"# Symbols in {target_rel}\n{json.dumps(names)}"
            ti = toks(PLAN_SYS, plan_user)
            try:
                plan = client.complete(system=PLAN_SYS, user=plan_user)
            except Exception:
                fracs.append(0.0); tok_in.append(ti); tok_out.append(0); continue
            to = toks(plan)
            picked = [n for n in re.findall(r'"([^"]+)"', plan) if n in spans][:6] \
                     or [n for n in names if n in plan][:6]
            snippet = "\n\n".join(
                "\n".join(src.splitlines()[spans[n][0]-1:spans[n][1]]) for n in picked)
            edit_user = f"# Issue\n{issue}\n\n"
            if cond == "guided":
                edit_user += f"# Module documentation\n{desc}\n\n"
            edit_user += f"# Symbols from {target_rel}\n{snippet}"
            ti += toks(EDIT_SYS, edit_user)
            try:
                reply = client.complete(system=EDIT_SYS, user=edit_user)
            except Exception:
                fracs.append(0.0); tok_in.append(ti); tok_out.append(to); continue
            to += toks(reply)
            patched = splice(src, spans, parse_blocks(reply))
            p, f_ = run_tests(env, target_rel, oracle_rel, patched)
            tot = p + f_
            fracs.append(round(p / tot if tot else 0.0, 3))
            if f_ == 0 and p > 0:
                resolved += 1
            tok_in.append(ti); tok_out.append(to)
        row[cond] = {"fracs": fracs, "mean": round(statistics.mean(fracs), 3),
                     "resolved": f"{resolved}/{N}",
                     "mean_tokens_in": round(statistics.mean(tok_in)),
                     "mean_tokens_out": round(statistics.mean(tok_out))}
        print(f"{fix:<28}{cond:<10}fracs={fracs} resolved={resolved}/{N} "
              f"tok_in~{row[cond]['mean_tokens_in']} (fullfile~{fullfile_tokens})", flush=True)
    results[fix] = row
    out_path.write_text(json.dumps(results, indent=1))

print("saved", out_path)
