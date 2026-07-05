Harder context-rot task: does a verbose description hurt when the task is hard?

The earlier context-rot check used five short facts and found no gap between compact and
verbose at any model size. We suspected the task was too easy. This is a harder version: 28
settings including confusable key families (max_retries vs max_retry_delay vs
connection_max_retries vs request_max_retries; read_timeout vs connect_timeout vs
socket_timeout vs handshake_timeout). The oracle checks ten specific values sitting among
their confusable neighbours. The compact description lists the keys verbatim; the verbose
description carries the same facts in prose, describing each key in words rather than stating
the literal identifier, with related keys scattered across paragraphs.

Result (fraction of runs passing all ten checks):

  Model            No desc.   Compact (108w)   Verbose (704w)
  flash-lite       0/8        8/8              0/8
  Gemma 3 4B       0/8        8/8              0/8
  llama3.2 (3B)    0/4        4/4              0/4

The two clean cases are flash-lite and Gemma 3 4B. Both produced complete, valid code and
failed the verbose condition purely on the keys: given the compact list they copy the exact
key strings, but given the prose they reconstruct plausible-sounding names from the
surrounding sentences (retry_count, retry_delay_ms, connection_retry_count) instead of the
literal keys (max_retries, max_retry_delay, connection_max_retries). Values are usually
correct; identifiers are not. The verbose form makes exact-identifier recovery fail.

llama3.2 (3B) shows the same direction and also paraphrased the keys, but its verbose output
was additionally incomplete (it emitted only the _default method, not the full class), so its
failure is confounded by a code-structure issue and is weaker evidence than the other two.

Honest scope: part of what drives the gap is that the verbose description never states the
literal key strings, only describes them, whereas the compact version lists them verbatim. So
the finding is precisely that prose-only descriptions of exact identifiers are unrecoverable
for smaller models, a concrete form of context degradation, rather than pure context-length
rot. This is the sharper task the earlier null result called for, and it shows verbosity is
not always free: when identifiers must be recovered exactly and the description buries them in
prose, the verbose form can destroy a description's usability.
