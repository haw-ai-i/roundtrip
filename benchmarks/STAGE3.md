Stage 3: automatically improving the documentation agent

Stage 3 treats the describe-step prompt as a harness and optimizes it against the
roundtrip benchmark, in the style of autoagent and metaharness: an outer loop where
a proposer rewrites the prompt, the benchmark scores the descriptions it produces,
and improvements are kept. The objective rewards fidelity (does the description
regenerate the code) with a penalty on length, so the loop is pushed toward
descriptions that are both complete and compact.

Setup. Two fixtures (tensorproduct, unitsystem), proposer gemini-2.5-pro, three
iterations, objective = mean roundtrip fidelity minus a small length penalty.

Result. The objective climbed at every iteration.

iter 0 (baseline): fidelity 0.737, words 1232, objective 0.326
iter 1: fidelity 1.000, words 1381, objective 0.540
iter 2: fidelity 1.000, words 1298, objective 0.567
iter 3: fidelity 1.000, words 1062, objective 0.646

The loop first raised fidelity to 1.0 on both fixtures (tensorproduct rose from
0.625, unitsystem from 0.848), making the descriptions complete. It then held
fidelity at 1.0 while cutting length from 1381 to 1062 words, making the complete
descriptions more compact. This is the compact-complete thesis discovered by the
optimizer itself: once descriptions are complete, further improvement comes from
making them shorter. The discovered prompt (stage3_best_prompt.txt) outperforms the
hand-written baseline, reaching full fidelity at fewer words.
