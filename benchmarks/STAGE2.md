# Stage 2: editing the description vs editing the code

Fixture: swe_sympy_contains (1.0 roundtrip baseline).
Edit: one description bullet — non-Set input "raise TypeError" -> "return S.false".

## Measurement note
Free-form regeneration rewrites the WHOLE file deterministically but non-minimally,
so a naive code diff overstated amplification (13.5x — mostly unrelated rewrites:
threading.local, renames, restructured branches).

Fix: minimal-edit regeneration (original code + edited spec -> smallest change).
Control = minimal-regen from the UNEDITED description.

## Result
| measure | value |
|---|---|
| description edit | 4 lines / 24 tokens |
| control drift (unedited desc, minimal) | 0 lines |
| code edit (edited desc, minimal) | 3 lines |

For this localized edit, description-edit and code-edit cost are comparable (~1:1).
The instrument now cleanly separates edit-driven change from regeneration churn, so
amplification can be measured honestly across edits of varying structural scope.

## Second edit: structural (tuple membership)
Edit: "if x is a tuple/Tuple, check membership component-wise -> And(Contains(a,s),...)".

| measure | value |
|---|---|
| description edit | 4 lines |
| control drift | 0 lines |
| code edit (minimal) | 5 lines |

Model implemented it compactly: `if isinstance(x,(tuple,Tuple)): return And(*(cls(i,s) for i in x))` + 2 imports.

## Finding
Both a localized edit (~3 code lines) and a structural edit (~5 code lines) come out
~1:1 with the description edit at the LINE level. Naive free-form amplification (13.5x)
was an artifact of non-minimal rewriting. Open question: is the Stage-2 hypothesis about
line-count, edit-effort, or required expertise? Line-count amplification is ~1x for these
single-file edits; cross-file / multi-callsite edits may differ.
