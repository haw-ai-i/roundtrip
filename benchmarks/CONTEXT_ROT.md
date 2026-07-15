Context rot check: does a verbose description hurt a weaker model?

We hypothesized that the equal-uplift compactness result might be specific to
flash-lite, and that a weaker model would show the verbose description hurting
through context rot, with the needed facts getting lost in filler.

We reran the comprehension task, where the needed facts appear only in the
description and the implementation is trivial, across smaller models. The result was
the same at every size we tested:

flash-lite: no description 0/8, compact 8/8, verbose 8/8
Gemma 4 31B (API): no description 0/8, compact 8/8, verbose 8/8
Gemma 3 4B (local): no description 0/8, compact 8/8, verbose 8/8

Verbosity stayed free rather than harmful, even on a 4B model. Context rot did not
appear on this task. One likely reason is that the task conveys only five short
key-value facts, which remain easy to recover even when surrounded by filler; context
rot is more likely to bite when a model must track many facts or find them among
distractors in a long context. So the honest reading is not that context rot is absent
in general, but that this fact-conveyance task does not trigger it at the sizes tested.
A harder task, rather than a smaller model, would be the next lever.
