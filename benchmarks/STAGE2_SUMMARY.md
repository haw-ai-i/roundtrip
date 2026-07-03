Stage 2 summary: standalone documentation and the compact-complete description

Stage 2 asks whether a natural-language description of a codebase, supplied to an
agent as standalone documentation, improves the agent's ability to complete a task,
and what property of the description carries that value.

The core result is that a description helps a weak agent exactly when it carries
information the code does not already expose. Across three codebases whose decision
contracts are hidden from the code's local structure, adding the description flips a
weak agent from consistent failure to consistent success. When the description
merely restates code the agent can already read, including a real 423-line source
file, it adds nothing. So documentation helps to the degree it supplies intent or
contract beyond what the code shows.

Given that a description can help, two properties determine how well. Completeness
drives uplift: when we vary how much of the needed information a description contains,
the agent's success rises in exact step with it, knowing precisely what the
description conveys and nothing more. Compactness, by contrast, is free: a concise
description conveys the same information as one many times longer, and the extra
length produces no additional uplift.

Put together, the value lies in the compact complete description. Completeness is
what the agent needs, and once a description is complete, further verbosity is wasted.
This is measurable within the benchmark, since a description's completeness is its
roundtrip fidelity: a description that regenerates the code carries the information an
agent needs, and the benchmark rewards making that description as compact as possible.
This is the target the documentation-writing system should optimize for.
