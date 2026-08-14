"""Aggregate the Section 7 transfer results over multi-file Kind-B instances.

Reports the paired comparison the experiment is designed to answer: does adding
an optimized-prompt description to a source-present issue-resolution agent
improve the pass fraction? Only fixtures where BOTH conditions scored are
included in the paired statistics, so a failed run in one condition cannot
skew the other. Fixtures that failed (no edit / describe empty) are listed
separately so they can be re-run rather than silently dropped.
"""
import json
import sys
from pathlib import Path

RESULTS = Path("benchmarks/baseline_results/transfer_kindb_omp.json")
CONDS = ["issue_only", "optimized"]


def load():
    if not RESULTS.exists():
        sys.exit("no results file at " + str(RESULTS))
    return json.loads(RESULTS.read_text(encoding="utf-8"))


def scored(row, cond):
    """Return the mean pass fraction for a condition, or None if it did not score."""
    cell = row.get(cond)
    if isinstance(cell, dict) and "mean" in cell:
        return cell["mean"]
    return None


def resolved_count(row, cond):
    """Return 1 if the condition fully resolved the issue (all tests pass)."""
    cell = row.get(cond)
    if not isinstance(cell, dict):
        return None
    r = cell.get("resolved")
    if not r:
        return None
    got, _, total = r.partition("/")
    try:
        return int(got)
    except ValueError:
        return None


def main():
    data = load()
    paired, incomplete = {}, {}
    for fix, row in data.items():
        vals = {c: scored(row, c) for c in CONDS}
        if all(v is not None for v in vals.values()):
            paired[fix] = vals
        else:
            incomplete[fix] = row

    print("=" * 78)
    print("SECTION 7 - transfer study, multi-file Kind-B, source present")
    print("=" * 78)
    print("fixtures recorded : " + str(len(data)))
    print("paired (both scored): " + str(len(paired)))
    print("incomplete/failed : " + str(len(incomplete)))
    print()

    if not paired:
        print("no paired fixtures yet")
        return

    print(f"{'fixture':<44}{'issue_only':>12}{'optimized':>12}{'delta':>10}")
    print("-" * 78)
    for fix in sorted(paired):
        a = paired[fix]["issue_only"]
        b = paired[fix]["optimized"]
        print(f"{fix:<44}{a:>12.3f}{b:>12.3f}{b - a:>+10.3f}")

    n = len(paired)
    mean_a = sum(v["issue_only"] for v in paired.values()) / n
    mean_b = sum(v["optimized"] for v in paired.values()) / n
    deltas = [v["optimized"] - v["issue_only"] for v in paired.values()]
    wins = sum(1 for d in deltas if d > 0)
    losses = sum(1 for d in deltas if d < 0)
    ties = sum(1 for d in deltas if d == 0)

    print("-" * 78)
    print(f"{'MEAN pass fraction':<44}{mean_a:>12.3f}{mean_b:>12.3f}{mean_b - mean_a:>+10.3f}")

    tok_a = [data[f]["issue_only"].get("tokens", {}).get("total", 0) for f in paired]
    tok_b = [data[f]["optimized"].get("tokens", {}).get("total", 0) for f in paired]
    if any(tok_a) or any(tok_b):
        ma = sum(tok_a) / len(tok_a)
        mb = sum(tok_b) / len(tok_b)
        print(f"{'MEAN resolve tokens':<44}{ma:>12.0f}{mb:>12.0f}{mb - ma:>+10.0f}")

    res_a = sum(x for x in (resolved_count(data[f], "issue_only") for f in paired) if x)
    res_b = sum(x for x in (resolved_count(data[f], "optimized") for f in paired) if x)
    print(f"{'RESOLVED (all tests pass)':<44}{res_a:>12d}{res_b:>12d}{res_b - res_a:>+10d}")
    print()
    print("paired sign test over " + str(n) + " fixtures:")
    print("  optimized better : " + str(wins))
    print("  issue_only better: " + str(losses))
    print("  tied             : " + str(ties))
    if deltas:
        print("  mean delta       : " + format(sum(deltas) / n, "+.4f"))

    if incomplete:
        print()
        print("NEEDS RE-RUN (purge these keys, then relaunch the sweep):")
        for fix, row in sorted(incomplete.items()):
            reasons = []
            for c in CONDS:
                cell = row.get(c)
                if not isinstance(cell, dict) or "mean" not in cell:
                    why = "missing"
                    if isinstance(cell, dict):
                        why = cell.get("failed") or cell.get("skipped") or "missing"
                    reasons.append(c + ": " + str(why))
            print("  " + fix + "  [" + "; ".join(reasons) + "]")


if __name__ == "__main__":
    main()
