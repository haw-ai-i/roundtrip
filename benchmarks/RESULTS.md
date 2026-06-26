# Roundtrip results (SWE-Bench Lite, gemini-flash)

| fixture | lines | pass_fraction | tests (p/f/e) | describe words | failure mode |
|---|---|---|---|---|---|
| swe_saferepr | 103 | — | — | — | lost one exact output literal |
| swe_sympy_unitsystem | 205 | — | — | — | 5/33 tests fail |
| swe_sympy_prefixes | 219 | — | — | — | import-time error: regenerated immutability constraint original omits |
| swe_sympy_tensorproduct | 420 | — | — | — | dropped matrix/trace integration imports |
| swe_sympy_ndim_array | 592 | — | — | — | importable but behavior off across the board |
