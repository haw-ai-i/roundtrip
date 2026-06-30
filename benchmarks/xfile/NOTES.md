# Cross-file workflow scaffold (Stage 2) — NOT YET a faithful test

W1 (code agent, raw code + request) vs W2 (edit description -> materialize),
same change ("allow hyphens in usernames"), judged by test_rule.py.

First run: W1 PASS (agent fixed all 4 inline sites), W2 FAIL (regenerated the
whole package from a short paragraph, restructured it, broke a return).

This scaffold is NOT yet faithful to the hypothesis:
- codebase is small enough to fit one prompt, so W1's multi-site task isn't hard
  (hypothesis is about large codebases where finding all call-sites is the difficulty);
- W2 regenerates from a thin hand-written summary, not the full generated description.
Open for Igor: target codebase scale, and whether W2 should edit the full
describe-step description rather than a summary.
