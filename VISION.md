# Coundetrip Vision

## Thesis

Today, many projects release C++ source code and call it open source because the source is the artifact humans can realistically inspect, understand, modify, and rebuild. The compiled binary is not treated as source, even though it fully determines the program behavior, because changing the binary directly is too difficult for normal development.

Coundetrip explores a possible future where this relationship shifts. If coding agents become reliable enough, a concise natural-language description of a tool or codebase could become the human-editable source artifact, while the conventional codebase becomes the generated implementation artifact. In that world, changing software logic would often mean editing the natural-language description and asking an agent to regenerate the implementation, rather than modifying the generated code by hand.

## Current Analogy

Coding agents today often feel closer to an IPython notebook workflow than to a traditional compiler workflow:

- The codebase has mutable state, similar to the state of a Python interpreter kernel.
- The user repeatedly issues natural-language commands that mutate that state.
- The user observes the result through tests, diffs, runtime behavior, or review.
- The process continues interactively until the codebase reaches the desired state.

This workflow is powerful, but it does not yet establish natural language as a durable source representation. The natural-language interaction is usually transient chat history, not a compact, reusable artifact that can regenerate the codebase.

## Future Compiler Analogy

In the envisioned future, coding agents take on a role analogous to compilers:

- Human-authored natural language is the primary source representation.
- The generated programming-language code is the implementation representation.
- Tests, behavior, and repository structure define whether the generated implementation is faithful.
- Updating the system means editing the source description and regenerating the implementation.

The right terminology still needs work. "Compiled code" is only an analogy, since the generated artifact may remain readable and editable. Possible terms include generated implementation, realized codebase, lowered code, materialized code, or derived code.

## Benchmark Idea

The benchmark should evaluate an agent's ability to act as this kind of compiler by measuring whether it can roundtrip real codebases:

1. Start with an existing codebase and its test suite.
2. Ask an agent to produce a concise natural-language description of the codebase.
3. Hide or remove the original implementation.
4. Ask an agent to regenerate the codebase using only the description and allowed scaffolding.
5. Run the original tests against the regenerated codebase.
6. Score both the description and the regenerated implementation.

This creates pressure on the description to capture the right abstractions, behavior, edge cases, and project structure without simply copying the code.

## Metric Families

### Description Quality

The first metric family evaluates the natural-language source artifact:

- Size: token count, word count, or compressed byte size.
- Readability: human judgment, style constraints, structure, or rubric-based review.
- Abstraction quality: whether the description explains intent and invariants rather than line-by-line code.
- Reusability: whether a different agent, or the same agent in a fresh context, can regenerate from it.

### Regeneration Fidelity

The second metric family evaluates the generated implementation:

- Test pass rate: fraction of original tests passed by the regenerated codebase.
- Build success: whether the regenerated project installs, compiles, or runs.
- Behavioral coverage: performance on hidden or mutation tests where available.
- Structural similarity: optional comparison of public APIs, file layout, or dependency boundaries.

## Prototype Goal

The first prototype should be small enough to run locally, but concrete enough to test the benchmark loop end to end. A good initial target is a set of tiny repositories or coding-kata style projects with real tests, clear behavior, and limited dependencies. The prototype should produce repeatable artifacts for each roundtrip: the source repository snapshot, the natural-language description, the regenerated repository, test logs, and scored metrics.
