"""Recitation / contamination sweep over SWE-Bench files.

For each task we fetch the file the gold patch touches (at base_commit), run the
roundtrip's describe -> regenerate, and record whether regenerate produced code
or was refused by the model's recitation filter. The recitation-block rate
across tasks estimates how much of the benchmark the model has memorized -- a
direct probe of the contamination that roundtrip benchmarks on public code
have to worry about.

This does NOT run tests; it only measures produce-vs-block. Pair it with the
fixture pipeline (which scores the produced ones) for the full picture.

Usage:
    uv run python benchmarks/contamination_sweep.py --n 5            # smoke test (free key)
    uv run python benchmarks/contamination_sweep.py --n 0 --sleep 1  # full sweep (paid key)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
from coundetrip.llm_agent import (  # noqa: E402
    GeminiClient,
    _DESCRIBE_SYSTEM,
    _REGENERATE_SYSTEM,
)

_FILE_RE = re.compile(r"^\+\+\+ b/(.+\.py)$", re.M)


def first_py_file(patch: str) -> str | None:
    m = _FILE_RE.findall(patch)
    return m[0] if m else None


def fetch(repo: str, commit: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _reason(client: GeminiClient) -> str:
    return str(getattr(client, "last_finish_reason", None))


def classify(client: GeminiClient, source: str) -> dict:
    spec = client.complete(system=_DESCRIBE_SYSTEM, user=source)
    if not spec:
        r = _reason(client)
        outcome = "recitation" if "RECITATION" in r else "describe_blocked"
        return {"outcome": outcome, "stage": "describe", "finish_reason": r}

    user = (
        "Specification:\n\n"
        + spec
        + "\n\nReproduce the module as source code from this specification alone."
    )
    reply = client.complete(system=_REGENERATE_SYSTEM, user=user)
    r = _reason(client)
    if reply:
        return {
            "outcome": "produced",
            "stage": "regenerate",
            "finish_reason": r,
            "reply_chars": len(reply),
            "spec_words": len(spec.split()),
        }
    outcome = "recitation" if "RECITATION" in r else "other_empty"
    return {"outcome": outcome, "stage": "regenerate", "finish_reason": r}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="number of tasks (0 = all)")
    ap.add_argument("--max-lines", type=int, default=600, help="skip files larger than this")
    ap.add_argument("--sleep", type=float, default=0.0, help="seconds between tasks (rate limit)")
    ap.add_argument("--model", default="gemini-3.5-flash")
    ap.add_argument("--out", default="contamination_sweep.jsonl")
    ap.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite")
    ap.add_argument("--instances", default="", help="comma-separated instance_ids to run (overrides --n)")
    ap.add_argument("--resume", action="store_true", help="skip instance_ids already present in --out and append")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("Need `datasets`: run `uv pip install datasets` (or pip install datasets).")

    ds = load_dataset(args.dataset, split="test")
    tasks = list(ds)
    if args.instances:
        wanted = {x.strip() for x in args.instances.split(",") if x.strip()}
        tasks = [t for t in tasks if t["instance_id"] in wanted]
    elif args.n:
        tasks = tasks[: args.n]

    client = GeminiClient(model=args.model)
    tally: dict[str, int] = {}
    out_path = Path(args.out)
    done: set[str] = set()
    if args.resume and out_path.exists():
        import json as _json
        for _ln in out_path.read_text(encoding="utf-8").splitlines():
            if _ln.strip():
                try:
                    done.add(_json.loads(_ln)["instance_id"])
                except Exception:
                    pass
        tasks = [t for t in tasks if t["instance_id"] not in done]
        print(f"resume: {len(done)} already done, {len(tasks)} remaining")
    mode = "a" if (args.resume and out_path.exists()) else "w"
    with out_path.open(mode, encoding="utf-8") as out:
        for i, row in enumerate(tasks, 1):
            rec = {
                "instance_id": row["instance_id"],
                "repo": row["repo"],
                "base_commit": row["base_commit"][:10],
            }
            f = first_py_file(row["patch"])
            rec["file"] = f
            if not f:
                rec["outcome"] = "no_py_file"
            else:
                try:
                    src = fetch(row["repo"], row["base_commit"], f)
                    rec["n_lines"] = src.count("\n")
                    if args.max_lines and rec["n_lines"] > args.max_lines:
                        rec["outcome"] = "skipped_too_large"
                    else:
                        rec.update(classify(client, src))
                except Exception as exc:  # noqa: BLE001
                    rec["outcome"] = "error"
                    rec["error"] = str(exc)[:300]

            tally[rec["outcome"]] = tally.get(rec["outcome"], 0) + 1
            out.write(json.dumps(rec) + "\n")
            out.flush()
            print(f"[{i}/{len(tasks)}] {rec['instance_id']:42s} {rec['outcome']:18s} {rec.get('finish_reason','')}")
            if args.sleep:
                time.sleep(args.sleep)

    print("\n=== tally ===")
    total = sum(tally.values())
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {k:18s} {v:4d}  ({100*v/total:.0f}%)")
    scoreable = tally.get("produced", 0)
    blocked = tally.get("recitation", 0)
    rel = scoreable + blocked
    if rel:
        print(f"\n  recitation-block rate (of completing tasks): {100*blocked/rel:.0f}%  ({blocked}/{rel})")
    print(f"  usage: {client.usage}")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
