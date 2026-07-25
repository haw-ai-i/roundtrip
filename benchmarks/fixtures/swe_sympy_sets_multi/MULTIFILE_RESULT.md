
Follow-up: import-repair loop
We prototyped a repair step in the regenerate stage that checks each regenerated file imports
cleanly in the target environment and, on failure, shows the model the error and asks for a fix.
This directly targets the dominant failure mode (hallucinated imports that crash a file before
tests run). The approach is sound and mirrors how a real coding agent iterates, but a naive
implementation is slow: importing a heavy library such as sympy repeatedly, across several files
and repair attempts, exceeds the per-stage time budget. Making repair practical needs a faster
import check and a small attempt cap. This is the recommended next step for multi-file work.
