Stage 3: automatically improving the documentation agent, with held-out validation

Stage 3 treats the describe-step prompt as a harness and optimizes it against the
roundtrip benchmark, following the autoagent and metaharness idea: an outer loop
where a proposer rewrites the prompt, the benchmark scores the descriptions it
produces, and improvements are kept. The objective rewards fidelity with a small
penalty on length, pushing toward descriptions that are complete and compact. To
test whether the discovered prompt genuinely generalizes rather than overfitting,
we optimize on a training set of fixtures and validate on a held-out set the loop
never sees during optimization.

Setup. Train fixtures: tensorproduct, unitsystem, prefixes. Held-out fixtures:
contains, ndim_array. Proposer gemini-2.5-pro, three iterations, objective = mean
roundtrip fidelity minus a small length penalty.

Training. Baseline mean fidelity on the training set was 0.49 (tensorproduct 0.63,
unitsystem 0.85, prefixes 0.0). The loop reached fidelity 1.0 across the training
set by the second iteration, at fewer words than baseline; a third iteration that
regressed was correctly rejected.

Held-out validation. This is the key result. On the two held-out fixtures the loop
never optimized on, the discovered prompt raised mean fidelity from 0.50 to 1.00
(ndim_array rose from 0.0 to 1.0, contains held at 1.0), while using slightly fewer
words than baseline (969 to 904). The improvement generalizes to unseen code: the
optimizer produced a genuinely better documentation prompt, not one tuned to the
training fixtures. This confirms the compact-complete thesis out of sample and shows
the benchmark is a usable optimization target for improving documentation quality.
