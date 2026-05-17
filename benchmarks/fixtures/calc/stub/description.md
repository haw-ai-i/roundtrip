# Calc fixture (natural-language source stub)

Implement a Python package `calc` with:

- `add(a: int, b: int) -> int` returning the sum of two integers.
- `mul(a: int, b: int) -> int` returning the product of two integers.

Place the module under `src/calc/__init__.py`. Add pytest tests under `tests/` that assert `add(2,3)==5` and `mul(4,5)==20`. Use `pyproject.toml` with pytest `pythonpath = ["src"]` and `testpaths = ["tests"]`.
