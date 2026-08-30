## sympy/simplify/radsimp.py
The complete natural-language specification of `sympy/simplify/radsimp.py` has been written to `/tmp/omp_desc_q5am36ht/radsimp_spec.md`. It covers all 14 code objects in the module:

| Function | Lines | Purpose |
|---|---|---|
| `collect()` | 22–422 | Collect additive terms by symbolic patterns/powers, with derivative support and order-term distribution |
| `rcollect()` | 425–453 | Recursively collect sums in an expression tree |
| `collect_sqrt()` | 456–532 | Group common square roots (and I) together |
| `collect_const()` | 535–669 | Non-greedy collection of terms with similar numeric coefficients, recursive |
| `radsimp()` | 672–917 | Rationalize denominators by removing square roots via conjugate multiplication (up to 4 radical terms) |
| `rad_rationalize()` | 920–939 | Recursive rationalization using surd splitting |
| `fraction()` | 942–1032 | Decompose expression into numerator/denominator pair |
| `numer()` / `denom()` | 1035–1040 | Convenience wrappers around `fraction()` |
| `fraction_expand()` / `numer_expand()` / `denom_expand()` + aliases | 1043–1059 | Expand numerator, denominator, or both separately |
| `split_surds()` | 1062–1100 | Split expression into surd and non-surd parts by GCD of squared bases |
| `_split_gcd()` | 1103–1126 | Private helper: partition integers by their running GCD |

Each function's signature, nested functions (for `collect` and `radsimp`), parameter defaults, step-by-step implementation logic, control flow, return values, and exception conditions are documented.

## sympy/simplify/sqrtdenest.py
Now I have the complete file. Let me write the full natural-language specification.

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from sympy.core import S, sympify, Mul, Add, Expr
from sympy.core.compatibility import range
from sympy.core.function import expand_mul, count_ops, _mexpand
from sympy.core.symbol import Dummy
from sympy.functions import sqrt, sign, root
from sympy.polys import Poly, PolynomialError
from sympy.utilities import default_sort_key
```

### Constants & Globals

None. All module-level objects are functions and one class.

---

## Code Objects

### `is_sqrt(expr)`

**Signature:** `is_sqrt(expr) -> bool`

Returns `True` if `expr` is a square root, i.e., `expr.is_Power` is true, `expr.exp.is_Rational` is true, and `abs(expr.exp) is S.Half`. Otherwise returns `False`.

---

### `sqrt_depth(p)`

**Signature:** `sqrt_depth(p) -> int`

Returns the maximum nesting depth of square roots within expression `p`.

- If `p.is_Atom`, returns `0`.
- If `p.is_Add` or `p.is_Mul`, returns `max(sqrt_depth(x) for x in p.args, key=default_sort_key)`.
- If `is_sqrt(p)` is true (i.e., `p` is a square root), returns `sqrt_depth(p.base) + 1`.
- Otherwise, returns `0`.

---

### `is_algebraic(p)`

**Signature:** `is_algebraic(p) -> bool`

Returns `True` if `p` consists only of rationals and/or square roots thereof combined via algebraic operations.

- If `p.is_Rational`, returns `True`.
- If `p.is_Atom` (and not rational), returns `False`.
- If `is_sqrt(p)` or (`p.is_Pow` and `p.exp.is_Integer`), recursively checks `is_algebraic(p.base)`.
- If `p.is_Add` or `p.is_Mul`, returns `all(is_algebraic(x) for x in p.args)`.
- Otherwise, returns `False`.

---

### `_subsets(n)`

**Signature:** `_subsets(n: int) -> list[list[int]]`

Returns all non-empty subsets of `{0, 1, ..., n-1}` encoded as binary vectors (length `n`, with `1` indicating inclusion), in reversed lexicographical order.

- If `n == 1`: returns `[[1]]`.
- If `n == 2`: returns `[[1, 0], [0, 1], [1, 1]]`.
- If `n == 3`: returns `[[1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]]`.
- If `n > 3`: recursively calls `_subsets(n - 1)`, then constructs:
  - `a0 = [x + [0] for x in b]` (each subset of size n-1 with a trailing 0),
  - `a1 = [x + [1] for x in b]` (each subset of size n-1 with a trailing 1),
  - Result: `a0 + [[0]*(n-1) + [1]] + a1`.

---

### `sqrtdenest(expr, max_iter=3)`

**Signature:** `sqrtdenest(expr, max_iter: int = 3) -> Expr`

Main entry point. Denests square roots in `expr` if possible; returns the expression unchanged otherwise. Based on algorithms from Fagin et al.

1. Converts `expr` via `sympify`, then applies `expand_mul`.
2. Iterates up to `max_iter` times:
   - Calls `_sqrtdenest0(expr)`. If the result equals `expr`, returns immediately (no further denesting possible).
   - Otherwise, updates `expr = z` and continues.
3. Returns the final `expr`.

---

### `_sqrt_match(p)`

**Signature:** `_sqrt_match(p) -> list | []`

Attempts to match expression `p` against the form `a + b*sqrt(r)`, where `r` has maximal `sqrt_depth` among addends of `p`. Returns `[a, b, r]` as a list, or an empty list on failure.

- If `p.is_Number`: returns `[p, 0, 0]`.
- If `p.is_Add`:
  - Sorts args by `default_sort_key`.
  - If all `(x**2).is_Rational` for each arg: calls `split_surds(p)` from `sympy.simplify.radsimp`, returning `[a, b, r]` (reordered as `a, b, r`).
  - Otherwise, finds the addend with maximum `(sqrt_depth(x), x, index)`. If max depth is 0, returns `[]`.
    - Pops that element as `r`.
    - If `r.is_Mul`: splits its args into those with `sqrt_depth < depth` (coefficient part → `b`) and those with equal depth (radicand part → `r`).
    - Iterates remaining addends: terms with depth less than max go to `a1`; terms at the same depth are checked — if identical to `r`, append 1 to `b1`; if a Mul containing `r`, strip `r` and append remainder to `b1`; otherwise, append to `a1`.
    - Returns `[Add(*a1), Add(*b1), r**2]`.
- If `p` is neither Number nor Add (i.e., a single term): calls `p.as_coeff_Mul()` → `(b, r)`. If `is_sqrt(r)`, returns `[0, b, r**2]`; otherwise returns `[]`.

---

### `SqrtdenestStopIteration`

**Signature:** `class SqrtdenestStopIteration(StopIteration)`

A custom exception class inheriting from `StopIteration`, used to signal that denesting could not proceed.

---

### `_sqrtdenest0(expr)`

**Signature:** `_sqrtdenest0(expr) -> Expr`

Recursively denests the arguments of `expr`.

- If `is_sqrt(expr)`:
  - Splits into numerator/denominator via `as_numer_denom()`.
  - If denominator is `S.One` (pure square root):
    - If the radicand (`n.base`) is an Add with more than 2 args and all `(x**2).is_Integer`, tries `_sqrtdenest_rec(n)`. On `SqrtdenestStopIteration`, catches and falls through.
    - Sorts addends of the radicand by `default_sort_key`, recursively denests each, re-adds them under a new sqrt via `_mexpand(Add(*[_sqrtdenest0(x) for x in args]))`.
    - Then calls `_sqrtdenest1(expr)` on the result.
  - If denominator is not `S.One`: recursively denests both numerator and denominator, returns their quotient.
- If `expr` is an `Add`: splits each term into coefficient (`c`) and radical part (`a`). If all coefficients are rational and all radical parts are square roots, calls `_sqrt_ratcomb(cs, args)`.
- If `expr` is any other `Expr` with non-empty `.args`, recursively applies `_sqrtdenest0` to each arg: returns `expr.func(*[_sqrtdenest0(a) for a in expr.args])`.
- Otherwise, returns `expr` unchanged.

---

### `_sqrtdenest_rec(expr)`

**Signature:** `_sqrtdenest_rec(expr) -> Expr`

Denests the square root of three or more surds using a recursive field-extension algorithm (Fagin et al., section 6). Raises `SqrtdenestStopIteration` if denesting fails.

- If not a Pow, calls `sqrtdenest(expr)` and returns.
- If radicand is negative: returns `sqrt(-1) * _sqrtdenest_rec(sqrt(-expr.base))`.
- Calls `split_surds(expr.base)` → `(g, a, b)`, then sets `a = a*sqrt(g)`. Swaps `a` and `b` if `a < b`.
- Computes `c2 = _mexpand(a**2 - b**2)`:
  - If `len(c2.args) > 2`: splits `c2` via `split_surds`, sets up recursive denesting chain: computes `c2_1 = _mexpand(a1**2 - b1**2)`, recursively denests `sqrt(c2_1)` → `c_1`, then `sqrt(a1 + c_1)` → `d_1`. Calls `rad_rationalize(b1, d_1)` for numerator/denominator. Computes `c = _mexpand(d_1/sqrt(2) + num/(den*sqrt(2)))`.
  - Otherwise: calls `_sqrtdenest1(sqrt(c2))` → `c`.
- If `sqrt_depth(c) > 1`, raises `SqrtdenestStopIteration`.
- Computes `ac = a + c`. If `len(ac.args) >= len(expr.args)` and `count_ops(ac) >= count_ops(expr.base)`, raises.
- Denests `d = sqrtdenest(sqrt(ac))`. If `sqrt_depth(d) > 1`, raises.
- Calls `rad_rationalize(b, d)` → `(num, den)`. Computes `r = _mexpand(d/sqrt(2) + num/(den*sqrt(2)))`, applies `radsimp(r)`, then `_mexpand(r)` and returns it.

---

### `_sqrtdenest1(expr, denester=True)`

**Signature:** `_sqrtdenest1(expr: Expr, denester: bool = True) -> Expr`

Main single-sqrt denesting dispatcher. Tries multiple strategies in order of increasing complexity.

1. If not a sqrt or if radicand is an atom, returns `expr`.
2. Calls `_sqrt_match(a)` on the radicand → `(a, b, r)`. If no match, returns `expr`.
3. Computes `d2 = _mexpand(a**2 - b**2*r)`:
   - If `d2.is_Rational` and positive: calls `_sqrt_numeric_denest(a, b, r, d2)`. If result is not None, returns it.
   - If `d2.is_Rational` and non-positive (fourth root case): computes `dr2 = _mexpand(-d2*r)`, `dr = sqrt(dr2)`. If `dr.is_Rational`, calls `_sqrt_numeric_denest(_mexpand(b*r), a, r, dr2)` → `z`; if not None, returns `z / root(r, 4)`.
   - Otherwise: calls `_sqrt_symbolic_denest(a, b, r)`. If result is not None, returns it.
4. If `denester` is False or `not is_algebraic(expr)`, returns `expr`.
5. Calls `sqrt_biquadratic_denest(expr, a, b, r, d2)`. If result is truthy, returns it.
6. Falls back to the full denester: calls `_denester([radsimp(expr**2)], [a, b, r, d2], 0, sqrt_depth(expr))` → `(z, f)`. If `av0[1]` (i.e., `b`) is None, returns `expr`. If `z` has same depth as original but more operations (`count_ops(z) > count_ops(expr)`), returns `expr`; otherwise returns `z`.
7. Returns `expr` unchanged if all strategies fail.

---

### `_sqrt_symbolic_denest(a, b, r)`

**Signature:** `_sqrt_symbolic_denest(a: Expr, b: Expr, r: Expr) -> Expr | None`

Symbolic denesting via polynomial substitution. Given `sqrt(a + b*sqrt(r))`, attempts to rewrite it as a simpler expression.

1. Sympifies `a, b, r`.
2. Calls `_sqrt_match(r)` → `(ra, rb, rr)`. If no match or `rb == 0`, returns `None`.
3. Creates a positive Dummy `y`. Substitutes `sqrt(rr) = (y**2 - ra)/rb` into `a`, then constructs `Poly(a_substituted, y)`. On `PolynomialError`, returns `None`.
4. If the polynomial has degree 2 with coefficients `(ca, cb, cc)`: computes `cb + b`, checks if `_mexpand((cb+b)**2 - 4*ca*cc).equals(0)`. If true:
   - Constructs `z = sqrt(ca * (sqrt(r) + cb/(2*ca))**2)`.
   - If `z.is_number`: applies `_mexpand(Mul._from_args(z.as_content_primitive()))`.
   - Returns `z`.

---

### `_sqrt_numeric_denest(a, b, r, d2)`

**Signature:** `_sqrt_numeric_denest(a: Expr, b: Expr, r: Expr, d2: Expr) -> Expr | None`

Denests `sqrt(a + b*sqrt(r))` when `d2 = a² - b²*r > 0` is rational. Returns the denested expression or `None`.

1. Computes `depthr = sqrt_depth(r)`, `d = sqrt(d2)`, `vad = a + d`.
2. Checks if `sqrt_depth(vad) < depthr + 1` or `(vad**2).is_Rational` (fourth root case). If so:
   - Computes `vad1 = radsimp(1/vad)`.
   - Returns `_mexpand(sqrt(vad/2) + sign(b)*sqrt((b**2*r*vad1/2).expand()))`, then `.expand()`.

---

### `sqrt_biquadratic_denest(expr, a, b, r, d2)`

**Signature:** `sqrt_biquadratic_denest(expr: Expr, a: Expr, b: Expr, r: Expr, d2: Expr) -> Expr | None`

Denests `sqrt(a + b*sqrt(r))` where `a, b, r` are linear combinations of square roots of positive rationals (SQRR), `r > 0`, `b ≠ 0`, and `d2 = a² - b²*r > 0`. Solves the biquadratic equation `4A⁴ - 4aA² + b²r = 0` for `A`, then computes `B = b/(2A)`, returning `|A + B*sqrt(r)|`.

1. If `r <= 0` or `d2 < 0` or `b == 0` or `sqrt_depth(expr.base) < 2`, returns `None`.
2. For each arg of `a, b, r`: checks that `(y**2).is_Integer and (y**2).is_positive`. If any fails, returns `None`.
3. Computes `sqd = _mexpand(sqrtdenest(sqrt(radsimp(d2))))`. If `sqrt_depth(sqd) > 1`, returns `None`.
4. For each candidate `x` in `[a/2 + sqd/2, a/2 - sqd/2]`:
   - Calls `A = sqrtdenest(sqrt(x))`. If `sqrt_depth(A) > 1`, skips.
   - Computes `Bn, Bd = rad_rationalize(b, _mexpand(2*A))`, then `B = Bn/Bd`.
   - Forms `z = A + B*sqrt(r)`. If `z < 0`, negates it.
   - Returns `_mexpand(z)`.
5. If no candidate works, returns `None`.

---

### `_denester(nested, av0, h, max_depth_level)`

**Signature:** `_denester(nested: list[Expr], av0: list, h: int, max_depth_level: int) -> tuple[Expr | None, list[int] | None]`

Recursive denesting algorithm based on Fagin et al. Denests a list of expressions sharing the same bottom-level radicand. Returns `(denested_expr, subset_flags)` or `(None, None)`.

- If `h > max_depth_level`, returns `(None, None)`.
- If `av0[1]` (i.e., `b`) is None, returns `(None, None)`.
- **Base case** (`av0[0] is None` and all elements of `nested` are Numbers): iterates over `_subsets(len(nested))`. For each binary vector `f`, computes `p = _mexpand(Mul(*[nested[i] for i in range(len(f)) if f[i]]))`. If `f.count(1) > 1 and f[-1]`, negates `p`. Checks if `sqrt(p).is_Rational`. If so, returns `(sqrt(p), f)`. Otherwise, returns `(sqrt(nested[-1]), [0]*len(nested))` (radicand from previous level).
- **Recursive case**:
  - If `av0[0] is not None`: sets `values = [av0[:2]]`, `R = av0[2]`, `nested2 = [av0[3], R]`, clears `av0[0]`.
  - Otherwise: calls `_sqrt_match(expr)` for each expr in `nested`, filters out falsy results. Validates that all matchings share the same radicand `R` (if mismatch, sets `av0[1] = None` and returns `(None, None)`). If no valid matches (`R is None`), returns `(sqrt(nested[-1]), [0]*len(nested))`.
  - Computes `nested2 = [_mexpand(v[0]**2) - _mexpand(R*v[1]**2) for v in values] + [R]`.
  - Recursively calls `_denester(nested2, av0, h+1, max_depth_level)` → `(d, f)`. If `f` is falsy, returns `(None, None)`.
  - **If no flags are set** (`not any(f[i])`): returns `(sqrt(v[0] + _mexpand(v[1]*d)), f)` where `v = values[-1]`.
  - **Otherwise**: computes `p = Mul(*[nested[i] for i in range(len(nested)) if f[i]])`, calls `_sqrt_match(p) → v`. If `1` is in `f` and appears before the last index with `f[len(nested)-1]` being true, negates both `v[0]` and `v[1]`.
    - **If `not f[len(nested)]`** (solution denests with square roots): computes `vad = _mexpand(v[0] + d)`. If `vad <= 0`, returns `(sqrt(nested[-1]), [0]*len(nested))`. Checks depth constraint: if not (`sqrt_depth(vad) <= sqrt_depth(R)+1` or `(vad**2).is_Number`), sets `av0[1]=None` and returns `(None, None)`. Calls `_sqrtdenest1(sqrt(vad), denester=False)` → `sqvad`. If depth constraint fails again, same error return. Computes `sqvad1 = radsimp(1/sqvad)`, returns `_mexpand(sqvad/sqrt(2) + (v[1]*sqrt(R)*sqvad1/sqrt(2)))`.
    - **Else** (`f[len(nested)]` is true, requires fourth root): computes `s2 = _mexpand(v[1]*R) + d`. If `s2 <= 0`, returns `(sqrt(nested[-1]), [0]*len(nested))`. Computes `FR = root(_mexpand(R), 4)`, `s = sqrt(s2)`. Returns `_mexpand(s/(sqrt(2)*FR) + v[0]*FR/(sqrt(2)*s))`.

---

### `_sqrt_ratcomb(cs, args)`

**Signature:** `_sqrt_ratcomb(cs: list[Expr], args: list[Expr]) -> Expr`

Denests rational combinations of radicals (sum of terms `c_i * sqrt(a_i)`). Based on section 5 of Fagin et al. Recursively processes pairs of square roots.

- Inner function `find(a)`: iterates over all pairs `(i, j)` with `i < j`. Computes `p = _mexpand(s1*s2)` where `s1 = a[i].base`, `s2 = a[j].base`. Calls `sqrtdenest(sqrt(p))` → `s`. If `s != sqrt(p)` (denesting succeeded), returns `(s, i, j)`.
- If no pair found (`find(args)` is None): returns `Add(*[c*arg for c, arg in zip(cs, args)])` unchanged.
- Otherwise: pops coefficient and argument at index `i2`, gets `a1 = args[i1]`. Updates `cs[i1] += radsimp(c2 * s / a1.base)` (replacing the second radical with `s/a1`). Recursively calls `_sqrt_ratcomb(cs, args)`.