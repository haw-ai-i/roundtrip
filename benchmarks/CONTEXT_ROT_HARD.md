Harder context-rot task: does a verbose description hurt when the task is hard?

The earlier context-rot check used five short facts and found no gap between compact and
verbose at any model size. We suspected the task was too easy, so we built a harder version:
28 settings including confusable key families (max_retries vs max_retry_delay vs
connection_max_retries vs request_max_retries; read_timeout vs connect_timeout vs
socket_timeout vs handshake_timeout), with an oracle checking ten specific values that sit
among their confusable neighbours.

A first version of the verbose description described each key in words but never stated the
literal key string, while the compact version listed keys verbatim. On that version the
verbose condition collapsed to 0/8 while compact stayed 8/8, which looked like context rot.
But the comparison was confounded: the verbose description did not actually contain the exact
identifiers the task required, so its failure could simply be missing information rather than
degradation over long context.

To remove the confound we wrote a fair verbose description that contains the exact literal key
strings (in backticks), embedded in the same long, filler-heavy prose with confusable keys
scattered across paragraphs. We then compared three conditions on Gemma 3 4B:

                    COMPACT   VERBOSE unfair   VERBOSE fair
                    (keys      (keys only       (keys present
                    listed)    described)       but buried)
  flash-lite        8/8        0/8              8/8
  gemini-2.5-flash  4/4        0/4              4/4
  Gemma 3 4B        8/8        0/8              8/8

The fair verbose description passes perfectly on both models. Even buried in long prose among confusable
neighbours, once the exact keys are present the small model recovers them without error, and
correctly distinguishes near-duplicate keys such as max_retries, max_retries_backoff, and
request_max_retries. Verbosity itself did not hurt.

Conclusion: on this task the apparent context-rot effect was a confound. The verbose form fails
only when it omits the exact identifiers the task needs, which is a completeness failure, not
context degradation. When the verbose description is complete, it matches the compact one even
at 4B and even with heavy filler and distractors. This reinforces the paper's finding:
verbosity beyond completeness adds nothing, and does not subtract either; what matters is
completeness. Igor's context-rot hypothesis does not hold on this task once the comparison is
made fair.
