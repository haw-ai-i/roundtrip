import sys, subprocess, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from coundetrip.llm_agent import GeminiClient, parse_file_blocks

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
FILES = ["minilib/accounts.py", "minilib/registry.py"]
code = {f: Path(f).read_text() for f in FILES}
REQUEST = "Allow hyphens in usernames (in addition to letters, digits, and underscores)."

DESCRIPTION = """\
# minilib package

Two modules manage user accounts with username validation.

Validation rule (applied everywhere a username is accepted): a username must be a
string of length 3 to 20, containing only letters, digits, or underscores.

- accounts.py: `Account(username)` validates on creation; `Account.rename(new)` re-validates.
- registry.py: `Registry.register(username)` validates before adding; `Registry.bulk_register(names)` validates each.
Invalid usernames raise ValueError.
"""

SYS_CODE = ("You are a coding agent. Apply the change request to the given files, "
            "modifying as little as possible. Output each changed file as:\n=== <path> ===\n<contents>\n")
SYS_DESC = ("Implement the package described by the specification. Output every file as:\n"
            "=== <path> ===\n<contents>\n")

def call(s,u): return GeminiClient(temperature=0.0).complete(system=s, user=u)

def run_test(outdir):
    r = subprocess.run([sys.executable, "test_rule.py"], cwd=outdir,
                       capture_output=True, text=True, env={**os.environ, "PYTHONPATH": outdir})
    out=(r.stdout+r.stderr).strip()
    return ("PASS" in r.stdout, out.splitlines()[-1] if out else "")

def materialize(reply, outdir):
    Path(outdir,"minilib").mkdir(parents=True, exist_ok=True)
    blocks = parse_file_blocks(reply)
    for path, content in blocks.items():
        p=Path(outdir,path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content)
    for f in FILES:
        if not Path(outdir,f).exists(): Path(outdir,f).write_text(code[f])
    Path(outdir,"test_rule.py").write_text(Path("test_rule.py").read_text())
    return list(blocks.keys())

w1_user = "".join(f"=== {f} ===\n{code[f]}\n\n" for f in FILES) + f"Change request: {REQUEST}\n"
w1_dir = tempfile.mkdtemp(prefix="w1_"); w1e=materialize(call(SYS_CODE,w1_user),w1_dir)
w1_pass,w1_msg = run_test(w1_dir)

edited = DESCRIPTION.replace("letters, digits, or underscores","letters, digits, underscores, or hyphens")
w2_dir = tempfile.mkdtemp(prefix="w2_"); w2e=materialize(call(SYS_DESC,f"Specification:\n\n{edited}\n"),w2_dir)
w2_pass,w2_msg = run_test(w2_dir)

print("CHANGE:", REQUEST)
print(f"\nW1 (code agent, no description): {len(w1e)} files -> {'PASS' if w1_pass else 'FAIL'}  [{w1_msg[:80]}]")
print(f"W2 (edit description, materialize): {len(w2e)} files -> {'PASS' if w2_pass else 'FAIL'}  [{w2_msg[:80]}]")
print(f"\nW1 dir: {w1_dir}\nW2 dir: {w2_dir}")
