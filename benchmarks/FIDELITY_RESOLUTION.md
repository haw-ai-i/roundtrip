Description fidelity predicts issue-resolution uplift

The benchmark scores a description by roundtrip fidelity. The motivating question is whether that
score predicts something practical: when an agent resolves an issue in an existing codebase, does
a higher-fidelity description of the relevant file help it more?

For each fixture we have a description with a known roundtrip fidelity. A mid-tier agent
(gemini-3.5-flash) implements the target file from the project scaffold, once without the
description and once with it, and the fixture's own tests are the acceptance criteria. The
description's contribution is the uplift: mean test-pass fraction with the description minus the
same without it. Four attempts per condition.

  fixture         fidelity  no_desc  with_desc  uplift
  contains        1.00      0.00     1.00       1.00
  saferepr        0.73      0.00     1.00       1.00
  tensorproduct   0.62      0.00     0.69       0.69
  unitsystem      0.85      0.00     0.55       0.55
  prefixes        0.00      0.00     0.00       0.00
  ndim_array      0.00      0.00     0.00       0.00

Pearson correlation between description fidelity and resolution uplift: 0.917.

Without the description the agent resolves none of these files, so the uplift is entirely the
description's contribution. That contribution tracks fidelity strongly: high-fidelity
descriptions let the agent resolve the issue, zero-fidelity descriptions add nothing, and the
middle fixtures fall in between. This is the benchmark's core justification: roundtrip fidelity,
measured with no reference to any downstream task, predicts how much a description helps an agent
resolve a real issue.

The result is preliminary. Six fixtures is a small sample and one agent is a single point of
comparison; a larger fixture set and more agents are needed for a statistically firm estimate,
which is planned before publication.
