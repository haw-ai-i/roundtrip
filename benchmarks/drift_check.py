"""Stage-2 step zero: regeneration drift baseline."""
import difflib, sys
from pathlib import Path

name = sys.argv[1]; rel = sys.argv[2]; run_ids = sys.argv[3:]

def gen_file(rid):
    p = Path("runs") / rid / name / "generated" / rel
    if not p.exists():
        gdir = Path("runs") / rid / name / "generated"
        cands = list(gdir.rglob(Path(rel).name)) if gdir.exists() else []
        p = cands[0] if cands else None
    return p

texts = {}
for rid in run_ids:
    p = gen_file(rid)
    texts[rid] = p.read_text().splitlines() if p and p.exists() else None
    print(f"{rid}: {'loaded '+str(len(texts[rid]))+' lines' if texts[rid] else 'MISSING'}")

ok = [r for r in run_ids if texts[r] is not None]
print("\n=== pairwise line diffs (same description, different runs) ===")
for i in range(len(ok)):
    for j in range(i+1, len(ok)):
        a, b = texts[ok[i]], texts[ok[j]]
        diff = list(difflib.unified_diff(a, b, lineterm=""))
        changed = sum(1 for d in diff if d and d[0] in "+-" and not d.startswith(("+++","---")))
        print(f"  {ok[i]} vs {ok[j]}: {'IDENTICAL' if changed==0 else str(changed)+' changed lines'}")
