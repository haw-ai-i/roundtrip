# Roundtrip results (SWE-Bench Lite, gemini-flash)

Scores are stable across 5 runs each (see VARIANCE.md).

| fixture | lines | pass_fraction | tests (p/f/e) | describe words | failure mode |
|---|---|---|---|---|---|
| swe_saferepr | 103 | 0.727 | 8p/3f/0e | 1001 | lost one exact output literal |
| swe_sympy_unitsystem | 205 | 0.848 | 28p/5f/0e | 1133 | 5/33 tests fail |
| swe_sympy_prefixes | 219 | 0.000 | 0p/0f/1e | 870 | import-time error: regenerated immutability constraint original omits |
| swe_sympy_tensorproduct | 420 | 0.625 | 5p/3f/0e | 1332 | dropped matrix/trace integration imports |
| swe_sympy_ndim_array | 592 | 0.000 | 0p/5f/0e | 1650 | importable but behavior off across the board |
