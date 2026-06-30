# Verified roundtrip results (SWE-Bench Verified, gemini-flash)

Recitation on Verified sympy: 0% (0/23 completing tasks) vs nonzero on Lite —
consistent with Google decontaminating Verified but not Lite.

| task | file | pass_fraction | note |
|---|---|---|---|
| sympy-24213 | physics/units/unitsystem.py | 0.848 | identical to Lite score for same file — metric measures regenerability, not contamination |
| sympy-24066 | physics/units/unitsystem.py | 0.000 | regenerated invalid syntax (SyntaxError) |
| sympy-23950 | sets/contains.py | 1.000 | perfect roundtrip on a decontaminated file |
