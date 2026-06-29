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
