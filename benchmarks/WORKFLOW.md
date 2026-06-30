# Stage 2 workflow comparison (Igor's reframing)

Compare two workflows a naive human (no prior code knowledge) could use to make
the same change, on input size AND success:
  W1 (code):  raw code + concise request -> coding agent -> code
  W2 (descr): edit description -> materialize -> code
Both judged by whether the new behavior is correctly produced.

## Validation: single-file (contains, tuple membership)
| workflow | human input | result |
|---|---|---|
| W1 (prompt to code agent) | 151 chars | correct: And(*[cls(i,s) for i in x]) |
| W2 (description edit)      | 173 chars | correct: And(*(Contains(elem,s) for elem in x)) |

Null as expected: for a small single-file change, prompting an agent on the raw
file is as easy as editing the description. Per Igor, the description advantage
should appear in CROSS-FILE / multi-call-site edits, where W1 requires knowing
which files and call-sites to touch. Next: build a cross-file fixture.
