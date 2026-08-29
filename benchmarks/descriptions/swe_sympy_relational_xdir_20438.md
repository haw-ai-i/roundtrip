## sympy/core/relational.py
Now I have the complete file. Let me write the comprehensive specification:

---

# Module Specification: `sympy/core/relational.py`

## 1. Imports

```python
from typing import Dict, Union, Type
from sympy.utilities.exceptions import SymPyDeprecationWarning
from .basic import S, Atom
from .compatibility import ordered
from .basic import Basic
from .evalf import EvalfMixin
from .function import AppliedUndef
from .sympify import _sympify, SympifyError
from .parameters import global_parameters
from sympy.core.logic import fuzzy_bool, fuzzy_xor, fuzzy_and, fuzzy_not
from sympy.logic.boolalg import Boolean, BooleanAtom
from .expr import Expr
from sympy.multipledispatch import dispatch
from .containers import Tuple
from .symbol import Symbol
```

## 2. Constants & Globals

### `__all__` (tuple)
```python
('Rel', 'Eq', 'Ne', 'Lt', 'Le', 'Gt', 'Ge',
 'Relational', 'Equality', 'Unequality',
 'StrictLessThan', 'LessThan', 'StrictGreaterThan', 'GreaterThan')
```

### `Relational.ValidRelationOperator` (dict) — assigned at module level after all classes are defined:
```python
{
    None: Equality,
    '==': Equality,
    'eq': Equality,
    '!=': Unequality,
    '<>': Unequality,
    'ne': Unequality,
    '>=': GreaterThan,
    'ge': GreaterThan,
    '<=': LessThan,
    'le': LessThan,
    '>': StrictGreaterThan,
    'gt': StrictGreaterThan,
    '<': StrictLessThan,
    'lt': StrictLessThan,
}
```

### Module-level aliases (simple assignments):
- `Rel = Relational`
- `Eq = Equality`
- `Ne = Unequality`
- `Ge = GreaterThan`
- `Le = LessThan`
- `Gt = StrictGreaterThan`
- `Lt = StrictLessThan`

## 3. Module-Level Functions

### `_nontrivBool(side)`
Returns `True` if `side` is an instance of `Boolean` and not an instance of `Atom`; otherwise returns `False`. Used to distinguish non-trivial Boolean expressions from atomic Booleans (`True`/`False`).

### `_canonical(cond)`
Takes a SymPy expression `cond`, finds all `Relational` atoms within it via `cond.atoms(Relational)`, builds a replacement dict mapping each relational to its `.canonical` form, and returns `cond.xreplace(reps)`. No exception handling is performed.

### `_n2(a, b)`
Takes two already-sympified expressions `a` and `b`. If both are comparable (`a.is_comparable` and `b.is_comparable`), computes `(a - b).evalf(2)`. If the result is also comparable, returns it; otherwise returns `None`. Used for fast numerical comparison with 2-digit precision.

### `_eval_is_ge(lhs, rhs)` — dispatch(Expr, Expr)
Default dispatcher returning `None`. Provides a hook for custom Expr subclasses to implement inequality comparisons via multiple dispatch.

### `_eval_is_eq(lhs, rhs)` — multiple dispatch variants:

1. **dispatch(Basic, Basic)** — default; returns `None`.
2. **dispatch(Tuple, Expr)** — returns `False` (a Tuple can never equal a non-Tuple Expr).
3. **dispatch(Tuple, AppliedUndef)** — returns `None` (indeterminate).
4. **dispatch(Tuple, Symbol)** — returns `None` (indeterminate).
5. **dispatch(Tuple, Tuple)** — if lengths differ, returns `False`; otherwise returns `fuzzy_and(fuzzy_bool(is_eq(s, o)) for s, o in zip(lhs, rhs))`, i.e., element-wise fuzzy equality combined with AND logic.

### `is_lt(lhs, rhs)`
Returns `fuzzy_not(is_ge(lhs, rhs))`. Fuzzy boolean: `True` if lhs < rhs, `False` if not, `None` if indeterminate.

### `is_gt(lhs, rhs)`
Returns `fuzzy_not(is_le(lhs, rhs))`. Fuzzy boolean: `True` if lhs > rhs, `False` if not, `None` if indeterminate.

### `is_le(lhs, rhs)`
Returns `is_ge(rhs, lhs)`. Fuzzy boolean: `True` if lhs ≤ rhs, `False` if not, `None` if indeterminate.

### `is_ge(lhs, rhs)`
Fuzzy boolean for "lhs ≥ rhs". Algorithm (all inputs must be `Expr` instances; raises `TypeError` otherwise):

1. Calls `_eval_is_ge(lhs, rhs)`. If returns non-`None`, return that value immediately.
2. Computes `n2 = _n2(lhs, rhs)`. If `n2` is not `None`: if `n2` is `S.Infinity` or `S.NegativeInfinity`, convert to Python float; otherwise keep as SymPy. Return `_sympify(n2 >= 0)`.
3. If both sides are extended-real (`lhs.is_extended_real and rhs.is_extended_real`):
   - If lhs is infinite and positive, return `True`.
   - If rhs is infinite and negative, return `True`.
4. Computes `diff = lhs - rhs`. If `diff is not S.NaN`, checks `diff.is_extended_nonnegative`; if non-`None`, returns that value.

### `is_neq(lhs, rhs)`
Returns `fuzzy_not(is_eq(lhs, rhs))`. Fuzzy boolean: `True` if lhs ≠ rhs, `False` if equal, `None` if indeterminate.

### `is_eq(lhs, rhs)`
Fuzzy boolean for mathematical equality. Algorithm:

1. **Custom `_eval_Eq` hooks**: For each ordering `(lhs, rhs), (rhs, lhs)`, checks if the first argument has an `_eval_Eq` method; calls it with the second argument. If returns non-`None`, return that value.
2. **Dispatch lookup**: Calls `_eval_is_eq(lhs, rhs)`. If non-`None`, return it.
3. **Asymmetric dispatch check**: If `dispatch(type(lhs), type(rhs)) != dispatch(type(rhs), type(lhs))`, calls `_eval_is_eq(rhs, lhs)` and returns if non-`None`.
4. **Structural equality**: If `lhs == rhs` (structural comparison), return `True`.
5. **Boolean atom check**: If both are `BooleanAtom` instances but not structurally equal, return `False` (e.g., `True != False`).
6. **Type mismatch**: If neither is a Symbol and one is Boolean while the other is not, return `False`.
7. **Infinite case** (`lhs.is_infinite or rhs.is_infinite`):
   - If exactly one is infinite, return `False`.
   - If exactly one is extended-real, return `False`.
   - If both are extended-real, return `fuzzy_xor([lhs.is_extended_positive, fuzzy_not(rhs.is_extended_positive)])`.
   - Otherwise, try splitting real/imaginary parts via `split_real_imag` (splits Add args into 'real', 'imag', or None buckets). If neither side has unknown (`None`) components, equate real and imaginary parts separately via `Eq` and combine with `fuzzy_and(map(fuzzy_bool, [...]))`.
   - Compare arguments: if not both NaN, return `fuzzy_bool(Eq(arg(lhs), arg(rhs)))`.
8. **Finite Expr case** (both are `Expr`):
   - Compute `dif = lhs - rhs`. Check `dif.is_zero`; if `False` and commutative, return `False`; if `True`, return `True`.
   - Try `_n2(lhs, rhs)`; if non-`None`, return `_sympify(n2 == 0)`.
   - Numerator/denominator analysis on `dif.as_numer_denom()`:
     - If numerator is zero: return `d.is_nonzero`.
     - If numerator is finite and denominator infinite: return `True`.
     - If numerator nonzero-finite and denominator infinite: check if the condition making denominator infinite also makes original expression equal; if so, return `None`, else return result of substitution.
     - If any addend in numerator is infinite: return `False`.

## 4. Classes

### `class Relational(Boolean, EvalfMixin)`

**Class attributes:**
- `__slots__ = ()` (empty)
- `ValidRelationOperator: Dict[Union[str, None], Type[Relational]]` — maps operator strings to subclass types; initialized after all subclasses are defined.
- `is_Relational = True`

#### `__new__(cls, lhs, rhs, rop=None, **assumptions)`

If `cls is Relational` (direct instantiation):
1. Look up the target class via `ValidRelationOperator.get(rop)`. If not found, raise `ValueError("Invalid relational operator symbol: %r" % rop)`.
2. If the resolved class is NOT a subclass of `(Eq, Ne)` and either `lhs` or `rhs` is a nontrivial Boolean (via `_nontrivBool`), raise `TypeError` with message about Booleans only being valid in Eq/Ne.
3. Delegate to `cls(lhs, rhs, **assumptions)`.

If `cls is not Relational` (subclass instantiation):
- Call `Basic.__new__(cls, lhs, rhs, **assumptions)` directly.

#### Properties:

**`lhs`**: Returns `self._args[0]`.

**`rhs`**: Returns `self._args[1]`.

**`reversed`**: Returns a new relational with sides swapped and operator mapped via `{Eq: Eq, Gt: Lt, Ge: Le, Lt: Gt, Le: Ge, Ne: Ne}`. Uses `Relational.__new__` to construct the result. If the current class is not in the mapping dict, uses the same class (identity).

**`reversedsign`**: Returns a new relational with both sides negated (`-a, -b`) and operator mapped via the same `{Eq: Eq, Gt: Lt, Ge: Le, Lt: Gt, Le: Ge, Ne: Ne}` dict. If either side is a `BooleanAtom`, returns `self` unchanged (no sign reversal for Booleans).

**`negated`**: Returns the logical negation of the relation via `{Eq: Ne, Ge: Lt, Gt: Le, Le: Gt, Lt: Ge, Ne: Eq}`. Constructs with `Relational.__new__`.

**`canonical`**: Normalizes the relational form:
1. If RHS is a number and both sides are numbers with LHS > RHS, reverse.
2. Else if LHS is a number (RHS not), reverse.
3. Else if args are not in `ordered()` order, reverse.
4. If either side is a `BooleanAtom`, return as-is.
5. If LHS has `could_extract_minus_sign()` returning truthy, return `reversedsign`.
6. Else if RHS is not a number and RHS has `could_extract_minus_sign()` returning truthy: compare `ordered([lhs, -rhs])`; if the first element differs from lhs, return `reversed.reversedsign`.
7. Return as-is.

#### Methods:

**`equals(self, other, failing_expression=False)`**: Returns `True` if both sides are mathematically identical and the relation type matches; returns `False` if definitively different; otherwise may return a fuzzy value or recurse. Algorithm:
1. If `other` is not `Relational`, fall through (returns nothing/None implicitly).
2. If `self == other` or `self.reversed == other`, return `True`.
3. If either relation's func is in `(Eq, Ne)`: if funcs differ, return `False`; recursively compare args via `.equals()` in both orderings; short-circuit on any `True`; if all four comparisons are `False`, return `False`; otherwise return the first non-boolean result.
4. Else (both are inequalities): if funcs differ after reversing one, return `False`; compare lhs and rhs separately; short-circuit on `False`; if lhs is `True`, return rhs's result; else return lhs's result.

**`_eval_simplify(self, **kwargs)`**: 
1. Simplify both args via their `.simplify()` methods, reconstruct the relation.
2. If still a relational: compute `dif = lhs - rhs`. If comparable, evaluate at 2 digits; if `equals(0)`, use `S.Zero`. Call `func._eval_relation(v, S.Zero)` to get a definitive result. Canonicalize.
3. If exactly one free real symbol exists: try linear simplification via `linear_coeffs(dif, x)`. Solve for the variable. Handle negative coefficient by negating both sides. Try polynomial fallback with GCD scaling; catch `PolynomialError`.
4. If two or more free symbols: try multivariate linear simplification via `linear_coeffs` and `gcd`; construct simplified expression. Catch `ValueError`.
5. Compare measure of result vs original using `kwargs['measure']` and `kwargs['ratio']`; return simplified if smaller, else return self.

**`_eval_trigsimp(self, **opts)`**: Returns `self.func(trigsimp(lhs), trigsimp(rhs))`, applying trigonometric simplification to each side independently.

**`expand(self, **kwargs)`**: Returns `self.func(*[arg.expand(**kwargs) for arg in self.args])`.

**`__bool__(self)`**: Raises `TypeError("cannot determine truth value of Relational")`. Symbolic relations cannot be coerced to Python bool.

**`_eval_as_set(self)`**: For univariate relations (asserts exactly one free symbol). Calls `solve_univariate_inequality(self, x, relational=False)`. If that raises `NotImplementedError`, wraps in `ConditionSet(x, self, S.Reals)`. Returns the resulting set.

**`binary_symbols`**: Returns an empty set by default. Overridden in subclasses.

---

### `class Equality(Relational)`

Represents mathematical equality (`==`). Inherits from `Relational`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '=='`
- `is_Equality = True`

#### `__new__(cls, lhs, rhs=None, **options)`

1. If `rhs is None`, emit a `SymPyDeprecationWarning` (feature deprecated since 1.5, issue 16587) and set `rhs = 0`.
2. Sympify both sides via `_sympify()`.
3. Extract `evaluate` from options (default: `global_parameters.evaluate`).
4. If evaluating: call `is_eq(lhs, rhs)`. If result is non-`None`, return `_sympify(val)`; else recurse with `cls(lhs, rhs, evaluate=False)`.
5. Otherwise: delegate to `Relational.__new__(cls, lhs, rhs)`.

#### Class method:

**`_eval_relation(cls, lhs, rhs)`**: Returns `_sympify(lhs == rhs)` (structural Python equality).

#### Properties:

**`binary_symbols`**: If `S.true` or `S.false` is in args and the other side is a Symbol, return `{that_symbol}`; otherwise empty set.

#### Methods:

**`_eval_rewrite_as_Add(self, *args, **kwargs)`**: Rewrites `Eq(L, R)` as `L - R`. If `evaluate=True`, returns `L - R` (full cancellation). If `evaluate=None`, returns `_unevaluated_Add(*Add.make_args(L) + Add.make_args(-R))` (canonical order, no cancellation). If `evaluate=False`, returns `Add._from_args(args)` (no cancellation, non-canonical).

**`_eval_simplify(self, **kwargs)`**: Simplifies via parent's `_eval_simplify`. Then if exactly one free symbol: rewrites as Add with `evaluate=False`, calls `linear_coeffs()`, solves for the variable. Uses `measure()` and `ratio` from kwargs to decide whether to accept simplification. Returns `.canonical`.

**`integrate(self, *args, **kwargs)`**: Delegates to `sympy.integrals.integrate(self, ...)`.

**`as_poly(self, *gens, **kwargs)`**: Returns `(self.lhs - self.rhs).as_poly(*gens, **kwargs)`, converting the equality into a polynomial form.

---

### `class Unequality(Relational)`

Represents mathematical inequality (`!=`). Inherits from `Relational`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '!='`

#### `__new__(cls, lhs, rhs, **options)`

1. Sympify both sides via `_sympify()`.
2. Extract `evaluate` from options (default: `global_parameters.evaluate`).
3. If evaluating: call `is_neq(lhs, rhs)`. If non-`None`, return `_sympify(val)`; else recurse with `cls(lhs, rhs, evaluate=False)`.
4. Otherwise: delegate to `Relational.__new__(cls, lhs, rhs, **options)`.

#### Class method:

**`_eval_relation(cls, lhs, rhs)`**: Returns `_sympify(lhs != rhs)` (structural Python inequality).

#### Properties:

**`binary_symbols`**: If `S.true` or `S.false` is in args and the other side is a Symbol, return `{that_symbol}`; otherwise empty set.

#### Methods:

**`_eval_simplify(self, **kwargs)`**: Calls `Equality(*self.args)._eval_simplify(**kwargs)`. If result is still an `Equality`, returns `self.func(*eq.args)` (reconstruct Ne). Otherwise, returns the negated result (`eq.negated`).

---

### `class _Inequality(Relational)`

Internal base class for all inequality types. Inherits from `Relational`.

**Class attributes:**
- `__slots__ = ()`

#### `__new__(cls, lhs, rhs, **options)`

1. Sympify both sides; if `SympifyError`, return `NotImplemented`.
2. Extract `evaluate` from options (default: `global_parameters.evaluate`).
3. If evaluating: validate that neither side is non-real (`is_extended_real is False`) — raises `TypeError`; validate neither is NaN — raises `TypeError`. Then call `cls._eval_relation(lhs, rhs, **options)`.
4. Otherwise: delegate to `Relational.__new__(cls, lhs, rhs, **options)`.

#### Class method:

**`_eval_relation(cls, lhs, rhs, **options)`**: Calls `cls._eval_fuzzy_relation(lhs, rhs)`. If result is non-`None`, return `_sympify(val)`; else return `cls(lhs, rhs, evaluate=False)`.

---

### `class _Greater(_Inequality)`

Internal helper providing `.gts` and `.lts` properties for GreaterThan/StrictGreaterThan. Inherits from `_Inequality`.

**Class attributes:**
- `__slots__ = ()`

#### Properties:
- **`gts`**: Returns `self._args[0]` (the greater-than side).
- **`lts`**: Returns `self._args[1]` (the less-than side).

---

### `class _Less(_Inequality)`

Internal helper providing `.gts` and `.lts` properties for LessThan/StrictLessThan. Inherits from `_Inequality`.

**Class attributes:**
- `__slots__ = ()`

#### Properties:
- **`gts`**: Returns `self._args[1]` (the greater-than side, i.e., RHS).
- **`lts`**: Returns `self._args[0]` (the less-than side, i.e., LHS).

---

### `class GreaterThan(_Greater)`

Represents `lhs >= rhs`. Inherits from `_Greater`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '>='`

#### Class method:

**`_eval_fuzzy_relation(cls, lhs, rhs)`**: Returns `is_ge(lhs, rhs)`.

---

### `class LessThan(_Greater)` — actually inherits from `_Less`

Represents `lhs <= rhs`. Inherits from `_Less`. Sets `__doc__ = GreaterThan.__doc__`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '<='`

#### Class method:

**`_eval_fuzzy_relation(cls, lhs, rhs)`**: Returns `is_le(lhs, rhs)`.

---

### `class StrictGreaterThan(_Greater)`

Represents `lhs > rhs`. Inherits from `_Greater`. Sets `__doc__ = GreaterThan.__doc__`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '>'`

#### Class method:

**`_eval_fuzzy_relation(cls, lhs, rhs)`**: Returns `is_gt(lhs, rhs)`.

---

### `class StrictLessThan(_Less)`

Represents `lhs < rhs`. Inherits from `_Less`. Sets `__doc__ = GreaterThan.__doc__`.

**Class attributes:**
- `__slots__ = ()`
- `rel_op = '<'`

#### Class method:

**`_eval_fuzzy_relation(cls, lhs, rhs)`**: Returns `is_lt(lhs, rhs)`.

## sympy/sets/handlers/comparison.py
Here is the complete natural-language specification of `sympy/sets/handlers/comparison.py`:

---

## Module-Level Preamble

### Imports

```python
from sympy.core.relational import Eq, is_eq
from sympy.core.basic import Basic
from sympy.core.logic import fuzzy_and, fuzzy_bool
from sympy.logic.boolalg import And
from sympy.multipledispatch import dispatch
from sympy.sets.sets import tfn, ProductSet, Interval, FiniteSet, Set
```

- `Eq` — equality relational predicate constructor.
- `is_eq` — function that attempts to determine whether two expressions are equal; returns a truthy/falsy/None fuzzy value.
- `fuzzy_and` — logical AND over a collection of fuzzy (three-valued: True/False/None) values; short-circuits on any False, otherwise returns the conjunction or None if undetermined.
- `fuzzy_bool` — coerces an arbitrary expression to a three-valued boolean (True, False, or None).
- `And` — symbolic logical AND constructor from SymPy's boolean algebra module.
- `dispatch` — decorator that registers multi-dispatch function variants keyed by argument types.
- `tfn` — truth-function dispatcher; takes an iterable of fuzzy values and returns a single fuzzy result (True if all are True, False if any is False, else None).
- `ProductSet`, `Interval`, `FiniteSet`, `Set` — SymPy set classes from `sympy.sets.sets`.

### Constants & Globals

None. The module defines only multi-dispatch function variants of `_eval_is_eq`.

---

## Code Objects (Functions)

All functions are named `_eval_is_eq` and decorated with `@dispatch(...)`. They form a multi-dispatch family that determines whether two SymPy set expressions are equal, returning:
- **`False`** — definitively not equal.
- **An `And(...)` expression** — symbolic equality condition (still to be evaluated).
- **A fuzzy boolean via `tfn[...]`** — computed from the conjunction of element-wise containment checks.
- **`None`** — undetermined / cannot decide.

### 1. `_eval_is_eq(Interval, FiniteSet)` — lines 9–11

**Signature:** `_eval_is_eq(lhs: Interval, rhs: FiniteSet) -> bool | None`

**Logic:** Always returns `False`. An interval (which contains infinitely many points or at least a continuum) can never be equal to a finite set.

---

### 2. `_eval_is_eq(FiniteSet, Interval)` — lines 14–16

**Signature:** `_eval_is_eq(lhs: FiniteSet, rhs: Interval) -> bool | None`

**Logic:** Always returns `False`. Same reasoning as above; order of arguments is swapped but the result is identical.

---

### 3. `_eval_is_eq(Interval, Interval)` — lines 19–24

**Signature:** `_eval_is_eq(lhs: Interval, rhs: Interval) -> bool | And`

**Logic:** Returns a symbolic `And(...)` expression that asserts equality of all four interval properties pairwise:
- `Eq(lhs.left, rhs.left)` — left endpoints are equal.
- `Eq(lhs.right, rhs.right)` — right endpoints are equal.
- `lhs.left_open == rhs.left_open` — both intervals share the same openness status at the left endpoint (both open or both closed).
- `lhs.right_open == rhs.right_open` — both intervals share the same openness status at the right endpoint.

The result is a symbolic `And` object; it evaluates to True only when all four conditions hold, False if any contradiction is detected, and remains symbolic otherwise.

---

### 4. `_eval_is_eq(FiniteSet, Interval)` (overload) — lines 27–29

**Signature:** `_eval_is_eq(lhs: FiniteSet, rhs: Interval) -> bool | None`

**Logic:** Always returns `False`. This is a second dispatch variant for `(FiniteSet, Interval)` that duplicates the result of variant #1. It serves as an explicit overload in the multi-dispatch registry (the first variant at lines 9–11 handles `(Interval, FiniteSet)`, this one handles the reverse order).

---

### 5. `_eval_is_eq(FiniteSet, FiniteSet)` — lines 32–40

**Signature:** `_eval_is_eq(lhs: FiniteSet, rhs: FiniteSet) -> bool | None`

**Logic:** Determines equality by checking mutual element containment:
1. Converts `lhs.args` and `rhs.args` to Python sets (`s_set`, `o_set`).
2. Defines a generator `all_in_both()` that yields two fuzzy values:
   - **Yield 1:** `fuzzy_and(lhs._contains(e) for e in o_set - s_set)` — checks whether every element unique to `rhs` is contained in `lhs`. If the set difference is empty, this yields True (vacuously).
   - **Yield 2:** `fuzzy_and(rhs._contains(e) for e in s_set - o_set)` — checks whether every element unique to `lhs` is contained in `rhs`. Again vacuous if the difference is empty.
3. Passes the generator of two fuzzy values into `tfn[...]`, which reduces them: returns True only if both yields are True (i.e., no elements differ), False if any containment check fails, and None otherwise.

**Return:** A single fuzzy boolean — `True` if the sets contain exactly the same elements, `False` if they differ in at least one element, or `None` if containment cannot be determined for some element.

---

### 6. `_eval_is_eq(ProductSet, ProductSet)` — lines 43–49

**Signature:** `_eval_is_eq(lhs: ProductSet, rhs: ProductSet) -> bool | None`

**Logic:**
1. If `len(lhs.sets) != len(rhs.sets)`, returns `False` immediately (different arity means the Cartesian products live in different spaces and cannot be equal).
2. Otherwise, zips corresponding component sets from both product sets: `(x, y)` for each pair of components at the same index.
3. For each pair, calls `is_eq(x, y)` to get a fuzzy equality result.
4. Maps each fuzzy result through `fuzzy_bool` to normalize it.
5. Passes all normalized results into `tfn[...]`, which reduces them: returns True only if every component pair is equal, False if any component pair differs, and None otherwise.

**Return:** A single fuzzy boolean — `True` if both product sets have the same arity and each corresponding component set is equal; `False` if arities differ or any component pair is unequal; `None` if equality of some component cannot be determined.

---

### 7. `_eval_is_eq(Set, Basic)` — lines 52–54

**Signature:** `_eval_is_eq(lhs: Set, rhs: Basic) -> bool | None`

**Logic:** Always returns `False`. A set object can never be equal to a non-set basic SymPy expression (e.g., a number, symbol, or function).

---

### 8. `_eval_is_eq(Set, Set)` — lines 57–59

**Signature:** `_eval_is_eq(lhs: Set, rhs: Set) -> None`

**Logic:** Returns `None`. This is the catch-all fallback dispatch for any pair of set types not covered by the more specific variants above. It indicates that equality cannot be determined generically and must be deferred to a higher-level handler or left unevaluated.

---

## Summary Table

| Dispatch Signature | Return Value |
|---|---|
| `(Interval, FiniteSet)` | `False` |
| `(FiniteSet, Interval)` (first) | `False` |
| `(Interval, Interval)` | `And(Eq(lefts), Eq(rights), left_open_eq, right_open_eq)` |
| `(FiniteSet, Interval)` (second) | `False` |
| `(FiniteSet, FiniteSet)` | `tfn[fuzzy_and(...)]` — mutual containment check |
| `(ProductSet, ProductSet)` | `tfn[...]` — arity check + per-component `is_eq` |
| `(Set, Basic)` | `False` |
| `(Set, Set)` (fallback) | `None` |

## sympy/sets/handlers/issubset.py
Here is the complete natural-language specification of `sympy/sets/handlers/issubset.py`:

---

## Module-Level Preamble

### Imports

```python
from sympy import S, Symbol
from sympy.core.logic import fuzzy_and, fuzzy_bool, fuzzy_not, fuzzy_or
from sympy.core.relational import Eq
from sympy.sets.sets import FiniteSet, Interval, Set, Union
from sympy.sets.fancysets import Complexes, Reals, Range, Rationals
from sympy.multipledispatch import dispatch
```

### Constants & Globals

- **`_inf_sets`** — A module-level list of six SymPy singleton sets: `[S.Naturals, S.Naturals0, S.Integers, S.Rationals, S.Reals, S.Complexes]`. This constant is defined but not referenced within this file.

### Code Objects (All named `is_subset_sets`)

The module defines a family of functions all sharing the name `is_subset_sets`, each decorated with `@dispatch(TypeA, TypeB)`. The `multipledispatch` mechanism routes calls to the most-specific overload based on the runtime types of the two arguments. Each overload returns either `True`, `False`, or `None` (meaning "undetermined").

---

#### 1. `is_subset_sets(a: Set, b: Set)` — Base fallback

- **Signature:** `(a: Set, b: Set) -> bool | None`
- **Logic:** Returns `None` unconditionally. This is the least-specific overload; it acts as a catch-all that signals "cannot determine" when no more specific dispatch matches.

---

#### 2. `is_subset_sets(a: Interval, b: Interval)` — Interval ⊆ Interval

- **Signature:** `(a: Interval, b: Interval) -> bool | None`
- **Logic (four guard checks in sequence; first match wins):**
  1. If `fuzzy_bool(a.start < b.start)` is truthy → return `False`. The left endpoint of `a` is strictly to the left of `b`'s left endpoint, so `a` cannot be contained in `b`.
  2. If `fuzzy_bool(a.end > b.end)` is truthy → return `False`. The right endpoint of `a` is strictly to the right of `b`'s right endpoint.
  3. If `b.left_open` is true **and** `a.left_open` is false **and** `fuzzy_bool(Eq(a.start, b.start))` is truthy → return `False`. The intervals share a left boundary value but `b` excludes it while `a` includes it, so `a`'s left endpoint lies outside `b`.
  4. If `b.right_open` is true **and** `a.right_open` is false **and** `fuzzy_bool(Eq(a.end, b.end))` is truthy → return `False`. Symmetric to (3) for the right boundary.
- **Return:** If none of the four guards fire, returns `None` (implicitly).

---

#### 3. `is_subset_sets(a_interval: Interval, b_fs: FiniteSet)` — Interval ⊆ FiniteSet

- **Signature:** `(a_interval: Interval, b_fs: FiniteSet) -> bool | None`
- **Logic:** If `fuzzy_not(a_interval.measure.is_zero)` is truthy (i.e., the interval has non-zero measure), return `False`. A non-degenerate interval cannot be a subset of any finite set.
- **Return:** Otherwise returns `None`.

---

#### 4. `is_subset_sets(a_interval: Interval, b_u: Union)` — Interval ⊆ Union

- **Signature:** `(a_interval: Interval, b_u: Union) -> bool | None`
- **Precondition check:** If not every element of `b_u.args` is an instance of `(Interval, FiniteSet)`, skip this overload (return `None`).
- **Logic (three guard checks in sequence):**
  1. Extract all interval members from `b_u.args`. If `fuzzy_bool(a_interval.start < s.start)` is truthy for **all** such intervals → return `False` (`a`'s start lies to the left of every union component's start).
  2. Similarly, if `fuzzy_bool(a_interval.end > s.end)` is truthy for **all** such intervals → return `False`.
  3. If `a_interval.measure.is_nonzero` (non-degenerate), define a helper `no_overlap(s1, s2) = fuzzy_or([s1.end <= s2.start, s1.start >= s2.end])`. If this returns truthy for **all** interval members of the union → return `False` (`a` is completely disjoint from every interval component).
- **Return:** Otherwise returns `None`.

---

#### 5. `is_subset_sets(a: Range, b: Range)` — Range ⊆ Range (step == 1)

- **Signature:** `(a: Range, b: Range) -> bool | None`
- **Logic:** Only fires when `a.step == b.step == 1`. Returns `fuzzy_and([fuzzy_bool(a.start >= b.start), fuzzy_bool(a.stop <= b.stop)])`. In other words, `a ⊆ b` iff `a`'s start is at or after `b`'s start **and** `a`'s stop is at or before `b`'s stop.
- **Return:** If the step condition fails, returns `None`.

---

#### 6. `is_subset_sets(a_range: Range, b_interval: Interval)` — Range ⊆ Interval

- **Signature:** `(a_range: Range, b_interval: Interval) -> bool | None`
- **Precondition:** Only fires when `a_range.step.is_positive`.
- **Logic (two conditions combined with `fuzzy_and`):**
  - **Left condition (`cond_left`):** If `b_interval.left_open` is true and `a_range.inf.is_finite`, then `cond_left = a_range.inf > b_interval.left`; otherwise `cond_left = a_range.inf >= b_interval.left`.
  - **Right condition (`cond_right`):** If `b_interval.right_open` is true and `a_range.sup.is_finite`, then `cond_right = a_range.sup < b_interval.right`; otherwise `cond_right = a_range.sup <= b_interval.right`.
- **Return:** `fuzzy_and([cond_left, cond_right])`. Otherwise returns `None`.

---

#### 7. `is_subset_sets(a_range: Range, b_finiteset: FiniteSet)` — Range ⊆ FiniteSet

- **Signature:** `(a_range: Range, b_finiteset: FiniteSet) -> bool | None`
- **Logic (multi-stage):**
  1. Attempt to read `a_size = a_range.size`. If this raises `ValueError` (symbolic range of unknown size), return `None`.
  2. If `a_size > len(b_finiteset)`, return `False` (range has more elements than the finite set).
  3. If any argument in `a_range.args` contains a `Symbol`, return `fuzzy_and(b_finiteset.contains(x) for x in a_range)` — check membership of each element of the range against the finite set, combined with fuzzy AND.
  4. Otherwise (concrete numeric range): Convert `a_range` to a Python `set` called `a_set`. Initialize `b_remaining = len(b_finiteset)` and `cnt_candidate = 0`. Iterate over each element `b` in `b_finiteset`:
     - If `b.is_Integer` → remove it from `a_set` via `discard`.
     - Else if `fuzzy_not(b.is_integer)` is truthy (definitely not an integer) → do nothing.
     - Otherwise (`b` might be an integer but unknown) → increment `cnt_candidate`.
     - Decrement `b_remaining`.
     - **Early-out 1:** If `len(a_set) > b_remaining + cnt_candidate`, return `False` (too many unmatched elements remain for the remaining candidates to cover).
     - **Early-out 2:** If `len(a_set) == 0`, return `True` (all range elements found in the finite set).
- **Return:** After exhausting all finite-set elements without early termination, return `None`.

---

#### 8. `is_subset_sets(a_interval: Interval, b_range: Range)` — Interval ⊆ Range

- **Signature:** `(a_interval: Interval, b_range: Range) -> bool | None`
- **Logic:** If `a_interval.measure.is_extended_nonzero`, return `False`. A non-degenerate interval cannot be a subset of a discrete range.
- **Return:** Otherwise returns `None`.

---

#### 9. `is_subset_sets(a_interval: Interval, b_rationals: Rationals)` — Interval ⊆ Rationals

- **Signature:** `(a_interval: Interval, b_rationals: Rationals) -> bool | None`
- **Logic:** If `a_interval.measure.is_extended_nonzero`, return `False`. A non-degenerate interval contains irrational numbers and thus cannot be a subset of the rationals.
- **Return:** Otherwise returns `None`.

---

#### 10. `is_subset_sets(a: Range, b: Complexes)` — Range ⊆ Complexes

- **Signature:** `(a: Range, b: Complexes) -> bool`
- **Logic:** Always returns `True`. Every range of integers is a subset of the complex numbers.

---

#### 11. `is_subset_sets(a: Complexes, b: Interval)` — Complexes ⊆ Interval

- **Signature:** `(a: Complexes, b: Interval) -> bool`
- **Logic:** Always returns `False`. The complex numbers cannot be a subset of any interval (which is a real set).

---

#### 12. `is_subset_sets(a: Complexes, b: Range)` — Complexes ⊆ Range

- **Signature:** `(a: Complexes, b: Range) -> bool`
- **Logic:** Always returns `False`.

---

#### 13. `is_subset_sets(a: Complexes, b: Rationals)` — Complexes ⊆ Rationals

- **Signature:** `(a: Complexes, b: Rationals) -> bool`
- **Logic:** Always returns `False`.

---

#### 14. `is_subset_sets(a: Rationals, b: Reals)` — Rationals ⊆ Reals

- **Signature:** `(a: Rationals, b: Reals) -> bool`
- **Logic:** Always returns `True`. The rationals are a subset of the reals.

---

#### 15. `is_subset_sets(a: Rationals, b: Range)` — Rationals ⊆ Range

- **Signature:** `(a: Rationals, b: Range) -> bool`
- **Logic:** Always returns `False`. The infinite set of rationals cannot be a subset of any finite range.