## sympy/core/basic.py
Now I have the full file content. Let me write the complete natural-language specification.

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division
from collections import Mapping, defaultdict
from itertools import chain
from .assumptions import BasicMeta, ManagedProperties
from .cache import cacheit
from .sympify import _sympify, sympify, SympifyError
from .compatibility import (iterable, Iterator, ordered, string_types, with_metaclass, zip_longest, range)
from .singleton import S
from inspect import getmro
```

## Constants & Globals

None at module level beyond the classes and functions defined below.

---

# Code Objects

## Class `Basic(with_metaclass(ManagedProperties))`

**Metaclass:** `ManagedProperties` (via `with_metaclass`).  
**Slots:** `_mhash` (int or None, hash value), `_args` (tuple of arguments), `_assumptions` (assumption store).

### Class-level Boolean Flags (all default `False`)

`is_number`, `is_Atom`, `is_Symbol`, `is_symbol`, `is_Indexed`, `is_Dummy`, `is_Wild`, `is_Function`, `is_Add`, `is_Mul`, `is_Pow`, `is_Number`, `is_Float`, `is_Rational`, `is_Integer`, `is_NumberSymbol`, `is_Order`, `is_Derivative`, `is_Piecewise`, `is_Poly`, `is_AlgebraicNumber`, `is_Relational`, `is_Equality`, `is_Boolean`, `is_Not`, `is_Matrix`, `is_Vector`, `is_Point`.

### Constructor: `__new__(cls, *args)`

Creates a new instance via `object.__new__(cls)`. Initializes `_assumptions` to `cls.default_assumptions`, sets `_mhash = None`, and stores `args` as `_args`. Returns the object. All items in `args` must be `Basic` objects.

### Method: `copy()`

Returns `self.func(*self.args)` — a new instance with identical arguments.

### Pickling Methods

- **`__reduce_ex__(self, proto)`**: Returns `(type(self), self.__getnewargs__(), self.__getstate__())`.
- **`__getnewargs__(self)`**: Returns `self.args`.
- **`__getstate__(self)`**: Returns `{}`.
- **`__setstate__(self, state)`**: For each `(k, v)` in `state`, calls `setattr(self, k, v)`.

### Method: `__hash__(self)`

Computes hash as `hash((type(self).__name__,) + self._hashable_content())` if `_mhash` is None; caches result in `_mhash`. Returns the cached or computed integer. Cannot be cached via `@cacheit` because the cache dict itself needs hashing (infinite recursion).

### Method: `_hashable_content(self)`

Returns `self._args` — a tuple of information used for hash and equality computation. Subclasses with additional relevant attributes should override this to include them.

### Property: `assumptions0`

Returns `{}` — the object's type-level initial assumptions dict. Subclasses (e.g., `Symbol`) override to return their actual assumptions0.

### Method: `compare(self, other)`

Returns `-1`, `0`, or `1`:
1. If `self is other`, returns `0`.
2. Compares class types: `(n1 > n2) - (n1 < n2)`. Returns non-zero if different.
3. Compares `_hashable_content()` lengths: `(len(st) > len(ot)) - (len(st) < len(ot))`.
4. Zips through `st` and `ot`: for each pair, converts frozensets to `Basic(*item)`; compares via `l.compare(r)` if both are `Basic`, else `(l > r) - (l < r)`. Returns first non-zero or `0`.

### Static Method: `_compare_pretty(a, b)`

Special comparison for pretty printing:
1. If exactly one of `a`, `b` is an `Order` instance, returns `1` (Order > non-Order).
2. If both are `Rational`: compares cross-products `a.p * b.q` vs `b.p * a.q`.
3. Otherwise, tries to match both against pattern `p1 * p2**p3` using `Wild`; if exponents found, recursively compares them via `Basic.compare(a3, b3)`. Falls back to `Basic.compare(a, b)`.

### Class Method: `fromiter(cls, args, **assumptions)`

Returns `cls(*tuple(args), **assumptions)` — creates an instance from any iterable.

### Class Method: `class_key(cls)`

Returns `(5, 0, cls.__name__)` — a tuple for ordering classes. Subclasses override (e.g., `Atom` returns `(2, 0, cls.__name__)`).

### Method: `sort_key(self, order=None)` *(cached via `@cacheit`)*

Builds a sort key:
1. Defines inner helper `inner_key(arg)`: if `arg` is `Basic`, calls `arg.sort_key(order)`; else returns `arg`.
2. Gets `_sorted_args`, maps each through `inner_key`.
3. Returns `(self.class_key(), len(args), tuple(inner_key'd args), S.One.sort_key(), S.One)`.

### Method: `__eq__(self, other)`

Returns boolean:
1. If `self is other`, returns `True`.
2. If types differ and either is a `Pow` with exponent `1`: unwraps the Pow (e.g., `a**1 == a`).
3. Sympifies `other` via `_sympify(other)`. On `SympifyError`, returns `False`.
4. If types still differ after sympification, returns `False`.
5. Returns `self._hashable_content() == other._hashable_content()`.

### Method: `__ne__(self, other)`

Returns `not self.__eq__(other)`.

### Method: `dummy_eq(self, other, symbol=None)`

Compares two expressions handling dummy symbols:
1. Collects free dummy symbols from `self`. If none, returns `self == other`.
2. If exactly one dummy, uses it; if more than one, raises `ValueError("only one dummy symbol allowed on the left-hand side")`.
3. If `symbol` is None: collects free symbols from `other`; if none, returns `self == other`; if exactly one, uses it; if more, raises `ValueError("specify a symbol in which expressions should be compared")`.
4. Creates a fresh dummy of the same class as the matched dummy (`dummy.__class__()`).
5. Returns `self.subs(dummy, tmp) == other.subs(symbol, tmp)`.

### Methods: `__repr__(self)` and `__str__(self)`

Both return `sstr(self, order=None)` from `sympy.printing.sstr`, using default (lex) ordering regardless of global settings.

### Method: `atoms(self, *types)`

Returns a set of atoms forming the current object:
1. If `types` is given, converts each element to its type (`type(t)` if not already a type).
2. If no types given, defaults to `(Atom,)`.
3. Iterates through `preorder_traversal(self)`, collecting instances matching any of the requested types into a set. Returns the set.

### Property: `free_symbols`

Returns `set().union(*[a.free_symbols for a in self.args])` — union of free symbols from all arguments. Subclasses with bound variables (e.g., `Integral`, `Derivative`) override this.

### Property: `canonical_variables`

Returns a dict mapping variables to canonical underscore-suffixed symbols:
1. If no `variables` attribute, returns `{}`.
2. Finds the longest suffix of underscores (`u = "_"`, `"__"`, etc.) such that no existing free symbol name ends with it.
3. Creates new `Symbol(name % i, **v.assumptions0)` for each variable at position `i`. Returns the mapping dict.

### Method: `rcall(self, *args)`

Delegates to `Basic._recursive_call(self, args)`. Applies an expression recursively through arguments (simulating operator notation like `(x + Lambda(y, 2*y))(z)` → `x + 2*z`).

### Static Method: `_recursive_call(expr_to_call, on_args)`

Helper for `rcall`:
1. Checks if `expr_to_call` has a custom `__call__` (via MRO scan). If callable and overridden (not just `Basic.__call__`), calls it directly — unless it's a `Symbol` (which transforms to `UndefFunction`).
2. If `expr_to_call.args` exists, recursively calls on each arg, then reconstructs with `type(expr_to_call)(*args)`.
3. Otherwise returns `expr_to_call` unchanged.

### Method: `is_hypergeometric(self, k)`

Returns `hypersimp(self, k) is not None` from `sympy.simplify.hypersimp`.

### Property: `is_comparable`

Returns whether the expression can be computed to a real number with precision:
1. If `self.is_real` is `False`, returns `False`.
2. If `self.is_number` is `False`, returns `False`.
3. Evaluates `as_real_imag()` at precision 2; if either component isn't a `Number`, returns `False`.
4. If imaginary part is non-zero, returns `False`.
5. Otherwise returns `n._prec != 1` (precision not ambiguous).

### Property: `func`

Returns `self.__class__` — the top-level constructor class of the expression.

### Property: `args`

Returns `self._args` — a tuple of arguments. Never use `_args` directly; always use `.args`.

### Property: `_sorted_args`

Returns `self.args`. Subclasses without fixed argument order override to return sorted args.

### Method: `as_poly(self, *gens, **args)`

Attempts conversion to polynomial via `Poly(self, *gens, **args)`. Returns the `Poly` object if `poly.is_Poly` is True; returns `None` on `PolynomialError` or if not a polynomial.

### Method: `as_content_primitive(self, radical=False, clear=True)`

Returns `(S.One, self)` — stub allowing Basic args (like Tuple) to be skipped during content/primitive computation. Subclasses like `Expr` override with real logic.

### Method: `subs(self, *args, **kwargs)`

Substitutes old for new after sympifying args. Accepts either 1 or 2 arguments:
- **One arg**: must be a dict, set, Mapping, or iterable of (old, new) tuples. Raises `ValueError` otherwise.
- **Two args**: treated as `(old, new)` wrapped in a list.

Processing:
1. Converts sequence to list. For each pair, sympifies both elements via `_sympify(si, strict=True)`. String values become `Symbol`. Pairs that can't be sympified are dropped (`None`). Pairs where old == new (via `_aresame`) are dropped.
2. If unordered (set/Mapping): sorts by `(count_ops, len(args))` descending, then by `default_sort_key`. Atom keys sorted by `default_sort_key`; non-atom keys grouped and sorted within groups.
3. **Simultaneous mode** (`simultaneous=True`): For each `(old, new)`, substitutes old with a dummy `d*m` (where `m` is a fresh Dummy), collects mappings `{d: new}`. After all substitutions, xreplaces `d → new` and `m → S.One`.
4. **Sequential mode** (default): Iteratively calls `rv._subs(old, new)` for each pair; breaks if result is no longer `Basic`. Returns final value.

### Method: `_subs(self, old, new, **hints)` *(cached via `@cacheit`)*

Core substitution logic:
1. If `_aresame(self, old)`, returns `new`.
2. Calls `self._eval_subs(old, new)`. If it returns non-None, uses that result.
3. Otherwise applies fallback (see below).

**Fallback inner function:** Traverses each argument via `arg._subs(old, new, **hints)`. If any arg changed (`not _aresame(arg, args[i])`), rebuilds with `self.func(*args)`. Handles `hack2` mode for `Mul`: if the result is no longer a `Mul`, separates numeric and non-numeric factors, reconstructing as `func(coeff, nonnumber, evaluate=False)` or returning just `nonnumber`/`coeff * nonnumber`.

### Method: `_eval_subs(self, old, new)`

Returns `None` — stub. Subclasses override to provide custom substitution logic (e.g., for bound variables). Returning `None` triggers the fallback argument traversal.

### Method: `xreplace(self, rule)`

Returns `self._xreplace(rule)[0]` — exact node replacement in expression tree using a dict-like `rule`. Replaces only entire nodes that are keys in `rule`.

### Method: `_xreplace(self, rule)` *(cached via `@cacheit`)*

Helper tracking whether replacement occurred. Returns `(value, changed)`:
1. If `self in rule`, returns `(rule[self], True)`.
2. Otherwise, recursively calls `_xreplace(rule)` on each arg. If any changed, reconstructs with `self.func(*args)` and returns `(new, True)`.
3. If no change, returns `(self, False)`.

### Method: `has(self, *patterns)`

Tests whether any subexpression matches any pattern. Returns `False` if patterns is empty. Delegates to `_has(pattern)` for each pattern; returns `any(...)`.

### Method: `_has(self, pattern)`

Helper for `has`:
1. If `pattern` is an `UndefinedFunction`, checks if any atom matching `Function` or `UndefinedFunction` has equal func or equals the pattern.
2. Sympifies `pattern`. If it's a metaclass (`BasicMeta`), checks `isinstance(arg, pattern)` for all preorder traversal results.
3. Otherwise tries `pattern._has_matcher()` to get an equality function; returns `any(match(arg) for arg in preorder_traversal(self))`. Falls back to `arg == pattern` on `AttributeError`.

### Method: `_has_matcher(self)`

Returns `self.__eq__` — used by `_has` as the matching predicate.

### Method: `replace(self, query, value, map=False, simultaneous=True, exact=False)`

Replaces matching subexpressions from bottom to top using `bottom_up`:
1. Sympifies `query` and `value` (catches `SympifyError`).
2. Determines `_query` and `_value` lambdas based on types:
   - **Type query**: `_query = lambda expr: isinstance(expr, query)`. If value is type/callable, applies it to `expr.args`. Raises `TypeError` otherwise.
   - **Basic (pattern) query**: `_query = lambda expr: expr.match(query)` (returns dict or None). Value can be Basic or callable; if Basic, does `value.subs(result)`; if callable, strips trailing `_` from Wild keys and passes as kwargs. If `exact=True`, only replaces when all matched values are non-zero.
   - **Callable query**: `_query = query`. Value must also be callable: `_value = lambda expr, result: value(expr)`.
3. Builds `mapping` dict and `mask` list (for simultaneous mode).
4. Inner function `rec_replace(expr)`: queries; if match, computes new value. In simultaneous mode, replaces with a Dummy placeholder in the mask. Returns expression.
5. Applies `bottom_up(self, rec_replace, atoms=True)`.
6. If simultaneous: reverses mask and xreplaces each dummy back to its original replacement.
7. If `map=True`: also returns `(rv, mapping)` (with mapping keys/values xreplaced through the mask in simultaneous mode).

### Method: `find(self, query, group=False)`

Finds all subexpressions matching a query:
1. Converts query via `_make_find_query(query)`.
2. Filters `preorder_traversal(self)` through the callable.
3. If `group=False`, returns `set(results)`. If `group=True`, returns dict `{result: count}`.

### Method: `count(self, query)`

Counts matching subexpressions via `_make_find_query(query)`, sums `bool(query(sub))` over all preorder traversal results.

### Method: `matches(self, expr, repl_dict={}, old=False)`

Pattern matching between Wild symbols in self and expressions in expr:
1. Sympifies `expr`. If not same class as self, returns `None`.
2. If `self == expr`, returns `repl_dict` (copy).
3. If arg counts differ, returns `None`.
4. Copies `repl_dict`; for each `(arg, other_arg)` pair: if equal, continues; else calls `arg.xreplace(d).matches(other_arg, d, old=old)`. Returns `None` on first mismatch; otherwise returns accumulated dict.

### Method: `match(self, pattern, old=False)`

Public interface to pattern matching. Sympifies `pattern`, delegates to `pattern.matches(self, old=old)`. Returns a dict mapping Wild symbols (with trailing `_`) to matched subexpressions, or `None` if no match.

### Method: `count_ops(self, visual=None)`

Delegates to `sympy.count_ops(self, visual)`.

### Method: `doit(self, **hints)`

Evaluates unevaluated objects (limits, integrals, sums, products):
1. If `deep=True` (default), recursively calls `term.doit(**hints)` on each Basic arg, then reconstructs with `self.func(*terms)`.
2. If `deep=False`, returns `self` unchanged.

### Method: `_eval_rewrite(self, pattern, rule, **hints)`

Rewrite helper:
1. If atom and has the named rule method, calls it; else returns self.
2. If `deep=True`, recursively rewrites args; else uses raw args.
3. If `pattern is None` or `isinstance(self, pattern)` and has the rule method, calls it with args. If result is non-None, returns it.
4. Otherwise reconstructs with `self.func(*args)`.

### Method: `rewrite(self, *args, **hints)`

Rewrites functions in terms of other functions:
1. If no args, returns self.
2. Last arg is the target (string → `_eval_rewrite_as_<target>` or callable → uses its name). Remaining args form the pattern filter.
3. If no pattern, calls `self._eval_rewrite(None, rule, **hints)`.
4. Filters patterns to those present in self (`self.has(p)`). If any match, calls `self._eval_rewrite(tuple(pattern), rule, **hints)`; else returns self.

### Class Variable: `_constructor_postprocessor_mapping`

Default `{}` — dict mapping expression node names to lists of postprocessing functions.

### Class Method: `_exec_constructor_postprocessors(cls, obj)` *(experimental)*

Applies constructor postprocessors:
1. Iterates over `obj.args`; for each arg, looks up its type's MRO in `_constructor_postprocessor_mapping`, collecting postprocessors keyed by class name.
2. Applies all postprocessors registered for `cls.__name__` sequentially (`obj = f(obj)`).
3. If any postprocessors were found and obj is not already in the mapping, stores them: `Basic._constructor_postprocessor_mapping[obj] = postprocessors`.
4. Returns (possibly modified) `obj`.

---

## Class `Atom(Basic)`

**Inherits from:** `Basic`.  
**Slots:** `[]` (empty — no additional slots).  
**Class flag:** `is_Atom = True`.

### Method: `matches(self, expr, repl_dict={}, old=False)`

If `self == expr`, returns `repl_dict`; else returns `None` (implicit).

### Method: `xreplace(self, rule, hack2=False)`

Returns `rule.get(self, self)`.

### Method: `doit(self, **hints)`

Returns `self`.

### Class Method: `class_key(cls)`

Returns `(2, 0, cls.__name__)` — lower priority than Basic's `(5, ...)`.

### Method: `sort_key(self, order=None)` *(cached via `@cacheit`)*

Returns `(self.class_key(), (1, (str(self),)), S.One.sort_key(), S.One)`.

### Method: `_eval_simplify(self, ratio, measure)`

Returns `self`.

### Property: `_sorted_args`

Raises `AttributeError('Atoms have no args. It might be necessary to make a check for Atoms in the calling code.')` — safeguard against accidentally using `_sorted_args` on atoms.

---

## Function: `_aresame(a, b)`

Returns `True` if `a` and `b` are structurally identical (same type at every node), else `False`. Uses `zip_longest(preorder_traversal(a), preorder_traversal(b))`:
1. For each pair `(i, j)`: if `i != j` or `type(i) != type(j)`, checks special cases for `UndefFunc`/`AppliedUndef` (compares via `class_key()`); otherwise returns `False`.
2. If all pairs match through the else clause of the for loop, returns `True`.

---

## Function: `_atomic(e)`

Returns atom-like quantities as far as substitution is concerned (`Derivative`, `Function`, and free `Symbol` instances). Skips atoms nested inside such constructs unless they also appear outside.
1. Gets `e.free_symbols` (or `{e}` on `AttributeError`).
2. Iterates through `preorder_traversal(e)`. Tracks `seen` set to avoid revisiting.
3. If a node is a free `Symbol`, adds it to result.
4. If a node is `Derivative` or `Function`, calls `pot.skip()` (skips its subtree) and adds the node itself.
5. Returns the set of atomic elements.

---

## Class `preorder_traversal(Iterator)`

**Inherits from:** `Iterator`.  
An iterator that yields nodes in pre-order traversal (current node, then children breadth-first).

### Constructor: `__init__(self, node, keys=None)`

Stores `_skip_flag = False`, initializes internal generator `self._pt = self._preorder_traversal(node, keys)`.

### Method: `_preorder_traversal(self, node, keys)` (generator)

1. Yields the current `node`.
2. If `_skip_flag` is set, clears it and returns (skips children).
3. If `node` is `Basic`: gets args from `_argset` (if available and no sorting needed) or `args`. If `keys` is truthy, sorts via `ordered(args, keys)`; if `keys == True`, uses default ordering. Recursively yields subtrees for each arg.
4. If `node` is iterable (but not Basic), recursively yields subtrees for each item.

### Method: `skip(self)`

Sets `_skip_flag = True` — prevents yielding current node's children on next iteration.

### Method: `__next__(self)`

Returns `next(self._pt)`.

### Method: `__iter__(self)`

Returns `self`.

---

## Function: `_make_find_query(query)`

Converts the argument of `Basic.find()` into a callable predicate:
1. Tries to sympify `query`; catches `SympifyError` (leaves as-is).
2. If result is a type, returns `lambda expr: isinstance(expr, query)`.
3. If result is a `Basic`, returns `lambda expr: expr.match(query) is not None`.
4. Otherwise assumes it's already callable and returns it directly.

## sympy/core/exprtools.py
Now I have all 1505 lines of the file. Let me write the complete specification.

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division

from sympy.core.add import Add
from sympy.core.compatibility import iterable, is_sequence, SYMPY_INTS, range
from sympy.core.mul import Mul, _keep_coeff
from sympy.core.power import Pow
from sympy.core.basic import Basic, preorder_traversal
from sympy.core.expr import Expr
from sympy.core.sympify import sympify
from sympy.core.numbers import Rational, Integer, Number, I
from sympy.core.singleton import S
from sympy.core.symbol import Dummy
from sympy.core.coreerrors import NonCommutativeExpression
from sympy.core.containers import Tuple, Dict
from sympy.utilities import default_sort_key
from sympy.utilities.iterables import (common_prefix, common_suffix, variations, ordered)

from collections import defaultdict
```

## Constants & Globals

- `_eps` — `Dummy(positive=True)`; a dummy symbol used as a placeholder for unknown positive/negative signs in `_monotonic_sign`.

---

# Code Objects

## Function: `_isnumber(i)`

**Signature:** `_isnumber(i) -> bool`

Returns `True` if `i` is an instance of `(SYMPY_INTS, float)` or has the attribute `i.is_Number` evaluating to truthy; otherwise returns `False`.

---

## Function: `_monotonic_sign(self)`

**Signature:** `_monotonic_sign(self) -> Expr | None`

Returns the value closest to 0 that `self` may have if all symbols are signed and the result is uniformly the same sign for all values of symbols. Returns a representative symbol (e.g., `Dummy('pos', positive=True)`) when the exact boundary cannot be determined, or `None` if the sign could be positive or negative, or `self` does not match any recognized form.

**Logic:**

1. If `self.is_real` is falsy, return `None`.
2. **Negation case:** If `-self` is a Symbol, recursively call `_monotonic_sign(-self)` and negate the result (if non-None).
3. **Atomic number case:** If `self` is not an Add and its denominator is numeric:
   - If `s.is_prime`: return 3 if odd, else 2.
   - If `s.is_positive`: return 2 if even, 1 if integer, else `_eps`.
   - If `s.is_negative`: return -2 if even, -1 if integer, else `- _eps`.
   - If `s` is zero/nonpositive/nonnegative: return `S.Zero`.
   - Otherwise: return `None`.
4. **Univariate case:** If `len(free_symbols) == 1`:
   - **Polynomial path:** If `self.is_polynomial()`, get the single free symbol `x`. Recursively call `_monotonic_sign(x)` to get `x0` (treating `_eps`/`-_eps` as 0). Compute derivative `d = self.diff(x)`. If `d` is not numeric, try `real_roots(d)`; on failure, fall back to `roots(d, x)` filtering for real roots. Evaluate `y = self.subs(x, x0)`.
     - If `x.is_nonnegative` and all roots ≤ x0: if `y.is_nonnegative` and `d.is_positive`, return `y` (or a positive Dummy); if `y.is_nonpositive` and `d.is_negative`, return `y` (or a negative/Nonpositive Dummy).
     - If `x.is_nonpositive` and all roots ≥ x0: symmetric logic with reversed sign conditions.
   - **Rational function path:** Otherwise, get numerator/denominator. If both are non-numeric, recursively check monotonicity of each; if denominator's sign is known (positive or negative), compute `v = n * den` and return an appropriate positive/negative/Nonpositive Dummy based on `v`'s sign.
   - Return `None`.
5. **Multivariate case:** Decompose as `c, a = self.as_coeff_Add()`:
   - **Rational monomial path (non-polynomial):** If `a` is not polynomial and not purely numeric numerator/denominator: if `a` is Mul/Pow, rational, all Pow exponents are integers, and `a` has known sign, build `v = 1`, multiply each factor's substituted monotonic value into `v`.
   - **Signed linear expression path (polynomial with constant):** If `c` is non-zero: if no non-numeric Powers exist in `a` and `a` has known sign/non-sign, substitute each free symbol with its monotonic value (or `_eps`/`-_eps` based on non-negativity), compute `v = a.xreplace(p)`.
   - **Combine:** If `v` was computed: `rv = v + c`. If `v.is_nonnegative and rv.is_positive`, return `rv.subs(_eps, 0)`. If `v.is_nonpositive and rv.is_negative`, return `rv.subs(_eps, 0)`.
6. Return `None` (implicit).

---

## Function: `decompose_power(expr)`

**Signature:** `decompose_power(expr) -> tuple[Expr, int]`

Decomposes a power into symbolic base and integer exponent. Assumes conditions for validity (exponent is integer or base is positive) without checking them.

**Logic:**

1. Get `(base, exp) = expr.as_base_exp()`.
2. If `exp.is_Number`:
   - If `exp` is Rational but not Integer: set `base = Pow(base, Rational(1, exp.q))`, then `exp = exp.p`.
   - Otherwise (Integer): `exp = exp.p`.
   - If not a Number at all: `(base, exp) = (expr, 1)`.
3. Else (`exp` is non-numeric):
   - Decompose: `exp, tail = exp.as_coeff_Mul(rational=True)`.
   - If `exp is S.NegativeOne`: `(base, exp) = (Pow(base, tail), -1)`.
   - If `exp is not S.One`: set `tail = _keep_coeff(Rational(1, exp.q), tail)`, then `(base, exp) = (Pow(base, tail), exp.p)`.
   - Otherwise: `(base, exp) = (expr, 1)`.
4. Return `(base, exp)`.

---

## Function: `decompose_power_rat(expr)`

**Signature:** `decompose_power_rat(expr) -> tuple[Expr, int]`

Decomposes a power into symbolic base and rational exponent. Similar to `decompose_power` but does not handle the case where `exp.is_Number` is True (it falls through without modification).

**Logic:**

1. Get `(base, exp) = expr.as_base_exp()`.
2. If `exp.is_Number`: if not Rational, set `(base, exp) = (expr, 1)`; otherwise do nothing (keep original base and rational exponent).
3. Else (`exp` is non-numeric): same logic as `decompose_power` — decompose coefficient/tail, handle -1/other cases with `Rational(1, exp.q)` scaling on tail.
4. Return `(base, exp)`.

---

## Class: `Factors(object)`

**Description:** Efficient representation of a product `f_1 * f_2 * ... * f_n` as a dictionary mapping factors to their exponents.

### Attributes

- `__slots__ = ['factors', 'gens']`
- `self.factors` — dict mapping factor (Expr) → exponent (Expr/Number).
- `self.gens` — frozenset of keys from `self.factors`.

### Method: `__init__(self, factors=None)`

**Signature:** `__init__(self, factors=None)`

Initializes from a dict-like object or expression. Handles many input types:

1. If `factors` is an int/float: convert to SymPy via `S(factors)`.
2. If already a `Factors`: copy its `.factors` dict.
3. If `None` or `S.One`: set `factors = {}`.
4. If `S.Zero` or `0`: set `factors = {S.Zero: S.One}`.
5. If a `Number`: decompose into factors — negative sign → `{-1: 1}`, then for the absolute value: Float/Integer/Infinity → `{n: 1}`; Rational → numerator as `{p: 1}` (if p≠1) and denominator as `{q: -1}`.
6. If a `Basic` with no args (atom): set `factors = {factors: S.One}`.
7. If an `Expr`: extract commutative/non-commutative parts via `args_cnc()`. Count occurrences of `I`, remove them, convert remaining commutative part to powers dict. Re-insert `I` with count as exponent. Non-commutative part becomes a single factor.
8. Otherwise: copy the dict-like object, then tidy up `-1/1/I` exponents if Rational — compute their combined value `i1`, decompose into args, and update factors accordingly (handling -1, I, Pow with negative-one base, 1, -1).

Set `self.factors = factors` and `self.gens = frozenset(factors.keys())`. Raises `TypeError` if keys are not hashable.

### Method: `__hash__(self)`

Returns `hash((keys_tuple, values_list))` where keys are ordered via `ordered(self.factors.keys())` and values are the corresponding exponent list.

### Method: `__repr__(self)`

Returns `"Factors({k1: v1, k2: v2, ...})"` with items ordered by `ordered`.

### Property: `is_zero`

Returns `True` if `len(factors) == 1 and S.Zero in factors`; else `False`.

### Property: `is_one`

Returns `True` if `self.factors` is empty; else `False`.

### Method: `as_expr(self)`

Converts the internal factor dict back to a SymPy expression. For each `(factor, exp)`:
- If `exp != 1`: get base/exponent of factor via `as_base_exp()`, multiply exponent by `exp` (using `_keep_coeff(Integer(exp), e)` for int, `_keep_coeff(exp, e)` for Rational, or direct multiplication otherwise), append `base**e`.
- If `exp == 1`: append `factor` directly.
Return `Mul(*args)`.

### Method: `mul(self, other)`

Returns a new `Factors` representing the product of self and other.

1. If `other` is not a `Factors`, convert it via `Factors(other)`.
2. If either is zero, return `Factors(S.Zero)`.
3. Copy `self.factors` into a dict. For each `(factor, exp)` in `other.factors`: if factor already exists, add exponents; if sum is 0, delete the key; otherwise update. Return new `Factors(factors)`.

Supports `__mul__` and `*` operator via delegation to this method.

### Method: `normal(self, other)`

Returns `(self_reduced, other_reduced)` with GCD factors removed from each. Optimized for few common factors; does not raise on zero.

1. If `other` is not a `Factors`, convert it. Handle zero cases: if `other.is_zero`, return `(Factors(), Factors(S.Zero))`; if `self.is_zero`, return `(Factors(S.Zero), Factors())`.
2. Copy both factor dicts. For each `(factor, self_exp)` in `self.factors`: try to find matching factor in `other.factors`. If found:
   - Compute `exp = self_exp - other_exp`.
   - If `exp == 0`: delete from both dicts.
   - Else if `_isnumber(exp)`: if positive, set `self_factors[factor] = exp` and delete from other; else delete from self and set `other_factors[factor] = -exp`.
   - Else: try `extract_additively(other_exp)` on `self_exp`; if result is non-None, update accordingly. If not extractable, use coefficient subtraction logic via `as_coeff_Add()` to peel off common additive parts.
3. Return `(Factors(self_factors), Factors(other_factors))`.

### Method: `div(self, other)`

Returns `(quo, rem)` with GCD removed from each. Optimized for many common factors. Behaves like polynomial division where negative exponents in the divisor go to the remainder (denominator).

1. Initialize `quo = dict(self.factors)`, `rem = {}`.
2. If `other` is not a `Factors`: convert it; raise `ZeroDivisionError` if zero; return `(Factors(S.Zero), Factors())` if self is zero.
3. For each `(factor, exp)` in `other.factors`: if factor exists in `quo`, compute `d = quo[factor] - exp`. If `_isnumber(d)`: if d ≤ 0, delete from quo; if d ≥ 0, set `quo[factor] = d` and continue (with `exp = -d` for remainder). If not numeric: try `extract_additively`; on failure, use coefficient subtraction logic similar to `normal()`.
4. Any factor in `other.factors` not in `quo` goes directly into `rem`.
5. Return `(Factors(quo), Factors(rem))`.

Supports `__divmod__`, `__div__`/`__truediv__` (via `quo`), and `/` operator.

### Method: `quo(self, other)`

Returns the quotient part of `self.div(other)`, i.e., `self.div(other)[0]`. Supports `//` via `__div__`.

### Method: `rem(self, other)`

Returns the remainder (denominator) part of `self.div(other)`, i.e., `self.div(other)[1]`. Supports `%` operator.

### Method: `pow(self, other)`

Raises self to a non-negative integer power. If `other` is a `Factors`, convert via `as_expr()` and check for Integer. For non-negative SYMPY_INT: multiply each exponent by `other`; return new `Factors`. Raises `ValueError` otherwise. Supports `**` operator.

### Method: `gcd(self, other)`

Returns the GCD of self and other as a `Factors`. Keys are the intersection of factors with minimum exponent for each common factor. If `other.is_zero`, returns copy of self's factors. For each common factor, compares exponents using `.is_negative` on their difference to pick the smaller one.

### Method: `lcm(self, other)`

Returns the LCM of self and other as a `Factors`. Keys are the union of all factors with maximum exponent for each. If either is zero, returns `Factors(S.Zero)`. For common factors, takes `max(exp, existing)`.

### Method: `__eq__(self, other)`

If `other` is not a `Factors`, convert it. Returns `self.factors == other.factors`.

### Method: `__ne__(self, other)`

Returns `not self.__eq__(other)`.

---

## Class: `Term(object)`

**Description:** Efficient representation of `coeff * (numer / denom)` where numer and denom are `Factors` objects.

### Attributes

- `__slots__ = ['coeff', 'numer', 'denom']`
- `self.coeff` — the coefficient (Expr/Number).
- `self.numer` — numerator as a `Factors`.
- `self.denom` — denominator as a `Factors`.

### Method: `__init__(self, term, numer=None, denom=None)`

**Signature:** `__init__(self, term, numer=None, denom=None)`

1. If `numer is None and denom is None`:
   - Raise `NonCommutativeExpression` if `term.is_commutative` is falsy.
   - Decompose: `(coeff, factors) = term.as_coeff_mul()`.
   - For each factor in `factors`: get `(base, exp) = decompose_power(factor)`. If base is Add, extract content via `primitive()` and multiply into coeff. Positive exponents go to numer defaultdict; negative exponents go to denom defaultdict (with absolute value).
   - Convert both dicts to `Factors` objects.
2. Else: set `coeff = term`; if numer/denom are None, create empty `Factors()`.

### Method: `__hash__(self)`

Returns `hash((self.coeff, self.numer, self.denom))`.

### Method: `__repr__(self)`

Returns `"Term(%s, %s, %s)" % (coeff, numer, denom)`.

### Method: `as_expr(self)`

Returns `self.coeff * (self.numer.as_expr() / self.denom.as_expr())`.

### Method: `mul(self, other)`

Multiplies two Terms. Computes `coeff = self.coeff * other.coeff`, `numer = self.numer.mul(other.numer)`, `denom = self.denom.mul(other.denom)`. Then normalizes by calling `numer.normal(denom)` and returns new `Term(coeff, numer, denom)`.

### Method: `inv(self)`

Returns `Term(1/self.coeff, self.denom, self.numer)` — inverts coefficient and swaps numerator/denominator.

### Method: `quo(self, other)`

Returns `self.mul(other.inv())`.

### Method: `pow(self, other)`

If `other < 0`: returns `self.inv().pow(-other)`. Else: returns `Term(self.coeff ** other, self.numer.pow(other), self.denom.pow(other))`.

### Method: `gcd(self, other)`

Returns `Term(self.coeff.gcd(other.coeff), self.numer.gcd(other.numer), self.denom.gcd(other.denom))`.

### Method: `lcm(self, other)`

Returns `Term(self.coeff.lcm(other.coeff), self.numer.lcm(other.numer), self.denom.lcm(other.denom))`.

### Operator Overloads

- `__mul__(self, other)`: if `other` is Term → `self.mul(other)`; else `NotImplemented`.
- `__div__/__truediv__(self, other)`: if `other` is Term → `self.quo(other)`; else `NotImplemented`.
- `__pow__(self, other)`: if `other` is SYMPY_INT → `self.pow(other)`; else `NotImplemented`.
- `__eq__(self, other)`: compares coeff, numer, denom for equality.
- `__ne__(self, other)`: negation of `__eq__`.

---

## Function: `_gcd_terms(terms, isprimitive=False, fraction=True)`

**Signature:** `_gcd_terms(terms, isprimitive=False, fraction=True) -> tuple[Expr, Expr, Expr]`

Helper for `gcd_terms`. Returns `(cont, numer, denom)` where the combined expression equals `cont * numer / denom`.

**Logic:**

1. If `terms` is a Basic (not Tuple), convert to Add args via `Add.make_args(terms)`.
2. Filter out zero terms and map each remaining term through `Term()`.
3. If no terms remain: return `(S.Zero, S.Zero, S.One)`.
4. If one term remains: `cont = terms[0].coeff`, `numer = terms[0].numer.as_expr()`, `denom = terms[0].denom.as_expr()`.
5. If multiple terms:
   - Compute GCD of all terms' coefficients via iterative `gcd`: start with first term, reduce each subsequent term's gcd into it.
   - Divide each term by the GCD coefficient: `terms[i] = term.quo(cont)`.
   - **Fraction path:** If `fraction=True`, compute common denominator as LCM of all term denominators. For each term, multiply its numerator by `denom / term.denom` and collect `term.coeff * numer.as_expr()` into numers list.
   - **Non-fraction path:** Collect raw `t.as_expr()` for each term; set denom to empty Factors.
   - Convert cont to expr: `cont = cont.as_expr()`. Build `numer = Add(*numers)`, `denom = denom.as_expr()`.
6. If not primitive and numer is an Add: extract content via `numer.primitive()`, multiply into cont, replace numer with the primitive part.
7. Return `(cont, numer, denom)`.

---

## Function: `gcd_terms(terms, isprimitive=False, clear=True, fraction=True)`

**Signature:** `gcd_terms(terms, isprimitive=False, clear=True, fraction=True) -> Expr`

Computes the GCD of terms and combines them into a single expression. Handles both Add expressions and sequences of expressions treated as summands. Recursively processes non-Add structures.

**Logic:**

1. **Masking (for nc handling):** Define inner `mask(terms)` function that replaces non-commutative portions with Dummy symbols, returning masked args and replacement dict.
2. Determine if input is "addlike": either an Add instance, or a non-Basic sequence (including sets) but not Dict.
3. **Add-like path:**
   - Convert to list of terms; mask non-commutatives.
   - Call `_gcd_terms(terms, isprimitive, fraction)` → `(cont, numer, denom)`.
   - Restore masked values: `numer = numer.xreplace(reps)`.
   - Extract coefficient and factors from cont via `as_coeff_Mul()`.
   - **Clear handling:** If `clear=False` and the coefficient is not an Integer and numer is Add: try dividing numerator by the integer part of the coefficient; if any resulting term has an integer coefficient, keep this form.
   - Return `_keep_coeff(coeff, factors * numer / denom, clear=clear)`.
4. **Non-addlike path:**
   - If not Basic: return as-is.
   - If atom: return as-is.
   - If Mul: extract coefficient and recursively gcd_terms each factor; recombine with `_keep_coeff`.
   - For other structures: define `handle(a)` that recursively processes args (avoiding treating internal args as Add terms); for Dict, process key-value pairs; otherwise call `terms.func(*[handle(i) for i in terms.args])`.

---

## Function: `factor_terms(expr, radical=False, clear=False, fraction=False, sign=True)`

**Signature:** `factor_terms(expr, radical=False, clear=False, fraction=False, sign=True) -> Expr`

Removes common factors from terms in all arguments without changing the underlying structure. No expansion or simplification; no processing of non-commutatives (handled via recursive descent).

**Logic:**

Inner function `do(expr)`:
1. If not Basic or is Atom: if iterable, return `type(expr)([do(i) for i in expr])`; else return expr unchanged.
2. If Pow/Function/iterable or lacks `args_cnc` attribute: recursively process args; if no change, return original; otherwise rebuild with new args via `expr.func(*newargs)`.
3. If Sum: delegate to `factor_sum(expr, radical=radical, clear=clear, fraction=fraction, sign=sign)`.
4. Otherwise (Add or other Expr with `args_cnc`):
   - Extract content/primitive: `(cont, p) = expr.as_content_primitive(radical=radical, clear=clear)`.
   - If `p.is_Add`:
     - Decompose into args via `Add.make_args(p)` and recursively process each.
     - **Negative sign handling:** If all processed args have negative leading coefficients, negate cont and flip all args.
     - **Special exponent protection:** For args where the exponent is a non-trivial Mul (e.g., `-(x+2)` in `exp(-(x+2))`), replace with Dummy to prevent gcd_terms from expanding it; track in `special` dict.
     - Rebuild as Add, call `gcd_terms(p, isprimitive=True, clear=clear, fraction=fraction)`, then restore via `.xreplace(special)`.
   - If `p.args` (non-Add with children): recursively process each arg and rebuild.
   - Return `_keep_coeff(cont, p, clear=clear, sign=sign)`.

Top-level: `expr = sympify(expr)`; return `do(expr)`.

---

## Function: `_mask_nc(eq, name=None)`

**Signature:** `_mask_nc(eq, name=None) -> tuple[Expr, dict | None, list]`

Replaces non-commutative objects in an expression with Dummy symbols. Returns `(masked_expr, replacement_dict, nc_symbols_list)`. If `replacement_dict` is `None`, the expression contains multiple distinct nc-symbols that cannot be fully commutatized. The third value lists all nc-symbols (original or masked) to watch for ordering issues.

**Logic:**

1. Set up numbered Dummy generator with given name prefix.
2. If `expr.is_commutative`: return `(eq, {}, [])`.
3. **Identify nc-objects:** Traverse preorder; skip already-replaced nodes. For each non-commutative node:
   - If Symbol: add to `nc_syms` set.
   - If not Add/Mul/Pow and all free symbols are commutative: replace with a Dummy (add to `rep`).
   - Otherwise: add to `nc_obj` set; skip traversal into it.
4. **Single nc case:** If exactly one nc object and no nc symbols, or exactly one nc symbol and no nc objects: replace that single entity with a commutative Dummy (so polys won't complain).
5. **Remaining nc-objects:** Sort by default_sort_key; replace each with an nc-Dummy (`Dummy(commutative=False)`); add to `nc_syms`.
6. Apply all substitutions: `expr = expr.subs(rep)`.
7. Sort `nc_syms` list by default_sort_key.
8. Return `(expr, {v: k for k, v in rep} or None, nc_syms)`.

---

## Function: `factor_nc(expr)`

**Signature:** `factor_nc(expr) -> Expr`

Returns the factored form of an expression while handling non-commutative terms. Works by masking nc objects, extracting common factors (commutative GCD, nc prefix/suffix), factoring the remaining commutative core, and restoring nc structure.

**Logic:**

1. Import `powsimp` from simplify and `gcd`, `factor` from polys.
2. Define `_pemexpand(expr)`: expands with minimal hints (`deep=True, mul=True, power_exp=True, multinomial=True`; disables `power_base, basic, log`).
3. Convert expr via `sympify()`. If not Expr or no args: return as-is. If not Add: recursively factor each arg.
4. **Mask nc:** Call `_mask_nc(expr)` → `(expr, rep, nc_symbols)`.
5. **Single nc case:** If `rep` is truthy (single nc replaced): call `factor(expr).subs(rep)` and return.
6. **Multiple nc case:** Otherwise:
   - Decompose each Add term into commutative/non-commutative parts via `args_cnc()`. Store as list of `(comm_list, nc_list)`.
   - Initialize `c = g = l = r = S.One`, `hit = False`.
   - **Extract commutative GCD:** For each term's commutative part, compute GCD. If non-trivial: split into coefficient `c` and factor `g`; divide out from all terms' commutative parts.
   - **Extract nc common prefix:** Compute `common_prefix` across all nc lists. If empty, try extracting a common power of the first nc element (check if all terms start with same base and integer exponent; take minimum). If successful: set `l = b**e`, multiply each term's first nc element by `b**-e`.
   - **Extract nc common suffix:** Compute `common_suffix` across all nc lists. Same power-extraction logic for the last nc element. If successful: set `r = b**e`, multiply each term's last nc element by `b**-e`.
   - **Rebuild middle:** If any extraction hit, rebuild as `Add(*[Mul(*cc) * Mul(*nc) for cc, nc in args])`; else keep original expr.
   - **Sort nc symbols:** Create replacement list of `(original_nc_symbol, Dummy())` sorted by default_sort_key to avoid sign flips from ordering changes. Reverse the un-replacement mapping.
   - Substitute sorted Dummies into middle, call `_mask_nc`, then `powsimp(factor(...))`.
   - Restore via `.subs(r2).subs(unrep1)`.
   - **Result handling:**
     - If result is Pow: return `_keep_coeff(c, g * l * new_mid * r)`.
     - If result is Mul: separate commutative and non-commutative factors. Build `pre_mid = g * Mul(*cfac) * l`. Expand the target (`expr/c`). Try all permutations of nc factors via `variations(ncfac, len(ncfac))`; return the first one whose expansion matches the target (wrapped with `_keep_coeff(c, ok)`).
     - If mid didn't factor successfully: return `_keep_coeff(c, g * l * mid * r)`.

## sympy/core/numbers.py
Now I have read the full file. Here is the complete natural-language specification:

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division
import decimal
import fractions
import math
import warnings
import re as regex
from collections import defaultdict
from .containers import Tuple
from .sympify import converter, sympify, _sympify, SympifyError
from .singleton import S, Singleton
from .expr import Expr, AtomicExpr
from .decorators import _sympifyit
from .cache import cacheit, clear_cache
from .logic import fuzzy_not
from sympy.core.compatibility import (as_int, integer_types, long, string_types, with_metaclass, HAS_GMPY, SYMPY_INTS, int_info)
import mpmath
import mpmath.libmp as mlib
from mpmath.libmp import mpf_pow, mpf_pi, mpf_e, phi_fixed
from mpmath.ctx_mp import mpnumeric
from mpmath.libmp.libmpf import (finf as _mpf_inf, fninf as _mpf_ninf, fnan as _mpf_nan, fzero as _mpf_zero, _normalize as mpf_normalize, prec_to_dps)
from sympy.utilities.misc import debug, filldedent
from .evaluate import global_evaluate
from sympy.utilities.exceptions import SymPyDeprecationWarning
```

## Constants & Globals

- `rnd = mlib.round_nearest` — alias for the mpmath round-nearest rounding mode.
- `_LOG2 = math.log(2)` — natural log of 2.
- `_errdict = {"divide": False}` — global error-handling flag; when `"divide"` is `True`, SymPy raises an exception on `0/0`; when `False` (default), it returns `NaN`.
- `_gcdcache = {}` — dict used as a cache for `(a, b) → gcd(a,b)` results in `igcd()`.
- `BIGBITS = 5000` — threshold bit-length above which Lehmer's algorithm is preferred over the standard Euclidean algorithm.
- `_intcache = {}` — dict caching `Integer` instances by their Python int value; pre-populated with `{0: S.Zero, 1: S.One, -1: S.NegativeOne}` at module load time.
- `_intcache_hits = 0` and `_intcache_misses = 0` — counters for integer cache tracing (used by `int_trace`).

## Module-Level Functions

### `comp(z1, z2, tol=None)` → `bool`

Returns whether the error between `z1` and `z2` is ≤ `tol`.

- If `type(z2) is str`: raises `ValueError` unless `z1` is a `Number`; returns `str(z1) == z2`.
- If `not z1` (i.e., `z1` is falsy): swaps `z1, z2`. If still not `z1`, returns `True`.
- If `tol` is `None`: if `type(z2) is str` and `z1.is_Number`, returns `str(z1) == z2`; otherwise converts both to `Float` and checks `int(abs(a - b)*10**prec_to_dps(min(a._prec, b._prec)))*2 <= 1`.
- If `tol` is a non-empty falsy value (e.g., `''`) and both are Numbers: returns `z1._prec == z2._prec and str(z1) == str(z2)`; else raises `ValueError`.
- Otherwise (`tol` is nonzero): computes `diff = abs(z1 - z2)`, `az1 = abs(z1)`. If `z2` is truthy and `az1 > 1`, returns `diff/az1 <= tol`; otherwise returns `diff <= tol`.

### `mpf_norm(mpf, prec)` → tuple

Normalizes an mpf tuple to the given precision. Handles special cases where mantissa is zero: if both mantissa and bit count are zero, returns `_mpf_zero`; otherwise returns the original mpf unchanged (to preserve inf/nan). Otherwise calls `mpf_normalize(sign, MPZ(man), expt, bc, prec, rnd)` and returns the result.

### `seterror(divide=False)` → None

Sets `_errdict["divide"]` to `divide`. If changed, calls `clear_cache()`.

### `_as_integer_ratio(p)` → `(int, int)`

Returns an integer ratio `(p_int, q_int)` for a number `p`. Extracts the mpf tuple from `p._mpf_` (or `mpmath.mpf(p)._mpf_`). Computes `p = ±man` (sign based on `neg_pow % 2`). If exponent < 0, sets `q = 2^(-expt)`; else `q = 1` and multiplies `p *= 2^expt`. Returns `(int(p), int(q))`.

### `_decimal_to_Rational_prec(dec)` → `(Rational, int)`

Converts a `decimal.Decimal` to a `Rational`, returning the Rational and its digit precision. Raises `TypeError` if `dec` is not finite. Extracts sign, digits, exponent from `dec.as_tuple()`. If exponent ≥ 0, returns `Integer(int(dec))`. Otherwise constructs `Rational(s*d, 10^(-e))` where `d` is the integer formed by the digit list and `s = (-1)^sign`.

### `_literal_float(f)` → `bool`

Returns `True` if string `f` matches the regex pattern `r"[-+]?((\d*\.\d+)|(\d+\.?))(eE[-+]?\d+)?"`, indicating it can be interpreted as a floating-point number.

### `igcd(*args)` → `int`

Computes the nonnegative integer GCD of two or more arguments using Euclid's algorithm with caching. Requires ≥ 2 args (raises `TypeError`). If `1 in args`, returns `1`. Otherwise iterates through args, computing `a = igcd2(a, b)` for each pair, caching results in `_gcdcache` keyed by `(a, b)` and `(b, a)`. Skips zero arguments. Returns the accumulated GCD.

### `igcd2(a, b)` → `int`

Computes GCD of two integers. On Python 3.5+, imported from `math.gcd`. On older versions: if both args have bit length > `BIGBITS`, delegates to `igcd_lehmer`; otherwise uses the standard Euclidean algorithm (`while b: a, b = b, a % b`), returning `abs(a)`.

### `igcd_lehmer(a, b)` → `int`

Computes GCD of two positive integers using Lehmer's algorithm for large numbers. Takes absolute values via `as_int`, ensures `a ≥ b`. Outer loop runs while `a.bit_length() > nbits` (where `nbits = 2 * int_info.bits_per_digit`) and `b ≠ 0`. Extracts most significant bits, then uses an inner loop to compute Euclidean quotients from small-integer arithmetic on those MSBs, accumulating transformation coefficients `(A, B, C, D)`. When the quotient can no longer be determined reliably, computes new long arguments via `a = A*a + B*b`, `b = C*a + D*b`. Finishes with standard Euclidean algorithm. Returns `a`.

### `ilcm(*args)` → `int`

Computes integer LCM of two or more args (raises `TypeError` if < 2). If `0 in args`, returns `0`. Otherwise iteratively computes `a = a*b // igcd(a, b)`.

### `igcdex(a, b)` → `(x, y, g)` tuple

Returns `x, y, g` such that `g = x*a + y*b = gcd(a, b)`. Handles edge cases: if both are zero, returns `(0, 1, 0)`. If only one is zero, returns the appropriate unit vector. Normalizes signs of inputs, tracks sign multipliers for output. Uses extended Euclidean algorithm with variables `x, y, r, s` initialized to `(1, 0, 0, 1)`, iterating while `b ≠ 0`: computes quotient and remainder, updates all four variables. Returns `(x*x_sign, y*y_sign, a)`.

### `mod_inverse(a, m)` → int or Rational

Returns `c` such that `(a * c) % m == 1` with the same sign as `a`. Raises `ValueError` if no inverse exists. First tries integer path: converts both to Python ints via `as_int`; if `m > 1`, calls `igcdex(a, m)`; if gcd is 1, computes `c = x % m` and adjusts sign. On failure (non-integer args), sympifies both; requires both be numbers or raises `TypeError`. If `m > 1`, returns `1/a`.

---

# Code Objects (Classes)

## Class `Number(AtomicExpr)`

**Attributes:**
- `is_commutative = True`
- `is_number = True`
- `is_Number = True`
- `_prec = -1` — default precision sentinel.

### `__new__(cls, *obj)` → Number subclass instance

Dispatches based on input type:
- If already a `Number`, returns it unchanged.
- If `SYMPY_INTS`, returns `Integer(obj)`.
- If 2-tuple, returns `Rational(*obj)`.
- If `float`, `mpmath.mpf`, or `decimal.Decimal`, returns `Float(obj)`.
- If string, sympifies and returns the result if it's a Number; else raises `ValueError`.
- Otherwise raises `TypeError`.

### Methods (abstract/overridable by subclasses):

- **`invert(other, *gens, **args)`** → int/Rational: calls `mod_inverse(self, other)` for numbers, otherwise delegates to `sympy.polys.polytools.invert`.
- **`__divmod__(self, other)`** → Tuple `(quotient, remainder)`: converts `other` to Number; raises `ZeroDivisionError` if zero. For Integer×Integer: returns `Tuple(*divmod(self.p, other.p))`. Otherwise computes `rat = self/other`, `w = sign(rat)*int(abs(rat))`, `r = self - other*w`, returns `Tuple(w, r)`.
- **`__rdivmod__(self, other)`** → Tuple: converts `other` to Number; returns `divmod(other, self)`.
- **`__round__(*args)`** → float: returns `round(float(self), *args)`.
- **`_as_mpf_val(prec)`** → tuple: abstract; raises `NotImplementedError`.
- **`_eval_evalf(prec)`** → Float: calls `Float._new(self._as_mpf_val(prec), prec)`.
- **`_as_mpf_op(prec)`** → (tuple, int): returns `(self._as_mpf_val(max(prec, self._prec)), max(prec, self._prec))`.
- **`__float__()`** → float: calls `mlib.to_float(self._as_mpf_val(53))`.
- **`floor()`**, **`ceiling()`**: abstract; raise `NotImplementedError`.
- **`_eval_conjugate()`** → self: returns `self`.
- **`_eval_order(*symbols)`** → Order: returns `Order(S.One, *symbols)`.
- **`_eval_subs(old, new)`** → expr: if `old == -self`, returns `new`; else returns `self`.
- **`_eval_is_finite()`** → True.
- **`class_key(cls)`** → tuple: `(1, 0, 'Number')`.
- **`sort_key(order=None)`** → tuple (cached): `(self.class_key(), (0, ()), (), self)`.

### Arithmetic operators (with `@_sympifyit('other', NotImplemented)`):

- **`__add__(self, other)`**: If `global_evaluate[0]` and `other` is a Number: propagates NaN/Infinity. Otherwise delegates to `AtomicExpr.__add__`.
- **`__sub__(self, other)`**: Similar NaN/Infinity propagation for subtraction. Delegates otherwise.
- **`__mul__(self, other)`**: If `global_evaluate[0]`: NaN if either is NaN; Infinity×positive→Infinity, Infinity×negative→NegativeInfinity, 0×∞→NaN. For Tuple input, returns `NotImplemented`. Otherwise delegates to `AtomicExpr.__mul__`.
- **`__div__(self, other)`** / `__truediv__`: If `global_evaluate[0]`: NaN if either is NaN; ∞/∞ or ∞/-∞ → 0. Delegates otherwise.

### Comparison operators:

- **`__eq__(other)`, `__ne__(other)`**: Abstract; raise `NotImplementedError`.
- **`__lt__(self, other)`**: Sympifies `other`; raises `TypeError` on failure; abstract — raises `NotImplementedError`.
- **`__le__(self, other)`**: Sympifies `other`; raises `TypeError` on failure; abstract — raises `NotImplementedError`.
- **`__gt__(self, other)`**: Delegates to `_sympify(other).__lt__(self)`.
- **`__ge__(self, other)`**: Delegates to `_sympify(other).__le__(self)`.

### Other methods:

- **`__hash__()`** → int: calls `super(Number, self).__hash__()`.
- **`is_constant(*wrt, **flags)`** → True.
- **`as_coeff_mul(*deps, **kwargs)`**: If rational or `rational=False`, returns `(self, ())`; if negative, returns `(-1, (-self,))`; else `(1, (self,))`.
- **`as_coeff_add(*deps)`**: If rational, returns `(self, ())`; else `(0, (self,))`.
- **`as_coeff_Mul(rational=False)`**: If rational and not self: `(self, 1)`; if not self: `(1, self)`.
- **`as_coeff_Add(rational=False)`**: If not rational: `(self, 0)`; else `(0, self)`.
- **`gcd(other)`**, **`lcm(other)`**, **`cofactors(other)`**: Delegate to `sympy.polys.gcd/lcm/cofactors`.

---

## Class `Float(Number)`

**Slots:** `_mpf_`, `_prec` (both set in `__new__`).
**Class attributes:** `is_rational = None`, `is_irrational = None`, `is_real = True`, `is_Float = True`.

### `__new__(cls, num, dps=None, prec=None, precision=None)` → Float instance

1. **Deprecation**: If `prec` is not None, issues a deprecation warning and sets `dps = prec`.
2. **Validation**: Raises `ValueError` if both `dps` and `precision` are provided (non-None).
3. **Input normalization** (before precision determination):
   - String: strips spaces; prepends `'0'` for `.xxx`; prepends `'0.'` for `-.xx`.
   - Python float zero → string `'0'`.
   - SYMPY_INTS/Integer → convert to string.
   - `S.Infinity` → `'+inf'`; `S.NegativeInfinity` → `'-inf'`.
   - `mpmath.mpf`: if no precision set, uses `num.context.prec`; converts to `_mpf_` tuple.
4. **Precision determination**:
   - If neither `dps` nor `precision` is given: defaults to 15 dps. If input is already a Float, returns it unchanged. If string matches `_literal_float`, parses via `decimal.Decimal` → `_decimal_to_Rational_prec` to get exact precision; sets `dps = max(15, dps)` and converts to binary precision.
   - If null-string precision (`precision == ''` or `dps == ''`): requires string input; parses via decimal; if integer literal, uses its digit count for precision. Raises `ValueError` on unrecognized format.
5. **Binary precision**: If `precision is None or ''`, converts from dps: `precision = mlib.libmpf.dps_to_prec(dps)`.
6. **MPF construction** based on input type:
   - float → `mlib.from_float(num, precision, rnd)`
   - string → `mlib.from_str(num, precision, rnd)`
   - decimal.Decimal → finite: `from_str(str(num))`; NaN → `_mpf_nan`; +inf → `_mpf_inf`; -inf → `_mpf_ninf`.
   - Rational → `mlib.from_rational(num.p, num.q, precision, rnd)`.
   - 3/4-tuple: if hex string mantissa (pickled), converts to long int; if 4-tuple, calls `Float._new(num, precision)`; if 3-tuple, evaluates `(S.NegativeOne**num[0]*num[1]*2**num[2]).evalf(precision)`.
   - Float → uses existing `_mpf_`, re-normalizes if new precision is lower.
   - Other → `mpmath.mpf(num, prec=prec)._mpf_`.
7. **Special cases**: If result equals `_mpf_nan`, returns `S.NaN`; zero passes through as a Float.
8. Creates object via `Expr.__new__(cls)`, sets `_mpf_` and `_prec`, returns it.

### `@classmethod _new(cls, _mpf_, _prec)` → Float instance

Creates a Float from raw mpf tuple and precision. Returns `S.Zero` if `_mpf_ == _mpf_zero`; returns `S.NaN` if NaN. Otherwise normalizes via `mpf_norm`, creates object, sets attributes.

### Pickling:
- **`__getnewargs__()`** → `(mlib.to_pickable(self._mpf_),)`.
- **`__getstate__()`** → `{'_prec': self._prec}`.
- **`_hashable_content()`** → `(self._mpf_, self._prec)`.

### Methods:
- **`floor()`** → Integer: `int(mlib.to_int(mlib.mpf_floor(self._mpf_, self._prec)))`.
- **`ceiling()`** → Integer: `int(mlib.to_int(mlib.mpf_ceil(self._mpf_, self._prec)))`.
- **`num` property** → `mpmath.mpf(self._mpf_)`.
- **`_as_mpf_val(prec)`** → tuple: calls `mpf_norm(self._mpf_, prec)`, logs debug if changed.
- **`_as_mpf_op(prec)`** → (tuple, int): returns `(self._mpf_, max(prec, self._prec))`.
- **`_eval_is_finite()`** → False if `_mpf_` is ±inf; else True.
- **`_eval_is_infinite()`** → True if ±inf; else False.
- **`_eval_is_integer()`** → True only if `_mpf_ == _mpf_zero`.
- **`_eval_is_negative()`** → True for -inf; False for +inf; else `self.num < 0`.
- **`_eval_is_positive()`** → True for +inf; False for -inf; else `self.num > 0`.
- **`_eval_is_zero()`** → True if `_mpf_ == _mpf_zero`.
- **`__nonzero__()`, `__bool__()`** → `self._mpf_ != _mpf_zero`.

### Arithmetic (all `@_sympifyit('other', NotImplemented)`):
- **`__neg__()`** → Float: `Float._new(mlib.mpf_neg(self._mpf_), self._prec)`.
- **`__add__(self, other)`**: If Number and evaluate: `Float._new(mlib.mpf_add(self._mpf_, rhs, prec, rnd), prec)` where `(rhs, prec) = other._as_mpf_op(self._prec)`.
- **`__sub__(self, other)`**: Same pattern with `mlib.mpf_sub`.
- **`__mul__(self, other)`**: Same pattern with `mlib.mpf_mul`.
- **`__div__(self, other)`** / `__truediv__`: If non-zero Number and evaluate: `Float._new(mlib.mpf_div(self._mpf_, rhs, prec, rnd), prec)`.
- **`__mod__(self, other)`**: Special case for Rational with q≠1: computes via Rational mod then rounds. For Float×Float where quotient is integer: returns `Float(0, prec)`. Otherwise uses `mlib.mpf_mod`.
- **`__rmod__(self, other)`**: If Float: delegates to `other.__mod__(self)`. Else uses `mlib.mpf_mod(rhs, self._mpf_, prec, rnd)`.

### Power:
- **`_eval_power(expt)`**: Zero base → 0 for positive expt, inf for negative. Integer exponent: `Float._new(mlib.mpf_pow_int(self._mpf_, expt.p, prec, rnd), prec)`. Rational with p=1 and odd q and negative self: returns `-1^expt * (-self)^expt`. General numeric exponent: tries `mlib.mpf_pow`; on ComplexResult, computes real+imaginary parts via `mlib.mpc_pow`.

### Comparison operators (all `@_sympifyit('other', NotImplemented)`):
- **`__eq__(self, other)`**: float → coerce to Float at same precision and compare mpf. NumberSymbol: if irrational, False; else delegates. Float: direct `_mpf_` comparison via `mlib.mpf_eq`. Other Number: converts to self's precision via `_as_mpf_val`, compares. Returns False for non-Number.
- **`__ne__(self, other)`** → `not self.__eq__(other)`.
- **`__gt__(self, other)`**: Sympifies; handles NumberSymbol (delegates to `other.__le__`). If comparable, evalf's other. For Number≠NaN: compares via `mlib.mpf_gt(self._mpf_, other._as_mpf_val(self._prec))`.
- **`__ge__(self, other)`**: Similar; uses `mlib.mpf_ge`.
- **`__lt__(self, other)`**: Similar; uses `mlib.mpf_lt`.
- **`__le__(self, other)`**: Similar; uses `mlib.mpf_le`.

### Other:
- **`__hash__()`** → int: calls `super(Float, self).__hash__()`.
- **`epsilon_eq(other, epsilon="1e-15")`** → bool: `abs(self - other) < Float(epsilon)`.
- **`_sage_()`** → sage RealNumber.
- **`__format__(format_spec)`** → str: formats as `decimal.Decimal(str(self))` with the spec.

---

## Class `Rational(Number)`

**Slots:** `p`, `q` (both set in `__new__`).
**Class attributes:** `is_real = True`, `is_integer = False`, `is_rational = True`, `is_Rational = True`.

### `@cacheit __new__(cls, p, q=None, gcd=None)` → Rational or Integer or Half instance

1. If `q is None`:
   - If `p` is already a Rational, returns it.
   - If string: splits on `/` (max 1 split); parses numerator/denominator via `fractions.Fraction`; returns `Rational(fp/fq)` with gcd=1. Strips spaces; tries `Fraction(p)` directly.
   - If not string and is `float/Float`: calls `_as_integer_ratio(p)`.
   - If not SYMPY_INTS or Rational: raises `TypeError`.
   - Sets `q = q or S.One`, `gcd = 1`.
2. Else (`q` provided): converts both to Rational via `Rational(p)` and `Rational(q)`.
3. Normalizes: if `q` is Rational, `p *= q.q; q = q.p`; if `p` is Rational, `q *= p.q; p = p.p`. Now both are integers.
4. If `q == 0`: returns `S.NaN` (if p==0) or `S.ComplexInfinity`.
5. Ensures `q > 0` (flips signs if needed).
6. Computes gcd via `igcd(abs(p), q)` if not provided; reduces fraction.
7. If `q == 1`, returns `Integer(p)`. If `p == 1, q == 2`, returns `S.Half`.
8. Otherwise creates object, sets `obj.p = p`, `obj.q = q`.

### Methods:
- **`limit_denominator(max_denominator=1000000)`** → Rational: uses `fractions.Fraction(self.p, self.q).limit_denominator(...)`.
- **`__getnewargs__()`** → `(self.p, self.q)`.
- **`_hashable_content()`** → `(self.p, self.q)`.
- **`_eval_is_positive()`** → `self.p > 0`.
- **`_eval_is_zero()`** → `self.p == 0`.

### Arithmetic (all `@_sympifyit('other', NotImplemented)`):
- **`__neg__()`** → Rational: `Rational(-self.p, self.q)`.
- **`__add__(self, other)`**: Integer: `Rational(self.p + self.q*other.p, self.q, 1)`. Rational: `Rational(self.p*other.q + self.q*other.p, self.q*other.q)`. Float: delegates to `other + self`.
- **`__radd__ = __add__`**.
- **`__sub__(self, other)`**: Integer: `Rational(self.p - self.q*other.p, self.q, 1)`. Rational: `Rational(self.p*other.q - self.q*other.p, self.q*other.q)`. Float: `-other + self`.
- **`__rsub__(self, other)`**: Integer: `Rational(self.q*other.p - self.p, self.q, 1)`. Rational: `Rational(self.q*other.p - self.p*other.q, self.q*other.q)`. Float: `-self + other`.
- **`__mul__(self, other)`**: Integer: `Rational(self.p*other.p, self.q, igcd(other.p, self.q))`. Rational: `Rational(self.p*other.p, self.q*other.q, igcd(self.p, other.q)*igcd(self.q, other.p))`. Float: delegates.
- **`__rmul__ = __mul__`**.
- **`__div__(self, other)`** / `__truediv__`: Integer (nonzero): `Rational(self.p, self.q*other.p, igcd(self.p, other.p))`; zero divisor → ComplexInfinity. Rational: `Rational(self.p*other.q, self.q*other.p, igcd(self.p, other.p)*igcd(self.q, other.q))`. Float: `self*(1/other)`.
- **`__rdiv__(self, other)`**: Integer: `Rational(other.p*self.q, self.p, igcd(self.p, other.p))`. Rational: `Rational(other.p*self.q, other.q*self.p, ...)`. Float: `other*(1/self)`.
- **`__mod__(self, other)`**: Rational: computes via integer division of cross-products. Float: converts to Rational mod then wraps in Float.
- **`__rmod__(self, other)`**: If Rational, delegates to `Rational.__mod__(other, self)`.

### Power:
- **`_eval_power(expt)`**: Float exponent → evalf at that precision. Negative expt: inverts base; handles negative base with odd/even denominators. Infinity exponent: returns ∞ if |self| > 1, zero if |self| < 1, complex infinity for self < -1. Integer exponent: `Rational(self.p**expt.p, self.q**expt.p)`. Rational exponent (p≠1): expands to `Integer(p)^expt * Integer(q)^(-expt)`; special case p=1 simplifies further. If negative base and even exponent: returns `(-self)**expt`.

### Conversion:
- **`_as_mpf_val(prec)`** → tuple: `mlib.from_rational(self.p, self.q, prec, rnd)`.
- **`_mpmath_(prec, rnd)`** → mpmath.mpf.
- **`__abs__()`** → Rational: `Rational(abs(self.p), self.q)`.
- **`__int__()`** → int: truncates toward zero (`p//q` with sign handling).
- **`floor()`** → Integer: `Integer(self.p // self.q)`.
- **`ceiling()`** → Integer: `-Integer(-self.p // self.q)`.

### Comparison (all `@_sympifyit('other', NotImplemented)`):
- **`__eq__(self, other)`**: Sympifies; NumberSymbol irrational → False. Rational: direct `(p,q)` comparison. Float: mpf equality at float's precision. Returns False for non-Number.
- **`__ne__(self, other)`** → `not self.__eq__(other)`.
- **`__gt__(self, other)`**: NumberSymbol → delegates to `other.__le__`. Rational: cross-multiplied comparison `p*other.q > q*other.p`. Float: mpf_gt at float's precision. Real symbolic: converts to Integer×symbolic comparison.
- **`__ge__(self, other)`**, **`__lt__(self, other)`**, **`__le__(self, other)`**: Similar patterns with appropriate operators.

### Other:
- **`__hash__()`** → int: calls `super(Rational, self).__hash__()`.
- **`factors(limit=None, use_trial=True, use_rho=False, use_pm1=False, verbose=False, visual=False)`** → dict: wrapper around `sympy.ntheory.factorrat`.
- **`gcd(other)`**: If Rational: `Rational(igcd(self.p, other.p), ilcm(self.q, other.q))`.
- **`lcm(other)`**: If Rational: `Rational(p*p'//igcd(p,p'), igcd(q,q'))`.
- **`as_numer_denom()`** → `(Integer(self.p), Integer(self.q))`.
- **`_sage_()`** → sage integer division.
- **`as_content_primitive(radical=False, clear=True)`**: Positive → `(self, 1)`; negative → `(-self, -1)`; zero → `(1, self)`.
- **`as_coeff_Mul(rational=False)`** → `(self, S.One)`.
- **`as_coeff_Add(rational=False)`** → `(self, S.Zero)`.

---

## Class `Integer(Rational)`

**Slots:** `p` (set in `__new__`).
**Class attributes:** `q = 1`, `is_integer = True`, `is_Integer = True`.

### `@int_trace __new__(cls, i)` → Integer instance

Strips spaces from string input. Converts to Python int via `int(i)`, raises `TypeError` if not possible. Checks `_intcache[ival]`; returns cached if present. Otherwise creates object, sets `obj.p = ival`, caches it, and returns it.

### Methods:
- **`__getnewargs__()`** → `(self.p,)`.
- **`_as_mpf_val(prec)`** → tuple: `mlib.from_int(self.p, prec)`.
- **`_mpmath_(prec, rnd)`** → mpmath.mpf.
- **`__int__()`**, **`__long__()`** → `self.p`.
- **`floor()`**, **`ceiling()`** → `Integer(self.p)`.

### Arithmetic (optimized for integers):
- **`__neg__()`** → Integer: `Integer(-self.p)`.
- **`__abs__()`**: Returns self if p≥0, else `Integer(-self.p)`.
- **`__divmod__(self, other)`**: Integer×Integer with evaluate: `Tuple(*divmod(self.p, other.p))`; else delegates.
- **`__rdivmod__(self, other)`**: integer_types → `Tuple(*divmod(other, self.p))`; else Number path.
- **`__add__(self, other)`**: int/Integer → direct addition; Rational → `Rational(self.p*other.q + other.p, other.q)`.
- **`__radd__(self, other)`**: int → `Integer(other + self.p)`; Rational → `Rational(other.p + self.p*other.q, other.q)`.
- **`__sub__(self, other)`**, **`__rsub__(self, other)`**: Similar patterns.
- **`__mul__(self, other)`**: int/Integer → direct multiplication; Rational → `Rational(self.p*other.p, other.q, igcd(self.p, other.q))`.
- **`__rmul__(self, other)`**: Symmetric.
- **`__mod__(self, other)`**, **`__rmod__(self, other)`**: int/Integer → direct mod; else delegates to Rational.

### Comparison:
- **`__eq__(self, other)`**: int → `self.p == other`; Integer → `self.p == other.p`; else delegates to Rational.
- **`__ne__(self, other)`** → `not self.__eq__(other)`.
- **`__gt__(self, other)`**, **`__lt__(self, other)`**, **`__ge__(self, other)`**, **`__le__(self, other)`**: Integer→Integer direct comparison; else delegates to Rational. All raise TypeError on non-sympifiable input.

### Other:
- **`__hash__()`** → `hash(self.p)`.
- **`__index__()`** → `self.p`.
- **`_eval_is_odd()`** → `bool(self.p % 2)`.
- **`_eval_power(expt)`**: ∞ exponent: ∞ if |p|>1, complex infinity otherwise. -∞ exponent: inverts base. Non-number even expt with negative self: returns `(-self)**expt`. Float exponent → delegates to Rational. Half-exponent of negative: extracts I. Negative exponent: inverts base with sign handling. Perfect root detection via `integer_nthroot(abs(p), q)`. Factor-based simplification: collects perfect powers from prime factorization (up to 2^15 limit), extracts integer and radical parts, identifies gcd of remaining exponents for combined radical.
- **`_eval_is_prime()`** → calls `sympy.ntheory.isprime(self)`.
- **`_eval_is_composite()`** → False if ≤ 1; else `fuzzy_not(self.is_prime)`.
- **`as_numer_denom()`** → `(self, S.One)`.
- **`__floordiv__(self, other)`** → `Integer(self.p // Integer(other).p)`.
- **`__rfloordiv__(self, other)`** → `Integer(Integer(other).p // self.p)`.

---

## Class `AlgebraicNumber(Expr)`

**Slots:** `rep`, `root`, `alias`, `minpoly`.
**Class attributes:** `is_AlgebraicNumber = True`, `is_algebraic = True`, `is_number = True`.

### `__new__(cls, expr, coeffs=None, alias=None, **args)` → AlgebraicNumber instance

1. Sympifies `expr`.
2. If tuple/Tuple: extracts `(minpoly, root)`, converts minpoly to Poly if needed.
3. If already an AlgebraicNumber: uses its `minpoly` and `root`.
4. Otherwise computes `minimal_polynomial(expr, gen, polys=True)` and sets `root = expr`.
5. Gets domain from minpoly.
6. If `coeffs` provided: converts to DMP (dense multivariate polynomial); reduces modulo minpoly if degree too high; stores as Tuple.
7. Else: default coefficients `[1, 0]`; adjusts sign for negative root.
8. Builds args tuple `(root, scoeffs)` plus optional alias.
9. Creates object via `Expr.__new__(cls, *sargs)`, sets all four attributes.

### Methods:
- **`__hash__()`** → int: calls super.
- **`_eval_evalf(prec)`** → Float: evaluates `self.as_expr()._evalf(prec)`.
- **`is_aliased` property** → bool: `self.alias is not None`.
- **`as_poly(x=None)`** → Poly/Dummy: uses alias or Dummy('x') as generator.
- **`as_expr(x=None)`** → expr: converts poly to expression and expands.
- **`coeffs()`** → list: SymPy coefficients from `self.rep.all_coeffs()`.
- **`native_coeffs()`** → list: native (non-SymPy) coefficients.
- **`to_algebraic_integer()`** → AlgebraicNumber: if leading coefficient is 1, returns self; otherwise transforms to monic form using the standard construction.
- **`_eval_simplify(ratio, measure)`** → AlgebraicNumber or self: checks if any root of minpoly (excluding CRootOf) has a simpler representation via `measure`.

---

## Class `RationalConstant(Rational)`

Abstract base for specific rational constants. Slots empty. `__new__(cls)` returns `AtomicExpr.__new__(cls)`.

## Class `IntegerConstant(Integer)`

Abstract base for specific integer constants. Slots empty. `__new__(cls)` returns `AtomicExpr.__new__(cls)`.

---

## Class `Zero(with_metaclass(Singleton, IntegerConstant))`

**Class attributes:** `p = 0`, `q = 1`, `is_positive = False`, `is_negative = False`, `is_zero = True`.
Slots empty.

- **`__abs__()`** (static) → S.Zero.
- **`__neg__()`** (static) → S.Zero.
- **`_eval_power(expt)`**: Positive expt → self; negative → ComplexInfinity; non-real → NaN; handles coefficient extraction from Mul for compound exponents.
- **`_eval_order(*symbols)`** → self.
- **`__nonzero__()`, `__bool__()`** → False.
- **`as_coeff_Mul(rational=False)`** → `(S.One, self)`.

---

## Class `One(with_metaclass(Singleton, IntegerConstant))`

**Class attributes:** `p = 1`, `q = 1`, `is_number = True`. Slots empty.

- **`__abs__()`** (static) → S.One.
- **`__neg__()`** (static) → S.NegativeOne.
- **`_eval_power(expt)`** → self.
- **`_eval_order(*symbols)`** → None.
- **`factors(...)`** (static): visual → S.One; else `{}`.

---

## Class `NegativeOne(with_metaclass(Singleton, IntegerConstant))`

**Class attributes:** `p = -1`, `q = 1`, `is_number = True`. Slots empty.

- **`__abs__()`** (static) → S.One.
- **`__neg__()`** (static) → S.One.
- **`_eval_power(expt)`**: Odd integer → self; even → S.One; NaN/∞/-∞ → NaN; Half → I; Rational with q=2 → `I^p`; general: splits into integer + fractional parts via divmod.

---

## Class `Half(with_metaclass(Singleton, RationalConstant))`

**Class attributes:** `p = 1`, `q = 2`, `is_number = True`. Slots empty.
- **`__abs__()`** (static) → S.Half.

---

## Class `Infinity(with_metaclass(Singleton, Number))`

**Class attributes:** `is_commutative = True`, `is_positive = True`, `is_infinite = True`, `is_number = True`, `is_prime = False`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`_latex(printer)`** → `"\\infty"`.
- **`_eval_subs(old, new)`**: If self==old, returns new.
- **Arithmetic (`@_sympifyit`)**: Addition/subtraction with NaN/-∞ → NaN; with Float inf → NaN; else ∞ or -inf as appropriate. Multiplication: 0×∞→NaN; positive×∞→∞; negative×∞→-∞ (with Float variants). Division: ∞/∞, ∞/-∞, ∞/NaN → NaN; ∞/positive → ∞; ∞/negative → -∞.
- **`__abs__()`** → S.Infinity.
- **`__neg__()`** → S.NegativeInfinity.
- **`_eval_power(expt)`**: Positive → ∞; negative → 0; NaN/ComplexInfinity → NaN; non-real: uses real part of exponent to determine outcome (positive→∞, negative→0, zero→NaN).
- **`_as_mpf_val(prec)`** → `mlib.finf`.
- **`_sage_()`** → sage.oo.
- **Comparison**: Always false for `<`; true for `>=`; handles finite/real cases appropriately.
- **`__mod__(self, other)`**, **`__rmod__`** → S.NaN.
- **`floor()`, `ceiling()`** → self.

---

## Class `NegativeInfinity(with_metaclass(Singleton, Number))`

**Class attributes:** `is_commutative = True`, `is_negative = True`, `is_infinite = True`, `is_number = True`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`_latex(printer)`** → `"\\-\\infty"`.
- **Arithmetic**: Addition/subtraction with NaN/+∞ → NaN; else -∞ or +inf as appropriate. Multiplication: 0×(-∞)→NaN; positive×(-∞)→-∞; negative×(-∞)→+∞ (with Float variants). Division: similar to Infinity but sign-flipped.
- **`__abs__()`** → S.Infinity.
- **`__neg__()`** → S.Infinity.
- **`_eval_power(expt)`**: NaN/±∞ exponents → NaN; positive odd integer → -∞; positive even → ∞; general: `(-1)^expt * ∞^expt`.
- **`_as_mpf_val(prec)`** → `mlib.fninf`.
- **`_sage_()`** → -(sage.oo).
- **Comparison**: Always false for `>` with real; true for `<`; handles finite/real cases appropriately.
- **`__mod__(self, other)`**, **`__rmod__`** → S.NaN.
- **`floor()`, `ceiling()`** → self.

---

## Class `NaN(with_metaclass(Singleton, Number))`

**Class attributes:** All property flags (`is_real`, `is_rational`, `is_algebraic`, `is_transcendental`, `is_integer`, `is_finite`, `is_zero`, `is_prime`, `is_positive`, `is_negative`) are `None`. `is_comparable = False`, `is_number = True`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`_latex(printer)`** → `"\\mathrm{NaN}"`.
- **Arithmetic (`@_sympifyit`)**: All four operations (+, -, *, /) return self (NaN propagates).
- **`floor()`, `ceiling()`** → self.
- **`_as_mpf_val(prec)`** → `_mpf_nan`.
- **`_sage_()`** → sage.NaN.
- **Comparison**: `__eq__` returns True only for `other is S.NaN`; `__ne__` returns True otherwise; `_eval_Eq(other)` always returns S.false (mathematical inequality). Comparison operators (`<`, `<=`, `>`, `>=`) are inherited from Expr (raise TypeError).

---

## Class `ComplexInfinity(with_metaclass(Singleton, AtomicExpr))`

**Class attributes:** `is_commutative = True`, `is_infinite = True`, `is_number = True`, `is_prime = False`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`_latex(printer)`** → `"\\tilde{\\infty}"`.
- **`__abs__()`** (static) → S.Infinity.
- **`floor()`, `ceiling()`** → self.
- **`__neg__()`** (static) → S.ComplexInfinity.
- **`_eval_power(expt)`**: ComplexInfinity exponent → NaN; zero exponent → NaN; positive → ∞̃; negative → 0.
- **`_sage_()`** → sage.UnsignedInfinityRing.gen().

---

## Class `NumberSymbol(AtomicExpr)`

Abstract base for mathematical constants (π, e, etc.).
**Class attributes:** `is_commutative = True`, `is_finite = True`, `is_number = True`, `is_NumberSymbol = True`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`approximation(number_cls)`**: Abstract; returns interval containing the value, or None.
- **`_eval_evalf(prec)`** → Float: calls `Float._new(self._as_mpf_val(prec), prec)`.
- **Comparison (`@_sympifyit`)**: `__eq__`: identity check first; irrational NumberSymbols never equal a Number. `__lt__`: uses `approximation_interval()` if available for Integer/Rational targets; otherwise evalf comparison. `__le__`: identity → True; else evalf comparison. `__gt__`, `__ge__`: use negation trick (`(-self) < (-other)`).
- **`__int__()`, `__long__()`**: Abstract; raises NotImplementedError (overridden by subclasses).

---

## Class `Exp1(with_metaclass(Singleton, NumberSymbol))` — the constant *e*

**Class attributes:** `is_real = True`, `is_positive = True`, `is_negative = False`, `is_irrational = True`, `is_number = True`, `is_algebraic = False`, `is_transcendental = True`. Slots empty.

- **`_latex(printer)`** → `"e"`.
- **`__abs__()`** (static) → S.Exp1.
- **`__int__()`** → 2.
- **`_as_mpf_val(prec)`** → `mpf_e(prec)`.
- **`approximation_interval(Integer)`** → `(Integer(2), Integer(3))`.
- **`_eval_power(expt)`** → `exp(expt)`.
- **`_eval_rewrite_as_sin()`**, **`_eval_rewrite_as_cos()`**: Return trigonometric expressions.
- **`_sage_()`** → sage.e.

---

## Class `Pi(with_metaclass(Singleton, NumberSymbol))` — the constant π

**Class attributes:** `is_real = True`, `is_positive = True`, `is_negative = False`, `is_irrational = True`, `is_number = True`, `is_algebraic = False`, `is_transcendental = True`. Slots empty.

- **`_latex(printer)`** → `"\\pi"`.
- **`__abs__()`** (static) → S.Pi.
- **`__int__()`** → 3.
- **`_as_mpf_val(prec)`** → `mpf_pi(prec)`.
- **`approximation_interval(Integer)`** → `(Integer(3), Integer(4))`; for Rational: `(Rational(223,71), Rational(22,7))`.
- **`_sage_()`** → sage.pi.

---

## Class `GoldenRatio(with_metaclass(Singleton, NumberSymbol))` — φ = (1+√5)/2

**Class attributes:** `is_real = True`, `is_positive = True`, `is_negative = False`, `is_irrational = True`, `is_number = True`, `is_algebraic = True`, `is_transcendental = False`. Slots empty.

- **`_latex(printer)`** → `"\\phi"`.
- **`__int__()`** → 1.
- **`_as_mpf_val(prec)`** → `phi_fixed`.
- **`approximation_interval(Integer)`** → `(Integer(1), Integer(2))`; for Rational: `(Rational(987,610), Rational(1597,987))`.
- **`_eval_expand_func(**kwargs)`** → `S.Half + sqrt(5)/2`.
- **`_eval_rewrite_as_sqrt = _eval_expand_func`**.

---

## Class `EulerGamma(with_metaclass(Singleton, NumberSymbol))` — γ ≈ 0.577...

**Class attributes:** `is_real = True`, `is_positive = True`, `is_negative = False`, `is_irrational = None`, `is_number = True`, `is_algebraic = None`, `is_transcendental = None`. Slots empty.

- **`_latex(printer)`** → `"\\gamma"`.
- **`__int__()`** → 0.
- **`_as_mpf_val(prec)`**: Uses mpmath's euler constant at given precision via `mpmath.euler` converted to mpf tuple.
- **`approximation_interval(Integer)`** → `(Integer(0), Integer(1))`.
- **`_sage_()`** → sage.euler_gamma.

---

## Class `Catalan(with_metaclass(Singleton, NumberSymbol))` — G ≈ 0.916...

**Class attributes:** `is_real = True`, `is_positive = True`, `is_negative = False`, `is_irrational = None`, `is_number = True`, `is_algebraic = None`, `is_transcendental = None`. Slots empty.

- **`_latex(printer)`** → `"C"`.
- **`__int__()`** → 0.
- **`_as_mpf_val(prec)`**: Uses mpmath's Catalan constant at given precision via `mpmath.catalan` converted to mpf tuple.
- **`approximation_interval(Integer)`** → `(Integer(0), Integer(1))`.
- **`_sage_()`** → sage.catalan.

---

## Class `ImaginaryUnit(with_metaclass(Singleton, AtomicExpr))` — i = √(-1)

**Class attributes:** `is_commutative = True`, `is_number = True`, `is_imaginary = True`. Slots empty.

- **`__new__(cls)`** → AtomicExpr.
- **`_latex(printer)`** → `"\\mathrm{i}"`.
- **`_eval_evalf(prec)`** → `Float._new((0, 0, 0, 1), prec) + Float._new((0, 1, 0, 1), prec)`.
- **`__abs__()`** (static) → S.One.
- **`__neg__()`** (static) → `-S.ImaginaryUnit` (i.e., `ImaginaryUnit * -1`).
- **`_eval_power(expt)`**: Integer exponents cycle through {1, i, -1, -i}. Rational with odd denominator: handles sign. Float exponent: uses complex power. General: returns `exp(I*Pi/2 * expt)`.
- **`_as_mpf_val(prec)`** → `(Float(0)._mpf_, Float(1)._mpf_)` (complex mpf tuple).
- **`_sage_()`** → sage.I.

---

## Module-Level Sympify Converters

```python
converter[float] = converter[decimal.Decimal] = Float
converter[fractions.Fraction] = sympify_fractions  # returns Rational(f.numerator, f.denominator)
if HAS_GMPY == 2:
    try:
        from gmpy import mpq as gmpy_mpq
        converter[gmpy_mpq] = sympify_mpq  # returns Rational(numerator, denominator)
    except ImportError:
        pass
converter[mpnumeric] = sympify_mpmath  # calls Expr._from_mpmath(x, x.context.prec)
converter[complex] = sympify_complex   # real + I*imag via sympify of each part
```

## Module-Level Singleton Aliases & Final Setup

- `oo = S.Infinity`
- `nan = S.NaN`
- `zoo = S.ComplexInfinity`
- `E = S.Exp1`
- `pi = S.Pi`
- `I = S.ImaginaryUnit`
- `_intcache[0] = S.Zero`, `_intcache[1] = S.One`, `_intcache[-1] = S.NegativeOne` (populated at end of module).
- Imports `Pow, integer_nthroot` from `.power`; sets `Mul.identity = One()`.
- Imports `Add` from `.add`; sets `Add.identity = Zero()`.

## sympy/geometry/entity.py
Now I have the full file content (566 lines). Here is the complete natural-language specification:

---

# Module-Level Preamble

## Imports

```python
from __future__ import division, print_function
from sympy.core.compatibility import is_sequence
from sympy.core.containers import Tuple
from sympy.core.basic import Basic
from sympy.core.sympify import sympify
from sympy.functions import cos, sin
from sympy.matrices import eye
from sympy.sets import Set
```

## Constants & Globals

**`ordering_of_classes`** — A module-level list of 20 class-name strings defining the canonical ordering for `__cmp__` comparisons between geometry entities. The exact sequence is:

```python
[
    "Point2D", "Point3D", "Point",
    "Segment2D", "Ray2D", "Line2D",
    "Segment3D", "Line3D", "Ray3D",
    "Segment", "Ray", "Line",
    "Plane",
    "Triangle", "RegularPolygon", "Polygon",
    "Circle", "Ellipse", "Curve", "Parabola"
]
```

---

# Code Objects

## Class `GeometryEntity(Basic)`

The base class for all geometrical entities. Inherits from `sympy.core.basic.Basic`. Does not represent any particular geometric entity itself; provides shared methods common to all subclasses.

### `__new__(cls, *args, **kwargs)`

Class factory method (overrides `Basic.__new__`). Internally defines a helper function `is_seq_and_not_point(a)`: returns `False` if `a` has attribute `is_Point` that is truthy; otherwise delegates to `is_sequence(a)`. For each element in `args`, if it passes `is_seq_and_not_point`, wraps it as `Tuple(*a)`; otherwise applies `sympify(a)`. Returns the result of `Basic.__new__(cls, *args)` with these processed arguments.

### `__cmp__(self, other)`

Compares two `GeometryEntity` instances. First compares class names lexicographically (`(n1 > n2) - (n1 < n2)`). If equal, searches the MRO of each object's class for a name present in `ordering_of_classes`; uses the first match found. Objects not found in the ordering fall back to the initial string comparison result. Returns `(i1 > i2) - (i1 < i2)` if both are found; otherwise returns the original string-comparison result.

### `__contains__(self, other)`

Returns `True` if `type(self) == type(other)` and `self == other`; otherwise raises `NotImplementedError`. Subclasses should override for more complex containment logic.

### `__getnewargs__(self)`

Returns `tuple(self.args)` — used by pickle to reconstruct the object.

### `__ne__(self, o)`

Returns `not self.__eq__(o)`.

### `__radd__(self, a)`, `__rdiv__(self, a)`, `__rmul__(self, a)`, `__rsub__(self, a)`

Reverse arithmetic operators; each delegates to the corresponding dunder method on `a` with `self` as argument (e.g., `__radd__` returns `a.__add__(self)`).

### `__repr__(self)`

Returns `type(self).__name__ + repr(self.args)`.

### `__str__(self)`

Imports `sstr` from `sympy.printing`; returns `type(self).__name__ + sstr(self.args)`.

### `_eval_subs(self, old, new)`

Handles substitution. If either `old` or `new` is a sequence (via `is_sequence`), converts both to `Point3D` if `self` is a `Point3D`, otherwise to `Point`; then calls `self._subs(old, new)`. Returns the result of `_subs` in that case; implicitly returns `None` otherwise.

### `_repr_svg_(self)`

Generates an SVG representation for IPython/Jupyter display. First retrieves `self.bounds`; if it raises `NotImplementedError` or `TypeError`, returns `None`. Builds an SVG header with markers (circle, arrow, reverse-arrow). Computes canvas bounds from `bounds` via `N()`; if the entity is a single point (`xmin == xmax and ymin == ymax`), buffers by ±0.5 in each direction; otherwise expands bounds by 10% of the widest dimension. Sets width/height to `min(max(100, range), 300)`. Computes `scale_factor = max(dx, dy) / max(width, height)` (or 1 if both are zero). Calls `self._svg(scale_factor)`; if that raises `NotImplementedError` or `TypeError`, returns `None`. Constructs a view-box string and a Y-flip transform matrix. Returns the concatenated SVG: header + `<g transform="...">` + entity SVG + closing tags.

### `_svg(self, scale_factor=1., fill_color="#66cc99")`

Abstract method; raises `NotImplementedError`. Subclasses override to return an SVG path element string.

### `_sympy_(self)`

Returns `self`.

### `ambient_dimension` (property)

Raises `NotImplementedError`. Subclasses must override to return the dimension of the ambient space.

### `bounds` (property)

Raises `NotImplementedError`. Subclasses must override to return a tuple `(xmin, ymin, xmax, ymax)` representing the bounding rectangle.

### `encloses(self, o)`

Determines whether entity `o` is strictly inside self's boundaries. Imports `Point`, `Segment`, `Ray`, `Line`, `Ellipse`, `Polygon`, `RegularPolygon`. Dispatches by type of `o`:
- **`Point`**: returns `self.encloses_point(o)`.
- **`Segment`**: returns `all(self.encloses_point(x) for x in o.points)`.
- **`Ray` or `Line`**: always returns `False`.
- **`Ellipse`**: returns `True` if self encloses the ellipse center, encloses the point `(center.x + hradius, center.y)`, and `self.intersection(o)` is empty.
- **`Polygon`** (including `RegularPolygon`): for `RegularPolygon`, first checks that self encloses the polygon's center; then returns `all(self.encloses_point(v) for v in o.vertices)`.
- Any other type: raises `NotImplementedError`.

### `equals(self, o)`

Returns `self == o`.

### `intersection(self, o)`

Raises `NotImplementedError`. Subclasses implement to return a list of intersection objects. The entity with the higher index in `ordering_of_classes` should handle intersections with lower-index types.

### `is_similar(self, other)`

Raises `NotImplementedError`. Determines whether two entities are similar (one can be obtained from the other by uniform scaling). Typically called via `are_similar()` in `util.py`.

### `reflect(self, line)`

Reflects the entity across a given `line` (a geometry entity with a `slope` attribute and `args`). Imports `atan`, `Point`, `Dummy`, `oo` from sympy. Three cases:
- **Horizontal line** (`l.slope == 0`): extracts y-coordinate `y = l.args[0].y`. If `y == 0` (x-axis), returns `g.scale(y=-1)`. Otherwise, builds replacement list `[(p, p.translate(y=2*(y - p.y))) for p in g.atoms(Point)]`.
- **Vertical line** (`l.slope == oo`): extracts x-coordinate `x = l.args[0].x`. If `x == 0` (y-axis), returns `g.scale(x=-1)`. Otherwise, builds replacement list `[(p, p.translate(x=2*(x - p.x))) for p in g.atoms(Point)]`.
- **Oblique line** (neither horizontal nor vertical): if `g` has no own `reflect` method and not all of `g.args` are `Point` instances, raises `NotImplementedError('reflect undefined or non-Point args in ...')`. Otherwise computes angle `a = atan(l.slope)`, gets coefficients `c = l.coefficients`, y-intercept `d = -c[-1]/c[1]`. Creates dummy variables `x, y = Dummy()`, builds a transform on a single point: `xf = Point(x, y).translate(y=-d).rotate(-a, o).scale(y=-1).rotate(a, o).translate(y=d)` (where `o = Point(0, 0)`). Builds replacement list `[(p, xf.xreplace({x: p.x, y: p.y})) for p in g.atoms(Point)]`. Returns `g.xreplace(dict(reps))` in all cases.

### `rotate(self, angle, pt=None)`

Rotates the entity by `angle` radians counterclockwise about point `pt` (default origin). Iterates over `self.args`; if an argument is a `GeometryEntity`, recursively calls `a.rotate(angle, pt)`; otherwise keeps it unchanged. Returns `type(self)(*newargs)`.

### `scale(self, x=1, y=1, pt=None)`

Scales the entity by multiplying coordinates by `x` and `y`. If `pt` is given: converts to `Point(pt, dim=2)`, then returns `self.translate(*(-pt).args).scale(x, y).translate(*pt.args)` (shift to origin, scale, shift back). Otherwise, iterates over `self.args`; if an argument is a `GeometryEntity`, calls `a.scale(x, y)`; otherwise keeps it. Returns `type(self)(*newargs)`.

### `translate(self, x=0, y=0)`

Translates the entity by adding `x` and `y` to coordinates. Iterates over `self.args`; if an argument is a `GeometryEntity`, calls `a.translate(x, y)`; otherwise keeps it unchanged. Returns `self.func(*newargs)`.

---

## Class `GeometrySet(GeometryEntity, Set)`

Parent class for all geometry entities that are also sympy Sets. Inherits from both `GeometryEntity` and `sympy.sets.Set`.

### `_contains(self, other)`

Handles containment checks for sympy.sets compatibility. If `other` is a `Set` with `is_FiniteSet` truthy, returns `all(self.__contains__(i) for i in other)`. Otherwise delegates to `self.__contains__(other)`.

### `_union(self, o)`

Returns the union of self and `o` as a sympy Set. Imports `Union`, `FiniteSet`. If `o.is_FiniteSet`: collects points from `o` not contained in self (`[p for p in o if not self._contains(p)]`). If all points are new (length equals len(o)), returns `None`; otherwise returns `Union(self, FiniteSet(*other_points))`. If `self._contains(o)`, returns `self`. Otherwise returns `None`.

### `_intersect(self, o)`

Returns a sympy Set of intersection objects. Imports `Set`, `FiniteSet`, `Union`, and `Point` from `sympy.geometry`. In a try block: if `o.is_FiniteSet`, computes `inter = FiniteSet(*(p for p in o if self.contains(p)))`; otherwise calls `self.intersection(o)`. If `NotImplementedError` is raised, returns `None`. Separates the intersection result into points (`FiniteSet(*[p for p in inter if isinstance(p, Point)])`) and non-points. Returns `Union(*(non_points + [points]))`.

---

## Function `translate(x, y)`

Returns a 3×3 identity matrix (from `eye(3)`) with `rv[2,0] = x` and `rv[2,1] = y`. This is the homogeneous transformation matrix for translating a 2-D point by `(x, y)`. Returns the modified matrix.

---

## Function `scale(x, y, pt=None)`

Returns a 3×3 scaling matrix (from `eye(3)*cos(th)` — actually starts as identity scaled element-wise, then sets `rv[0,0] = x` and `rv[1,1] = y`). If `pt` is given: converts to `Point(pt, dim=2)`, computes translation matrices `tr1 = translate(*(-pt).args)` and `tr2 = translate(*pt.args)`, returns the product `tr1 * rv * tr2`. Otherwise returns `rv` directly. This is the homogeneous transformation matrix for scaling a 2-D point by `(x, y)`, optionally relative to a pivot point.

---

## Function `rotate(th)`

Returns a 3×3 rotation matrix for rotating a 2-D point about the origin by angle `th` radians. Computes `s = sin(th)`. Starts with `rv = eye(3) * cos(th)`, then sets `rv[0,1] = s`, `rv[1,0] = -s`, and explicitly sets `rv[2,2] = 1`. This produces the standard homogeneous rotation matrix:

```
| cos(th)  sin(th)  0 |
| -sin(th) cos(th)  0 |
|    0       0      1 |
```

## sympy/physics/optics/medium.py
Now I have the complete file. Here is the specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import division
from sympy.physics.units import second, meter, kilogram, ampere
from sympy import Symbol, sympify, sqrt
from sympy.physics.units import speed_of_light, u0, e0
from sympy.printing import sstr   # imported inside __str__
```

### Constants & Globals

| Name | Definition |
|---|---|
| `c` | `speed_of_light.convert_to(meter/second)` — the SI value of the speed of light in m/s. |
| `_e0mksa` | `e0.convert_to(ampere**2*second**4/(kilogram*meter**3))` — vacuum permittivity expressed in MKSA base units. |
| `_u0mksa` | `u0.convert_to(meter*kilogram/(ampere**2*second**2))` — vacuum permeability expressed in MKSA base units. |

### Exported API

```python
__all__ = ['Medium']
```

---

## Code Objects

### Class `Medium(Symbol)`

A subclass of `sympy.Symbol`. Represents an optical medium whose electromagnetic properties (permittivity, permeability) determine wave propagation characteristics such as refractive index and intrinsic impedance.

#### Constructor: `__new__(cls, name, permittivity=None, permeability=None, n=None)`

1. Calls `super(Medium, cls).__new__(cls, name)` to create the Symbol instance with `name` as its argument.
2. Stores three private attributes via `sympify()`:
   - `obj._permittivity = sympify(permittivity)`
   - `obj._permeability = sympify(permeability)`
   - `obj._n = sympify(n)`
3. **Consistency / derivation logic:**
   - **If `n` is not None** (refractive index was provided):
     - If `permittivity` is given but `permeability` is `None`: compute `obj._permeability = n**2 / (c**2 * obj._permittivity)`.
     - If `permeability` is given but `permittivity` is `None`: compute `obj._permittivity = n**2 / (c**2 * obj._permeability)`.
     - If **both** `permittivity` and `permeability` are not None: verify consistency by checking that `abs(n - c * sqrt(obj._permittivity * obj._permeability)) > 1e-6`; if true, raise `ValueError("Values are not consistent.")`.
   - **Else if** both `permittivity` and `permeability` are provided (but `n` is None): derive the refractive index as `obj._n = c * sqrt(permittivity * permeability)`.
   - **Else if** neither `permittivity` nor `permeability` is given: default to vacuum values — set `obj._permittivity = _e0mksa` and `obj._permeability = _u0mksa`.
4. Returns the constructed object.

#### Property: `intrinsic_impedance` (read-only)

Returns `sqrt(self._permeability / self._permittivity)` — the intrinsic impedance of the medium in ohms, derived from permeability and permittivity.

#### Property: `speed` (read-only)

Returns `1 / sqrt(self._permittivity * self._permeability)` — the speed of electromagnetic wave propagation through the medium.

#### Property: `refractive_index` (read-only)

Returns `c / self.speed` — the ratio of the speed of light in vacuum to the speed in this medium, i.e., the refractive index.

#### Property: `permittivity` (read-only)

Returns `self._permittivity` directly.

#### Property: `permeability` (read-only)

Returns `self._permeability` directly.

#### Method: `__str__(self)`

Imports `sstr` from `sympy.printing`. Returns the string concatenation of `type(self).__name__` (which is `"Medium"`) and `sstr(self.args)` — producing a human-readable representation like `"Medium(name)"`.

#### Comparison Methods

| Method | Implementation |
|---|---|
| `__lt__(self, other)` | Returns `self.refractive_index < other.refractive_index` (compares by refractive index). |
| `__gt__(self, other)` | Returns `not self.__lt__(other)`. |
| `__eq__(self, other)` | Returns `self.refractive_index == other.refractive_index`. |
| `__ne__(self, other)` | Returns `not self.__eq__(other)`. |

All comparison methods delegate to the refractive index property; two Medium instances are considered equal if and only if their refractive indices are equal.

---

### Summary of Data Flow

- **Inputs:** A name (string), optionally permittivity, permeability, or refractive index `n` — any combination is accepted as long as at least one pair of the three physical quantities is provided.
- **Internal state:** `_permittivity`, `_permeability`, and `_n` are always populated after construction (derived from inputs or defaulted to vacuum values).
- **Derived properties** (`intrinsic_impedance`, `speed`, `refractive_index`) are computed on-the-fly from the stored `_permittivity` and `_permeability`. The `_n` attribute is used only during construction for consistency checking and derivation.

## sympy/physics/vector/dyadic.py
Here is the complete natural-language specification of `sympy/physics/vector/dyadic.py`:

---

## Module-Level Preamble

### Imports

```python
from sympy.core.backend import sympify, Add, ImmutableMatrix as Matrix
from sympy.core.compatibility import unicode
from .printing import (VectorLatexPrinter, VectorPrettyPrinter,
                       VectorStrPrinter)
```

### Constants & Globals

- `__all__ = ['Dyadic']` — the sole public export.

---

## Code Objects

### Function: `_check_dyadic(other)`

**Signature:** `_check_dyadic(other: object) -> Dyadic`

**Logic:**
1. Tests whether `other` is an instance of `Dyadic`.
2. If not, raises `TypeError('A Dyadic must be supplied')`.
3. Returns `other` unchanged if it passes the check.

---

### Class: `Dyadic(object)`

**Inheritance:** `object` (no metaclass).

#### Internal Data Representation

The dyadic is stored as an instance attribute `self.args`, which is a **list of 3-tuples**. Each tuple has the form `(measure_number, left_unit_vector, right_unit_vector)`. The list contains only unique unit-vector pairs; like terms are combined during construction. Zero-measure-number entries and zero-unit-vector entries are removed.

#### Attribute: `args`

- Type: `list[tuple[Expr, Vector, Vector]]`
- Initialized in `__init__`; each element is `(scalar_expr, left_vector, right_vector)`.

---

#### Method: `__init__(self, inlist)`

**Signature:** `__init__(self, inlist: list | int) -> None`

**Logic:**
1. Initializes `self.args = []`.
2. If `inlist == 0`, replaces it with `[]` (zero dyadic).
3. While `inlist` is non-empty, iterates over the first element of `inlist`:
   - Searches `self.args` for a tuple whose second and third elements (the unit vectors) match those of `inlist[0]`.
   - If found: adds the measure numbers together (`self.args[i][0] + inlist[0][0]`), replaces the entry, removes it from `inlist`, sets `added = 1`, breaks.
   - If not found: appends `inlist[0]` to `self.args`, removes it from `inlist`.
4. After combining all entries, sweeps through `self.args` removing any tuple whose measure number is zero **or** whose left or right unit vector is zero (using bitwise-or `|` as logical OR).

---

#### Method: `__add__(self, other)`

**Signature:** `__add__(self, other: object) -> Dyadic`

**Logic:**
1. Validates `other` via `_check_dyadic(other)`.
2. Returns a new `Dyadic(self.args + other.args)`, which triggers the combining logic of `__init__`.

---

#### Method: `__radd__(self, other)`

**Alias:** `__radd__ = __add__` — commutative addition; delegates to `__add__`.

---

#### Method: `__and__(self, other)`

**Signature:** `__and__(self, other: Dyadic | Vector) -> Dyadic | Vector`

**Logic (inner product / dot):**
1. Imports `Vector` and `_check_vector` from `sympy.physics.vector.vector`.
2. **If `other` is a `Dyadic`:**
   - Validates via `_check_dyadic(other)`.
   - Initializes `ol = Dyadic(0)`.
   - For each tuple `(v[0], v[1], v[2])` in `self.args` and each tuple `(v2[0], v2[1], v2[2])` in `other.args`:
     - Computes the scalar product of the right unit vector of self with the left unit vector of other: `v[2] & v2[1]`.
     - Forms a new dyadic term: `v[0] * v2[0] * (v[2] & v2[1]) * (v[1] | v2[2])` — the product of measure numbers times the scalar inner-product coefficient, times the outer product of the remaining unit vectors.
     - Adds to `ol`.
   - Returns `ol` (a `Dyadic`).
3. **If `other` is a `Vector`:**
   - Validates via `_check_vector(other)`.
   - Initializes `ol = Vector(0)`.
   - For each tuple `(v[0], v[1], v[2])` in `self.args`:
     - Computes the dot product of the right unit vector with the other vector: `v[2] & other`.
     - Forms a new vector term: `v[0] * v[1] * (v[2] & other)`.
     - Adds to `ol`.
   - Returns `ol` (a `Vector`).

---

#### Method: `dot(self, other)`

**Alias:** `dot = __and__` — named convenience for the inner product.

---

#### Method: `__mul__(self, other)`

**Signature:** `__mul__(self, other) -> Dyadic`

**Logic:**
1. Creates a copy of `self.args`.
2. For each tuple in the copy, multiplies the measure number by `sympify(other)`, keeping the unit vectors unchanged.
3. Returns a new `Dyadic(newlist)`.

---

#### Method: `__rmul__(self, other)`

**Alias:** `__rmul__ = __mul__` — commutative scalar multiplication; delegates to `__mul__`.

---

#### Method: `__div__(self, other)` / `__truediv__(self, other)`

**Signature:** `__div__(self, other) -> Dyadic`; `__truediv__ = __div__`

**Logic:** Returns `self.__mul__(1 / other)`, i.e., multiplies by the reciprocal of `other`.

---

#### Method: `__sub__(self, other)`

**Signature:** `__sub__(self, other: object) -> Dyadic`

**Logic:** Returns `self.__add__(other * -1)`, i.e., adds the negation of `other`.

---

#### Method: `__rsub__(self, other)`

**Signature:** `__rsub__(self, other: object) -> Dyadic`

**Logic:** Returns `(-1 * self) + other`, i.e., subtracts self from other.

---

#### Method: `__neg__(self)`

**Signature:** `__neg__(self) -> Dyadic`

**Logic:** Returns `self * -1`.

---

#### Method: `__eq__(self, other)`

**Signature:** `__eq__(self, other: object) -> bool`

**Logic:**
1. If `other == 0`, replaces it with `Dyadic(0)`.
2. Validates via `_check_dyadic(other)`.
3. If both `self.args` and `other.args` are empty lists, returns `True`.
4. If either is empty (but not both), returns `False`.
5. Otherwise, returns `set(self.args) == set(other.args)` — compares the sets of tuples for equality.

---

#### Method: `__ne__(self, other)`

**Signature:** `__ne__(self, other: object) -> bool`

**Logic:** Returns `not self.__eq__(other)`.

---

#### Method: `__xor__(self, other)`

**Signature:** `__xor__(self, other: Vector) -> Dyadic`

**Logic (cross product — Dyadic × Vector):**
1. Imports `_check_vector` from `sympy.physics.vector.vector`.
2. Validates `other` via `_check_vector(other)`.
3. Initializes `ol = Dyadic(0)`.
4. For each tuple `(v[0], v[1], v[2])` in `self.args`:
   - Computes the cross product of the right unit vector with other: `v[2] ^ other`.
   - Forms a new dyadic term: `v[0] * (v[1] | (v[2] ^ other))` — scalar times outer product of left unit vector and the resulting cross-product vector.
   - Adds to `ol`.
5. Returns `ol` (a `Dyadic`).

---

#### Method: `cross(self, other)`

**Alias:** `cross = __xor__` — named convenience for the cross product.

---

#### Method: `__rand__(self, other)`

**Signature:** `__rand__(self, other: Vector) -> Vector`

**Logic (inner product — Vector · Dyadic):**
1. Imports `Vector` and `_check_vector`.
2. Validates `other` via `_check_vector(other)`.
3. Initializes `ol = Vector(0)`.
4. For each tuple `(v[0], v[1], v[2])` in `self.args`:
   - Computes the dot product of the left unit vector with other: `v[1] & other`.
   - Forms a new vector term: `v[0] * v[2] * (v[1] & other)`.
   - Adds to `ol`.
5. Returns `ol` (a `Vector`).

---

#### Method: `__rxor__(self, other)`

**Signature:** `__rxor__(self, other: Vector) -> Dyadic`

**Logic (cross product — Vector × Dyadic):**
1. Imports `_check_vector`.
2. Validates `other` via `_check_vector(other)`.
3. Initializes `ol = Dyadic(0)`.
4. For each tuple `(v[0], v[1], v[2])` in `self.args`:
   - Computes the cross product of other with the left unit vector: `other ^ v[1]`.
   - Forms a new dyadic term: `v[0] * ((other ^ v[1]) | v[2])` — scalar times outer product of the resulting cross-product vector and right unit vector.
   - Adds to `ol`.
5. Returns `ol` (a `Dyadic`).

---

#### Method: `_latex(self, printer=None)`

**Signature:** `_latex(self, printer=None) -> str`

**Logic:**
1. Assigns `ar = self.args`. If empty, returns `str(0)`.
2. Creates a `VectorLatexPrinter()` instance `mlp`.
3. For each tuple `(v[0], v[1], v[2])`:
   - **Coefficient is 1:** appends `' + ' + mlp.doprint(v[1]) + r"\otimes " + mlp.doprint(v[2])`.
   - **Coefficient is −1:** appends `' - ' + mlp.doprint(v[1]) + r"\otimes " + mlp.doprint(v[2])`.
   - **Coefficient is nonzero and not ±1:**
     - Gets the LaTeX string `arg_str = mlp.doprint(v[0])`.
     - If `v[0]` is an instance of `Add`, wraps it in parentheses: `'(%s)' % arg_str`.
     - If `arg_str` starts with `'-'`: strips the minus sign, sets prefix to `' - '`.
     - Otherwise: sets prefix to `' + '`.
     - Appends `prefix + arg_str + mlp.doprint(v[1]) + r"\otimes " + mlp.doprint(v[2])`.
4. Joins all parts into a single string.
5. Strips leading `' + '` (3 chars) or leading space if present.
6. Returns the result.

---

#### Method: `_pretty(self, printer=None)`

**Signature:** `_pretty(self, printer=None) -> Fake`

**Logic:**
1. Captures `e = self`. Defines an inner class `Fake(object)` with attribute `baseline = 0` and a method `render(self, *args, **kwargs)`:
   - Assigns `ar = e.args`.
   - Determines `use_unicode`: if `printer` is provided, reads `printer._settings` (if any) for `_use_unicode`; otherwise imports and calls `pretty_use_unicode()`.
   - Creates a pretty printer: `mpp = printer if printer else VectorPrettyPrinter(settings)` where `settings = printer._settings if printer else {}`.
   - If `ar` is empty, returns `unicode(0)`.
   - Sets the bar character to Unicode "⊗" (`\N{CIRCLED TIMES}`) if `use_unicode`, otherwise `"|"`.
   - For each tuple `(v[0], v[1], v[2])`:
     - **Coefficient is 1:** extends output list with `[u" + ", mpp.doprint(v[1]), bar, mpp.doprint(v[2])]`.
     - **Coefficient is −1:** extends with `[u" - ", mpp.doprint(v[1]), bar, mpp.doprint(v[2])]`.
     - **Coefficient is nonzero and not ±1:**
       - If `v[0]` is an instance of `Add`: gets the pretty-printed string wrapped in parens via `mpp._print(v[0]).parens()[0]`.
       - Otherwise: `arg_str = mpp.doprint(v[0])`.
       - If `arg_str` starts with `u"-"`: strips it, sets prefix to `u" - "`.
       - Otherwise: prefix is `u" + "`.
       - Extends output list with `[prefix, arg_str, u" ", mpp.doprint(v[1]), bar, mpp.doprint(v[2])]`.
   - Joins all parts into a single Unicode string.
   - Strips leading `' + '` (3 chars) or leading space if present.
   - Returns the result.
2. Returns an instance of `Fake()`.

---

#### Method: `__str__(self, printer=None)`

**Signature:** `__str__(self, printer=None) -> str`

**Logic:**
1. Assigns `ar = self.args`. If empty, returns `str(0)`.
2. Creates a `VectorStrPrinter()` instance (used only for the measure number).
3. For each tuple `(v[0], v[1], v[2])`:
   - **Coefficient is 1:** appends `' + (' + str(v[1]) + '|' + str(v[2]) + ')'`.
   - **Coefficient is −1:** appends `' - (' + str(v[1]) + '|' + str(v[2]) + ')'`.
   - **Coefficient is nonzero and not ±1:**
     - Gets the string `arg_str = VectorStrPrinter().doprint(v[0])`.
     - If `v[0]` is an instance of `Add`, wraps in parentheses: `"(%s)" % arg_str`.
     - If `arg_str[0] == '-'`: strips it, sets prefix to `' - '`.
     - Otherwise: prefix is `' + '`.
     - Appends `prefix + arg_str + '*(' + str(v[1]) + '|' + str(v[2]) + ')'`.
4. Joins all parts into a single string.
5. Strips leading `' + '` (3 chars) or leading space if present.
6. Returns the result.

---

#### Method: `_sympystr` / `_sympyrepr` / `__repr__`

**Aliases:**
- `_sympystr = __str__`
- `_sympyrepr = _sympystr`
- `__repr__ = __str__`

All delegate to the string representation method.

---

#### Method: `express(self, frame1, frame2=None)`

**Signature:** `express(self, frame1: ReferenceFrame, frame2: ReferenceFrame | None = None) -> Dyadic`

**Logic:**
1. Imports `express` from `sympy.physics.vector.functions`.
2. Delegates to the global function: `return express(self, frame1, frame2)`.
3. If `frame2` is provided, expresses the left unit vectors in `frame1` and the right unit vectors in `frame2`; otherwise expresses both sides in `frame1`.

---

#### Method: `to_matrix(self, reference_frame, second_reference_frame=None)`

**Signature:** `to_matrix(self, reference_frame: ReferenceFrame, second_reference_frame: ReferenceFrame | None = None) -> ImmutableMatrix`

**Logic:**
1. If `second_reference_frame is None`, sets it to `reference_frame`.
2. Constructs a 9-element list by iterating over each unit vector `i` in `reference_frame` and each unit vector `j` in `second_reference_frame`:
   - Computes `i.dot(self).dot(j)` — the double-dot projection of the dyadic onto the `(i, j)` basis pair.
3. Wraps the list in `Matrix(...)` (which is `ImmutableMatrix`) and reshapes to a 3×3 matrix via `.reshape(3, 3)`.
4. Returns the resulting `ImmutableMatrix`.

---

#### Method: `doit(self, **hints)`

**Signature:** `doit(self, **hints: dict) -> Dyadic`

**Logic:**
1. For each tuple `(v[0], v[1], v[2])` in `self.args`, creates a new dyadic term with the measure number expanded via `.doit(**hints)` while keeping unit vectors unchanged.
2. Sums all resulting single-term dyadics, starting from `Dyadic(0)`.
3. Returns the result.

---

#### Method: `dt(self, frame)`

**Signature:** `dt(self, frame: ReferenceFrame) -> Dyadic`

**Logic:**
1. Imports `time_derivative` from `sympy.physics.vector.functions`.
2. Delegates to the global function: `return time_derivative(self, frame)`.

---

#### Method: `simplify(self)`

**Signature:** `simplify(self) -> Dyadic`

**Logic:**
1. Initializes `out = Dyadic(0)`.
2. For each tuple `(v[0], v[1], v[2])` in `self.args`:
   - Creates a new dyadic term with the measure number simplified via `.simplify()`, keeping unit vectors unchanged.
   - Adds to `out`.
3. Returns `out`.

---

#### Method: `subs(self, *args, **kwargs)`

**Signature:** `subs(self, *args, **kwargs) -> Dyadic`

**Logic:**
1. For each tuple `(v[0], v[1], v[2])` in `self.args`, creates a new dyadic term with the measure number substituted via `.subs(*args, **kwargs)`, keeping unit vectors unchanged.
2. Sums all resulting single-term dyadics, starting from `Dyadic(0)`.
3. Returns the result.

---

#### Method: `applyfunc(self, f)`

**Signature:** `applyfunc(self, f: Callable[[Expr], Expr]) -> Dyadic`

**Logic:**
1. If `f` is not callable, raises `TypeError("'`f' must be callable.")`.
2. Initializes `out = Dyadic(0)`.
3. For each tuple `(a, b, c)` in `self.args`:
   - Applies the function to the measure number: `f(a)`.
   - Adds a new dyadic term `f(a) * (b | c)` to `out` (using `__add__` and `__mul__`).
4. Returns `out`.

---

## sympy/physics/vector/frame.py
Now I have the complete file read. Here is the full natural-language specification:

---

# Module-Level Preamble

## Imports

```python
from sympy.core.backend import (diff, expand, sin, cos, sympify,
                   eye, symbols, ImmutableMatrix as Matrix, MatrixBase)
from sympy import (trigsimp, solve, Symbol, Dummy)
from sympy.core.compatibility import string_types, range
from sympy.physics.vector.vector import Vector, _check_vector

__all__ = ['CoordinateSym', 'ReferenceFrame']
```

## Constants & Globals

- `__all__` — list of two strings: `'CoordinateSym'`, `'ReferenceFrame'`.
- `Vector.simp` — a class-level boolean attribute on the `Vector` class (imported from `.vector`) that controls whether trigonometric simplification is applied in methods like `variable_map`.

---

# Code Objects

## Class `CoordinateSym(Symbol)`

A subclass of `sympy.core.Symbol` representing a coordinate variable associated with a specific `ReferenceFrame` and dimension index. Instances are accessed via frame indexing (e.g., `frame[0]`, `frame['x']`). Equality is based on the pair `(frame, index)`.

### `__new__(cls, name, frame, index)`

**Signature:** `def __new__(cls, name: str, frame: ReferenceFrame, index: int)`

1. Calls `super()._sanitize(assumptions, cls)` with an empty dict to extract sympy assumptions.
2. Creates the Symbol object via `super().__xnew__(cls, name, **assumptions)`.
3. Validates `frame` by calling `_check_frame(frame)` (raises `VectorTypeError` if not a `ReferenceFrame`).
4. Validates `index`: must be in `range(0, 3)` (i.e., 0, 1, or 2); raises `ValueError("Invalid index specified")` otherwise.
5. Stores the tuple `(frame, index)` as `obj._id`.
6. Returns `obj`.

### Property `frame`

Returns `self._id[0]`, i.e., the `ReferenceFrame` this coordinate symbol belongs to.

### `__eq__(self, other)`

1. If `other` is an instance of `CoordinateSym` and `other._id == self._id`, returns `True`.
2. Otherwise returns `False`.

### `__ne__(self, other)`

Returns `not self.__eq__(other)`.

### `__hash__(self)`

Returns the hash of the tuple `(self._id[0].__hash__(), self._id[1])`, i.e., hashes based on frame identity and index.

---

## Class `ReferenceFrame(object)`

Represents a reference frame in classical mechanics with an orthonormal basis (x, y, z unit vectors), orientation relative to parent frames via direction cosine matrices (DCMs), and angular velocity/acceleration relative to other frames.

### Class Variable

- `_count` — integer class-level counter tracking the total number of `ReferenceFrame` instances created; incremented in `__init__`.

### Instance Attributes (initialized in `__init__`)

| Attribute | Type / Description |
|---|---|
| `name` | `str` — the frame's display name |
| `index` | `int` — unique creation order index from `_count` |
| `indices` | `tuple` or `list` of 3 strings — custom indices for basis vectors (default: `['x', 'y', 'z']`) |
| `str_vecs` | `list` of 3 strings — console printing representations of basis vectors |
| `pretty_vecs` | `list` of 3 Unicode strings — pretty-printing representations |
| `latex_vecs` | `list` of 3 LaTeX strings — LaTeX printing representations (overridden by `latexs` parameter) |
| `_var_dict` | `dict` — cache for variable mapping results, keyed by `(otherframe, Vector.simp)` |
| `_dcm_dict` | `dict` — stores DCMs for direct parent-child relationships only; key is child frame → value is the DCM matrix |
| `_dcm_cache` | `dict` — full cache of all pairwise DCMs between this frame and any other; key is other frame → value is the 3×3 DCM matrix |
| `_ang_vel_dict` | `dict` — angular velocity mappings; key is reference frame → value is a `Vector` |
| `_ang_acc_dict` | `dict` — angular acceleration mappings; key is reference frame → value is a `Vector` |
| `_dlist` | `list` of 3 dicts: `[self._dcm_dict, self._ang_vel_dict, self._ang_acc_dict]` |
| `_cur` | `int` — set to 0 (unused in current code) |
| `_x`, `_y`, `_z` | `Vector` objects representing the three orthonormal basis vectors of this frame |
| `varlist` | `tuple` of 3 `CoordinateSym` instances: `(self[0], self[1], self[2])` — coordinate symbols for x, y, z dimensions |

### `__init__(self, name, indices=None, latexs=None, variables=None)`

**Signature:** `def __init__(self, name, indices=None, latexs=None, variables=None)`

1. Validates `name`: must be a string; raises `TypeError` otherwise.
2. **Custom indices path** (`indices is not None`): validates that `indices` is a list/tuple of exactly 3 strings; builds `str_vecs`, `pretty_vecs`, `latex_vecs` using the custom index names (e.g., `"Name['1']"`, `"name_1"`, `"\mathbf{\hat{name}_{1}}"`).
3. **Default indices path** (`indices is None`): sets `str_vecs = ["Name.x", "Name.y", "Name.z"]`, `pretty_vecs = ["name_x", "name_y", "name_z"]`, `latex_vecs = ["\mathbf{\hat{name}_x}", ...]`, and `self.indices = ['x', 'y', 'z']`.
4. **Custom LaTeX override** (`latexs is not None`): validates that `latexs` is a list/tuple of exactly 3 strings; replaces `self.latex_vecs` with the provided values.
5. Sets `self.name = name`, initializes `_var_dict`, `_dcm_dict`, `_dcm_cache`, `_ang_vel_dict`, `_ang_acc_dict` as empty dicts, and sets `_dlist` and `_cur`.
6. Creates basis vectors: `_x = Vector([(Matrix([1,0,0]), self)])`, similarly for y and z with `[0,1,0]` and `[0,0,1]`.
7. **Variables**: if `variables is not None`, validates it as a list/tuple of 3 strings; otherwise defaults to `[name+'_x', name+'_y', name+'_z']`. Creates three `CoordinateSym` instances with these names, the frame, and indices 0/1/2 respectively, stored in `self.varlist`.
8. Increments `ReferenceFrame._count` and assigns it to `self.index`.

### `__getitem__(self, ind)`

**Signature:** `def __getitem__(self, ind)`

- If `ind` is **not a string**: if `ind < 3`, returns `self.varlist[ind]` (a `CoordinateSym`); otherwise raises `ValueError("Invalid index provided")`.
- If `ind` **is a string**: matches against `self.indices[0]`, `[1]`, or `[2]`; returns `self.x`, `self.y`, or `self.z` respectively. Raises `ValueError('Not a defined index')` if no match.

### `__iter__(self)`

Returns an iterator over `[self.x, self.y, self.z]`.

### `__str__(self)` / `__repr__`

Returns `self.name`. `__repr__` is aliased to `__str__`.

### `_dict_list(self, other, num)` (private)

**Signature:** `def _dict_list(self, other, num: int)` — where `num` indexes into `self._dlist` (0=DCM dict, 1=ang_vel dict, 2=ang_acc dict).

Finds the shortest path of frames from `self` to `other` through direct parent-child relationships stored in `_dlist[num]`. Uses a BFS-like expansion:
1. Starts with `outlist = [[self]]` and iteratively extends each path by appending neighbors found in the last frame's dict at index `num`.
2. After convergence, filters paths to keep only those ending at `other`, sorts by length, and returns the shortest path (first element).
3. Raises `ValueError('No Connecting Path found between <self.name> and <other.name>')` if no path exists.

### `_w_diff_dcm(self, otherframe)` (private)

**Signature:** `def _w_diff_dcm(self, otherframe)` — computes angular velocity by time-differentiating the DCM.

1. Imports `dynamicsymbols` from `.functions`.
2. Gets `dcm2diff = self.dcm(otherframe)`.
3. Differentiates with respect to `dynamicsymbols._t`: `diffed = dcm2diff.diff(dynamicsymbols._t)`.
4. Computes `angvelmat = diffed * dcm2diff.T` (the transpose of the DCM).
5. Extracts three components: `w1 = trigsimp(expand(angvelmat[7]))`, `w2 = trigsimp(expand(angvelmat[2]))`, `w3 = trigsimp(expand(angvelmat[3]))`.
6. Returns `-Vector([(Matrix([w1, w2, w3]), self)])` (negated angular velocity vector expressed in this frame).

### `variable_map(self, otherframe)`

**Signature:** `def variable_map(self, otherframe: ReferenceFrame) -> dict[CoordinateSym, Expr]`

Returns a dictionary mapping each of `self`'s coordinate symbols to expressions in terms of `otherframe`'s coordinates.

1. Validates `otherframe` via `_check_frame`.
2. Checks cache `(otherframe, Vector.simp)` in `self._var_dict`; returns cached result if present.
3. Computes `vars_matrix = self.dcm(otherframe) * Matrix(otherframe.varlist)` (matrix multiplication of the DCM with the other frame's coordinate symbols).
4. For each index `i` and basis vector `x` from iterating `self`: sets `mapping[self.varlist[i]]` to either `trigsimp(vars_matrix[i], method='fu')` if `Vector.simp` is True, or just `vars_matrix[i]`.
5. Caches the result in `self._var_dict[(otherframe, Vector.simp)]` and returns it.

### `ang_acc_in(self, otherframe)`

**Signature:** `def ang_acc_in(self, otherframe: ReferenceFrame) -> Vector`

Returns the angular acceleration of this frame in `otherframe`.

1. Validates `otherframe`.
2. If `otherframe` is in `self._ang_acc_dict`, returns the cached value.
3. Otherwise computes and returns `self.ang_vel_in(otherframe).dt(otherframe)` (the time derivative of angular velocity with respect to `otherframe`).

### `ang_vel_in(self, otherframe)`

**Signature:** `def ang_vel_in(self, otherframe: ReferenceFrame) -> Vector`

Returns the angular velocity of this frame in `otherframe`.

1. Validates `otherframe`.
2. Gets the path from `self` to `otherframe` via `_dict_list(otherframe, 1)` (using the angular velocity dict).
3. Initializes `outvec = Vector(0)`.
4. For each consecutive pair `(flist[i], flist[i+1])` along the path: adds `flist[i]._ang_vel_dict[flist[i + 1]]` to `outvec`.
5. Returns the accumulated vector (sum of angular velocities along the chain).

### `dcm(self, otherframe)`

**Signature:** `def dcm(self, otherframe: ReferenceFrame) -> Matrix`

Returns the 3×3 direction cosine matrix from this frame to `otherframe`, satisfying `N.xyz = N.dcm(B) * B.xyz`.

1. Validates `otherframe`.
2. If `otherframe` is in `self._dcm_cache`, returns the cached DCM.
3. Gets the path via `_dict_list(otherframe, 0)` (using the DCM dict).
4. Initializes `outdcm = eye(3)`.
5. For each consecutive pair along the path: multiplies `outdcm *= flist[i]._dcm_dict[flist[i + 1]]` (left-to-right matrix multiplication of parent-child DCMs).
6. Caches the result bidirectionally: `self._dcm_cache[otherframe] = outdcm` and `otherframe._dcm_cache[self] = outdcm.T`.
7. Returns `outdcm`.

### `orient(self, parent, rot_type, amounts, rot_order='')`

**Signature:** `def orient(self, parent: ReferenceFrame, rot_type: str, amounts, rot_order: str = '')`

Defines the orientation of this frame relative to a parent frame. Sets up DCM and angular velocity relationships bidirectionally between `self` and `parent`.

1. Validates `parent` via `_check_frame`.
2. **Amounts normalization**: if `rot_type == 'DCM'`, validates that `amounts` is a `MatrixBase`; otherwise converts each element of `amounts` to a list and sympifies non-Vector elements.
3. Defines inner helper `_rot(axis, angle)` returning the 3×3 DCM for a simple rotation about axis 1 (x), 2 (y), or 3 (z) by the given angle using sin/cos.
4. Normalizes `rot_order`: converts to uppercase, replaces X→1, Y→2, Z→3. Validates against approved orders: `'123', '231', '312', '132', '213', '321', '121', '131', '212', '232', '313', '323', ''`. Raises `TypeError` if invalid.
5. Normalizes `rot_type` to uppercase.
6. **Rotation type handling** — computes `parent_orient` (the DCM from parent to this frame):

   - **'AXIS'**: Validates no rotation order, amounts is a list/tuple of length 2. Extracts `theta = amounts[0]`, `axis = amounts[1]`. Checks axis is time-invariant (`axis.dt(parent) == 0`). Expresses axis in parent frame and normalizes to unit vector with components `[axis_x, axis_y, axis_z]`. Computes Rodrigues' rotation formula: `(I - n*n^T)*cos(θ) + [n]_×*sin(θ) + n*n^T`, where `[n]_×` is the skew-symmetric cross-product matrix.

   - **'QUATERNION'**: Validates no rotation order, amounts has length 4. Unpacks `q0, q1, q2, q3`. Constructs DCM from quaternion components using the standard quaternion-to-rotation-matrix formula (9-element symmetric matrix).

   - **'BODY'**: Validates amounts and rot_order each have length 3. Parses axis digits a1, a2, a3. Computes `parent_orient = _rot(a1, amounts[0]) * _rot(a2, amounts[1]) * _rot(a3, amounts[2])` (right-to-left body-fixed rotations).

   - **'SPACE'**: Same validation as Body. Computes `parent_orient = _rot(a3, amounts[2]) * _rot(a2, amounts[1]) * _rot(a1, amounts[0])` (left-to-right space-fixed rotations — reversed order from Body).

   - **'DCM'**: Sets `parent_orient = amounts` directly.

7. **Cache reset**: Iterates over all frames in `self._dcm_cache.keys()`. Collects frames that are keys in `self._dcm_dict` into `dcm_dict_del`, and all cached frame references into `dcm_cache_del`. Deletes these entries from the respective dicts/caches on both sides.
8. **Store DCM**: Resets `self._dcm_dict = self._dlist[0] = {}`. Updates: `self._dcm_dict[parent] = parent_orient.T` and `parent._dcm_dict[self] = parent_orient`.
9. **Update cache**: Resets `self._dcm_cache = {}`, then populates with the same direct relationship: `self._dcm_cache[parent] = parent_orient.T`, `parent._dcm_cache[self] = parent_orient`.
10. **Angular velocity computation** — computes `wvec` (angular velocity of this frame in parent):

    - **'QUATERNION'**: Imports `dynamicsymbols._t`. Differentiates q0-q3 w.r.t. time to get q0d-q3d. Computes angular velocity components:
      ```
      w1 = 2*(q1d*q0 + q2d*q3 - q3d*q2 - q0d*q1)
      w2 = 2*(q2d*q0 + q3d*q1 - q1d*q3 - q0d*q2)
      w3 = 2*(q3d*q0 + q1d*q2 - q2d*q1 - q0d*q3)
      ```
      `wvec = Vector([(Matrix([w1, w2, w3]), self)])`.

    - **'AXIS'**: Differentiates the angle: `thetad = amounts[0].diff(dynamicsymbols._t)`. Computes `wvec = thetad * amounts[1].express(parent).normalize()`.

    - **'DCM'**: Calls `self._w_diff_dcm(parent)` (time-differentiate DCM method).

    - **Body/Space** ('BODY', 'SPACE'): Imports `CoercionFailed` and `kinematic_equations`. Unpacks `q1, q2, q3 = amounts`. Creates dummy symbols `u1, u2, u3`. Calls `kinematic_equations([u1,u2,u3], [q1,q2,q3], rot_type, rot_order)` to get kinematic differential equations. Expands them and solves for `[u1, u2, u3]` in terms of time derivatives of q's. Constructs `wvec = u1*self.x + u2*self.y + u3*self.z`. If `CoercionFailed` or `AssertionError` is raised, falls back to `_w_diff_dcm(parent)`.

11. Stores angular velocity bidirectionally: `self._ang_vel_dict[parent] = wvec`, `parent._ang_vel_dict[self] = -wvec`.
12. Clears variable map cache: `self._var_dict = {}`.

### `orientnew(self, newname, rot_type, amounts, rot_order='', variables=None, indices=None, latexs=None)`

**Signature:** `def orientnew(self, newname: str, rot_type: str, amounts, rot_order: str = '', variables=None, indices=None, latexs=None) -> ReferenceFrame`

Creates a **new** `ReferenceFrame` oriented relative to this frame (self is the parent).

1. Creates a new instance via `self.__class__(newname, variables, indices, latexs)` — note: positional args map as `(name=newname, indices=variables, latexs=indices)`.
2. Calls `newframe.orient(self, rot_type, amounts, rot_order)` to set up the orientation relationship.
3. Returns `newframe`.

### `set_ang_acc(self, otherframe, value)`

**Signature:** `def set_ang_acc(self, otherframe: ReferenceFrame, value: Vector)`

Defines the angular acceleration of this frame in `otherframe`.

1. If `value == 0`, replaces with `Vector(0)`.
2. Validates via `_check_vector(value)` and `_check_frame(otherframe)`.
3. Stores bidirectionally: `self._ang_acc_dict[otherframe] = value` and `otherframe._ang_acc_dict[self] = -value`.

### `set_ang_vel(self, otherframe, value)`

**Signature:** `def set_ang_vel(self, otherframe: ReferenceFrame, value: Vector)`

Defines the angular velocity of this frame in `otherframe`.

1. If `value == 0`, replaces with `Vector(0)`.
2. Validates via `_check_vector(value)` and `_check_frame(otherframe)`.
3. Stores bidirectionally: `self._ang_vel_dict[otherframe] = value` and `otherframe._ang_vel_dict[self] = -value`.

### Property `x`, `y`, `z`

Each returns the corresponding basis `Vector`: `self._x`, `self._y`, `self._z` respectively. These are unit vectors expressed as `Vector([(Matrix([1,0,0]), self)])` etc.

### `partial_velocity(self, frame, *gen_speeds)`

**Signature:** `def partial_velocity(self, frame: ReferenceFrame, *gen_speeds) -> Vector | tuple[Vector]`

Returns the partial angular velocities of this frame in the given frame with respect to one or more generalized speeds.

1. For each `speed` in `gen_speeds`: computes `self.ang_vel_in(frame).diff(speed, frame, var_in_dcm=False)` — the partial derivative of the angular velocity w.r.t. that speed (with DCM variables held constant).
2. If exactly one generalized speed is provided, returns a single `Vector`.
3. Otherwise returns a `tuple` of `Vector`s corresponding to each generalized speed in order.

---

## Function `_check_frame(other)`

**Signature:** `def _check_frame(other) -> None`

1. Imports `VectorTypeError` from `.vector`.
2. If `other` is not an instance of `ReferenceFrame`, raises `VectorTypeError(other, ReferenceFrame('A'))`.
3. Otherwise returns silently (no return value).

## sympy/physics/vector/vector.py
Now I have the complete file read (all 710 lines). Here is the full natural-language specification:

---

# Natural-Language Specification of `sympy/physics/vector/vector.py`

## 1. Module-Level Preamble

### Imports

```python
from sympy.core.backend import (S, sympify, expand, sqrt, Add, zeros,
    ImmutableMatrix as Matrix)
from sympy import trigsimp
from sympy.core.compatibility import unicode
from sympy.utilities.misc import filldedent
```

### Constants & Globals

- **`__all__`** — `['Vector']` (the sole public export).
- **`Vector.simp`** — Class-level boolean attribute, defaulting to `False`. When set to `True`, methods that produce trigonometric results will apply `trigsimp(..., recursive=True)` before returning.

---

## 2. Code Objects

### Class `Vector(object)`

A class representing mathematical vectors as a collection of (measure-number, reference-frame) pairs stored in the instance attribute `self.args`. Each element of `self.args` is a tuple `(v, k)` where:
- `v` is an `ImmutableMatrix` of shape `(3, 1)` containing the three scalar components along that frame's basis vectors.
- `k` is a `ReferenceFrame` object (the frame to which those components belong).

The internal representation merges coefficients for duplicate frames and discards any component whose measure number equals `[0, 0, 0]`.

#### `__init__(self, inlist)`

**Signature:** `(self, inlist)` — `inlist` is either the integer `0`, a list of tuples `(scalar, ReferenceFrame)`, or a dict mapping `ReferenceFrame → ImmutableMatrix(3×1)`.

**Logic:**
1. Initialize `self.args = []`.
2. If `inlist == 0`, replace with `[]`.
3. If `inlist` is a `dict`, use it directly as `d`; otherwise, build `d` by iterating over `(scalar, frame)` pairs in the list and accumulating: for each pair, if its frame key already exists in `d`, add the scalar to the existing matrix; else set `d[frame] = scalar`.
4. For each `(k, v)` in `d.items()`: if `v != Matrix([0, 0, 0])`, append `(v, k)` to `self.args`.

**Return:** None (constructor).

---

#### `__hash__(self)`

Returns `hash(tuple(self.args))`.

---

#### `__add__(self, other)`

**Signature:** `(self, other)` — `other` must be a `Vector`; validated by `_check_vector(other)`.

**Logic:** Returns `Vector(self.args + other.args)`, concatenating the component lists. The `Vector` constructor will merge duplicate frames and discard zero components.

**Return:** A new `Vector`.

---

#### `__and__(self, other)` — Dot product (`&`)

**Signature:** `(self, other)` — `other` must be a `Vector`; validated by `_check_vector(other)`. If `other` is a `Dyadic`, returns `NotImplemented`.

**Logic:**
1. Initialize `out = S(0)`.
2. For each component `(v1_scalar, v1_frame)` in `self.args` and each `(v2_scalar, v2_frame)` in `other.args`:
   - Compute the contribution: `(v2_scalar.T * v2_frame.dcm(v1_frame) * v1_scalar)[0]`, where `dcm` is the direction-cosine matrix from `v1_frame` to `v2_frame`. This transforms `v1_scalar` into `v2_frame`'s basis, then takes the element-wise product with `v2_scalar` and sums.
   - Add to `out`.
3. If `Vector.simp`, return `trigsimp(sympify(out), recursive=True)`; else return `sympify(out)`.

**Return:** A scalar (SymPy number/expression).

---

#### `__div__(self, other)` / `__truediv__`

**Signature:** `(self, other)` — `other` is any sympifyable scalar.

**Logic:** Returns `self.__mul__(sympify(1) / other)`.

**Return:** A new `Vector` scaled by `1/other`.

---

#### `__eq__(self, other)`

**Signature:** `(self, other)` — Tests equality of two vectors.

**Logic:**
1. If `other == 0`, replace with `Vector(0)`.
2. Try `_check_vector(other)`. On `TypeError`, return `False`.
3. If both `self.args` and `other.args` are empty, return `True`.
4. If exactly one is empty, return `False`.
5. Take the first frame from `self.args[0][1]`; for each basis vector `v` in that frame: if `expand((self - other) & v) != 0`, return `False`.
6. Return `True`.

**Return:** Boolean.

---

#### `__mul__(self, other)`

**Signature:** `(self, other)` — `other` is any sympifyable scalar.

**Logic:**
1. Copy `self.args` into `newlist`.
2. For each element in `newlist`, multiply its measure-number matrix by `sympify(other)`: `newlist[i] = (sympify(other) * newlist[i][0], newlist[i][1])`.
3. Return `Vector(newlist)`.

**Return:** A new `Vector` scaled by `other`.

---

#### `__ne__(self, other)`

Returns `not self.__eq__(other)`.

---

#### `__neg__(self)`

Returns `self * -1`.

---

#### `__or__(self, other)` — Outer product (`|`)

**Signature:** `(self, other)` — `other` must be a `Vector`; validated by `_check_vector(other)`. Returns a `Dyadic`.

**Logic:**
1. Initialize `ol = Dyadic(0)`.
2. For each component `(v_scalar, v_frame)` in `self.args` and each `(v2_scalar, v2_frame)` in `other.args`:
   - Expand both measure-number matrices into their 3×1 components (`[0][0]`, `[0][1]`, `[0][2]`).
   - For all 9 combinations of basis-vector pairs from the two frames (x⊗x, x⊗y, x⊗z, y⊗x, …, z⊗z), create a `Dyadic` entry: `(v_scalar[j1] * v2_scalar[j2], v_frame.basis_j1, v2_frame.basis_j2)` and add to `ol`.
3. Return `ol`.

**Return:** A `Dyadic` (rank-2 tensor).

---

#### `_latex(self, printer=None)`

Generates LaTeX string representation of the vector.

**Logic:**
1. If `self.args` is empty, return `"0"`.
2. For each component `(v_scalar, v_frame)` in `self.args`, iterate over basis indices 0, 1, 2:
   - If coefficient `[j] == 1`: append `' + ' + frame.latex_vecs[j]`.
   - If coefficient `[j] == -1`: append `' - ' + frame.latex_vecs[j]`.
   - If coefficient `[j] != 0` and not ±1: format the coefficient via `VectorLatexPrinter().doprint(...)`, wrap in parentheses if it is an `Add`; strip leading `-` and prepend `' - '` (else `' + '`); append.
3. Join all parts; strip leading `' + '` or `' '` prefix.

**Return:** LaTeX string.

---

#### `_pretty(self, printer=None)`

Generates pretty-printed text representation of the vector using `sympy.printing.pretty.stringpict.prettyForm`.

**Logic:**
1. Returns a `Fake` object whose `render(*args, **kwargs)` method:
   - If `self.args` is empty, returns `"0"`.
   - For each component and basis index 0–2:
     - Coefficient == 1: print the frame's pretty vector name directly.
     - Coefficient == -1: print the frame's pretty vector name with a leading minus sign (using `prettyForm.left(" - ")` and binding).
     - Coefficient != 0, ±1: if it is an `Add`, wrap in parentheses; otherwise print normally; then place the frame's pretty vector name to its right.
   - Sum all `prettyForm` objects with `__add__`; render and strip trailing whitespace from each line.

**Return:** A `Fake` object with a `render` method producing the pretty-printed string.

---

#### `__ror__(self, other)` — Outer product (reverse)

**Signature:** `(self, other)` — `other` must be a `Vector`; validated by `_check_vector(other)`. Returns a `Dyadic`.

**Logic:** Identical to `__or__` but iterates `other.args` in the outer loop and `self.args` in the inner loop (outer product is not commutative, so order matters).

**Return:** A `Dyadic`.

---

#### `__rsub__(self, other)`

Returns `(-1 * self) + other`.

---

#### `__str__(self, printer=None, order=True)`

Generates string representation of the vector.

**Logic:**
1. If `order` is falsy or there is exactly 1 component: use `list(self.args)` as-is.
2. If empty: return `"0"`.
3. Otherwise: build a dict mapping frame → summed measure-number, sort frames by their `index` attribute, rebuild ordered list.
4. For each component and basis index 0–2:
   - Coefficient `[j] == 1`: append `' + ' + frame.str_vecs[j]`.
   - Coefficient `[j] == -1`: append `' - ' + frame.str_vecs[j]`.
   - Coefficient `[j] != 0, ±1`: format via `VectorStrPrinter().doprint(...)`, wrap in parentheses if `Add`; strip leading `-` and prepend `' - '` (else `' + '`); append with `'*'` separator between coefficient and basis name.
5. Join all parts; strip leading `' + '` or `' '`.

**Return:** String representation.

---

#### `__sub__(self, other)`

Returns `self.__add__(other * -1)`.

---

#### `__xor__(self, other)` — Cross product (`^`)

**Signature:** `(self, other)` — `other` must be a `Vector`; validated by `_check_vector(other)`. If `other` is a `Dyadic`, returns `NotImplemented`.

**Logic:**
1. If `other.args` is empty, return `Vector(0)`.
2. Define inner helper `_det(mat)` computing the determinant of a 3×3 list-of-lists using the standard formula: `a(ei − fh) − b(di − fg) + c(dh − eg)`.
3. For each component `(v_scalar, v_frame)` in `other.args`:
   - Extract basis vectors `tempx = v_frame.x`, `tempy = v_frame.y`, `tempz = v_frame.z`.
   - Build a 3×3 matrix:
     ```
     [[tempx, tempy, tempz],
      [self & tempx, self & tempy, self & tempz],
      [Vector([ar[i]]) & tempx, Vector([ar[i]]) & tempy, Vector([ar[i]]) & tempz]]
     ```
   - Compute `_det(tempm)` and extend `outlist` with the result's `.args`.
4. Return `Vector(outlist)`.

**Return:** A new `Vector` (the cross product).

---

#### Class-level aliases

```python
_sympystr = __str__
_sympyrepr = _sympystr
__repr__ = __str__
__radd__ = __add__
__rand__ = __and__
__rmul__ = __mul__
```

---

#### `separate(self)`

Returns a dict mapping each `ReferenceFrame` in `self.args` to the corresponding single-component `Vector`. For each `(scalar, frame)` in `self.args`, sets `components[frame] = Vector([(scalar, frame)])`.

**Return:** `dict[ReferenceFrame, Vector]`.

---

#### `dot(self, other)`

Returns `self & other`. Docstring copied from `__and__.__doc__`.

---

#### `cross(self, other)`

Returns `self ^ other`. Docstring copied from `__xor__.__doc__`.

---

#### `outer(self, other)`

Returns `self | other`. Docstring copied from `__or__.__doc__`.

---

#### `diff(self, var, frame, var_in_dcm=True)`

**Signature:** `(self, var, frame, var_in_dcm=True)` — Computes the partial derivative of the vector with respect to a symbol `var`, taken in reference frame `frame`.

**Logic:**
1. Sympify `var`; validate `frame` via `_check_frame(frame)`.
2. For each component `(measure_number, component_frame)` in `self.args`:
   - If `component_frame == frame`: append `(measure_number.diff(var), frame)` to `inlist`.
   - Else if `not var_in_dcm` or `frame.dcm(component_frame).diff(var) == zeros(3, 3)` (the DCM does not depend on `var`): append `(measure_number.diff(var), component_frame)`.
   - Else: re-express the single-component vector in `frame`, differentiate its measure number with respect to `var`, then re-express back into `component_frame`; extend `inlist` with the result's `.args`.
3. Return `Vector(inlist)`.

**Return:** A new `Vector` (the partial derivative).

---

#### `express(self, otherframe, variables=False)`

Delegates to the global `express(self, otherframe, variables=variables)` from `sympy.physics.vector`. Returns an equivalent vector expressed in `otherframe`. If `variables=True`, coordinate symbols are also re-expressed.

**Return:** A new `Vector`.

---

#### `to_matrix(self, reference_frame)`

**Signature:** `(self, reference_frame)` — Returns the 3×1 matrix of components along each basis vector of `reference_frame`.

**Logic:** Returns `Matrix([self.dot(unit_vec) for unit_vec in reference_frame]).reshape(3, 1)`, where iterating over a `ReferenceFrame` yields its three basis vectors.

**Return:** `ImmutableMatrix` of shape `(3, 1)`.

---

#### `doit(self, **hints)`

Calls `.doit(**hints)` on each measure-number matrix component via `applyfunc(lambda x: x.doit(**hints))`, then returns the resulting `Vector`.

**Return:** A new `Vector`.

---

#### `dt(self, otherframe)`

Delegates to the global `time_derivative(self, otherframe)`. Returns the time derivative of this vector as taken in frame `otherframe`.

**Return:** A new `Vector`.

---

#### `simplify(self)`

For each component `(scalar, frame)` in `self.args`, replaces the measure number with `scalar.simplify()`. Returns the resulting `Vector`.

**Return:** A new simplified `Vector`.

---

#### `subs(self, *args, **kwargs)`

For each component `(scalar, frame)` in `self.args`, replaces the measure number with `scalar.subs(*args, **kwargs)`. Returns the resulting `Vector`.

**Return:** A new `Vector` with substitutions applied.

---

#### `magnitude(self)`

Returns `sqrt(self & self)`, i.e., the Euclidean norm of the vector.

**Return:** SymPy expression (square root of dot product with itself).

---

#### `normalize(self)`

Returns `Vector(self.args + []) / self.magnitude()`. The `self.args + []` creates a shallow copy; dividing by magnitude normalizes to unit length.

**Return:** A new `Vector` of unit magnitude, codirectional with `self`.

---

#### `applyfunc(self, f)`

**Signature:** `(self, f)` — `f` must be callable.

**Logic:**
1. If `not callable(f)`, raise `TypeError("f must be callable.")`.
2. For each component `(scalar, frame)` in `self.args`, replace the measure number with `scalar.applyfunc(f)`.
3. Return the resulting `Vector`.

**Return:** A new `Vector` with function `f` applied element-wise to each measure-number matrix.

---

### Class `VectorTypeError(TypeError)`

A custom exception subclass of `TypeError`.

#### `__init__(self, other, want)`

Constructs an error message: `"Expected an instance of <type(want)>, but received object '<other>' of <type(other)>."` (wrapped via `filldedent`). Calls `super().__init__(msg)`.

---

### Function `_check_vector(other)`

**Signature:** `(other)` — Validates that `other` is a `Vector` instance.

**Logic:** If `not isinstance(other, Vector)`, raise `TypeError('A Vector must be supplied')`; else return `other`.

**Return:** The validated `Vector`, or raises `TypeError`.

## sympy/polys/agca/modules.py
Now I have the complete file. Let me write the specification.

---

# Module Specification: `sympy/polys/agca/modules.py`

## 1. Module-Level Preamble

### Imports
```python
from __future__ import print_function, division
from copy import copy
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.orderings import ProductOrder, monomial_key
from sympy.polys.domains.field import Field
from sympy.polys.agca.ideals import Ideal
from sympy.core.compatibility import iterable, reduce, range
```

### Module-Level Constants / Lambdas
- `_subs0 = lambda x: x[0]` — returns the first element of a sequence.
- `_subs1 = lambda x: x[1:]` — returns all elements except the first.

---

## 2. Code Objects

### Class `Module(object)`

**Purpose:** Abstract base class for modules over rings. Not instantiated directly; use ring constructors instead (e.g., `ring.free_module(n)`).

**Attributes:**
- `self.ring` — the containing ring, set in `__init__`.
- `self.dtype` — type of elements (set by subclasses).

**Methods:**

#### `__init__(self, ring)`
Sets `self.ring = ring`.

#### `convert(self, elem, M=None)`
Converts `elem` into the internal representation. If `M` is provided and not None, it should be a module containing `elem`. Raises `CoercionFailed` if `elem` is not an instance of `self.dtype`; otherwise returns `elem` unchanged.

#### `submodule(self, *gens)`
Raises `NotImplementedError`. Subclasses override to generate submodules.

#### `quotient_module(self, other)`
Raises `NotImplementedError`. Subclasses override to form quotient modules.

#### `__div__(self, e)` / `__truediv__ = __div__`
If `e` is not a `Module`, wraps it as `self.submodule(*e)`. Then returns `self.quotient_module(e)`. Implements the `/` operator for forming quotient modules.

#### `contains(self, elem)`
Returns `True` if `elem` can be converted into this module (by calling `self.convert(elem)`), catching `CoercionFailed` and returning `False`.

#### `__contains__(self, elem)`
Delegates to `self.contains(elem)`.

#### `subset(self, other)`
Returns `True` if every element of the iterable `other` is contained in this module (via `all(self.contains(x) for x in other)`).

#### `__eq__(self, other)`
Returns `self.is_submodule(other) and other.is_submodule(self)`.

#### `__ne__(self, other)`
Returns `not (self == other)`.

#### `is_zero(self)`
Raises `NotImplementedError`. Returns True if the module is zero.

#### `is_submodule(self, other)`
Raises `NotImplementedError`. Returns True if `other` is a submodule of `self`.

#### `multiply_ideal(self, other)`
Raises `NotImplementedError`. Multiplies this module by ideal `other`.

#### `__mul__(self, e)` / `__rmul__ = __mul__`
If `e` is not an `Ideal`, attempts to wrap it as `self.ring.ideal(e)`. If that fails with `CoercionFailed` or `NotImplementedError`, returns `NotImplemented`. Otherwise calls and returns `self.multiply_ideal(e)`.

#### `identity_hom(self)`
Raises `NotImplementedError`. Returns the identity homomorphism on this module.

---

### Class `ModuleElement(object)`

**Purpose:** Base class for module element wrappers. Wraps primitive data types as module elements, stores a reference to the containing module, and implements arithmetic operators.

**Attributes:**
- `self.module` — the containing module (set in `__init__`).
- `self.data` — internal data representation (set in `__init__`).

**Methods:**

#### `__init__(self, module, data)`
Sets `self.module = module`, `self.data = data`.

#### `add(self, d1, d2)`
Returns `d1 + d2`. Subclasses override for custom addition.

#### `mul(self, m, d)`
Returns `m * d` (module data multiplied by coefficient). Subclasses override.

#### `div(self, m, d)`
Returns `m / d` (module data divided by coefficient). Subclasses override.

#### `eq(self, d1, d2)`
Returns `d1 == d2`. Subclasses override for custom equality.

#### `__add__(self, om)`
If `om` is not of the same class and from the same module, attempts to convert it via `self.module.convert(om)`, catching `CoercionFailed` → returns `NotImplemented`. Otherwise returns a new instance: `self.__class__(self.module, self.add(self.data, om.data))`.

#### `__radd__ = __add__`

#### `__neg__(self)`
Returns `self.__class__(self.module, self.mul(self.data, self.module.ring.convert(-1)))`.

#### `__sub__(self, om)`
If `om` is not of the same class and from the same module, attempts conversion via `self.module.convert(om)`, catching `CoercionFailed` → returns `NotImplemented`. Otherwise returns `self.__add__(-om)`.

#### `__rsub__(self, om)`
Returns `(-self).__add__(om)`.

#### `__mul__(self, o)`
If `o` is not an instance of `self.module.ring.dtype`, attempts conversion via `self.module.ring.convert(o)`, catching `CoercionFailed` → returns `NotImplemented`. Otherwise returns `self.__class__(self.module, self.mul(self.data, o))`.

#### `__rmul__ = __mul__`

#### `__div__(self, o)` / `__truediv__ = __div__`
If `o` is not an instance of `self.module.ring.dtype`, attempts conversion via `self.module.ring.convert(o)`, catching `CoercionFailed` → returns `NotImplemented`. Otherwise returns `self.__class__(self.module, self.div(self.data, o))`.

#### `__eq__(self, om)`
If `om` is not of the same class and from the same module, attempts conversion via `self.module.convert(om)`, catching `CoercionFailed` → returns `False`. Otherwise returns `self.eq(self.data, om.data)`.

#### `__ne__(self, om)`
Returns `not self.__eq__(om)`.

---

### Class `FreeModuleElement(ModuleElement)`

**Purpose:** Element of a free module. Data stored as a tuple.

**Inherits from:** `ModuleElement`

**Methods (overrides):**

#### `add(self, d1, d2)`
Returns `tuple(x + y for x, y in zip(d1, d2))`.

#### `mul(self, d, p)`
Returns `tuple(x * p for x in d)`.

#### `div(self, d, p)`
Returns `tuple(x / p for x in d)`.

#### `__repr__(self)`
From `sympy import sstr`; returns `'[' + ', '.join(sstr(x) for x in self.data) + ']'`.

#### `__iter__(self)`
Delegates to `self.data.__iter__()`.

#### `__getitem__(self, idx)`
Returns `self.data[idx]`.

---

### Class `FreeModule(Module)`

**Purpose:** Abstract base class for free modules. Not instantiated directly; use ring constructors.

**Attributes:**
- `self.dtype = FreeModuleElement` (class attribute).
- `self.ring` — from parent.
- `self.rank` — rank of the free module, set in `__init__`.

#### `__init__(self, ring, rank)`
Calls `Module.__init__(self, ring)`, then sets `self.rank = rank`.

#### `__repr__(self)`
Returns `repr(self.ring) + "**" + repr(self.rank)`.

#### `is_submodule(self, other)`
If `other` is a `SubModule`, returns `other.container == self`. If `other` is a `FreeModule`, returns `other.ring == self.ring and other.rank == self.rank`. Otherwise returns `False`.

#### `convert(self, elem, M=None)`
- If `elem` is a `FreeModuleElement`: if `elem.module is self`, return it; if ranks differ, raise `CoercionFailed`; otherwise convert each component via `self.ring.convert(x, elem.module.ring)` and wrap in new `FreeModuleElement(self, tuple(...))`.
- If `iterable(elem)`: converts each element via `self.ring.convert(x)`, checks length equals `self.rank`, raises `CoercionFailed` if not; returns `FreeModuleElement(self, tpl)`.
- If `elem is 0` (identity comparison): returns `FreeModuleElement(self, tuple(self.ring.convert(0) for _ in range(self.rank)))`.
- Otherwise: raises `CoercionFailed`.

#### `is_zero(self)`
Returns `self.rank == 0`.

#### `basis(self)`
From `sympy.matrices import eye`; creates identity matrix of size `self.rank`, returns tuple of converted rows: `tuple(self.convert(M.row(i)) for i in range(self.rank))`.

#### `quotient_module(self, submodule)`
Returns `QuotientModule(self.ring, self, submodule)`.

#### `multiply_ideal(self, other)`
Returns `self.submodule(*self.basis()).multiply_ideal(other)`.

#### `identity_hom(self)`
From `sympy.polys.agca.homomorphisms import homomorphism`; returns `homomorphism(self, self, self.basis())`.

---

### Class `FreeModulePolyRing(FreeModule)`

**Purpose:** Free module over a generalized polynomial ring. Not instantiated directly; use ring constructors.

**Inherits from:** `FreeModule`

#### `__init__(self, ring, rank)`
Calls `FreeModule.__init__(self, ring, rank)`. Imports `PolynomialRingBase` from `sympy.polys.domains.old_polynomialring`; raises `NotImplementedError` if `ring` is not a `PolynomialRingBase`. Raises `NotImplementedError` if `ring.dom` is not a `Field`.

#### `submodule(self, *gens, **opts)`
Returns `SubModulePolyRing(gens, self, **opts)`.

---

### Class `FreeModuleQuotientRing(FreeModule)`

**Purpose:** Free module over a quotient ring. Not instantiated directly; use ring constructors.

**Inherits from:** `FreeModule`

**Attributes:**
- `self.quot` — the quotient module `F / (I * F)`, where `F = self.ring.ring.free_module(self.rank)` and `I` is `self.ring.base_ideal`. Set in `__init__`.

#### `__init__(self, ring, rank)`
Calls `FreeModule.__init__(self, ring, rank)`. Imports `QuotientRing`; raises `NotImplementedError` if `ring` is not a `QuotientRing`. Creates `F = self.ring.ring.free_module(self.rank)`, sets `self.quot = F / (self.ring.base_ideal * F)`.

#### `__repr__(self)`
Returns `"(" + repr(self.ring) + ")" + "**" + repr(self.rank)`.

#### `submodule(self, *gens, **opts)`
Returns `SubModuleQuotientRing(gens, self, **opts)`.

#### `lift(self, elem)`
Lifts element of this module to the quotient module `self.quot`. Returns `self.quot.convert([x.data for x in elem])`.

#### `unlift(self, elem)`
Pushes down an element from `self.quot` back to self (undoes `lift`). Returns `self.convert(elem.data)`.

---

### Class `SubModule(Module)`

**Purpose:** Base class for submodules of free modules.

**Attributes:**
- `self.ring` — from parent, set in `__init__`.
- `self.gens` — tuple of generators (converted via container), set in `__init__`.
- `self.container` — the containing module, set in `__init__`.
- `self.rank` — rank of the container, set in `__init__`.
- `self.dtype` — from container, set in `__init__`.

#### `__init__(self, gens, container)`
Calls `Module.__init__(self, container.ring)`. Sets `self.gens = tuple(container.convert(x) for x in gens)`, `self.container = container`, `self.rank = container.rank`, `self.ring = container.ring`, `self.dtype = container.dtype`.

#### `__repr__(self)`
Returns `'<' + ', '.join(repr(x) for x in self.gens) + '>'`.

#### `_contains(self, other)`
Implementation of containment. `other` is guaranteed to be a `FreeModuleElement`. Raises `NotImplementedError`. Subclasses override.

#### `_syzygies(self)`
Computes syzygies wrt generators. Raises `NotImplementedError`. Subclasses override.

#### `_in_terms_of_generators(self, e)`
Expresses element in terms of generators. Raises `NotImplementedError`. Subclasses override.

#### `convert(self, elem, M=None)`
If `elem` is already a container dtype and `elem.module is self`, returns it unchanged. Otherwise copies the converted result from `self.container.convert(elem, M)`, sets `r.module = self`, checks containment via `self._contains(r)`, raises `CoercionFailed` if not contained; otherwise returns `r`.

#### `_intersect(self, other, **options)`
Implementation of intersection (other is a submodule of the same free module). Raises `NotImplementedError`. Subclasses override.

#### `_module_quotient(self, other, **options)`
Implementation of quotient ideal `{f ∈ R | f·N ⊂ M}`. Raises `NotImplementedError`. Subclasses override.

#### `intersect(self, other, **options)`
If `other` is not a `SubModule`, raises `TypeError`. If containers differ, raises `ValueError`. Returns `self._intersect(other, **options)`. Optionally returns `(res, rela, relb)` when `relations=True`.

#### `module_quotient(self, other, **options)`
If `other` is not a `SubModule`, raises `TypeError`. If containers differ, raises `ValueError`. Returns `self._module_quotient(other, **options)`. Optionally returns `(res, rel)` when `relations=True` and `other` is principal.

#### `union(self, other)`
If `other` is not a `SubModule`, raises `TypeError`. If containers differ, raises `ValueError`. Returns `self.__class__(self.gens + other.gens, self.container)`.

#### `is_zero(self)`
Returns `all(x == 0 for x in self.gens)`.

#### `submodule(self, *gens)`
If the new generators are not a subset of this module (via `self.subset(gens)`), raises `ValueError`. Returns `self.__class__(gens, self.container)`.

#### `is_full_module(self)`
Returns `all(self.contains(x) for x in self.container.basis())`.

#### `is_submodule(self, other)`
If `other` is a `SubModule`, returns `self.container == other.container and all(self.contains(x) for x in other.gens)`. If `other` is a `FreeModule` or `QuotientModule`, returns `self.container == other and self.is_full_module()`. Otherwise returns `False`.

#### `syzygy_module(self, **opts)`
Creates free module `F = self.ring.free_module(len(self.gens))`. Calls `_syzygies()` to get syzygy vectors, filters out zero elements (via `F.convert(x) != 0`), and returns `F.submodule(*filtered_gens, **opts)`.

#### `in_terms_of_generators(self, e)`
Attempts `e = self.convert(e)`, raising `ValueError` on `CoercionFailed`. Returns `self._in_terms_of_generators(e)`.

#### `reduce_element(self, x)`
Returns `x` unchanged (no-op base implementation). Subclasses override.

#### `quotient_module(self, other, **opts)`
If `not self.is_submodule(other)`, raises `ValueError`. Returns `SubQuotientModule(self.gens, self.container.quotient_module(other), **opts)`.

#### `__add__(self, oth)` / `__radd__ = __add__`
Returns `self.container.quotient_module(self).convert(oth)`. This implements the `+` operator to produce a subquotient element.

#### `multiply_ideal(self, I)`
Returns `self.submodule(*[x*g for [x] in I._module.gens for g in self.gens])`. Multiplies each generator by each ideal generator.

#### `inclusion_hom(self)`
Returns `self.container.identity_hom().restrict_domain(self)`. The natural map from this submodule to its container.

#### `identity_hom(self)`
Returns `self.container.identity_hom().restrict_domain(self).restrict_codomain(self)`. The identity homomorphism on this submodule.

---

### Class `SubQuotientModule(SubModule)`

**Purpose:** Submodule of a quotient module (equivalently, quotient of a submodule). Not instantiated directly; use constructing methods.

**Attributes:**
- `self.killed_module` — the submodule used to form the quotient, set in `__init__`.
- `self.base` — constructed as `self.container.base.submodule(*[x.data for x in self.gens], **opts).union(self.killed_module)`, set in `__init__`.

#### `__init__(self, gens, container, **opts)`
Calls `SubModule.__init__(self, gens, container)`. Sets `self.killed_module = self.container.killed_module`. Sets `self.base` as described above.

#### `_contains(self, elem)`
Returns `self.base.contains(elem.data)`.

#### `_syzygies(self)`
Computes syzygies by projecting the base's syzygies: returns `[X[:len(self.gens)] for X in self.base._syzygies()]`. The algorithm lifts to a larger free module and projects.

#### `_in_terms_of_generators(self, e)`
Returns `self.base._in_terms_of_generators(e.data)[:len(self.gens)]`.

#### `is_full_module(self)`
Returns `self.base.is_full_module()`.

#### `quotient_hom(self)`
Returns `self.base.identity_hom().quotient_codomain(self.killed_module)`. The natural map from base to self.

---

### Class `ModuleOrder(ProductOrder)`

**Purpose:** A product monomial order with a zeroth term as module index, used for elimination orders in syzygy/intersection computations.

**Inherits from:** `ProductOrder`

#### `__init__(self, o1, o2, TOP)`
If `TOP` is True: calls `ProductOrder.__init__(self, (o2, _subs1), (o1, _subs0))`. If `TOP` is False: calls `ProductOrder.__init__(self, (o1, _subs0), (o2, _subs1))`.

---

### Class `SubModulePolyRing(SubModule)`

**Purpose:** Submodule of a free module over a generalized polynomial ring. Uses Gröbner basis computations for containment, syzygies, intersections, and quotients.

**Attributes:**
- `self.order` — monomial order (a `ModuleOrder` instance), set in `__init__`.
- `self._gb` — cached Gröbner basis (None initially).
- `self._gbe` — cached extended Gröbner basis relations (None initially).

#### `__init__(self, gens, container, order="lex", TOP=True)`
Calls `SubModule.__init__(self, gens, container)`. Raises `NotImplementedError` if `container` is not a `FreeModulePolyRing`. Sets `self.order = ModuleOrder(monomial_key(order), self.ring.order, TOP)`, `self._gb = None`, `self._gbe = None`.

#### `__eq__(self, other)`
If `other` is a `SubModulePolyRing` with different order, returns `False`. Otherwise delegates to `SubModule.__eq__(self, other)`.

#### `_groebner(self, extended=False)`
Returns standard basis in sdm form. Imports `sdm_groebner`, `sdm_nf_mora` from `sympy.polys.distributedmodules`. Converts generators via `self.ring._vector_to_sdm(x, self.order)`. If `_gbe is None and extended`: computes both GB and relations, caches them. If `_gb is None`: computes GB only, caches it. Returns `(self._gb, self._gbe)` if extended, else `self._gb`.

#### `_groebner_vec(self, extended=False)`
Returns standard basis in element form. If not extended: converts sdm vectors back via `self.ring._sdm_to_vector(x, self.rank)`, wraps as module elements. If extended: calls `_groebner(extended=True)`, returns `(element_list, relation_vectors_as_lists)`.

#### `_contains(self, x)`
Imports `sdm_zero`, `sdm_nf_mora` from `sympy.polys.distributedmodules`. Returns `True` if the Mora normal form of `x` against the Gröbner basis equals zero: `sdm_nf_mora(self.ring._vector_to_sdm(x, self.order), self._groebner(), self.order, self.ring.dom) == sdm_zero()`.

#### `_syzygies(self)`
Computes syzygies per [SCA, algorithm 2.5.4]. Creates identity matrix `im = eye(k)` where `k = len(self.gens)`, rank `r = self.rank`. Builds a free module `Rkr = self.ring.free_module(r + k)`. For each generator `f` at index `j`: constructs vector of length `r+k` with components of `f` in first `r` positions and identity row in last `k` positions. Creates submodule `F = Rkr.submodule(*newgens, order='ilex', TOP=False)` (elimination order). Computes Gröbner basis `G = F._groebner_vec()`. Filters to elements with zero in first `r` components: `[x[r:] for x in G if all(y == self.ring.convert(0) for y in x[:r])]`. Returns these filtered vectors.

#### `_in_terms_of_generators(self, e)`
Per [SCA, 2.8.1]. Creates submodule `M = self.ring.free_module(self.rank).submodule(*((e,) + self.gens))`. Computes syzygy module with `order="ilex", TOP=False` (descending order). Gets Gröbner basis `G = S._groebner_vec()`. Finds the element where first component is a unit: `[x for x in G if self.ring.is_unit(x[0])][0]`. Returns `[-x/e[0] for x in e[1:]]` (negated coefficients divided by leading coefficient).

#### `reduce_element(self, x, NF=None)`
Imports `sdm_nf_mora`. If `NF is None`, uses default Mora normal form. Converts `x` to sdm via `self.ring._vector_to_sdm(x, self.order)`, applies normal form against Gröbner basis, converts back via `self.ring._sdm_to_vector(...)` and wraps as container element.

#### `_intersect(self, other, relations=False)`
Per [SCA, section 2.8.2]. Let `fi = self.gens`, `hi = other.gens`, `r = self.rank`. Builds coefficient matrix `ci` of size `r × 2r` with identity blocks on diagonal and anti-diagonal positions. Builds data vectors: `di = [list(f) + [0]*r for f in fi]`, `ei = [[0]*r + list(h) for h in hi]`. Creates free module `self.ring.free_module(2*r).submodule(*(ci + di + ei))`, computes syzygies. Filters to nonzero in first `r` components: `[x for x in syz if any(y != self.ring.zero for y in x[:r])]`. Result submodule generated by negated first-r components: `self.container.submodule(*([-y for y in x[:r]] for x in nonzero))`. If `relations=True`, also returns relation vectors from positions `[r:r+len(fi)]` and `[r+len(fi):]`.

#### `_module_quotient(self, other, relations=False)`
Per [SCA, section 2.8.4]. If `relations and len(other.gens) != 1`: raises `NotImplementedError`. If no generators: returns `self.ring.ideal(1)`. If one generator `g1 = list(other.gens[0]) + [1]`, builds submodule of rank `r+1` with `(f, 1)` and `(fi, 0)` vectors using elimination order `'ilex', TOP=False`. If not relations: returns ideal from last component of Gröbner basis elements with zero in first r components. If relations: also returns relation coefficients. For multiple generators: computes intersection of individual quotients via `reduce(lambda x, y: x.intersect(y), (self._module_quotient(self.container.submodule(x)) for x in other.gens))`.

---

### Class `SubModuleQuotientRing(SubModule)`

**Purpose:** Submodule of a free module over a quotient ring. Delegates computations to the underlying subquotient.

**Attributes:**
- `self.quot` — the subquotient generated by lifts of generators, set in `__init__`.

#### `__init__(self, gens, container)`
Calls `SubModule.__init__(self, gens, container)`. Sets `self.quot = self.container.quot.submodule(*[self.container.lift(x) for x in self.gens])`.

#### `_contains(self, elem)`
Returns `self.quot._contains(self.container.lift(elem))`.

#### `_syzygies(self)`
Returns `[tuple(self.ring.convert(y, self.quot.ring) for y in x) for x in self.quot._syzygies()]`, converting syzygy coefficients from the quotient ring back to this module's ring.

#### `_in_terms_of_generators(self, elem)`
Returns `[self.ring.convert(x, self.quot.ring) for x in self.quot._in_terms_of_generators(self.container.lift(elem))]`.

---

### Class `QuotientModuleElement(ModuleElement)`

**Purpose:** Element of a quotient module.

**Inherits from:** `ModuleElement`

#### `eq(self, d1, d2)`
Returns `self.module.killed_module.contains(d1 - d2)`. Two elements are equal iff their difference lies in the killed submodule.

#### `__repr__(self)`
Returns `repr(self.data) + " + " + repr(self.module.killed_module)`.

---

### Class `QuotientModule(Module)`

**Purpose:** Quotient module `base / killed_module`. Not instantiated directly; use ring constructors or `/` operator.

**Attributes:**
- `self.dtype = QuotientModuleElement` (class attribute).
- `self.base` — the base free module, set in `__init__`.
- `self.killed_module` — the submodule being quotiented out, set in `__init__`.
- `self.rank` — rank of the base module, set in `__init__`.

#### `__init__(self, ring, base, submodule)`
Calls `Module.__init__(self, ring)`. If `not base.is_submodule(submodule)`, raises `ValueError`. Sets `self.base = base`, `self.killed_module = submodule`, `self.rank = base.rank`.

#### `__repr__(self)`
Returns `repr(self.base) + "/" + repr(self.killed_module)`.

#### `is_zero(self)`
Returns `self.base == self.killed_module` (quotient is zero iff base equals killed module).

#### `is_submodule(self, other)`
If `other` is a `QuotientModule`: returns `self.killed_module == other.killed_module and self.base.is_submodule(other.base)`. If `other` is a `SubQuotientModule`: returns `other.container == self`. Otherwise returns `False`.

#### `submodule(self, *gens, **opts)`
Returns `SubQuotientModule(gens, self, **opts)`. Creates a submodule of the quotient module.

#### `convert(self, elem, M=None)`
If `elem` is a `QuotientModuleElement`: if `elem.module is self`, return it; if `self.killed_module.is_submodule(elem.module.killed_module)`, returns `QuotientModuleElement(self, self.base.convert(elem.data))`; otherwise raises `CoercionFailed`. Otherwise (not already an element): returns `QuotientModuleElement(self, self.base.convert(elem))`.

#### `identity_hom(self)`
Returns `self.base.identity_hom().quotient_codomain(self.killed_module).quotient_domain(self.killed_module)`. The identity homomorphism on the quotient module.

#### `quotient_hom(self)`
Returns `self.base.identity_hom().quotient_codomain(self.killed_module)`. The natural projection map from base to this quotient module.

## sympy/polys/domains/domain.py
Now I have the complete file (lines 1–541). Here is the full natural-language specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division

from sympy.polys.domains.domainelement import DomainElement

from sympy.core import Basic, sympify
from sympy.core.compatibility import HAS_GMPY, integer_types, is_sequence

from sympy.polys.polyerrors import UnificationFailed, CoercionFailed, DomainError
from sympy.polys.orderings import lex
from sympy.polys.polyutils import _unify_gens

from sympy.utilities import default_sort_key, public
from sympy.core.decorators import deprecated
```

### Constants & Class-Level Attributes (all on `Domain`)

| Name | Type / Value | Notes |
|---|---|---|
| `dtype` | `None` | Python type of domain elements; overridden by subclasses. |
| `zero` | `None` | Domain zero element; overridden by subclasses. |
| `one` | `None` | Domain one element; overridden by subclasses. |
| `is_Ring` | `False` (bool) | Flag: is this domain a ring? |
| `is_Field` | `False` (bool) | Flag: is this domain a field? |
| `has_assoc_Ring` | `False` (bool) | Does this domain have an associated ring? |
| `has_assoc_Field` | `False` (bool) | Does this domain have an associated field? |
| `is_FiniteField`, `is_FF` | `False` (bool, alias) | Is a finite field. |
| `is_IntegerRing`, `is_ZZ` | `False` (bool, alias) | Is the integer ring ℤ. |
| `is_RationalField`, `is_QQ` | `False` (bool, alias) | Is the rational field ℚ. |
| `is_RealField`, `is_RR` | `False` (bool, alias) | Is a real floating-point field. |
| `is_ComplexField`, `is_CC` | `False` (bool, alias) | Is a complex floating-point field. |
| `is_AlgebraicField`, `is_Algebraic` | `False` (bool, alias) | Is an algebraic number field. |
| `is_PolynomialRing`, `is_Poly` | `False` (bool, alias) | Is a polynomial ring K[X]. |
| `is_FractionField`, `is_Frac` | `False` (bool, alias) | Is a rational function field K(X). |
| `is_SymbolicDomain`, `is_EX` | `False` (bool, alias) | Is the symbolic expression domain EX. |
| `is_Exact` | `True` (bool) | Does this domain support exact arithmetic? |
| `is_Numerical` | `False` (bool) | Is this a purely numerical domain? |
| `is_Simple` | `False` (bool) | Is this a simple (non-composite) domain? |
| `is_Composite` | `False` (bool) | Is this a composite domain (e.g. K[X])? |
| `is_PID` | `False` (bool) | Is this a principal ideal domain? |
| `has_CharacteristicZero` | `False` (bool) | Does this domain have characteristic zero? |
| `rep` | `None` (str or None) | String representation of the domain. |
| `alias` | `None` (str or None) | Short alias for conversion dispatch. |

### Deprecated Properties

- **`has_Field`** (`@property`, deprecated since 1.1, issue #12723): Returns `self.is_Field`.
- **`has_Ring`** (`@property`, deprecated since 1.1, issue #12723): Returns `self.is_Ring`.

---

## Code Objects (Class and Methods)

### Class: `Domain(object)`

Abstract base class representing a mathematical domain (e.g., ℤ, ℚ, ℝ, ℂ, GF(p), K[X], …). Instances are singletons; subclasses override the boolean flags above to identify their type.

#### `__init__(self)`
Raises `NotImplementedError`. Subclasses must not call this directly; they use singleton instances instead.

#### `__str__(self) → str`
Returns `self.rep`.

#### `__repr__(self) → str`
Returns `str(self)`.

#### `__hash__(self) → int`
Returns `hash((self.__class__.__name__, self.dtype))`.

#### `new(self, *args) → dtype`
Constructs a domain element by calling `self.dtype(*args)`.

#### `tp (property) → type`
Alias for `self.dtype`.

#### `__call__(self, *args) → dtype`
Delegates to `self.new(*args)`; allows constructing elements via `domain(value1, value2, …)`.

#### `normal(self, *args) → dtype`
Constructs a domain element by calling `self.dtype(*args)`. Same as `new`.

#### `convert_from(self, element, base) → dtype`
Converts `element` (an object from domain `base`) to `self.dtype`. Dispatches via an alias-based method name: if `base.alias is not None`, looks up `getattr(self, "from_" + base.alias)`; otherwise `getattr(self, "from_" + base.__class__.__name__)`. If the found callable returns a non-`None` result, that result is returned. Otherwise raises `CoercionFailed` with a message `"can't convert {element} of type {type(element)} from {base} to {self}"`.

#### `convert(self, element, base=None) → dtype`
Converts an arbitrary Python/SymPy object into this domain's dtype. If `base is not None`, delegates to `self.convert_from(element, base)`. Otherwise follows a cascade of type checks:

1. If `self.of_type(element)` (i.e., `isinstance(element, self.tp)`), return `element` unchanged.
2. Import `PythonIntegerRing`, `GMPYIntegerRing`, `GMPYRationalField`, `RealField`, `ComplexField`.
3. If `isinstance(element, integer_types)`: call `self.convert_from(element, PythonIntegerRing())`.
4. If `HAS_GMPY` is true: check `isinstance(element, GMPYIntegerRing().tp)` → convert via that ring; check `isinstance(element, GMPYRationalField().tp)` → convert via that field.
5. If `isinstance(element, float)`: create `RealField(tol=False)(element)` and convert from it.
6. If `isinstance(element, complex)`: create `ComplexField(tol=False)(element)` and convert from it.
7. If `isinstance(element, DomainElement)`: call `self.convert_from(element, element.parent())`.
8. If `self.is_Numerical` is true and the element has attribute `is_ground == True`, call `self.convert(element.LC())`.
9. If `isinstance(element, Basic)` (SymPy object): try `self.from_sympy(element)`, catching `(TypeError, ValueError)`.
10. Otherwise: if not a sequence, attempt `sympify(element)` then `self.from_sympy()` on the result; catch errors.
11. If none of the above succeeds, raise `CoercionFailed` with `"can't convert {element} of type {type(element)} to {self}"`.

#### `of_type(self, element) → bool`
Returns `isinstance(element, self.tp)`. (Note: docstring admits this is not always correct for e.g. PolyElement.)

#### `__contains__(self, a) → bool`
Returns `True` if `self.convert(a)` succeeds without raising `CoercionFailed`; otherwise `False`.

#### `to_sympy(self, a) → Basic`
Converts domain element `a` to a SymPy object. Raises `NotImplementedError` (must be overridden).

#### `from_sympy(self, a) → dtype`
Converts a SymPy `Basic` object into this domain's dtype. Raises `NotImplementedError` (must be overridden).

#### Conversion helper methods (class-level defaults; all return `None`)

These are classmethods or static-style methods used by `convert_from`. Each takes `(K1, a, K0)` where `K1` is the target domain, `a` is the source element, and `K0` is the source domain:

- **`from_FF_python(K1, a, K0)`** — Convert `ModularInteger(int)`. Returns `None`.
- **`from_ZZ_python(K1, a, K0)`** — Convert Python `int`. Returns `None`.
- **`from_QQ_python(K1, a, K0)`** — Convert Python `Fraction`. Returns `None`.
- **`from_FF_gmpy(K1, a, K0)`** — Convert GMPY `ModularInteger(mpz)`. Returns `None`.
- **`from_ZZ_gmpy(K1, a, K0)`** — Convert GMPY `mpz`. Returns `None`.
- **`from_QQ_gmpy(K1, a, K0)`** — Convert GMPY `mpq`. Returns `None`.
- **`from_RealField(K1, a, K0)`** — Convert real element. Returns `None`.
- **`from_ComplexField(K1, a, K0)`** — Convert complex element. Returns `None`.
- **`from_AlgebraicField(K1, a, K0)`** — Convert algebraic number. Returns `None`.
- **`from_PolynomialRing(K1, a, K0)`** — If `a.is_ground`, returns `K1.convert(a.LC, K0.dom)`. Otherwise falls through (implicit `None`).
- **`from_FractionField(K1, a, K0)`** — Convert rational function. Returns `None`.
- **`from_ExpressionDomain(K1, a, K0)`** — Returns `K1.from_sympy(a.ex)`.
- **`from_GlobalPolynomialRing(K1, a, K0)`** — If `a.degree() <= 0`, returns `K1.convert(a.LC(), K0.dom)`. Otherwise implicit `None`.
- **`from_GeneralizedPolynomialRing(K1, a, K0)`** — Delegates to `K1.from_FractionField(a, K0)`.

#### `unify_with_symbols(K0, K1, symbols)` (staticmethod / classmethod)
If either `K0.is_Composite` and its symbols intersect `symbols`, or `K1.is_Composite` and its symbols intersect `symbols`, raises `UnificationFailed("can't unify {K0} with {K1}, given {tuple(symbols)} generators")`. Otherwise returns `K0.unify(K1)`.

#### `unify(K0, K1, symbols=None)` (staticmethod / classmethod)
Constructs a minimal domain containing elements of both `K0` and `K1`. The hierarchy from smallest to largest is: GF(p), ZZ, QQ, RR, CC, ALG, K[X], K(X), EX.

Logic flow:
1. If `symbols is not None`, delegate to `K0.unify_with_symbols(K1, symbols)`.
2. If `K0 == K1`, return `K0`.
3. If either is symbolic (`is_EX`), return that one.
4. **Composite domains** (polynomial/fraction rings): Extract ground domains and symbol lists. Unify the ground domains via `K0_ground.unify(K1_ground)`. Unify generators via `_unify_gens()`. Pick order from whichever operand is composite. If one is a fraction field and the other a polynomial ring, neither ground domain is a field, but the unified ground domain *is* a field → downgrade to its associated ring via `.get_ring()`. Choose class: prefer `K0.__class__` if K0 is composite and (K1 is not composite or K0 is fraction field or K1 is polynomial ring); else use `K1.__class__`. If the chosen class is `GlobalPolynomialRing`, instantiate with `(domain, symbols)`. Otherwise instantiate with `(domain, symbols, order)`.
5. **Real/Complex fields**: Define inner helper `mkinexact(cls, K0, K1)` that creates a new instance of `cls` with `prec=max(K0.precision, K1.precision)` and `tol=max(K0.tolerance, K1.tolerance)`. Then: both Complex → `mkinexact`; Complex+Real or Real+Complex → `mkinexact`; both Real → `mkinexact`; one is Real/Complex and the other isn't → return the Real/Complex operand.
6. **Algebraic fields**: Both algebraic → create new instance with unified ground domain and `_unify_gens(K0.orig_ext, K1.orig_ext)`. One algebraic → return that one.
7. **Rational field**: If either is QQ, return QQ.
8. **Integer ring**: If either is ZZ, return ZZ.
9. **Finite fields**: Both GF(p) → new instance of `K0.__class__` with modulus `max(K0.mod, K1.mod, key=default_sort_key)`.
10. Otherwise fall back to the symbolic domain `EX`.

#### `__eq__(self, other) → bool`
Returns `isinstance(other, Domain) and self.dtype == other.dtype`.

#### `__ne__(self, other) → bool`
Returns `not self.__eq__(other)`.

#### `map(self, seq)`
Recursively applies this domain's constructor to every leaf element of a nested list `seq`. For each element: if it is a `list`, recurse; otherwise call `self(elt)`. Returns the transformed structure.

#### `get_ring(self) → Domain`
Returns an associated ring. Raises `DomainError('there is no ring associated with {self}')`.

#### `get_field(self) → Domain`
Returns an associated field. Raises `DomainError('there is no field associated with {self}')`.

#### `get_exact(self) → Domain`
Returns `self` (the domain itself, since the base class defaults to exact arithmetic).

#### `__getitem__(self, symbols)`
Syntactic sugar for polynomial ring creation: if `symbols` has `__iter__`, calls `self.poly_ring(*symbols)`; otherwise `self.poly_ring(symbols)`.

#### `poly_ring(self, *symbols, **kwargs) → PolynomialRing`
Returns a new `PolynomialRing(self, symbols, order=lex)` (imports from `sympy.polys.domains.polynomialring`).

#### `frac_field(self, *symbols, **kwargs) → FractionField`
Returns a new `FractionField(self, symbols, order=lex)` (imports from `sympy.polys.domains.fractionfield`).

#### `old_poly_ring(self, *symbols, **kwargs) → PolynomialRing`
Returns a new polynomial ring using the legacy module: `PolynomialRing(self, *symbols, **kwargs)` (from `sympy.polys.domains.old_polynomialring`).

#### `old_frac_field(self, *symbols, **kwargs) → FractionField`
Returns a new fraction field using the legacy module: `FractionField(self, *symbols, **kwargs)` (from `sympy.polys.domains.old_fractionfield`).

#### `algebraic_field(self, *extension)`
Raises `DomainError("can't create algebraic field over {self}")`. Subclasses override this.

#### `inject(self, *symbols)`
Injects generators into the domain. Raises `NotImplementedError` (must be overridden).

### Arithmetic / Predication Methods (default implementations)

These methods provide default behavior that delegates to Python operators or SymPy; subclasses may override for efficiency:

- **`is_zero(self, a) → bool`**: Returns `not a`.
- **`is_one(self, a) → bool`**: Returns `a == self.one`.
- **`is_positive(self, a) → bool`**: Returns `a > 0`.
- **`is_negative(self, a) → bool`**: Returns `a < 0`.
- **`is_nonpositive(self, a) → bool`**: Returns `a <= 0`.
- **`is_nonnegative(self, a) → bool`**: Returns `a >= 0`.
- **`abs(self, a)`**: Returns `abs(a)`.
- **`neg(self, a)`**: Returns `-a`.
- **`pos(self, a)`**: Returns `+a`.
- **`add(self, a, b)`**: Returns `a + b`.
- **`sub(self, a, b)`**: Returns `a - b`.
- **`mul(self, a, b)`**: Returns `a * b`.
- **`pow(self, a, b)`**: Returns `a ** b`.

### Arithmetic Methods (abstract — raise NotImplementedError)

These must be overridden by concrete domain subclasses:

- **`exquo(self, a, b)`** — Exact quotient. Raises `NotImplementedError`.
- **`quo(self, a, b)`** — Quotient (truncated). Raises `NotImplementedError`.
- **`rem(self, a, b)`** — Remainder (`a % b`). Raises `NotImplementedError`.
- **`div(self, a, b)`** — Returns `(quotient, remainder)`. Raises `NotImplementedError`.
- **`invert(self, a, b)`** — Modular inverse of `a mod b`. Raises `NotImplementedError`.
- **`revert(self, a)`** — Multiplicative inverse (`a⁻¹`). Raises `NotImplementedError`.
- **`numer(self, a)`** — Numerator of `a`. Raises `NotImplementedError`.
- **`denom(self, a)`** — Denominator of `a`. Raises `NotImplementedError`.
- **`gcdex(self, a, b)`** — Extended GCD. Raises `NotImplementedError`.
- **`gcd(self, a, b)`** — Greatest common divisor. Raises `NotImplementedError`.
- **`lcm(self, a, b)`** — Least common multiple. Raises `NotImplementedError`.
- **`log(self, a, b)`** — Logarithm of `a` base `b`. Raises `NotImplementedError`.
- **`sqrt(self, a)`** — Square root of `a`. Raises `NotImplementedError`.

### Derived Arithmetic Methods (default implementations using abstract methods)

- **`half_gcdex(self, a, b) → tuple`**: Calls `self.gcdex(a, b)`, unpacks `(s, t, h)`, returns `(s, h)`.
- **`cofactors(self, a, b) → tuple`**: Computes `gcd = self.gcd(a, b)`, then `cfa = self.quo(a, gcd)`, `cfb = self.quo(b, gcd)`; returns `(gcd, cfa, cfb)`.

### Numeric / Comparison Methods (default implementations)

- **`evalf(self, a, prec=None, **options) → Basic`**: Returns `self.to_sympy(a).evalf(prec, **options)`.
- **`n = evalf`** — Alias.
- **`real(self, a)`**: Returns `a` unchanged.
- **`imag(self, a)`**: Returns `self.zero`.
- **`almosteq(self, a, b, tolerance=None) → bool`**: Returns `a == b`.

### `characteristic(self) → int`
Returns the characteristic of this domain. Raises `NotImplementedError('characteristic()')`.

## sympy/polys/domains/expressiondomain.py
Here is the complete natural-language specification of `sympy/polys/domains/expressiondomain.py`:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from sympy.polys.domains.field import Field
from sympy.polys.domains.simpledomain import SimpleDomain
from sympy.polys.domains.characteristiczero import CharacteristicZero
from sympy.core import sympify, SympifyError
from sympy.utilities import public
from sympy.polys.polyutils import PicklableWithSlots
```

### Constants & Globals

- `@public` — decorator applied to the `ExpressionDomain` class (marks it as a public API).

---

## Code Objects

### Class: `ExpressionDomain(Field, CharacteristicZero, SimpleDomain)`

**Metaclass:** None.

**Inheritance:** Inherits from `Field`, `CharacteristicZero`, and `SimpleDomain`.

**Class-level attributes:**
- `is_SymbolicDomain = is_EX = True` — two boolean flags set to `True`.
- `dtype = Expression` — class attribute referencing the inner `Expression` nested class.
- `zero = Expression(0)` — singleton representing zero; constructed by passing integer `0` to `Expression`.
- `one = Expression(1)` — singleton representing one; constructed by passing integer `1` to `Expression`.
- `rep = 'EX'` — string representation identifier.
- `has_assoc_Ring = False` — boolean flag indicating no associated ring.
- `has_assoc_Field = True` — boolean flag indicating an associated field exists.

**`__init__(self)`:** No-op; takes only `self`, does nothing.

#### Method: `to_sympy(self, a)`
Takes an `Expression` instance `a`. Calls `a.as_expr()` and returns the raw SymPy expression (the `.ex` attribute).

#### Method: `from_sympy(self, a)`
Takes any object `a` (typically a SymPy expression). Returns `self.dtype(a)`, i.e., wraps it in an `Expression` instance.

#### Class method: `from_ZZ_python(K1, a, K0)`
Class method. Takes a Python `int` (`a`) and a domain `K0`. Converts via `K1(K0.to_sympy(a))`: first converts the int to its SymPy representation using `K0`, then wraps in `ExpressionDomain` (`K1`).

#### Class method: `from_QQ_python(K1, a, K0)`
Class method. Takes a Python `Fraction` (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the fraction to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_ZZ_gmpy(K1, a, K0)`
Class method. Takes a GMPY `mpz` (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the GMPY integer to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_QQ_gmpy(K1, a, K0)`
Class method. Takes a GMPY `mpq` (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the GMPY rational to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_RealField(K1, a, K0)`
Class method. Takes an mpmath `mpf` (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the mpmath float to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_PolynomialRing(K1, a, K0)`
Class method. Takes a DMP (dense multivariate polynomial) object (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the polynomial to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_FractionField(K1, a, K0)`
Class method. Takes a DMF (dense multivariate fraction) object (`a`) and domain `K0`. Converts via `K1(K0.to_sympy(a))`: converts the rational function to SymPy via `K0`, then wraps in `ExpressionDomain`.

#### Class method: `from_ExpressionDomain(K1, a, K0)`
Class method. Takes an `Expression` instance (`a`) and domain `K0`. Returns `a` directly (identity conversion).

#### Method: `get_ring(self)`
Returns `self`. Documented as a workaround — EX is not actually a ring but the parent interface requires this method.

#### Method: `get_field(self)`
Returns `self`. Indicates that ExpressionDomain serves as its own associated field.

#### Method: `is_positive(self, a)`
Takes an `Expression` instance `a`. Returns `a.ex.as_coeff_mul()[0].is_positive`: extracts the coefficient part of the expression and checks whether it is positive.

#### Method: `is_negative(self, a)`
Takes an `Expression` instance `a`. Returns `a.ex.as_coeff_mul()[0].is_negative`: same pattern as `is_positive`, checking for negativity.

#### Method: `is_nonpositive(self, a)`
Takes an `Expression` instance `a`. Returns `a.ex.as_coeff_mul()[0].is_nonpositive`.

#### Method: `is_nonnegative(self, a)`
Takes an `Expression` instance `a`. Returns `a.ex.as_coeff_mul()[0].is_nonnegative`.

#### Method: `numer(self, a)`
Takes an `Expression` instance `a`. Delegates to `a.numer()` and returns the result (an `Expression` wrapping the numerator).

#### Method: `denom(self, a)`
Takes an `Expression` instance `a`. Delegates to `a.denom()` and returns the result (an `Expression` wrapping the denominator).

#### Method: `gcd(self, a, b)`
Takes two `Expression` instances `a` and `b`. Returns `a.gcd(b)`, delegating to the inner `Expression.gcd` method.

#### Method: `lcm(self, a, b)`
Takes two `Expression` instances `a` and `b`. Returns `a.lcm(b)`, delegating to the inner `Expression.lcm` method.

---

### Nested Class: `ExpressionDomain.Expression(PicklableWithSlots)`

**Inheritance:** Inherits from `PicklableWithSlots`.

**`__slots__ = ['ex']`:** Single slot storing the raw SymPy expression.

#### Method: `__init__(self, ex)`
Takes any value `ex`. If `ex` is already an `Expression` instance (checked via `isinstance(ex, self.__class__)`), copies its `.ex` attribute directly. Otherwise, passes `ex` through `sympify()` and stores the result in `self.ex`.

#### Method: `__repr__(f)`
Returns `'EX(%s)' % repr(f.ex)`: a string representation of the form `EX(<inner_repr>)`.

#### Method: `__str__(f)`
Returns `'EX(%s)' % str(f.ex)`: same format as `__repr__` but using `str()` on the inner expression.

#### Method: `__hash__(self)`
Returns `hash((self.__class__.__name__, self.ex))`: hash based on the class name and the raw SymPy expression.

#### Method: `as_expr(f)`
Returns `f.ex`: unwraps and returns the raw SymPy expression.

#### Method: `numer(f)`
Calls `f.ex.as_numer_denom()` to get a `(numerator, denominator)` tuple. Returns a new `Expression` wrapping just the numerator (index `[0]`).

#### Method: `denom(f)`
Calls `f.ex.as_numer_denom()`. Returns a new `Expression` wrapping just the denominator (index `[1]`).

#### Method: `simplify(f, ex)`
Takes a raw SymPy expression `ex`. Calls `ex.cancel()` to simplify/cancel common factors in rational expressions. Wraps and returns the result as a new `Expression`.

#### Method: `__abs__(f)`
Returns `f.__class__(abs(f.ex))`: absolute value of the inner expression, wrapped in a new `Expression`.

#### Method: `__neg__(f)`
Returns `f.__class__(-f.ex)`: negation of the inner expression, wrapped in a new `Expression`.

#### Private method: `_to_ex(f, g)`
Takes any value `g`. Attempts to construct an `Expression` from it via `f.__class__(g)`. If `SympifyError` is raised (i.e., `g` cannot be converted to a SymPy expression), returns `None`. Otherwise returns the new `Expression`.

#### Method: `__add__(f, g)`
Binary addition. Calls `_to_ex(g)` to convert `g` to an `Expression`. If conversion succeeds (`g is not None`), returns `f.simplify(f.ex + g.ex)`. If it fails, returns `NotImplemented`.

#### Method: `__radd__(f, g)`
Reverse addition. Constructs a temporary `Expression` from `g`, then returns `f.simplify(temp.ex + f.ex)`.

#### Method: `__sub__(f, g)`
Binary subtraction. Calls `_to_ex(g)`. If successful, returns `f.simplify(f.ex - g.ex)`. Otherwise returns `NotImplemented`.

#### Method: `__rsub__(f, g)`
Reverse subtraction. Constructs a temporary `Expression` from `g`, then returns `f.simplify(temp.ex - f.ex)`.

#### Method: `__mul__(f, g)`
Binary multiplication. Calls `_to_ex(g)`. If successful, returns `f.simplify(f.ex * g.ex)`. Otherwise returns `NotImplemented`.

#### Method: `__rmul__(f, g)`
Reverse multiplication. Constructs a temporary `Expression` from `g`, then returns `f.simplify(temp.ex * f.ex)`.

#### Method: `__pow__(f, n)`
Exponentiation. Calls `_to_ex(n)` to convert the exponent. If successful, returns `f.simplify(f.ex ** n.ex)`. Otherwise returns `NotImplemented`.

#### Method: `__truediv__(f, g)`
True division. Calls `_to_ex(g)`. If successful, returns `f.simplify(f.ex / g.ex)`. Otherwise returns `NotImplemented`.

#### Method: `__rtruediv__(f, g)`
Reverse true division. Constructs a temporary `Expression` from `g`, then returns `f.simplify(temp.ex / f.ex)`.

#### Attribute: `__div__ = __truediv__`
Python 2 compatibility alias for `__truediv__`.

#### Attribute: `__rdiv__ = __rtruediv__`
Python 2 compatibility alias for `__rtruediv__`.

#### Method: `__eq__(f, g)`
Equality comparison. Converts `g` to an `Expression` via `f.__class__(g)`, then compares the raw inner expressions: returns `f.ex == converted_g.ex`.

#### Method: `__ne__(f, g)`
Inequality. Returns `not f.__eq__(g)`.

#### Method: `__nonzero__(f)`
Python 2 truthiness check. Returns `f.ex != 0`: the expression is falsy only if its inner value equals zero.

#### Attribute: `__bool__ = __nonzero__`
Python 3 compatibility alias for `__nonzero__`.

#### Method: `gcd(f, g)`
Greatest common divisor. Converts `g` to an `Expression` via `f.__class__(g)`. Imports `gcd` from `sympy.polys` and returns `f.__class__(gcd(f.ex, converted_g.ex))`: wraps the result in a new `Expression`.

#### Method: `lcm(f, g)`
Least common multiple. Converts `g` to an `Expression` via `f.__class__(g)`. Imports `lcm` from `sympy.polys` and returns `f.__class__(lcm(f.ex, converted_g.ex))`: wraps the result in a new `Expression`.

---

## sympy/polys/domains/pythonrational.py
Now I have the full file. Here is the complete specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
import operator
from sympy.polys.polyutils import PicklableWithSlots
from sympy.polys.domains.domainelement import DomainElement
from sympy.core.compatibility import integer_types
from sympy.core.sympify import converter
from sympy.core.numbers import Rational, Integer
from sympy.printing.defaults import DefaultPrinting
from sympy.utilities import public
```

### Constants & Globals

- `converter[PythonRational]` — maps the `PythonRational` type to the `sympify_pythonrational` function (see below). This registers automatic conversion of `PythonRational` instances into SymPy's native `Rational`.

---

## Code Objects

### Class: `PythonRational(DefaultPrinting, PicklableWithSlots, DomainElement)`

Decorated with `@public`. A rational number type backed by Python integers. Stores the fraction in reduced form as numerator/denominator.

#### Slots & Attributes

- `__slots__ = ['p', 'q']` — only two instance attributes exist:
  - **`p`** (int): the numerator, always stored in lowest terms with a positive denominator. Special case: if the value is zero, `p=0` and `q=1`.
  - **`q`** (int): the denominator, always ≥ 1.

#### Methods

##### `parent(self) → PythonRationalField`

Returns a new `PythonRationalField()` instance from `sympy.polys.domains`.

##### `__init__(self, p: int | Integer | Rational, q: int = 1, _gcd: bool = True)`

Constructs a reduced rational number.

1. If `p` is an `Integer`, replace it with its internal numerator (`p.p`).
2. If `p` is a `Rational`, unpack both parts: set `p = p.p` and `q = p.q`.
3. If `q == 0`, raise `ZeroDivisionError('rational number')`.
4. If `q < 0`, negate both `p` and `q` (ensuring the denominator is positive).
5. If `p == 0`: set `self.p = 0`, `self.q = 1` (canonical zero).
6. Else if `p == 1` or `q == 1`: store as-is (`self.p = p`, `self.q = q`). No GCD reduction needed since the fraction is already reduced.
7. Otherwise: compute `x = gcd(p, q)` using `sympy.polys.domains.groundtypes.python_gcd`. If `x != 1`, divide both by `x` (`p //= x`, `q //= x`). Store the result in `self.p` and `self.q`.

The `_gcd` parameter (default `True`) is an internal optimization flag: when called from arithmetic methods that already perform GCD reduction, it is passed as `False` to skip redundant computation.

##### `new(cls, p: int, q: int) → PythonRational`

Class method that bypasses `__init__`. Creates a raw instance via `object.__new__(cls)` and sets `p` and `q` directly without reduction or validation. Used internally by arithmetic methods where the result is already known to be reduced.

##### `__hash__(self) → int`

Returns `hash(self.p)` if `self.q == 1`; otherwise returns `hash((self.p, self.q))`. This ensures that equal rationals have equal hashes regardless of representation.

##### `__int__(self) → int`

Performs floor division toward negative infinity:
- If `p < 0`: returns `-((-p) // q)` (i.e., ceiling of the absolute value with a negation).
- Otherwise: returns `p // q`.

This matches Python's integer division semantics for true floor behavior.

##### `__float__(self) → float`

Returns `float(self.p) / self.q`.

##### `__abs__(self) → PythonRational`

Returns `self.new(abs(self.p), self.q)` — absolute value of the numerator, denominator unchanged.

##### `__pos__(self) → PythonRational`

Returns `self.new(+self.p, self.q)` — unary plus (identity).

##### `__neg__(self) → PythonRational`

Returns `self.new(-self.p, self.q)` — negation of the numerator.

##### `__add__(self, other) → PythonRational | NotImplemented`

Adds two rationals or a rational and an integer.

- **If `other` is `PythonRational`:**
  - Let `(ap, aq)` = `(self.p, self.q)` and `(bp, bq)` = `(other.p, other.q)`.
  - Compute `g = gcd(aq, bq)`.
  - If `g == 1`: numerator `p = ap * bq + aq * bp`, denominator `q = aq * bq`.
  - If `g > 1`: compute `q1 = aq // g`, `q2 = bq // g`; then `p = ap * q2 + bp * q1`, `q = q1 * q2`. Then reduce further: `g2 = gcd(p, g)`, and set `p //= g2`, `q *= (g // g2)`. This two-stage reduction ensures the result is fully reduced.
- **If `other` is an integer** (`integer_types`): compute `p = self.p + self.q * other`, `q = self.q`. The fraction may not be reduced, but `__init__` will reduce it (with `_gcd=False` since no GCD was done here).
- **Otherwise**: return `NotImplemented`.

Returns `self.__class__(p, q, _gcd=False)`.

##### `__radd__(self, other) → PythonRational | NotImplemented`

Commutative addition for integers on the left. If `other` is not an integer, returns `NotImplemented`. Computes `p = self.p + self.q * other`, `q = self.q`, and returns `self.__class__(p, q, _gcd=False)`.

##### `__sub__(self, other) → PythonRational | NotImplemented`

Subtracts two rationals or a rational from an integer.

- **If `other` is `PythonRational`:**
  - Same structure as `__add__`, but with subtraction: numerator `p = ap * bq - aq * bp`. The GCD-based reduction logic is identical to addition (two-stage: first reduce by the common denominator factor, then re-reduce by any remaining gcd of numerator and that factor).
- **If `other` is an integer:** compute `p = self.p - self.q * other`, `q = self.q`.
- **Otherwise**: return `NotImplemented`.

Returns `self.__class__(p, q, _gcd=False)`.

##### `__rsub__(self, other) → PythonRational | NotImplemented`

Subtraction with integer on the left. If `other` is not an integer, returns `NotImplemented`. Computes `p = self.q * other - self.p`, `q = self.q`, and returns `self.__class__(p, q, _gcd=False)`.

##### `__mul__(self, other) → PythonRational | NotImplemented`

Multiplies two rationals or a rational by an integer.

- **If `other` is `PythonRational`:**
  - Let `(ap, aq)` and `(bp, bq)` be the numerators/denominators.
  - Cross-cancel: `x1 = gcd(ap, bq)`, `x2 = gcd(bp, aq)`.
  - Result: `p = (ap // x1) * (bp // x2)`, `q = (aq // x2) * (bq // x1)`. This avoids unnecessary growth before the final reduction in `__init__`.
- **If `other` is an integer:** compute `x = gcd(other, self.q)`; then `p = self.p * (other // x)`, `q = self.q // x`. Cross-cancels common factors between the integer and denominator.
- **Otherwise**: return `NotImplemented`.

Returns `self.__class__(p, q, _gcd=False)`.

##### `__rmul__(self, other) → PythonRational | NotImplemented`

Commutative multiplication for integers on the left. If `other` is not an integer, returns `NotImplemented`. Computes `x = gcd(self.q, other)`; then `p = self.p * (other // x)`, `q = self.q // x`. Returns `self.__class__(p, q, _gcd=False)`.

##### `__div__(self, other) → PythonRational | NotImplemented`

Division of two rationals or a rational by an integer. (`__truediv__` is aliased to this.)

- **If `other` is `PythonRational`:**
  - Let `(ap, aq)` and `(bp, bq)` be the numerators/denominators.
  - Cross-cancel: `x1 = gcd(ap, bp)`, `x2 = gcd(bq, aq)`.
  - Result: `p = (ap // x1) * (bq // x2)`, `q = (aq // x2) * (bp // x1)`.
- **If `other` is an integer:** compute `x = gcd(other, self.p)`; then `p = self.p // x`, `q = self.q * (other // x)`. Cross-cancels common factors between the integer and numerator.
- **Otherwise**: return `NotImplemented`.

Returns `self.__class__(p, q, _gcd=False)`.

##### `__rdiv__(self, other) → PythonRational | NotImplemented`

Division with integer on the left: `other / self`. (`__rtruediv__` is aliased to this.) If `other` is not an integer, returns `NotImplemented`. Computes `x = gcd(self.p, other)`; then `p = self.q * (other // x)`, `q = self.p // x`. Returns `self.__class__(p, q)` — note: `_gcd=True` here (default), so full reduction is performed.

##### `__mod__(self, other) → PythonRational`

Always returns `self.__class__(0)`. The modulo of a rational by any value is always zero in this implementation (since rationals are closed under division with no remainder concept).

##### `__divmod__(self, other) → tuple[PythonRational, PythonRational]`

Returns `(self // other, self % other)` — i.e., `(self.__truediv__(other), self.__class__(0))`.

##### `__pow__(self, exp: int) → PythonRational`

Raises the rational to an integer power.

- If `exp < 0`: swap numerator and denominator (`p, q = q, p`) and negate the exponent (`exp = -exp`).
- Returns `self.__class__(p ** exp, q ** exp, _gcd=False)`. Since both base values are raised to the same positive integer power, the result is already in lowest terms (no GCD needed).

##### `__nonzero__(self) → bool` / `__bool__(self) → bool`

Returns `True` if `self.p != 0`, `False` otherwise. `__bool__` is an alias for Python 3 compatibility.

##### `__eq__(self, other) → bool`

- If `other` is `PythonRational`: returns `self.q == other.q and self.p == other.p` (exact slot comparison).
- If `other` is an integer: returns `True` only if `self.q == 1` and `self.p == other`.
- Otherwise: returns `False`.

##### `__ne__(self, other) → bool`

Returns `not self.__eq__(other)`.

##### `_cmp(self, other, op)` → int | NotImplemented

Internal comparison helper. Computes `diff = self - other`; if a `TypeError` is raised (e.g., incompatible type), returns `NotImplemented`. Otherwise applies the given operator (`operator.lt`, `operator.le`, `operator.gt`, or `operator.ge`) to `diff.p` and `0`, returning the result. Since `self.q > 0` always, comparing `diff.p` against zero is equivalent to comparing the full rational values.

##### `__lt__(self, other) → bool`

Returns `self._cmp(other, operator.lt)`.

##### `__le__(self, other) → bool`

Returns `self._cmp(other, operator.le)`.

##### `__gt__(self, other) → bool`

Returns `self._cmp(other, operator.gt)`.

##### `__ge__(self, other) → bool`

Returns `self._cmp(other, operator.ge)`.

#### Properties

- **`numer`** (property): returns `self.p` (the numerator).
- **`denom`** (property): returns `self.q` (the denominator).
- **`numerator`**: alias for `numer`.
- **`denominator`**: alias for `denom`.

---

### Function: `sympify_pythonrational(arg: PythonRational) → Rational`

Returns `Rational(arg.p, arg.q)` — converts a `PythonRational` into SymPy's native `Rational` type by passing its numerator and denominator.

This function is registered as the converter for `PythonRational` in the global `converter` dict from `sympy.core.sympify`, enabling automatic conversion when `sympify()` is called on a `PythonRational` instance.

## sympy/polys/domains/quotientring.py
Now I have the full file (199 lines). Here is the complete specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from sympy.polys.domains.ring import Ring
from sympy.polys.polyerrors import NotReversible, CoercionFailed
from sympy.polys.agca.modules import FreeModuleQuotientRing
from sympy.utilities import public
```

### Constants & Globals

No module-level constants or globals beyond the two classes defined below. The `@public` decorator from `sympy.utilities` is applied to `QuotientRingElement`.

---

## Code Objects

### Class: `QuotientRingElement(object)`

**Decorators:** `@public` (from `sympy.utilities`)

**Attributes:**
- `ring` — reference to the containing `QuotientRing` instance. Set in `__init__`.
- `data` — an element of `ring.ring` (i.e., a base-ring element) that represents this quotient-element. Set in `__init__`.

**Methods:**

#### `__init__(self, ring, data)`
Stores the two arguments as instance attributes: `self.ring = ring`, `self.data = data`. No validation or transformation is performed.

#### `__str__(self)`
Imports `sstr` from `sympy` and returns a string of the form `"<data> + <base_ideal>"`, where `<data>` is the result of `sstr(self.data)` and `<base_ideal>` is `str(self.ring.base_ideal)`.

#### `__add__(self, om)`
If `om` is not an instance of `QuotientRingElement` or its ring differs from `self.ring`, attempts to coerce `om` via `self.ring.convert(om)`. If coercion raises `NotImplementedError` or `CoercionFailed`, returns `NotImplemented`. Otherwise, constructs and returns a new element: `self.ring(self.data + om.data)` — i.e., the quotient-ring constructor is called with the sum of the underlying base-ring data.

#### `__radd__(self, om)`
Alias for `__add__`.

#### `__neg__(self)`
Returns `self.ring(self.data * self.ring.ring.convert(-1))` — negation by multiplying the underlying data by `-1` converted into the base ring type.

#### `__sub__(self, om)`
Delegates to `self.__add__(-om)`, i.e., adds the negation of `om`.

#### `__rsub__(self, om)`
Returns `(-self).__add__(om)`, i.e., the negation of self added to `om` (which will be coerced via `__add__`).

#### `__mul__(self, o)`
If `o` is not an instance of `QuotientRingElement` or its ring differs from `self.ring`, attempts to coerce `o` via `self.ring.convert(o)`. If coercion raises `NotImplementedError` or `CoercionFailed`, returns `NotImplemented`. Otherwise, constructs and returns a new element: `self.ring(self.data * o.data)` — the quotient-ring constructor called with the product of the underlying base-ring data.

#### `__rmul__(self, o)`
Alias for `__mul__`.

#### `__rdiv__(self, o)`
Returns `self.ring.revert(self) * o` — right division by computing the multiplicative inverse (revert) of self and multiplying by `o`.

#### `__rtruediv__(self, o)`
Alias for `__rdiv__`.

#### `__div__(self, o)`
If `o` is not an instance of `QuotientRingElement` or its ring differs from `self.ring`, attempts to coerce `o` via `self.ring.convert(o)`. If coercion raises `NotImplementedError` or `CoercionFailed`, returns `NotImplemented`. Otherwise, returns `self.ring.revert(o) * self` — i.e., multiplies self by the multiplicative inverse of `o`.

#### `__truediv__(self, o)`
Alias for `__div__`.

#### `__pow__(self, oth)`
Returns `self.ring(self.data ** oth)` — raises the underlying base-ring data to the power `oth` and wraps it in a new quotient-element.

#### `__eq__(self, om)`
If `om` is not an instance of `QuotientRingElement` or its ring differs from `self.ring`, returns `False`. Otherwise, computes `self - om` and passes the result to `self.ring.is_zero(...)`, returning whatever that method reports. Equality in the quotient ring means the difference lies in the ideal.

#### `__ne__(self, om)`
Returns `not self.__eq__(om)`.

---

### Class: `QuotientRing(Ring)`

**Base class:** `Ring` (from `sympy.polys.domains.ring`)

**Class attributes:**
- `has_assoc_Ring = True` — indicates this domain has an associated base ring.
- `has_assoc_Field = False` — indicates no associated field.
- `dtype = QuotientRingElement` — the element type for this domain.

#### `__init__(self, ring, ideal)`
Validates that `ideal.ring == ring`; if not, raises `ValueError` with message `'Ideal must belong to %s, got %s' % (ring, ideal)`. Stores `self.ring = ring` and `self.base_ideal = ideal`. Initializes `self.zero = self(self.ring.zero)` — the quotient-element representing zero. Initializes `self.one = self(self.ring.one)` — the quotient-element representing one.

#### `__str__(self)`
Returns a string of the form `"<ring>/<base_ideal>"`, where `<ring>` is `str(self.ring)` and `<base_ideal>` is `str(self.base_ideal)`.

#### `__hash__(self)`
Returns `hash((self.__class__.__name__, self.dtype, self.ring, self.base_ideal))` — a hash based on the class name, element type, base ring, and ideal.

#### `new(self, a)`
Constructs a quotient-element from `a`. If `a` is not already an instance of `self.ring.dtype`, converts it via `self.ring(a)`. Then reduces the result modulo the base ideal by calling `self.base_ideal.reduce_element(...)` and wraps it in `self.dtype(self, ...)`. Returns the new quotient-element.

#### `__eq__(self, other)`
Returns `True` if `other` is an instance of `QuotientRing` and both `self.ring == other.ring` and `self.base_ideal == other.base_ideal`; otherwise returns `False`.

#### `from_ZZ_python(K1, a, K0)` *(classmethod-style)*
Converts a Python `int` object to the quotient-element type. Calls `K1(K1.ring.convert(a, K0))` — converts the integer into the base ring (with target domain `K0`) and wraps it in the quotient ring constructor.

#### `from_QQ_python = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_ZZ_gmpy = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_QQ_gmpy = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_RealField = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_GlobalPolynomialRing = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_FractionField = from_ZZ_python`
Alias for `from_ZZ_python`.

#### `from_sympy(self, a)`
Converts a SymPy object by calling `self.ring.from_sympy(a)` to get the base-ring element, then wraps it in the quotient ring constructor: `self(...)`. Returns the resulting quotient-element.

#### `to_sympy(self, a)`
Extracts the underlying data from quotient-element `a` via `a.data`, converts it back to SymPy via `self.ring.to_sympy(a.data)`, and returns the result.

#### `from_QuotientRing(self, a, K0)`
If `K0 == self` (same domain), returns `a` unchanged. Otherwise returns `None` implicitly — no conversion is performed for cross-domain quotient-ring coercion.

#### `poly_ring(self, *gens)`
Raises `NotImplementedError('nested domains not allowed')`. Polynomial rings over quotient rings are not supported.

#### `frac_field(self, *gens)`
Raises `NotImplementedError('nested domains not allowed')`. Fraction fields over quotient rings are not supported.

#### `revert(self, a)`
Computes the multiplicative inverse of quotient-element `a`. Constructs an ideal `I = self.ring.ideal(a.data) + self.base_ideal` (the sum of the principal ideal generated by `a.data` and the base ideal). Calls `I.in_terms_of_generators(1)[0]` to find a representation of 1 in terms of generators; if this succeeds, wraps the result as a quotient-element via `self(...)` and returns it. If a `ValueError` is raised (meaning 1 is not in the ideal), raises `NotReversible('%s not a unit in %r' % (a, self))`.

#### `is_zero(self, a)`
Returns `self.base_ideal.contains(a.data)` — checks whether the underlying data of quotient-element `a` belongs to the base ideal. Returns `True` if it does (meaning `a` represents zero in the quotient), `False` otherwise.

#### `free_module(self, rank)`
Creates and returns a `FreeModuleQuotientRing(self, rank)` — a free module of the given rank over this quotient ring.

## sympy/polys/fields.py
Here is the complete natural-language specification of `sympy/polys/fields.py`:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from operator import add, mul, lt, le, gt, ge
from sympy.core.compatibility import is_sequence, reduce, string_types
from sympy.core.expr import Expr
from sympy.core.symbol import Symbol
from sympy.core.sympify import CantSympify, sympify
from sympy.polys.rings import PolyElement
from sympy.polys.orderings import lex
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.polyoptions import build_options
from sympy.polys.polyutils import _parallel_dict_from_expr
from sympy.polys.domains.domainelement import DomainElement
from sympy.polys.domains.polynomialring import PolynomialRing
from sympy.polys.domains.fractionfield import FractionField
from sympy.polys.constructor import construct_domain
from sympy.printing.defaults import DefaultPrinting
from sympy.utilities import public
from sympy.utilities.magic import pollute
```

### Constants & Globals

- **`_field_cache: dict`** — A module-level dictionary used as a singleton cache for `FracField` instances. Keys are 5-tuples `(cls.__name__, symbols, ngens, domain, order)` and values are the cached `FracField` objects. This ensures that constructing the same field twice returns the identical object.

---

## Code Objects

### Function: `field(symbols, domain, order=lex)`

**Signature:** `def field(symbols, symbols, domain, order=lex) → tuple[FracField, Symbol, ...]`

Constructs a new rational function field and returns a tuple whose first element is the `FracField` instance followed by its generator symbols. Internally calls `FracField(symbols, domain, order)` to create `_field`, then returns `(_field,) + _field.gens`. The `gens` attribute of `FracField` is a tuple of `FracElement` objects representing the field generators (one per symbol).

---

### Function: `xfield(symbols, domain, order=lex)`

**Signature:** `def xfield(symbols, domain, order=lex) → tuple[FracField, tuple[FracElement, ...]]`

Constructs a new rational function field and returns a 2-tuple: `(field, (x1, ..., xn))`. Internally calls `FracField(symbols, domain, order)` to create `_field`, then returns `(_field, _field.gens)`. The second element is the tuple of generator elements.

---

### Function: `vfield(symbols, domain, order=lex)`

**Signature:** `def vfield(symbols, domain, order=lex) → FracField`

Constructs a new rational function field and injects each generator into the global namespace under its symbol's name. Internally calls `FracField(symbols, domain, order)` to create `_field`, then calls `pollute([sym.name for sym in _field.symbols], _field.gens)` to pollute the caller's global namespace with the generators. Returns `_field`.

---

### Function: `sfield(exprs, *symbols, **options)`

**Signature:** `def sfield(exprs, *symbols, **options) → tuple[FracField, FracElement | list[FracElement]]`

Constructs a rational function field by deriving generators and domain from the input expressions. Parameters:
- `exprs`: A single `Expr` or a sequence of `Expr` (sympifiable).
- `symbols`: Optional sequence of `Symbol`/`Expr`.
- `options`: Keyword arguments understood by `build_options`.

**Logic:**
1. If `exprs` is not a sequence, wrap it in a list and set `single = True`; otherwise `single = False`.
2. Sympify all expressions: `exprs = list(map(sympify, exprs))`.
3. Build options via `build_options(symbols, options)`, producing `opt` with fields including `gens`, `domain`, and `order`.
4. For each expression, extract numerator and denominator via `expr.as_numer_denom()`, collecting all into `numdens`.
5. Convert the full list of numerators and denominators to parallel-dict representation: `reps, opt = _parallel_dict_from_expr(numdens, opt)`.
6. If `opt.domain` is still `None`, extract all coefficients from the reps (`sum([list(rep.values()) for rep in reps], [])`) and infer a domain via `construct_domain(coeffs, opt=opt)`.
7. Create the field: `_field = FracField(opt.gens, opt.domain, opt.order)`.
8. For each pair of consecutive reps (i.e., numerator/denominator pairs), construct a `FracElement`: `fracs.append(_field(tuple(reps[i:i+2])))`.
9. If `single` is True, return `(_field, fracs[0])`; otherwise return `(_field, fracs)`.

---

### Class: `FracField(DefaultPrinting)`

**Inheritance:** `DefaultPrinting` (no metaclass).

**Attributes (set in `__new__`):**
- **`ring: PolyRing`** — The underlying polynomial ring. Created as `PolyRing(symbols, domain, order)`.
- **`dtype: type`** — A dynamically created subclass of `FracElement`, named `"FracElement"`, with a class attribute `field` set to this instance (`obj`). This binds each element to its parent field.
- **`symbols: tuple[Symbol, ...]`** — The symbols defining the field generators.
- **`ngens: int`** — Number of generators (from `ring.ngens`).
- **`domain: Domain`** — The coefficient domain (from `ring.domain`).
- **`order: str`** — The monomial ordering (from `ring.order`, default `"lex"`).
- **`zero: FracElement`** — The additive identity, constructed as `obj.dtype(ring.zero)`.
- **`one: FracElement`** — The multiplicative identity, constructed as `obj.dtype(ring.one)`.
- **`gens: tuple[FracElement, ...]`** — Generator elements, produced by `_gens()`, which maps each ring generator through `self.dtype(gen)`.
- **Dynamic attributes:** For each `(symbol, generator)` pair where the symbol is a `Symbol`, if no attribute with that name already exists on `obj`, sets `setattr(obj, symbol.name, generator)`. This allows accessing generators as `field.x` for a symbol `x`.
- **`_hash_tuple: tuple`** — The 5-tuple used as the cache key.
- **`_hash: int`** — Cached hash value of `_hash_tuple`.

#### Method: `__new__(cls, symbols, domain, order=lex)`

Singleton constructor. Creates a `PolyRing(symbols, domain, order)`, extracts its `symbols`, `ngens`, `domain`, and `order`. Builds the cache key tuple `(cls.__name__, symbols, ngens, domain, order)`. If already in `_field_cache`, returns the cached object; otherwise creates a new instance via `object.__new__(cls)`, initializes all attributes as described above, caches it, and returns it.

#### Method: `_gens() → tuple[FracElement, ...]`

Returns a tuple of polynomial generators by mapping each element of `self.ring.gens` through `self.dtype(gen)`.

#### Method: `__getnewargs__() → tuple`

Returns `(self.symbols, self.domain, self.order)` for pickle reconstruction.

#### Method: `__hash__() → int`

Returns `self._hash`.

#### Method: `__eq__(other) → bool`

Returns `True` if `other` is a `FracField` and the 4-tuple `(self.symbols, self.ngens, self.domain, self.order)` equals `(other.symbols, other.ngens, other.domain, other.order)`.

#### Method: `__ne__(other) → bool`

Returns `not self.__eq__(other)`.

#### Method: `raw_new(numer, denom=None) → FracElement`

Creates a new field element without canceling the fraction. If `denom` is `None`, passes it through as-is to `self.dtype(numer, denom)` (the `FracElement.__init__` will default `denom` to `self.ring.one`).

#### Method: `new(numer, denom=None) → FracElement`

Creates a new field element with automatic fraction cancellation. If `denom` is `None`, defaults to `self.ring.one`. Calls `numer.cancel(denom)` to reduce the fraction, then delegates to `raw_new(reduced_numer, reduced_denom)`.

#### Method: `domain_new(element) → FracElement`

Converts a domain element into a field element via `self.domain.convert(element)`, returning it directly (no wrapping in `new`).

#### Method: `ground_new(element) → FracElement`

Attempts to create a ground (constant) field element from `element`. First tries `self.new(self.ring.ground_new(element))`. If that raises `CoercionFailed`:
- If the domain is not itself a Field but has an associated field (`not domain.is_Field and domain.has_assoc_Field`), obtains the ground field via `domain.get_field()`, converts the element there, extracts its numerator and denominator, creates ring-level ground elements from them via `ring.ground_new(...)`, and returns `self.raw_new(numer, denom)`.
- Otherwise, re-raises the exception.

#### Method: `field_new(element) → FracElement`

Converts various input types into a field element:
- If `element` is a `FracElement` from this same field (`self == element.field`), returns it unchanged; otherwise raises `NotImplementedError("conversion")`.
- If `element` is a `PolyElement`, calls `element.clear_denoms()` to get `(denom, numer)`, sets the numerator's ring to `self.ring`, creates a ground element from the denominator via `ring.ground_new(denom)`, and returns `raw_new(numer, denom)`.
- If `element` is a 2-tuple, maps each element through `self.ring.ring_new()` to get `(numer, denom)`, then calls `self.new(numer, denom)` (with cancellation).
- If `element` is a string type, raises `NotImplementedError("parsing")`.
- If `element` is an `Expr`, delegates to `self.from_expr(element)`.
- Otherwise, falls through to `self.ground_new(element)`.

#### Method: `__call__(element) → FracElement`

Alias for `field_new`. Allows calling the field as a constructor function.

#### Method: `_rebuild_expr(expr, mapping) → object`

Recursively rebuilds a SymPy expression into field-compatible objects using `mapping` (a dict from symbols to generators). Inner function `_rebuild`:
- If `expr` is in `mapping`, returns the mapped generator.
- If `expr.is_Add`, recursively rebuilds each arg and reduces with `add`.
- If `expr.is_Mul`, recursively rebuilds each arg and reduces with `mul`.
- If `expr.is_Pow` and `expr.exp` is an integer, recursively rebuilds the base and raises to `int(expr.exp)`.
- Otherwise, tries `domain.convert(expr)`; if that fails and the domain has an associated field, delegates to `domain.get_field().convert(expr)`; otherwise re-raises.

Returns `_rebuild(sympify(expr))`.

#### Method: `from_expr(expr) → FracElement`

Converts a SymPy expression into a field element. Creates a mapping from symbols to generators via `dict(zip(self.symbols, self.gens))`, calls `_rebuild_expr(expr, mapping)` to get an intermediate representation, then converts it via `self.field_new(frac)`. If `CoercionFailed` is raised during rebuilding, raises `ValueError("expected an expression convertible to a rational function in %s, got %s" % (self, expr))`.

#### Method: `to_domain() → FractionField`

Returns `FractionField(self)`, wrapping this field as a domain.

#### Method: `to_ring() → PolyRing`

Returns a new `PolyRing(self.symbols, self.domain, self.order)`.

---

### Class: `FracElement(DomainElement, DefaultPrinting, CantSympify)`

**Inheritance:** Multiple inheritance from `DomainElement`, `DefaultPrinting`, and `CantSympify`. Each instance is bound to its parent field via the dynamically-created subclass's `field` attribute.

**Attributes (set in `__init__`):**
- **`numer: PolyElement`** — The numerator polynomial element.
- **`denom: PolyElement`** — The denominator polynomial element. Always non-zero.
- **`_hash: int | None`** — Cached hash value, lazily initialized to `None`.

#### Method: `__init__(self, numer, denom=None)`

If `denom` is `None`, sets it to `self.field.ring.one`. If `denom` evaluates to falsy (zero), raises `ZeroDivisionError("zero denominator")`. Stores both as instance attributes.

#### Method: `raw_new(f, numer, denom) → FracElement`

Classmethod-style (receives an instance as first arg). Creates a new element of the same class without cancellation: `self.__class__(numer, denom)`.

#### Method: `new(f, numer, denom) → FracElement`

Creates a new element with automatic fraction cancellation via `numer.cancel(denom)`, then delegates to `raw_new`.

#### Method: `to_poly(f) → PolyElement`

Returns `self.numer` if `self.denom == 1`; otherwise raises `ValueError("f.denom should be 1")`. Used to extract the polynomial from a pure-polynomial field element.

#### Method: `parent(f) → FractionField`

Returns `self.field.to_domain()`, i.e., wraps the parent field as a `FractionField` domain object.

#### Method: `__getnewargs__(f) → tuple`

Returns `(self.field, self.numer, self.denom)` for pickle reconstruction.

#### Method: `__hash__(f) → int`

Lazily computes and caches the hash: if `_hash` is `None`, sets it to `hash((self.field, self.numer, self.denom))`. Returns the cached value.

#### Method: `copy(f) → FracElement`

Returns a shallow copy via `self.raw_new(self.numer.copy(), self.denom.copy())`.

#### Method: `set_field(f, new_field) → FracElement`

If `self.field == new_field`, returns `self`. Otherwise, gets the new ring from `new_field.ring`, converts both numerator and denominator to that ring via `.set_ring(new_ring)`, then creates a new element in the target field: `new_field.new(numer, denom)`.

#### Method: `as_expr(f, *symbols) → Expr`

Returns `self.numer.as_expr(*symbols) / self.denom.as_expr(*symbols)`, converting back to a SymPy expression.

#### Method: `__eq__(f, g) → bool`

If `g` is a `FracElement` from the same field (`isinstance(g, FracElement) and f.field == g.field`), returns `f.numer == g.numer and f.denom == g.denom`. Otherwise (for non-element comparison), checks if `f.numer == g and f.denom == f.field.ring.one` — i.e., whether the element equals a ground value.

#### Method: `__ne__(f, g) → bool`

Returns `not f.__eq__(g)`.

#### Method: `__nonzero__(f) → bool` / `__bool__(f) → bool`

Returns `bool(f.numer)` — truthiness is determined by whether the numerator is non-zero. `__bool__` is an alias for Python 3 compatibility.

#### Method: `sort_key(f) → tuple`

Returns `(self.denom.sort_key(), self.numer.sort_key())`, a tuple used for ordering elements.

#### Method: `_cmp(f1, f2, op) → bool | NotImplemented`

If `f2` is an element of the same field (`isinstance(f2, f1.field.dtype)`), returns `op(f1.sort_key(), f2.sort_key())`. Otherwise returns `NotImplemented`.

#### Comparison Methods: `__lt__`, `__le__`, `__gt__`, `__ge__`

Each delegates to `_cmp(f2, lt/le/gt/ge)` respectively.

#### Method: `__pos__(f) → FracElement`

Unary plus. Returns `self.raw_new(self.numer, self.denom)` — a new element with the same numerator and denominator (negates all coefficients per docstring, though implementation just copies).

#### Method: `__neg__(f) → FracElement`

Unary negation. Returns `self.raw_new(-self.numer, self.denom)`.

#### Method: `_extract_ground(f, element) → tuple[int, object | None, object | None]`

Attempts to extract a ground (constant) value from `element`, returning `(op, g_numer, g_denom)` where `op` is 1 for an exact domain match, -1 for a field conversion match, or 0 otherwise.
- Tries `domain.convert(element)`. If successful, returns `(1, element, None)`.
- If that fails and the domain has an associated field (`not domain.is_Field and domain.has_assoc_Field`), tries converting through `ground_field = domain.get_field()`. If successful there, returns `(-1, ground_field.numer(element), ground_field.denom(element))`.
- Otherwise returns `(0, None, None)`.

#### Method: `__add__(f, g) → FracElement | NotImplemented`

Adds rational functions. Logic by type of `g`:
- If `not g` (zero), returns `f`; if `not f`, returns `g`.
- If `g` is a field element (`isinstance(g, field.dtype)`): if denominators are equal, returns `f.new(f.numer + g.numer, f.denom)`; otherwise returns `f.new(f.numer*g.denom + f.denom*g.numer, f.denom*g.denom)`.
- If `g` is a polynomial element (`isinstance(g, field.ring.dtype)`), returns `f.new(f.numer + f.denom*g, f.denom)`.
- Otherwise: checks cross-field compatibility. If `field.domain` is a `FractionField` whose inner field matches `g.field`, proceeds; if `g.field.domain` is a `FractionField` whose inner field matches `field`, delegates to `g.__radd__(f)`; otherwise returns `NotImplemented`. For `PolyElement` with mismatched ring, delegates to `g.__radd__(f)`.
- Finally falls through to `f.__radd__(g)`.

#### Method: `__radd__(f, c) → FracElement | NotImplemented`

Right-addition. If `c` is a polynomial element (`isinstance(c, f.field.ring.dtype)`), returns `f.new(f.numer + f.denom*c, f.denom)`. Otherwise calls `_extract_ground(c)` to get `(op, g_numer, g_denom)`:
- `op == 1`: returns `f.new(f.numer + f.denom*g_numer, f.denom)`.
- `op == 0` (not a ground): returns `NotImplemented`.
- `op == -1` (field conversion): returns `f.new(f.numer*g_denom + f.denom*g_numer, f.denom*g_denom)`.

#### Method: `__sub__(f, g) → FracElement | NotImplemented`

Subtracts rational functions. Logic mirrors `__add__`:
- If `not g`, returns `f`; if `not f`, returns `-g`.
- If `g` is a field element: equal denominators → `f.new(f.numer - g.numer, f.denom)`; otherwise → `f.new(f.numer*g.denom - f.denom*g.numer, f.denom*g.denom)`.
- If `g` is a polynomial element: returns `f.new(f.numer - f.denom*g, f.denom)`.
- Cross-field checks same as `__add__`, delegating to `g.__rsub__(f)` when appropriate.
- Falls through to `_extract_ground(g)` handling:
  - `op == 1`: returns `f.new(f.numer - f.denom*g_numer, f.denom)`.
  - `op == 0`: returns `NotImplemented`.
  - `op == -1`: returns `f.new(f.numer*g_denom - f.denom*g_numer, f.denom*g_denom)`.

#### Method: `__rsub__(f, c) → FracElement | NotImplemented`

Right-subtraction. If `c` is a polynomial element, returns `f.new(-f.numer + f.denom*c, f.denom)`. Otherwise calls `_extract_ground(c)`:
- `op == 1`: returns `f.new(-f.numer + f.denom*g_numer, f.denom)`.
- `op == 0`: returns `NotImplemented`.
- `op == -1`: returns `f.new(-f.numer*g_denom + f.denom*g_numer, f.denom*g_denom)`.

#### Method: `__mul__(f, g) → FracElement | NotImplemented`

Multiplies rational functions. If either operand is zero (`not f or not g`), returns `field.zero`.
- If `g` is a field element: returns `f.new(f.numer*g.numer, f.denom*g.denom)`.
- If `g` is a polynomial element: returns `f.new(f.numer*g, f.denom)`.
- Cross-field checks same pattern as addition/subtraction; delegates to `g.__rmul__(f)` when appropriate.
- Falls through to `f.__rmul__(g)`.

#### Method: `__rmul__(f, c) → FracElement | NotImplemented`

Right-multiplication. If `c` is a polynomial element, returns `f.new(f.numer*c, f.denom)`. Otherwise calls `_extract_ground(c)`:
- `op == 1`: returns `f.new(f.numer*g_numer, f.denom)`.
- `op == 0`: returns `NotImplemented`.
- `op == -1`: returns `f.new(f.numer*g_numer, f.denom*g_denom)`.

#### Method: `__truediv__(f, g) → FracElement | NotImplemented`

Division. If `not g`, raises `ZeroDivisionError`.
- If `g` is a field element: returns `f.new(f.numer*g.denom, f.denom*g.numer)`.
- If `g` is a polynomial element: returns `f.new(f.numer, f.denom*g)`.
- Cross-field checks same pattern; delegates to `g.__rtruediv__(f)` when appropriate.
- Falls through to `_extract_ground(g)`:
  - `op == 1`: returns `f.new(f.numer, f.denom*g_numer)`.
  - `op == 0`: returns `NotImplemented`.
  - `op == -1`: returns `f.new(f.numer*g_denom, f.denom*g_numer)`.

#### Method: `__div__ = __truediv__`

Python 2 compatibility alias.

#### Method: `__rtruediv__(f, c) → FracElement | NotImplemented`

Right-division (c / f). If `not f`, raises `ZeroDivisionError`.
- If `c` is a polynomial element: returns `f.new(f.denom*c, f.numer)`.
- Otherwise calls `_extract_ground(c)`:
  - `op == 1`: returns `f.new(f.denom*g_numer, f.numer)`.
  - `op == 0`: returns `NotImplemented`.
  - `op == -1`: returns `f.new(f.denom*g_numer, f.numer*g_denom)`.

#### Method: `__rdiv__ = __rtruediv__`

Python 2 compatibility alias.

#### Method: `__pow__(f, n) → FracElement`

Raises to integer power `n`:
- If `n >= 0`, returns `self.raw_new(f.numer**n, f.denom**n)`.
- If `n < 0` and `not f` (zero numerator), raises `ZeroDivisionError`.
- Otherwise (`n < 0` and non-zero): returns `self.raw_new(f.denom**-n, f.numer**-n)` — inverts the fraction.

#### Method: `diff(f, x) → FracElement`

Computes partial derivative with respect to symbol `x` using quotient rule. Converts `x` to a polynomial via `x.to_poly()`, then returns `f.new(f.numer.diff(x)*f.denom - f.numer*f.denom.diff(x), f.denom**2)`.

#### Method: `__call__(f, *values) → FracElement`

Evaluates the element by substituting values for generators. If `0 < len(values) <= f.field.ngens`, calls `self.evaluate(list(zip(f.field.gens, values)))`. Otherwise raises `ValueError("expected at least 1 and at most %s values, got %s" % (f.field.ngens, len(values)))`.

#### Method: `evaluate(f, x, a=None) → FracElement`

Evaluates the element by substituting polynomial variables with values. Two calling conventions:
- If `x` is a list and `a` is `None`: converts each `(X, a)` pair to `(X.to_poly(), a)`, then calls `f.numer.evaluate(x)` and `f.denom.evaluate(x)`.
- Otherwise: converts `x` via `x.to_poly()`, then calls `f.numer.evaluate(x, a)` and `f.denom.evaluate(x, a)`.

After evaluation, gets the field from the result's ring (`numer.ring.to_field()`) and returns `field.new(numer, denom)`.

#### Method: `subs(f, x, a=None) → FracElement`

Substitutes values into the element (similar to `evaluate` but uses `.subs()` instead of `.evaluate()`). Two calling conventions mirror `evaluate`:
- If `x` is a list and `a` is `None`: converts pairs via `(X.to_poly(), a)`, then calls `f.numer.subs(x)` and `f.denom.subs(x)`.
- Otherwise: converts `x` via `x.to_poly()`, then calls `f.numer.subs(x, a)` and `f.denom.subs(x, a)`.

Returns `self.new(numer, denom)` — an element in the same field.

#### Method: `compose(f, x, a=None) → NotImplementedError`

Placeholder method that always raises `NotImplementedError`. Intended for function composition but not yet implemented.

## sympy/polys/monomials.py
Now I have the complete file (515 lines). Here is the specification:

---

# Module Specification: `sympy/polys/monomials.py`

## 1. Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from textwrap import dedent
from sympy.core import S, Mul, Tuple, sympify
from sympy.core.compatibility import exec_, iterable, range
from sympy.polys.polyutils import PicklableWithSlots, dict_from_expr
from sympy.polys.polyerrors import ExactQuotientFailed
from sympy.utilities import public
```

### Module Docstring

The module provides tools and arithmetic operations for monomials of distributed polynomials. A monomial is represented as a tuple of integer exponents (one per variable), e.g., `(3, 4, 1)` represents `x³·y⁴·z¹`.

---

## 2. Code Objects

### Function: `itermonomials(variables, degree)` *(decorated with `@public`)*

**Signature:** `def itermonomials(variables, degree) -> set`

**Parameters:**
- `variables`: a list of symbolic variable objects (e.g., SymPy symbols).
- `degree`: an integer specifying the maximum total degree.

**Returns:** A `set` of SymPy expression monomials of total degree at most `degree`.

**Logic:**
1. If `variables` is empty, return `{S.One}` (the set containing only the constant 1).
2. Otherwise, recursively decompose: take the first variable `x = variables[0]` and the remaining `tail = variables[1:]`.
3. Start with `monoms = itermonomials(tail, degree)` — monomials using only the tail variables up to the given degree.
4. For each integer `i` from 1 through `degree` inclusive:
   - Compute `itermonomials(tail, degree - i)`.
   - Multiply each resulting monomial by `x**i`.
   - Union these into `monoms`.
5. Return the accumulated set.

This is a recursive algorithm that generates all monomials of total degree ≤ `degree` over the given variables. The total count equals `(V + N)! / (V! · N!)` where `V = len(variables)` and `N = degree`.

---

### Function: `monomial_count(V, N)`

**Signature:** `def monomial_count(V, N) -> Rational`

**Parameters:**
- `V`: integer — number of variables.
- `N`: integer — total degree.

**Returns:** The binomial coefficient `(V + N)! / (V! · N!)`, computed using SymPy's `factorial`.

**Logic:** Imports `factorial` from `sympy` and returns `factorial(V + N) / factorial(V) / factorial(N)`.

---

### Function: `monomial_mul(A, B)`

**Signature:** `def monomial_mul(A, B) -> tuple[int, ...]`

**Parameters:**
- `A`: a tuple of non-negative integers (exponent vector).
- `B`: a tuple of non-negative integers (same length as `A`).

**Returns:** A new tuple where each element is the sum of corresponding elements: `(a₀+b₀, a₁+b₁, …)`. Implements component-wise addition.

---

### Function: `monomial_div(A, B)`

**Signature:** `def monomial_div(A, B) -> tuple[int, ...] | None`

**Parameters:**
- `A`: exponent tuple (dividend).
- `B`: exponent tuple (divisor), same length as `A`.

**Returns:** The quotient exponent tuple if every component of `A - B` is ≥ 0; otherwise `None`.

**Logic:** Calls `monomial_ldiv(A, B)` to compute element-wise subtraction. If all resulting components are non-negative, returns the result as a tuple; else returns `None`.

---

### Function: `monomial_ldiv(A, B)`

**Signature:** `def monomial_ldiv(A, B) -> tuple[int, ...]`

**Parameters:**
- `A`: exponent tuple.
- `B`: exponent tuple (same length).

**Returns:** A new tuple of element-wise differences: `(a₀-b₀, a₁-b₁, …)`. May contain negative values.

---

### Function: `monomial_pow(A, n)`

**Signature:** `def monomial_pow(A, n) -> tuple[int, ...]`

**Parameters:**
- `A`: exponent tuple.
- `n`: integer multiplier.

**Returns:** A new tuple where each element is multiplied by `n`: `(a₀·n, a₁·n, …)`.

---

### Function: `monomial_gcd(A, B)`

**Signature:** `def monomial_gcd(A, B) -> tuple[int, ...]`

**Parameters:**
- `A`, `B`: exponent tuples of the same length.

**Returns:** A new tuple where each element is the minimum of corresponding elements: `(min(a₀,b₀), min(a₁,b₁), …)`.

---

### Function: `monomial_lcm(A, B)`

**Signature:** `def monomial_lcm(A, B) -> tuple[int, ...]`

**Parameters:**
- `A`, `B`: exponent tuples of the same length.

**Returns:** A new tuple where each element is the maximum of corresponding elements: `(max(a₀,b₀), max(a₁,b₁), …)`.

---

### Function: `monomial_divides(A, B)`

**Signature:** `def monomial_divides(A, B) -> bool`

**Parameters:**
- `A`, `B`: exponent tuples of the same length.

**Returns:** `True` if every component of `A` is ≤ the corresponding component of `B` (i.e., A divides B); otherwise `False`.

---

### Function: `monomial_max(*monoms)`

**Signature:** `def monomial_max(*monoms) -> tuple[int, ...]`

**Parameters:**
- `*monoms`: one or more exponent tuples of the same length.

**Returns:** A new tuple where each element is the maximum across all input tuples at that position. Mutates a list copy internally; returns a tuple.

---

### Function: `monomial_min(*monoms)`

**Signature:** `def monomial_min(*monoms) -> tuple[int, ...]`

**Parameters:**
- `*monoms`: one or more exponent tuples of the same length.

**Returns:** A new tuple where each element is the minimum across all input tuples at that position. Mutates a list copy internally; returns a tuple.

---

### Function: `monomial_deg(M)`

**Signature:** `def monomial_deg(M) -> int`

**Parameters:**
- `M`: an exponent tuple.

**Returns:** The sum of all elements in the tuple (total degree).

---

### Function: `term_div(a, b, domain)`

**Signature:** `def term_div(a, b, domain) -> tuple[tuple[int,...], coeff] | None`

**Parameters:**
- `a`: a 2-tuple `(monomial_exponents, leading_coefficient)`.
- `b`: a 2-tuple `(monomial_exponents, leading_coefficient)`.
- `domain`: a SymPy domain object with attributes/methods `.is_Field`, `.quo()`, and `%` operator.

**Returns:** A 2-tuple `(quotient_monomial_tuple, quotient_coefficient)` if the division is exact; otherwise `None`.

**Logic:**
1. Unpack: `a_lm, a_lc = a`; `b_lm, b_lc = b`.
2. Compute `monom = monomial_div(a_lm, b_lm)`.
3. If `domain.is_Field` is true:
   - If `monom is not None`, return `(monom, domain.quo(a_lc, b_lc))`; else `None`.
4. Otherwise (non-field/ring):
   - If `monom is not None` AND `a_lc % b_lc == 0` (i.e., exact integer division of coefficients), return `(monom, domain.quo(a_lc, b_lc))`; else `None`.

---

### Class: `MonomialOps(ngens)`

**Inheritance:** `object`

**Purpose:** Code generator that produces fast, specialized monomial arithmetic functions via dynamic code generation using `exec_()`.

#### Attribute
- `ngens`: integer — number of generators (variables), set in `__init__`.

#### Method: `__init__(self, ngens)`
- Stores `ngens` as `self.ngens`.

#### Method: `_build(self, code, name) -> callable`
- Executes the given Python source string `code` via `exec_(code, ns)` in a fresh namespace dict.
- Returns the function object named `name` from that namespace.

#### Method: `_vars(self, name) -> list[str]`
- Returns a list of `ngens` strings: `[f"{name}0", f"{name}1", …, f"{name}{ngens-1}"]`.

#### Method: `mul(self) -> callable`
Generates and returns a function `monomial_mul(A, B)` that unpacks two single-element tuples containing exponent vectors, performs element-wise addition of the individual components, and packs the result back into a single-element tuple. The generated code has each component as an explicit local variable (e.g., `a0`, `a1`, …).

#### Method: `pow(self) -> callable`
Generates and returns a function `monomial_pow(A, k)` that unpacks a single-element tuple containing an exponent vector, multiplies each component by scalar `k`, and packs the result back into a single-element tuple.

#### Method: `mulpow(self) -> callable`
Generates and returns a function `monomial_mulpow(A, B, k)` that unpacks two single-element tuples, computes element-wise `(a_i + b_i * k)`, and packs the result back into a single-element tuple.

#### Method: `ldiv(self) -> callable`
Generates and returns a function `monomial_ldiv(A, B)` that unpacks two single-element tuples, performs element-wise subtraction of components, and packs the result back into a single-element tuple.

#### Method: `div(self) -> callable`
Generates and returns a function `monomial_div(A, B)` that unpacks two single-element tuples, computes element-wise differences with an early-return guard: for each component `i`, if `a_i - b_i < 0`, immediately returns `None`; otherwise packs the result tuple back into a single-element tuple.

#### Method: `lcm(self) -> callable`
Generates and returns a function `monomial_lcm(A, B)` that unpacks two single-element tuples and for each component pair `(a_i, b_i)` selects `a_i if a_i >= b_i else b_i`, packing the result back into a single-element tuple.

#### Method: `gcd(self) -> callable`
Generates and returns a function `monomial_gcd(A, B)` that unpacks two single-element tuples and for each component pair `(a_i, b_i)` selects `a_i if a_i <= b_i else b_i`, packing the result back into a single-element tuple.

---

### Class: `Monomial(PicklableWithSlots)` *(decorated with `@public`)*

**Inheritance:** `PicklableWithSlots` (from `sympy.polys.polyutils`).

**Slots:** `['exponents', 'gens']` — instance attributes stored in `__slots__`.

#### Attribute
- `exponents`: tuple of ints — the exponent vector. Set in `__init__`.
- `gens`: tuple/list of SymPy symbols (or `None`) — the generator variables corresponding to each exponent position. Set in `__init__`.

#### Method: `__init__(self, monom, gens=None)`
**Parameters:**
- `monom`: either an iterable of integers (exponent vector) or a single symbolic expression that represents a monomial.
- `gens`: optional list/tuple of generator symbols; if not provided and `monom` is an expression, inferred via `dict_from_expr()`.

**Logic:**
1. If `monom` is not iterable:
   - Call `rep, gens = dict_from_expr(sympify(monom), gens=gens)`.
   - If the resulting dictionary has exactly one key and its value equals 1, extract that key as the monomial tuple; otherwise raise `ValueError("Expected a monomial got {monom}")`.
2. Set `self.exponents = tuple(map(int, monom))`.
3. Set `self.gens = gens`.

#### Method: `rebuild(self, exponents, gens=None) -> Monomial`
- Returns a new instance of the same class with the given `exponents` and either the provided `gens` or `self.gens`.

#### Method: `__len__(self) -> int`
- Returns `len(self.exponents)`.

#### Method: `__iter__(self)`
- Returns an iterator over `self.exponents`.

#### Method: `__getitem__(self, item) -> int`
- Returns `self.exponents[item]` (supports indexing and slicing).

#### Method: `__hash__(self) -> int`
- Returns `hash((self.__class__.__name__, self.exponents, self.gens))`.

#### Method: `__str__(self) -> str`
- If `self.gens` is truthy: returns a string like `"x**2*y**3"` by joining `f"{gen}**{exp}"` for each `(gen, exp)` pair.
- Otherwise: returns `f"Monomial({self.exponents})"`.

#### Method: `as_expr(self, *gens) -> Mul`
**Parameters:**
- `*gens`: optional override of generator symbols; defaults to `self.gens`.

**Returns:** A SymPy `Mul` expression representing the product of each generator raised to its exponent.

**Logic:**
1. Use provided `gens` or fall back to `self.gens`.
2. If no generators available, raise `ValueError("can't convert {self} to an expression without generators")`.
3. Return `Mul(*[gen**exp for gen, exp in zip(gens, self.exponents)])`.

#### Method: `__eq__(self, other) -> bool`
- If `other` is a `Monomial`: compare `self.exponents == other.exponents`.
- If `other` is a `tuple` or `Tuple`: compare `self.exponents == other`.
- Otherwise: return `False`.

#### Method: `__ne__(self, other) -> bool`
- Returns `not self.__eq__(other)`.

#### Method: `__mul__(self, other) -> Monomial | NotImplementedError`
**Parameters:**
- `other`: a `Monomial`, `tuple`, or `Tuple`.

**Returns:** A new `Monomial` with exponents computed by `monomial_mul(self.exponents, other_exponents)` via `rebuild()`. If `other` is not a `Monomial`/`tuple`/`Tuple`, returns `NotImplementedError`.

#### Method: `__div__(self, other) -> Monomial | ExactQuotientFailed`
**Parameters:**
- `other`: a `Monomial`, `tuple`, or `Tuple`.

**Returns:** A new `Monomial` with exponents from `monomial_div(self.exponents, other_exponents)` via `rebuild()`. If the division is not exact (returns `None`), raises `ExactQuotientFailed(self, Monomial(other))`. If `other` is not a valid type, returns `NotImplementedError`.

#### Method: `__floordiv__ = __truediv__ = __div__`
- Both floor division and true division operators delegate to `__div__`.

#### Method: `__pow__(self, other) -> Monomial | ValueError`
**Parameters:**
- `other`: an integer exponent.

**Returns:**
- If `n == 0`: returns a new `Monomial` with all-zero exponents (the constant 1 monomial), same length as self.
- If `n > 0`: iteratively multiplies the exponent tuple by itself `n-1` times using `monomial_mul()`, then rebuilds and returns the result.
- If `n < 0`: raises `ValueError("a non-negative integer expected, got {other}")`.

#### Method: `gcd(self, other) -> Monomial`
**Parameters:**
- `other`: a `Monomial` or tuple/Tuple of exponents.

**Returns:** A new `Monomial` with exponents from `monomial_gcd(self.exponents, other_exponents)` via `rebuild()`. If `other` is not a valid type, raises `TypeError("an instance of Monomial class expected, got {other}")`.

#### Method: `lcm(self, other) -> Monomial`
**Parameters:**
- `other`: a `Monomial` or tuple/Tuple of exponents.

**Returns:** A new `Monomial` with exponents from `monomial_lcm(self.exponents, other_exponents)` via `rebuild()`. If `other` is not a valid type, raises `TypeError("an instance of Monomial class expected, got {other}")`.

---

## sympy/polys/polyclasses.py
Now I have the complete file. Let me write the full natural-language specification.

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division
from sympy.core.sympify import CantSympify
from sympy.polys.polyutils import PicklableWithSlots
from sympy.polys.polyerrors import CoercionFailed, NotReversible
from sympy import oo
from sympy.polys.densebasic import (dmp_validate, dup_normal, dmp_normal, dup_convert, dmp_convert, dmp_from_sympy, dup_strip, dup_degree, dmp_degree_in, dmp_degree_list, dmp_negative_p, dup_LC, dmp_ground_LC, dup_TC, dmp_ground_TC, dmp_ground_nth, dmp_one, dmp_ground, dmp_zero_p, dmp_one_p, dmp_ground_p, dup_from_dict, dmp_from_dict, dmp_to_dict, dmp_deflate, dmp_inject, dmp_eject, dmp_terms_gcd, dmp_list_terms, dmp_exclude, dmp_slice_in, dmp_permute, dmp_to_tuple)
from sympy.polys.densearith import (dmp_add_ground, dmp_sub_ground, dmp_mul_ground, dmp_quo_ground, dmp_exquo_ground, dmp_abs, dup_neg, dmp_neg, dup_add, dmp_add, dup_sub, dmp_sub, dup_mul, dmp_mul, dmp_sqr, dup_pow, dmp_pow, dmp_pdiv, dmp_prem, dmp_pquo, dmp_pexquo, dmp_div, dup_rem, dmp_rem, dmp_quo, dmp_exquo, dmp_add_mul, dmp_sub_mul, dmp_max_norm, dmp_l1_norm)
from sympy.polys.densetools import (dmp_clear_denoms, dmp_integrate_in, dmp_diff_in, dmp_eval_in, dup_revert, dmp_ground_trunc, dmp_ground_content, dmp_ground_primitive, dmp_ground_monic, dmp_compose, dup_decompose, dup_shift, dup_transform, dmp_lift)
from sympy.polys.euclidtools import (dup_half_gcdex, dup_gcdex, dup_invert, dmp_subresultants, dmp_resultant, dmp_discriminant, dmp_inner_gcd, dmp_gcd, dmp_lcm, dmp_cancel)
from sympy.polys.sqfreetools import (dup_gff_list, dmp_sqf_p, dmp_sqf_norm, dmp_sqf_part, dmp_sqf_list, dmp_sqf_list_include)
from sympy.polys.factortools import (dup_cyclotomic_p, dmp_irreducible_p, dmp_factor_list, dmp_factor_list_include)
from sympy.polys.rootisolation import (dup_isolate_real_roots_sqf, dup_isolate_real_roots, dup_isolate_all_roots_sqf, dup_isolate_all_roots, dup_refine_real_root, dup_count_real_roots, dup_count_complex_roots, dup_sturm)
from sympy.polys.polyerrors import UnificationFailed, PolynomialError
```

## Constants & Globals

- `oo` — imported from `sympy`; used as the return value for `DMP.homogeneous_order()` when the polynomial is zero.

---

# Code Objects

## GenericPoly (class)

**Inheritance:** `PicklableWithSlots`

A mixin base class providing shared methods for all three polynomial representations (`DMP`, `DMF`, `ANP`). Its methods are called on instances of subclasses and delegate to the subclass's own attributes.

### Methods

- **`ground_to_ring(f)`**: Returns `f.set_domain(f.dom.get_ring())`. Converts the ground domain to a ring.
- **`ground_to_field(f)`**: Returns `f.set_domain(f.dom.get_field())`. Converts the ground domain to a field.
- **`ground_to_exact(f)`**: Returns `f.set_domain(f.dom.get_exact())`. Makes the ground domain exact.
- **`_perify_factors(per, result, include)`** (classmethod): Takes a factory function `per`, a factorization `result`, and a boolean `include`. If `include` is true, unpacks `(coeff, factors) = result`; otherwise `coeff = result`. Maps each polynomial factor `g` in `factors` through `per(g)`, returning pairs `(per(g), k)` for each exponent `k`. Returns `(coeff, factors)` if `include` else just `factors`.

---

## init_normal_DMP (function)

**Signature:** `init_normal_DMP(rep, lev, dom)` → `DMP`

Normalizes the representation via `dmp_normal(rep, lev, dom)` and returns `DMP(normalized_rep, dom, lev)`.

---

## DMP (class) — Dense Multivariate Polynomials over K

**Inheritance:** `PicklableWithSlots`, `CantSympify`
**Metaclass:** None

### Slots & Attributes

- `__slots__ = ['rep', 'lev', 'dom', 'ring']`
  - `rep`: nested list representation of the polynomial coefficients (dense, multivariate).
  - `lev`: integer number of variable levels; `None` for univariate.
  - `dom`: ground domain object.
  - `ring`: optional ring object for strict quotient checking.

### Constructor

**`__init__(self, rep, dom, lev=None, ring=None)`**: If `lev is not None`, converts `rep` from a dict via `dmp_from_dict(rep, lev, dom)` if it's a dict, or wraps it as a ground element via `dmp_ground(dom.convert(rep), lev)` if it's not a list. Otherwise (if `lev is None`), validates and infers level: `rep, lev = dmp_validate(rep)`. Sets all four slot attributes.

### Factory Methods (classmethods)

- **`zero(cls, lev, dom, ring=None)`**: Returns `DMP(0, dom, lev, ring)`.
- **`one(cls, lev, dom, ring=None)`**: Returns `DMP(1, dom, lev, ring)`.
- **`from_list(cls, rep, lev, dom)`**: Creates from native coefficients: `cls(dmp_convert(rep, lev, None, dom), dom, lev)`.
- **`from_sympy_list(cls, rep, lev, dom)`**: Creates from SymPy coefficients: `cls(dmp_from_sympy(rep, lev, dom), dom, lev)`.
- **`from_dict(cls, rep, lev, dom)`**: Creates from dict representation: `cls(dmp_from_dict(rep, lev, dom), dom, lev)`.
- **`from_monoms_coeffs(cls, monoms, coeffs, lev, dom, ring=None)`**: Returns `DMP(dict(zip(monoms, coeffs)), dom, lev, ring)`.

### Conversion Methods

- **`to_ring(f)`**: Returns `f.convert(f.dom.get_ring())`.
- **`to_field(f)`**: Returns `f.convert(f.dom.get_field())`.
- **`to_exact(f)`**: Returns `f.convert(f.dom.get_exact())`.
- **`convert(f, dom)`**: If `f.dom == dom`, returns self; else returns `DMP(dmp_convert(f.rep, f.lev, f.dom, dom), dom, f.lev)`.
- **`to_dict(f, zero=False)`**: Returns `dmp_to_dict(f.rep, f.lev, f.dom, zero=zero)`.
- **`to_sympy_dict(f, zero=False)`**: Calls `dmp_to_dict`, then maps each value through `f.dom.to_sympy(v)`.
- **`to_tuple(f)`**: Returns `dmp_to_tuple(f.rep, f.lev)` for hashing.

### Structural Methods

- **`slice(f, m, n, j=0)`**: Returns `f.per(dmp_slice_in(f.rep, m, n, j, f.lev, f.dom))`.
- **`coeffs(f, order=None)`**: Returns list of non-zero coefficients in lex order: `[c for _, c in dmp_list_terms(f.rep, f.lev, f.dom, order=order)]`.
- **`monoms(f, order=None)`**: Returns list of non-zero monomials in lex order: `[m for m, _ in dmp_list_terms(f.rep, f.lev, f.dom, order=order)]`.
- **`terms(f, order=None)`**: Returns all `(monomial, coefficient)` pairs via `dmp_list_terms(...)`.
- **`all_coeffs(f)`**: For univariate only (`not f.lev`). If zero, returns `[f.dom.zero]`; else returns list of coefficients from `f.rep`. Raises `PolynomialError` for multivariate.
- **`all_monoms(f)`**: For univariate only. Computes degree via `dup_degree(f.rep)`. If degree < 0 (zero), returns `[(0,)]`; else returns `[(n - i,) for i, c in enumerate(f.rep)]`. Raises `PolynomialError` for multivariate.
- **`all_terms(f)`**: For univariate only. If degree < 0, returns `[((0,), f.dom.zero)]`; else returns `[((n - i,), c) for i, c in enumerate(f.rep)]`. Raises `PolynomialError` for multivariate.
- **`lift(f)`**: Returns `f.per(dmp_lift(f.rep, f.lev, f.dom), dom=f.dom.dom)`, converting algebraic coefficients to rationals.
- **`deflate(f)`**: Returns `(J, f.per(F))` where `(J, F) = dmp_deflate(f.rep, f.lev, f.dom)`.
- **`inject(f, front=False)`**: Returns `f.__class__(F, f.dom.dom, lev)` from `dmp_inject(...)`.
- **`eject(f, dom, front=False)`**: Returns `f.__class__(F, dom, f.lev - len(dom.symbols))` from `dmp_eject(...)`.
- **`exclude(f)`**: Returns `(J, f.__class__(F, f.dom, u))` from `dmp_exclude(f.rep, f.lev, f.dom)`, removing useless generators.
- **`permute(f, P)`**: Returns `f.per(dmp_permute(f.rep, P, f.lev, f.dom))`.
- **`terms_gcd(f)`**: Returns `(J, f.per(F))` from `dmp_terms_gcd(...)`.

### Ground Operations

- **`add_ground(f, c)`**: Returns `f.per(dmp_add_ground(f.rep, f.dom.convert(c), f.lev, f.dom))`.
- **`sub_ground(f, c)`**: Returns `f.per(dmp_sub_ground(...))`.
- **`mul_ground(f, c)`**: Returns `f.per(dmp_mul_ground(...))`.
- **`quo_ground(f, c)`**: Returns `f.per(dmp_quo_ground(...))`.
- **`exquo_ground(f, c)`**: Returns `f.per(dmp_exquo_ground(...))`.
- **`abs(f)`**: Returns `f.per(dmp_abs(f.rep, f.lev, f.dom))`.
- **`neg(f)`**: Returns `f.per(dmp_neg(f.rep, f.lev, f.dom))`.

### Arithmetic Operations (binary)

Each binary operation first calls `f.unify(g)` to get `(lev, dom, per, F, G)`, then delegates to the corresponding dense function and wraps via `per(...)`.

- **`add(f, g)`**: `per(dmp_add(F, G, lev, dom))`.
- **`sub(f, g)`**: `per(dmp_sub(F, G, lev, dom))`.
- **`mul(f, g)`**: `per(dmp_mul(F, G, lev, dom))`.
- **`sqr(f)`**: Returns `f.per(dmp_sqr(f.rep, f.lev, f.dom))`.
- **`pow(f, n)`**: If `n` is int, returns `f.per(dmp_pow(f.rep, n, f.lev, f.dom))`; else raises `TypeError`.
- **`pdiv(f, g)`**: Returns `(per(q), per(r))` from `dmp_pdiv(F, G, lev, dom)`.
- **`prem(f, g)`**: Returns `per(dmp_prem(F, G, lev, dom))`.
- **`pquo(f, g)`**: Returns `per(dmp_pquo(F, G, lev, dom))`.
- **`pexquo(f, g)`**: Returns `per(dmp_pexquo(F, G, lev, dom))`.
- **`div(f, g)`**: Returns `(per(q), per(r))` from `dmp_div(F, G, lev, dom)`.
- **`rem(f, g)`**: Returns `per(dmp_rem(F, G, lev, dom))`.
- **`quo(f, g)`**: Returns `per(dmp_quo(F, G, lev, dom))`.
- **`exquo(f, g)`**: Computes `res = per(dmp_exquo(F, G, lev, dom))`; if `f.ring` is set and `res not in f.ring`, raises `ExactQuotientFailed(f, g, f.ring)`. Returns `res`.

### Degree & Norm Methods

- **`degree(f, j=0)`**: If `j` is int, returns `dmp_degree_in(f.rep, j, f.lev)`; else raises `TypeError`.
- **`degree_list(f)`**: Returns `dmp_degree_list(f.rep, f.lev)`.
- **`total_degree(f)`**: Returns `max(sum(m) for m in f.monoms())`.
- **`homogenize(f, s)`**: Builds a homogeneous polynomial by adding a new variable (or augmenting existing variable at index `s`). Iterates over `f.terms()`, computes degree deficit `i = td - d`, and adds `(i,)` to the monomial tuple or increments index `s`. Returns `DMP(result, f.dom, f.lev + int(new_symbol), f.ring)`.
- **`homogeneous_order(f)`**: If zero, returns `-oo`. Otherwise checks all monomials have equal total degree; if so returns that degree, else `None`.
- **`LC(f)`**: Returns `dmp_ground_LC(f.rep, f.lev, f.dom)`.
- **`TC(f)`**: Returns `dmp_ground_TC(f.rep, f.lev, f.dom)`.
- **`nth(f, *N)`**: If all elements of `N` are ints, returns `dmp_ground_nth(f.rep, N, f.lev, f.dom)`; else raises `TypeError`.
- **`max_norm(f)`**: Returns `dmp_max_norm(f.rep, f.lev, f.dom)`.
- **`l1_norm(f)`**: Returns `dmp_l1_norm(f.rep, f.lev, f.dom)`.

### Algebraic Operations

- **`clear_denoms(f)`**: Returns `(coeff, f.per(F))` from `dmp_clear_denoms(...)`.
- **`integrate(f, m=1, j=0)`**: Validates `m` and `j` are ints; returns `f.per(dmp_integrate_in(f.rep, m, j, f.lev, f.dom))`.
- **`diff(f, m=1, j=0)`**: Validates `m` and `j` are ints; returns `f.per(dmp_diff_in(f.rep, m, j, f.lev, f.dom))`.
- **`eval(f, a, j=0)`**: Validates `j` is int; returns `f.per(dmp_eval_in(f.rep, f.dom.convert(a), j, f.lev, f.dom), kill=True)`.

### Euclidean & GCD Operations (univariate-restricted)

Each calls `f.unify(g)` then delegates to dense functions. Univariate methods raise `ValueError('univariate polynomial expected')` if `lev != 0`.

- **`half_gcdex(f, g)`**: If univariate, returns `(per(s), per(h))` from `dup_half_gcdex(F, G, dom)`.
- **`gcdex(f, g)`**: If univariate, returns `(per(s), per(t), per(h))` from `dup_gcdex(F, G, dom)`.
- **`invert(f, g)`**: If univariate, returns `per(dup_invert(F, G, dom))`.
- **`revert(f, n)`**: If univariate, returns `f.per(dup_revert(f.rep, n, f.dom))`.

### Resultant & Subresultant Operations

- **`subresultants(f, g)`**: Returns `list(map(per, R))` from `dmp_subresultants(F, G, lev, dom)`.
- **`resultant(f, g, includePRS=False)`**: If `includePRS`, returns `(per(res, kill=True), list(map(per, R)))`; else returns `per(dmp_resultant(F, G, lev, dom), kill=True)`.
- **`discriminant(f)`**: Returns `f.per(dmp_discriminant(f.rep, f.lev, f.dom), kill=True)`.

### Cofactors & Factor Operations

- **`cofactors(f, g)`**: Returns `(per(h), per(cff), per(cfg))` from `dmp_inner_gcd(F, G, lev, dom)`.
- **`gcd(f, g)`**: Returns `per(dmp_gcd(F, G, lev, dom))`.
- **`lcm(f, g)`**: Returns `per(dmp_lcm(F, G, lev, dom))`.
- **`cancel(f, g, include=True)`**: Unifies both. If `include`, returns `(F, G)` from `dmp_cancel(..., include=True)`. Else returns `(cF, cG, F, G)` from `dmp_cancel(..., include=False)`.

### Normalization & Truncation

- **`trunc(f, p)`**: Returns `f.per(dmp_ground_trunc(f.rep, f.dom.convert(p), f.lev, f.dom))`.
- **`monic(f)`**: Returns `f.per(dmp_ground_monic(f.rep, f.lev, f.dom))`.
- **`content(f)`**: Returns `dmp_ground_content(f.rep, f.lev, f.dom)`.
- **`primitive(f)`**: Returns `(cont, f.per(F))` from `dmp_ground_primitive(...)`.

### Composition & Decomposition (univariate-restricted)

- **`compose(f, g)`**: Unifies both; returns `per(dmp_compose(F, G, lev, dom))`.
- **`decompose(f)`**: If univariate, returns `[f.per(g) for g in dup_decompose(f.rep, f.dom)]`; else raises `ValueError`.
- **`shift(f, a)`**: If univariate, returns `f.per(dup_shift(f.rep, f.dom.convert(a), f.dom))`; else raises `ValueError`.
- **`transform(f, p, q)`**: For univariate only. Unifies `p` and `q`, then unifies `f` with them; if level is 0, returns `per(dup_transform(F, P, Q, dom))`; else raises `ValueError`.

### Sturm & Root Isolation (univariate-restricted)

- **`sturm(f)`**: If univariate, returns `[f.per(s) for s in dup_sturm(f.rep, f.dom)]`; else raises `ValueError`.
- **`gff_list(f)`**: If univariate, returns `[(f.per(g), k) for g, k in dup_gff_list(f.rep, f.dom)]`; else raises `ValueError`.

### Square-Free Operations

- **`sqf_norm(f)`**: Returns `(s, f.per(g), f.per(r, dom=f.dom.dom))` from `dmp_sqf_norm(...)`.
- **`sqf_part(f)`**: Returns `f.per(dmp_sqf_part(f.rep, f.lev, f.dom))`.
- **`sqf_list(f, all=False)`**: Returns `(coeff, [(f.per(g), k) for g, k in factors])` from `dmp_sqf_list(...)`.
- **`sqf_list_include(f, all=False)`**: Returns `[(f.per(g), k) for g, k in dmp_sqf_list_include(...)]`.

### Factorization

- **`factor_list(f)`**: Returns `(coeff, [(f.per(g), k) for g, k in factors])` from `dmp_factor_list(...)`.
- **`factor_list_include(f)`**: Returns `[(f.per(g), k) for g, k in dmp_factor_list_include(...)]`.

### Root Isolation (univariate-restricted)

- **`intervals(f, all=False, eps=None, inf=None, sup=None, fast=False, sqf=False)`**: If univariate, dispatches to `dup_isolate_real_roots`, `dup_isolate_real_roots_sqf`, `dup_isolate_all_roots`, or `dup_isolate_all_roots_sqf` based on flags. Else raises `PolynomialError`.
- **`refine_root(f, s, t, eps=None, steps=None, fast=False)`**: If univariate, returns `dup_refine_real_root(...)`; else raises `PolynomialError`.
- **`count_real_roots(f, inf=None, sup=None)`**: Returns `dup_count_real_roots(f.rep, f.dom, inf=inf, sup=sup)`.
- **`count_complex_roots(f, inf=None, sup=None)`**: Returns `dup_count_complex_roots(f.rep, f.dom, inf=inf, sup=sup)`.

### Properties (boolean predicates)

- **`is_zero`** (`@property`): Returns `dmp_zero_p(f.rep, f.lev)`.
- **`is_one`** (`@property`): Returns `dmp_one_p(f.rep, f.lev, f.dom)`.
- **`is_ground`** (`@property`): Returns `dmp_ground_p(f.rep, None, f.lev)`.
- **`is_sqf`** (`@property`): Returns `dmp_sqf_p(f.rep, f.lev, f.dom)`.
- **`is_monic`** (`@property`): Returns `f.dom.is_one(dmp_ground_LC(f.rep, f.lev, f.dom))`.
- **`is_primitive`** (`@property`): Returns `f.dom.is_one(dmp_ground_content(f.rep, f.lev, f.dom))`.
- **`is_linear`** (`@property`): Returns `all(sum(monom) <= 1 for monom in dmp_to_dict(f.rep, f.lev, f.dom).keys())`.
- **`is_quadratic`** (`@property`): Returns `all(sum(monom) <= 2 for monom in dmp_to_dict(f.rep, f.lev, f.dom).keys())`.
- **`is_monomial`** (`@property`): Returns `len(f.to_dict()) <= 1`.
- **`is_homogeneous`** (`@property`): Returns `f.homogeneous_order() is not None`.
- **`is_irreducible`** (`@property`): Returns `dmp_irreducible_p(f.rep, f.lev, f.dom)`.
- **`is_cyclotomic`** (`@property`): If univariate, returns `dup_cyclotomic_p(f.rep, f.dom)`; else `False`.

### Internal Helper Methods

- **`unify(f, g)`**: Raises `UnificationFailed` if `g` is not a `DMP` or levels differ. If domains and rings match, returns `(f.lev, f.dom, f.per, f.rep, g.rep)`. Otherwise unifies domains via `f.dom.unify(g.dom)`, unifies rings (if both non-None), converts representations via `dmp_convert`, defines a closure `per(rep, dom=dom, lev=lev, kill=False)` that constructs `DMP(rep, dom, lev - 1 if kill else lev, ring)`, and returns `(lev, dom, per, F, G)`.
- **`per(f, rep, dom=None, kill=False, ring=None)`**: Creates a new `DMP` from representation. If `kill` is true and level > 0, decrements level; if level == 0, returns raw `rep`. Uses `f.dom` and `f.ring` as defaults. Returns `DMP(rep, dom, lev, ring)`.

### Dunder / Operator Methods

- **`__repr__(f)`**: Returns `"%s(%s, %s, %s)" % (f.__class__.__name__, f.rep, f.dom, f.ring)`.
- **`__hash__(f)`**: Returns `hash((f.__class__.__name__, f.to_tuple(), f.lev, f.dom, f.ring))`.
- **`__abs__(f)`**: Returns `f.abs()`.
- **`__neg__(f)`**: Returns `f.neg()`.
- **`__add__(f, g)`**: If `g` is not a `DMP`, tries to convert via `dmp_ground(f.dom.convert(g), f.lev)`, falling back to `f.ring.convert(g)` if available; returns `NotImplemented` on failure. Otherwise calls `f.add(g)`.
- **`__radd__(f, g)`**: Returns `f.__add__(g)`.
- **`__sub__(f, g)`**: Same coercion logic as `__add__`; calls `f.sub(g)`.
- **`__rsub__(f, g)`**: Returns `(-f).__add__(g)`.
- **`__mul__(f, g)`**: If `DMP`, calls `f.mul(g)`. Else tries `f.mul_ground(g)`, falling back to `f.ring.convert(g)` via `f.exquo(...)`. Returns `NotImplemented` on failure.
- **`__div__(f, g)** / **`__truediv__ = __div__`**: If `DMP`, calls `f.exquo(g)`. Else tries `f.mul_ground(g)`, falling back to `f.ring.convert(g)` via `f.exquo(...)`. Returns `NotImplemented` on failure.
- **`__rdiv__(f, g)** / **`__rtruediv__ = __rdiv__`**: If `DMP`, calls `g.exquo(f)`. Else tries `f.ring.convert(g).exquo(f)`. Returns `NotImplemented`.
- **`__rmul__(f, g)`**: Returns `f.__mul__(g)`.
- **`__pow__(f, n)`**: Returns `f.pow(n)`.
- **`__divmod__(f, g)`**: Returns `f.div(g)`.
- **`__mod__(f, g)`**: Returns `f.rem(g)`.
- **`__floordiv__(f, g)`**: If `DMP`, calls `f.quo(g)`. Else tries `f.quo_ground(g)`. Returns `NotImplemented` on failure.
- **`__eq__(f, g)`**: Tries to unify; if levels match and representations equal, returns `True`; else `False`. Catches `UnificationFailed`.
- **`__ne__(f, g)`**: Returns `not f.__eq__(g)`.
- **`eq(f, g, strict=False)`**: If not strict, calls `__eq__`; else calls `_strict_eq(g)`.
- **`ne(f, g, strict=False)`**: Returns `not f.eq(g, strict=strict)`.
- **`_strict_eq(f, g)`**: Returns `isinstance(g, f.__class__) and f.lev == g.lev and f.dom == g.dom and f.rep == g.rep`.
- **`__lt__(f, g)`**, **`__le__(f, g)`**, **`__gt__(f, g)`**, **`__ge__(f, g)`**: Unify both, then compare representations via the corresponding list comparison operator.
- **`__nonzero__(f)`**: Returns `not dmp_zero_p(f.rep, f.lev)`.
- **`__bool__ = __nonzero__`**.

---

## init_normal_DMF (function)

**Signature:** `init_normal_DMF(num, den, lev, dom)` → `DMF`

Normalizes both numerator and denominator via `dmp_normal`, returns `DMF(normalized_num, normalized_den, dom, lev)`.

---

## DMF (class) — Dense Multivariate Fractions over K

**Inheritance:** `PicklableWithSlots`, `CantSympify`

### Slots & Attributes

- `__slots__ = ['num', 'den', 'lev', 'dom', 'ring']`
  - `num`: numerator polynomial representation (nested list).
  - `den`: denominator polynomial representation.
  - `lev`: number of variable levels; `None` for univariate.
  - `dom`: ground domain object.
  - `ring`: optional ring for strict quotient checking.

### Constructor

**`__init__(self, rep, dom, lev=None, ring=None)`**: Calls `_parse(rep, dom, lev)` to get `(num, den, lev)`. Cancels common factors via `dmp_cancel(num, den, lev, dom)`. Sets all five slot attributes.

### Factory Methods (classmethods)

- **`new(cls, rep, dom, lev=None, ring=None)`**: Calls `_parse(rep, dom, lev)`, creates object via `object.__new__(cls)`, sets slots directly without canceling, returns it.
- **`zero(cls, lev, dom, ring=None)`**: Returns `cls.new(0, dom, lev, ring=ring)`.
- **`one(cls, lev, dom, ring=None)`**: Returns `cls.new(1, dom, lev, ring=ring)`.

### Internal Parsing

**`_parse(cls, rep, dom, lev=None)`**: If `rep` is a tuple `(num, den)`, validates both via `dmp_validate` (or converts from dict if `lev` given). Raises `ZeroDivisionError('fraction denominator')` if denominator is zero. If numerator is zero, sets denominator to `dmp_one(lev, dom)`. If denominator is negative, negates both numerator and denominator. Else (`rep` not a tuple), treats it as the numerator only, sets denominator to `dmp_one(lev, dom)`, normalizing similarly. Returns `(num, den, lev)`.

### Unification Methods

- **`poly_unify(f, g)`**: Raises `UnificationFailed` if `g` is not a `DMP` or levels differ. If domains/rings match, returns `(f.lev, f.dom, f.per, (f.num, f.den), g.rep)`. Otherwise unifies domain and ring, converts representations, defines closure `per(num, den, cancel=True, kill=False)` that optionally cancels via `dmp_cancel` and constructs a new `DMF`, returns `(lev, dom, per, F, G)`.
- **`frac_unify(f, g)`**: Same logic as `poly_unify` but for two `DMF` objects; both sides are represented as `(num, den)` tuples.

### Helper Methods

- **`per(f, num, den, cancel=True, kill=False, ring=None)`**: Creates a new `DMF`. If `kill`, decrements level or returns raw `num/den`. Optionally cancels via `dmp_cancel`. Returns `f.__class__.new((num, den), dom, lev, ring=ring)`.
- **`half_per(f, rep, kill=False)`**: Creates a `DMP` from representation. If `kill`, decrements level or returns raw `rep`. Returns `DMP(rep, f.dom, lev)`.

### Numerator / Denominator Extraction

- **`numer(f)`**: Returns `f.half_per(f.num)`.
- **`denom(f)`**: Returns `f.half_per(f.den)`.
- **`cancel(f)`**: Returns `f.per(f.num, f.den)`, removing common factors.

### Arithmetic Operations (binary)

Each operation checks if `g` is a `DMP` or `DMF`:

- **`add(f, g)`**: If `DMP`, uses `poly_unify`; computes `num = dmp_add_mul(F_num, F_den, G, lev, dom), den = F_den`. Else uses `frac_unify`; computes `num = dmp_add(dmp_mul(F_num, G_den), dmp_mul(F_den, G_num)), den = dmp_mul(F_den, G_den)`. Returns `per(num, den)`.
- **`sub(f, g)`**: Same pattern; if `DMP`, uses `dmp_sub_mul`; else computes `num = dmp_sub(dmp_mul(F_num, G_den), dmp_mul(F_den, G_num))`.
- **`mul(f, g)`**: If `DMP`, `num = dmp_mul(F_num, G), den = F_den`. Else `num = dmp_mul(F_num, G_num), den = dmp_mul(F_den, G_den)`.
- **`pow(f, n)`**: If int, returns `f.per(dmp_pow(f.num, n, f.lev, f.dom), dmp_pow(f.den, n, f.lev, f.dom), cancel=False)`. Else raises `TypeError`.
- **`quo(f, g)`** / **`exquo = quo`**: If `DMP`, `num = F_num, den = dmp_mul(F_den, G)`. Else `num = dmp_mul(F_num, G_den), den = dmp_mul(F_den, G_num)`. Checks strict ring membership; raises `ExactQuotientFailed(f, g, f.ring)` if result not in ring.
- **`invert(f, check=True)`**: If `check` and `f.ring is not None` and `not f.ring.is_unit(f)`, raises `NotReversible(f, f.ring)`. Returns `f.per(f.den, f.num, cancel=False)`.

### Properties (boolean predicates)

- **`is_zero`** (`@property`): Returns `dmp_zero_p(f.num, f.lev)`.
- **`is_one`** (`@property`): Returns `dmp_one_p(f.num, f.lev, f.dom) and dmp_one_p(f.den, f.lev, f.dom)`.

### Dunder / Operator Methods

- **`__repr__(f)`**: Returns `"%s((%s, %s), %s, %s)" % (f.__class__.__name__, f.num, f.den, f.dom, f.ring)`.
- **`__hash__(f)`**: Returns `hash((f.__class__.__name__, dmp_to_tuple(f.num, f.lev), dmp_to_tuple(f.den, f.lev), f.lev, f.dom, f.ring))`.
- **`__neg__(f)`**: Returns `f.per(dmp_neg(f.num, f.lev, f.dom), f.den, cancel=False)`.
- **`__add__(f, g)`**: If `DMP` or `DMF`, calls `f.add(g)`. Else tries `f.half_per(g)`, falling back to `f.ring.convert(g)`. Returns `NotImplemented` on failure.
- **`__radd__(f, g)`**: Returns `f.__add__(g)`.
- **`__sub__(f, g)**: Same coercion as `__add__`; calls `f.sub(g)`.
- **`__rsub__(f, g)`**: Returns `(-f).__add__(g)`.
- **`__mul__(f, g)**: If `DMP`/`DMF`, calls `f.mul(g)`. Else tries `f.half_per(g)`, falling back to `f.ring.convert(g)`.
- **`__rmul__(f, g)`**: Returns `f.__mul__(g)`.
- **`__pow__(f, n)`**: Returns `f.pow(n)`.
- **`__div__(f, g)** / **`__truediv__ = __div__`**: If `DMP`/`DMF`, calls `f.quo(g)`. Else tries `f.half_per(g)`, falling back to `f.ring.convert(g)`.
- **`__rdiv__(self, g)** / **`__rtruediv__ = __rdiv__`**: Returns `self.invert(check=False)*g`; checks strict ring membership. Raises `ExactQuotientFailed(g, self, self.ring)` if needed.
- **`__eq__(f, g)`**: If `DMP`, uses `poly_unify`; returns `True` if denominator is one and numerator equals the other polynomial. If `DMF`, uses `frac_unify`; compares `(num, den)` tuples directly. Catches `UnificationFailed`.
- **`__ne__(f, g)`**: Same pattern as `__eq__` but negated comparison.
- **`__lt__(f, g)`, `__le__(f, g)`, `__gt__(f, g)`, `__ge__(f, g)`**: Uses `frac_unify`; compares representations via list operators.
- **`__nonzero__(f)`**: Returns `not dmp_zero_p(f.num, f.lev)`.
- **`__bool__ = __nonzero__`**.

---

## init_normal_ANP (function)

**Signature:** `init_normal_ANP(rep, mod, dom)` → `ANP`

Normalizes both representation and modulus via `dup_normal`, returns `ANP(normalized_rep, normalized_mod, dom)`.

---

## ANP (class) — Dense Algebraic Number Polynomials over a field

**Inheritance:** `PicklableWithSlots`, `CantSympify`

### Slots & Attributes

- `__slots__ = ['rep', 'mod', 'dom']`
  - `rep`: list of coefficients for the polynomial (dense univariate).
  - `mod`: modulus polynomial (the irreducible polynomial defining the algebraic extension).
  - `dom`: ground domain object.

### Constructor

**`__init__(self, rep, mod, dom)`**: If `rep` is a dict, converts via `dup_from_dict(rep, dom)`. Else if not a list, wraps as `[dom.convert(rep)]`. Strips trailing zeros via `dup_strip(rep)`. For `mod`: if it's a `DMP`, uses `mod.rep`; else if dict, converts via `dup_from_dict(mod, dom)`; else strips via `dup_strip(mod)`. Sets all three slot attributes.

### Factory Methods (classmethods)

- **`zero(cls, mod, dom)`**: Returns `ANP(0, mod, dom)`.
- **`one(cls, mod, dom)`**: Returns `ANP(1, mod, dom)`.

### Conversion Methods

- **`to_dict(f)`**: Returns `dmp_to_dict(f.rep, 0, f.dom)`.
- **`to_sympy_dict(f)`**: Calls `dmp_to_dict`, maps values through `f.dom.to_sympy(v)`.
- **`to_list(f)`**: Returns `f.rep`.
- **`to_sympy_list(f)`**: Returns `[f.dom.to_sympy(c) for c in f.rep]`.
- **`to_tuple(f)`**: Returns `dmp_to_tuple(f.rep, 0)`.
- **`from_list(cls, rep, mod, dom)`**: Returns `ANP(dup_strip(list(map(dom.convert, rep))), mod, dom)`.

### Unification & Helper Methods

- **`unify(f, g)`**: Raises `UnificationFailed` if `g` is not an `ANP` or modulus differs. If domains match, returns `(f.dom, f.per, f.rep, g.rep, f.mod)`. Otherwise unifies domains via `f.dom.unify(g.dom)`, converts both representations and optionally the modulus, defines `per = lambda rep: ANP(rep, mod, dom)`, returns `(dom, per, F, G, mod)`.
- **`per(f, rep, mod=None, dom=None)`**: Returns `ANP(rep, mod or f.mod, dom or f.dom)`.

### Arithmetic Operations (binary)

Each calls `f.unify(g)` to get `(dom, per, F, G, mod)`:

- **`neg(f)`**: Returns `f.per(dup_neg(f.rep, f.dom))`.
- **`add(f, g)`**: Returns `per(dup_add(F, G, dom))`.
- **`sub(f, g)`**: Returns `per(dup_sub(F, G, dom))`.
- **`mul(f, g)`**: Returns `per(dup_rem(dup_mul(F, G, dom), mod, dom))` — multiplication reduced modulo the algebraic modulus.
- **`pow(f, n)`**: If int and negative, inverts first via `dup_invert(f.rep, f.mod, f.dom)`, then raises to `-n`. Returns `per(dup_rem(dup_pow(F, n, f.dom), f.mod, f.dom))`. Else raises `TypeError`.
- **`div(f, g)`**: Returns `(per(dup_rem(dup_mul(F, dup_invert(G, mod, dom), dom), mod, dom)), self.zero(mod, dom))`.
- **`rem(f, g)`**: Always returns `self.zero(mod, dom)`.
- **`quo(f, g)`** / **`exquo = quo`**: Returns `per(dup_rem(dup_mul(F, dup_invert(G, mod, dom), dom), mod, dom))`.

### Coefficient Methods

- **`LC(f)`**: Returns `dup_LC(f.rep, f.dom)`.
- **`TC(f)`**: Returns `dup_TC(f.rep, f.dom)`.

### Properties (boolean predicates)

- **`is_zero`** (`@property`): Returns `not f` (uses `__bool__`).
- **`is_one`** (`@property`): Returns `f.rep == [f.dom.one]`.
- **`is_ground`** (`@property`): Returns `not f.rep or len(f.rep) == 1`.

### Dunder / Operator Methods

- **`__repr__(f)`**: Returns `"%s(%s, %s, %s)" % (f.__class__.__name__, f.rep, f.mod, f.dom)`.
- **`__hash__(f)`**: Returns `hash((f.__class__.__name__, f.to_tuple(), dmp_to_tuple(f.mod, 0), f.dom))`.
- **`__neg__(f)`**: Returns `f.neg()`.
- **`__add__(f, g)**: If `ANP`, calls `f.add(g)`. Else tries `f.per(g)`. Returns `NotImplemented` on failure.
- **`__radd__(f, g)`**: Returns `f.__add__(g)`.
- **`__sub__(f, g)**: Same coercion as `__add__`; calls `f.sub(g)`.
- **`__rsub__(f, g)`**: Returns `(-f).__add__(g)`.
- **`__mul__(f, g)**: If `ANP`, calls `f.mul(g)`. Else tries `f.per(g)`.
- **`__rmul__(f, g)`**: Returns `f.__mul__(g)`.
- **`__pow__(f, n)`**: Returns `f.pow(n)`.
- **`__divmod__(f, g)`**: Returns `f.div(g)`.
- **`__mod__(f, g)`**: Returns `f.rem(g)`.
- **`__div__(f, g)** / **`__truediv__ = __div__`**: If `ANP`, calls `f.quo(g)`. Else tries `f.per(g)`.
- **`__eq__(f, g)`**: Tries to unify; returns `F == G`; catches `UnificationFailed` → `False`.
- **`__ne__(f, g)`**: Same pattern but returns `F != G` or `True`.
- **`__lt__(f, g)`, `__le__(f, g)`, `__gt__(f, g)`, `__ge__(f, g)`**: Unify both; compare representations via list operators.
- **`__nonzero__(f)`**: Returns `bool(f.rep)`.
- **`__bool__ = __nonzero__`**.

## sympy/polys/polytools.py
The specification has been successfully written to `polytools_spec.md` (33,629 bytes). It covers all **104 sections** across:

- **Module preamble**: All 59 lines of imports precisely listed
- **Class `Poly(Expr)`** (~4,070 lines): Full blueprint including constructor, ~80 methods (arithmetic, GCD, factorization, root-finding, etc.), all dunder methods, domain conversion, and property accessors
- **Class `PurePoly(Poly)`** (~90 lines): Overrides for hash, equality, free_symbols, and unified representation without generator symbols
- **Module utility functions**: All degree/coefficient/division/GCD/factor/root-finding/cancel/reduced/groebner helpers with their option flags (`polys`, `auto`, `deep`, etc.)
- **Class `GroebnerBasis(Basic)`** (~270 lines): Constructor, properties (exprs/polys/domain/order/is_zero_dimensional), FGLM conversion, reduce/contains methods
- **Function `poly()`** (~80 lines): Efficient expression-to-Poly transformation with Add/Mul factor handling

Each code object includes exact signatures, parameter defaults, control flow conditions, return types/values, and exception-raising conditions — sufficient for a code-generation AI to recreate the original file.

## sympy/polys/rings.py
The complete natural-language specification of `sympy/polys/rings.py` has been written to `/tmp/omp_desc_llg_6s95/rings_spec.md`. Here's a summary of what it covers:

**Structure:**
1. **Module-Level Preamble** — All 32 imports listed precisely, plus the `_ring_cache` global constant.

2. **Module-Level Functions** (4 public + 1 private):
   - `ring()` / `xring()` / `vring()` — ring construction helpers with different return formats
   - `sring()` — auto-infer ring from expressions
   - `_parse_symbols()` — symbol normalization helper

3. **Class `PolyRing(DefaultPrinting, IPolys)`** — The polynomial ring itself:
   - Singleton caching via `__new__` and `_ring_cache`
   - 20+ attributes including dynamically-generated monomial operation functions (`monomial_mul`, `monomial_pow`, etc.)
   - Factory methods: `from_dict`, `from_terms`, `from_list`, `from_expr`, `ring_new`/`__call__`
   - Ring manipulation: `clone`, `drop`, `compose`, `add_gens`, `to_ground`, `to_field`, `to_domain`
   - Bulk operations: `add()`, `mul()`

4. **Class `PolyElement(DomainElement, DefaultPrinting, CantSympify, dict)`** — The polynomial elements (dict-backed sparse representation):
   - All arithmetic operators (`__add__`, `__sub__`, `__mul__`, `__pow__`, `__truediv__`, etc.) with full coercion logic for cross-ring PolynomialRing cases
   - Division algorithms: `div()`, `rem()`, `quo()`, `exquo()` (multivariate division per CLO p64)
   - Power computation: `_pow_generic` (binary exponentiation), `_pow_multinomial`, `square()`
   - 18 boolean properties (`is_generator`, `is_ground`, `is_monic`, `is_squarefree`, etc.)
   - Degree methods: `degree()`, `degrees()`, `tail_degree()`, `tail_degrees()`
   - Leading term accessors: `leading_expv()`, `LC`, `LM`, `LT`, `leading_monom()`, `leading_term()`
   - GCD/LCM/cofactors with domain-specific dispatch (`_gcd_ZZ` → `heugcd`, `_gcd_QQ` via clearing denominators)
   - Deflation/inflation, cancel, diff, evaluate/subs/compose
   - 17 delegation methods to dense polynomial algorithms on the ring

## sympy/polys/rootoftools.py
Now I have the full file. Here is the complete specification:

---

# Module Specification: `sympy/polys/rootoftools.py`

## 1. Module-Level Preamble

### Imports

```python
from __future__ import print_function, division

from sympy.core import (S, Expr, Integer, Float, I, Add, Lambda, symbols,
        sympify, Rational, Dummy)
from sympy.core.cache import cacheit
from sympy.core.function import AppliedUndef
from sympy.functions.elementary.miscellaneous import root as _root

from sympy.polys.polytools import Poly, PurePoly, factor
from sympy.polys.rationaltools import together
from sympy.polys.polyfuncs import symmetrize, viete

from sympy.polys.rootisolation import (
    dup_isolate_complex_roots_sqf,
    dup_isolate_real_roots_sqf)

from sympy.polys.polyroots import (
    roots_linear, roots_quadratic, roots_binomial,
    preprocess_roots, roots)

from sympy.polys.polyerrors import (
    MultivariatePolynomialError,
    GeneratorsNeeded,
    PolynomialError,
    DomainError)

from sympy.polys.domains import QQ

from mpmath import mpf, mpc, findroot, workprec
from mpmath.libmp.libmpf import prec_to_dps

from sympy.utilities import lambdify, public

from sympy.core.compatibility import range

from math import log as mathlog
```

### Constants & Globals

- **`__all__`** = `['CRootOf']` — the single exported name.
- **`_ispow2(i)`**: Helper function (lines 42–44). Computes `v = mathlog(i, 2)`, returns `v == int(v)`. Determines whether integer `i` is an exact power of 2.
- **`_reals_cache`** = `{}`: Module-level dict mapping a square-free `PurePoly` factor to its list of real root isolating intervals (ordered by position on the real line).
- **`_complexes_cache`** = `{}`: Module-level dict mapping a square-free `PurePoly` factor to its list of complex root isolating rectangles (sorted per the indexing convention).

---

## 2. Code Objects

### Function: `_ispow2(i)`

- **Signature**: `_ispow2(i) -> bool`
- **Logic**: Computes `v = math.log(i, 2)`. Returns `True` if `v == int(v)` (i.e., `i` is an exact power of 2), else `False`.
- **Used by**: `_separate_imaginary_from_complex()` to detect whether a binomial `a*x^n + b` with even degree has imaginary roots.

---

### Function: `rootof(f, x, index=None, radicals=True, expand=True)`

- **Signature**: `rootof(f: Expr, x: Symbol | None = None, index: int | Integer | None = None, radicals: bool = True, expand: bool = True) -> CRootOf`
- **Decorated with** `@public`.
- **Logic**: Simply delegates to `CRootOf(f, x, index=index, radicals=radicals, expand=expand)` and returns the result. This is a convenience factory function.

---

### Class: `RootOf(Expr)`

- **Inheritance**: `Expr` (from `sympy.core`).
- **Slots**: `['poly']` — stores a `PurePoly`.
- **Decorated with** `@public`.
- **`__new__(cls, f, x, index=None, radicals=True, expand=True)`**: Does not construct a `RootOf` directly. Instead delegates to the module-level `rootof()` function (which returns a `CRootOf`). This is because only complex roots are supported; this class exists as an abstract base.

---

### Class: `ComplexRootOf(RootOf)` — also aliased as `CRootOf`

- **Inheritance**: `RootOf(Expr)`.
- **Slots**: `['index']` (inherited from `RootOf`, adds `poly`).
- **Class attributes**: `is_complex = True`, `is_number = True`.
- **Decorated with** `@public`.
- **Alias at module level**: `CRootOf = ComplexRootOf` (line 750).

#### Constructor: `__new__(cls, f, x, index=None, radicals=False, expand=True)`

- **Parameters**:
  - `f`: univariate polynomial expression.
  - `x`: generator symbol; if `index is not None and x.is_Integer`, then `x` becomes `None` and `index = x`.
  - `index`: integer root index (0-based from left on real line, or sorted by real part then imaginary part for complex). Negative indices are accepted: `-degree ≤ index < degree`; negative values are converted via `index += degree`.
  - `radicals`: if `True` and the polynomial is linear/quadratic/binomial, return an explicit radical expression instead of a `CRootOf`. Default `False` (to satisfy `eval(repr(expr)) == expr`).
  - `expand`: whether to expand `f` before creating the `PurePoly`.

- **Logic**:
  1. Sympify `x`; if `index is not None and x.is_Integer`, swap: `x = None, index = x`. Otherwise sympify `index`.
  2. If `index` is an Integer, convert to Python `int`; else raise `ValueError("expected an integer root index, got {index}")`.
  3. Create `poly = PurePoly(f, x, greedy=False, expand=expand)`. Raise `PolynomialError` if not univariate.
  4. Get `degree = poly.degree()`. If `degree <= 0`, raise `PolynomialError("can't construct CRootOf object for {f}")`.
  5. Validate index range: `-degree ≤ index < degree`; else raise `IndexError`. Convert negative indices: `index += degree` if `index < 0`.
  6. Get domain; if not exact, convert via `poly.to_exact()`.
  7. Try trivial roots: `roots = cls._roots_trivial(poly, radicals)`. If not `None`, return `roots[index]`.
  8. Preprocess: `coeff, poly = preprocess_roots(poly)`. Get domain; if not `is_ZZ`, raise `NotImplementedError("CRootOf is not supported over {dom}")`.
  9. Look up the indexed root via `root = cls._indexed_root(poly, index)`. Return `coeff * cls._postprocess_root(root, radicals)`.

#### Class Method: `_new(cls, poly, index)` — Raw constructor

- Creates a new instance without validation. Calls `Expr.__new__(cls)`, sets `obj.poly = PurePoly(poly)` and `obj.index = index`. Attempts to copy cache entries from the original `poly` key into the new `PurePoly` key (catches `KeyError`). Returns `obj`.

#### Method: `_hashable_content(self)`

- Returns `(self.poly, self.index)`. Used for hashing/equality.

#### Property: `expr`

- Returns `self.poly.as_expr()` — the polynomial as a SymPy expression.

#### Property: `args`

- Returns `(self.expr, Integer(self.index))`.

#### Property: `free_symbols`

- Always returns `set()`. CRootOf is considered to have no free symbols (it represents a specific root).

#### Method: `_eval_is_real(self)`

- Returns `True` if `self.index < len(_reals_cache[self.poly])`, i.e., the index falls within the range of real roots. Otherwise implicitly returns `None`/falsy.

#### Class Method: `real_roots(cls, poly, radicals=True)`

- Calls `cls._get_roots("_real_roots", poly, radicals)`. Returns a list of all real roots (as explicit expressions or CRootOf objects).

#### Class Method: `all_roots(cls, poly, radicals=True)`

- Calls `cls._get_roots("_all_roots", poly, radicals)`. Returns a list of all real and complex roots.

#### Class Method: `_get_reals_sqf(cls, factor)`

- Cached lookup for real root isolating intervals of a square-free factor. Checks `_reals_cache[factor]`; if absent, calls `dup_isolate_real_roots_sqf(factor.rep.rep, factor.rep.dom, blackbox=True)`, caches it, and returns it.

#### Class Method: `_get_complexes_sqf(cls, factor)`

- Cached lookup for complex root isolating rectangles of a square-free factor. Checks `_complexes_cache[factor]`; if absent, calls `dup_isolate_complex_roots_sqf(factor.rep.rep, factor.rep.dom, blackbox=True)`, caches it, and returns it.

#### Class Method: `_get_reals(cls, factors)`

- Takes list of `(factor, k)` tuples (from `factor_list()`). For each, gets real isolating intervals via `_get_reals_sqf(factor)` and extends the result with `[(root, factor, k) for root in real_part]`. Returns the combined list.

#### Class Method: `_get_complexes(cls, factors)`

- Same pattern as `_get_reals`, but uses `_get_complexes_sqf` for complex isolating rectangles.

#### Class Method: `_reals_sorted(cls, reals)`

- Takes a list of `(root_interval, factor, multiplicity)` tuples.
  1. Makes all real intervals pairwise disjoint by calling `u.refine_disjoint(v)` on each pair (iterating i over all j > i). Updates the list in place.
  2. Sorts by interval lower bound: `sorted(reals, key=lambda r: r[0].a)`.
  3. Groups roots by factor into a cache dict; updates `_reals_cache[factor]` for each factor.
- Returns sorted list of `(interval, factor, multiplicity)` tuples.

#### Class Method: `_separate_imaginary_from_complex(cls, complexes)`

- Takes list of `(interval, factor, k)` tuples. Separates purely imaginary roots from general complex roots.
  - Helper `is_imag(c)`: For a tuple `(u, f, k)`, if the polynomial has length 2 (binomial) and degree 2 → returns `True` (both roots are imaginary). If binomial with `_ispow2(deg)` and `LC()*TC() < 0` → returns `None` (mixed: some imaginary). Otherwise `False`.
  - Sifts by factor, then within each factor sifts by `is_imag` result. Purely imaginary (`True`) go to `imag` list; non-imaginary (`False`) go to `complexes` list.
  - For mixed cases (`None`): iteratively checks if the real interval's lower bound is positive (`u.ax * u.bx > 0`). If so, moves to `complexes`; otherwise refines via `u._inner_refine()` and retries. When exactly 2 remain in the mixed list, both are added to `imag`.
- Returns `(imag_list, complexes_list)`.

#### Class Method: `_refine_complexes(cls, complexes)`

- Takes list of `(interval, factor, k)` tuples. Refines until no bounding rectangles would intersect when slid horizontally or vertically (enabling unambiguous sorting).
  1. Makes all intervals pairwise disjoint via `refine_disjoint`.
  2. Checks x-ranges: extracts unique `(ax, bx)` pairs; if fewer than `N+1` distinct ranges exist (where `N = len(complexes)//2 - 1`), refines each interval via `_inner_refine()` and retries the loop. Otherwise breaks.
- Returns refined list.

#### Class Method: `_complexes_sorted(cls, complexes)`

- Takes list of `(interval, factor, k)` tuples.
  1. Separates imaginary roots via `_separate_imaginary_from_complex`.
  2. Refines non-imaginary complexes via `_refine_complexes`.
  3. Sorts imaginary roots: key function computes `r = _root(abs(f.TC()/f.LC()), f.degree())`; returns `-r` if interval's y-range is negative, else `+r`.
  4. Sorts non-imaginary complexes by lower x-bound (`c[0].a`). Finds insertion point for imaginary roots: iterates reversed list to find first where `bx <= 0`, computes index `i = len(complexes) - i - 1` (with adjustment if `i > 0`). Inserts imag at position `i`.
  5. Updates `_complexes_cache[factor]` for each factor.
- Returns sorted combined list.

#### Class Method: `_reals_index(cls, reals, index)`

- Maps a global real root index to `(poly, local_index)` within the appropriate factor. Iterates through `reals`, accumulating multiplicities (`i += k`). When `index < i + k`, finds the poly and counts how many times it appeared before position `j` in the list to get the local index. Returns `(factor, 0)`.

#### Class Method: `_complexes_index(cls, complexes, index)`

- Maps a global complex root index (offset by real count) to `(poly, local_index)`. Similar logic to `_reals_index`, but adds `len(_reals_cache[poly])` to the local index at the end. Returns `(factor, adjusted_index)`.

#### Class Method: `_count_roots(cls, roots)`

- Returns `sum(k for _, _, k in roots)`. Counts total roots with multiplicity.

#### Class Method: `_indexed_root(cls, poly, index)`

- Gets a single root by global index from a composite polynomial.
  1. Calls `poly.factor_list()` to get `(content, factors)`.
  2. Computes real intervals; if `index < reals_count`, sorts and returns via `_reals_index`.
  3. Otherwise computes complex intervals, sorts, and returns via `_complexes_index(complexes, index - reals_count)`.

#### Class Method: `_real_roots(cls, poly)`

- Returns list of `(poly, local_index)` tuples for all real roots of a composite polynomial. Gets factors, gets/ sorts real intervals, iterates `range(reals_count)`, appends each via `_reals_index`.

#### Class Method: `_all_roots(cls, poly)`

- Same as `_real_roots` but also appends complex roots (sorted) via `_complexes_index`. Returns list of `(poly, local_index)` tuples for all real and complex roots.

#### Class Method: `@cacheit _roots_trivial(cls, poly, radicals)`

- Computes explicit radical roots for linear, quadratic, and binomial polynomials.
  - If degree == 1: returns `roots_linear(poly)`.
  - If not `radicals`: returns `None`.
  - If degree == 2: returns `roots_quadratic(poly)`.
  - If `poly.length() == 2 and poly.TC()` (binomial): returns `roots_binomial(poly)`.
  - Otherwise: returns `None`.

#### Class Method: `_preprocess_roots(cls, poly)`

- Ensures polynomial is compatible with CRootOf. Converts to exact if domain not exact; calls `preprocess_roots(poly)` which returns `(coeff, poly)`. If resulting domain is not ZZ, raises `NotImplementedError`. Returns `(coeff, poly)`.

#### Class Method: `_postprocess_root(cls, root, radicals)`

- Given a `(poly, index)` tuple from the indexing methods: tries `_roots_trivial(poly, radicals)`. If not None, returns `roots[index]` (explicit expression). Otherwise returns `cls._new(poly, index)` (a CRootOf object).

#### Class Method: `_get_roots(cls, method, poly, radicals)`

- Generic root-fetching pipeline. Validates univariate; preprocesses to get `(coeff, poly)`. Iterates over results of `getattr(cls, method)(poly)` (one of `_real_roots` or `_all_roots`). For each `(poly, index)`, computes `coeff * cls._postprocess_root(root, radicals)` and appends. Returns list of root expressions.

#### Method: `_get_interval(self)`

- Retrieves the isolating interval/rectangle for this specific root from cache. If real: returns `_reals_cache[self.poly][self.index]`. If complex: returns `_complexes_cache[self.poly][self.index - len(_reals_cache[self.poly])]`.

#### Method: `_set_interval(self, interval)`

- Updates the isolating interval/rectangle in cache for this root. Same indexing logic as `_get_interval`, but writes `interval` into the appropriate cache entry.

#### Method: `_eval_subs(self, old, new)`

- Always returns `self`. Substitution is not allowed to change a CRootOf object (it represents an exact mathematical constant).

#### Method: `_eval_evalf(self, prec)`

- Numerically evaluates this root to the given precision using mpmath.
  1. Enters `workprec(prec)`.
  2. Gets generator `g = self.poly.gen`; if not a Symbol, creates a Dummy and substitutes; lambdifies the expression.
  3. Gets isolating interval via `_get_interval()`. If complex (not real), refines until imaginary bounds change (`while interval.ay == ay or interval.by == by: interval.refine()`).
  4. Enters main loop:
     - **Real case**: Converts interval endpoints to `mpf`; if `a == b`, root = a, break; else `x0 = mpf(str(interval.center))`.
     - **Complex case**: Converts all four bounds (`ax, bx, ay, by`) to `mpf`; if all equal (degenerate rectangle), determines sign of imaginary part from `(deg - i) % 2` and interval y-sign; root = `mpc(ax, ay)`, break; else `x0 = mpc(*map(str, interval.center))`.
     - Calls `findroot(func, x0)`. Verifies the found root lies within the interval (real: `a <= root <= b`; complex: bounds check). If verified, break. Catches `UnboundLocalError` and `ValueError`, refines interval, retries.
  5. Returns `Float._new(root.real._mpf_, prec) + I * Float._new(root.imag._mpf_, prec)`.

#### Method: `eval_rational(self, tol)`

- Returns a Rational approximation to this real root within tolerance `tol` using bisection.
  - If not real, raises `NotImplementedError("eval_rational() only works for real polynomials so far")`.
  - Lambdifies the expression; gets interval; converts bounds to `Rational(str(...))`; calls `bisect(func, a, b, tol)`.

#### Method: `_eval_Eq(self, other)`

- Determines whether `self == other` (exact equality check for root expressions).
  1. If `type(self) == type(other)`, delegates to `__eq__`.
  2. If `other` is not a number or has `AppliedUndef`, returns `S.false`.
  3. If `other` is infinite, returns `S.false`.
  4. Substitutes `other` into the polynomial expression; if result is not zero (`z is False`), returns `S.false`.
  5. Compares `(is_real, is_imaginary)` of both; if they differ and neither has unknown (`None`) status, returns `S.false`.
  6. Refines interval until bounds change (to ensure distinctness from other roots).
  7. If `other` has no imaginary part: if self is real, converts interval to Rational and checks `a < other < b`; else returns `S.false`.
  8. If self is complex: converts all four interval bounds to Rational; returns `sympify((r1 < re < r2) and (i1 < im < i2))`.

---

### Class: `RootSum(Expr)`

- **Inheritance**: `Expr` (from `sympy.core`).
- **Slots**: `['poly', 'fun', 'auto']`.
- **Decorated with** `@public`.

#### Constructor: `__new__(cls, expr, func=None, x=None, auto=True, quadratic=False)`

- **Parameters**:
  - `expr`: univariate polynomial expression.
  - `func`: a univariate function (Lambda or Function) to apply to each root; defaults to identity (`Lambda(poly.gen, poly.gen)`).
  - `x`: generator symbol for the polynomial.
  - `auto`: if `True` and the function is rational in the variable, use the rational-case algorithm (Viete's formulas + symmetrization) instead of symbolic CRootOf objects.
  - `quadratic`: if `True`, use explicit quadratic formula for quadratic factors.

- **Logic**:
  1. Transform: `coeff, poly = cls._transform(expr, x)` via `PurePoly` and `preprocess_roots`. Raise `MultivariatePolynomialError` if not univariate.
  2. If `func is None`, set to identity Lambda. Else validate it's a univariate function (check `is_Function` or `nargs == 1`); wrap in Lambda if needed; else raise `ValueError`.
  3. Extract `var, expr = func.variables[0], func.expr`. If `coeff != S.One`, substitute `var → coeff*var` in the expression.
  4. Get degree. If `expr` does not contain `var`, return `deg * expr` (sum of constant over all roots).
  5. Decompose `expr`: if Add, split into `add_const + expr_without_var`; if Mul, split into `mul_const * expr_without_var`.
  6. Create new Lambda with the variable-free part.
  7. Check if function is rational in var via `_is_func_rational(poly, func)`.
  8. Factor polynomial: `(_, factors), terms = poly.factor_list()`. For each `(poly, k)`:
     - If linear: term = `func(roots_linear(poly)[0])`.
     - If quadratic and `quadratic=True` and factor is quadratic: term = `sum(map(func, roots_quadratic(poly)))`.
     - Else if not rational or not auto: term = `cls._new(poly, func, auto)` (symbolic RootSum).
     - Else: term = `cls._rational_case(poly, func)` (closed-form via Viete's formulas).
     - Append `k * term` to terms.
  9. Return `mul_const * Add(*terms) + deg * add_const`.

#### Class Method: `_new(cls, poly, func, auto=True)` — Raw constructor

- Creates instance without validation: `obj = Expr.__new__(cls)`, sets `obj.poly = poly`, `obj.fun = func`, `obj.auto = auto`. Returns `obj`.

#### Class Method: `new(cls, poly, func, auto=True)` — Smart constructor

- If `func.expr` does not contain any of `func.variables`, returns `func.expr` (constant). Otherwise checks rationality; if rational and auto, calls `_rational_case`; else calls `_new`.

#### Class Method: `_transform(cls, expr, x)`

- Creates `PurePoly(expr, x, greedy=False)`, applies `preprocess_roots(poly)`, returns `(coeff, poly)`.

#### Class Method: `_is_func_rational(cls, poly, func)`

- Returns `func.expr.is_rational_function(func.variables[0])`. Checks if the function is a rational expression in its variable.

#### Class Method: `_rational_case(cls, poly, func)`

- Handles sums of rational functions over roots using symmetrization (Viete's formulas).
  1. Creates dummy root symbols `roots = symbols('r:0', 'r:1', ..., 'r:n')` where n = degree.
  2. Computes `f = sum(expr.subs(var, r) for r in roots)`.
  3. Gets numerator/denominator via `together(f).as_numer_denom()`, expands both.
  4. Converts to Poly objects over domain `QQ[roots]` (catches `GeneratorsNeeded` if constant).
  5. Extracts coefficient lists `p_coeff, q_coeff`.
  6. Calls `symmetrize(p_coeff + q_coeff, formal=True)` → `(coeffs, mapping)`.
  7. Gets Viete's formulas: `formulas, values = viete(poly, roots)`, builds substitution list from mapping.
  8. Substitutes Viete relations into coeffs.
  9. Splits back into p_coeff and q_coeff; reconstructs polynomial expressions.
  10. Returns `factor(p / q)`.

#### Method: `_hashable_content(self)`

- Returns `(self.poly, self.fun)`.

#### Property: `expr`

- Returns `self.poly.as_expr()`.

#### Property: `args`

- Returns `(self.expr, self.fun, self.poly.gen)`.

#### Property: `free_symbols`

- Returns `self.poly.free_symbols | self.fun.free_symbols`.

#### Property: `is_commutative`

- Always returns `True`.

#### Method: `doit(self, **hints)`

- If `hints.get('roots', True)` is False, returns `self` unchanged.
  - Otherwise calls `roots(self.poly, multiple=True)`. If fewer roots than degree (defective polynomial), returns self. Else returns `Add(*[self.fun(r) for r in _roots])` — fully evaluated sum.

#### Method: `_eval_evalf(self, prec)`

- Numerically evaluates the root sum. Calls `self.poly.nroots(n=prec_to_dps(prec))`. If that raises `DomainError` or `PolynomialError`, returns self. Else returns `Add(*[self.fun(r) for r in _roots])`.

#### Method: `_eval_derivative(self, x)`

- Differentiates the function inside the RootSum. Extracts `var, expr = self.fun.args`; creates new Lambda with `expr.diff(x)`; calls `self.new(self.poly, func, self.auto)`.

---

### Function: `bisect(f, a, b, tol)`

- **Signature**: `bisect(f: Callable[[Any], Any], a: Number, b: Number, tol: Rational) -> Rational`
- **Logic** (robust bisection method):
  1. Sympify `a`, `b`. Evaluate `fa = f(a)`, `fb = f(b)`. If `fa * fb >= 0`, raise `ValueError("bisect: f(a) and f(b) must have opposite signs")`.
  2. While `(b - a > tol)`: compute midpoint `c = (a + b)/2`; evaluate `fc = f(c)`. If `fc == 0`, return `c` immediately. If `fa * fc < 0`, set `b = c, fb = fc`; else set `a = c, fa = fc`.
  3. Return `(a + b)/2` (midpoint of final interval).

---

## 3. Summary of Data Flow and Relationships

- **Root isolation** is the core mechanism: polynomials are factored into square-free components; each component's real/complex roots are isolated into disjoint intervals/rectangles via `dup_isolate_real_roots_sqf` / `dup_isolate_complex_roots_sqf`. These intervals are cached in `_reals_cache` and `_complexes_cache`.
- **Indexing**: Roots are globally indexed — first all real roots (sorted left-to-right), then complex roots (sorted by real part, then imaginary part). Negative indices count from the right. The `_indexed_root`, `_reals_index`, and `_complexes_index` methods map global indices to `(poly_factor, local_index)` tuples.
- **Trivial roots**: Linear, quadratic, and binomial polynomials can be solved in radicals; these bypass interval-based indexing entirely when `radicals=True`.
- **RootSum** computes sums of a function applied to all roots. For rational functions, it uses symmetrization (Viete's formulas) to produce closed-form expressions without explicit root objects. For non-rational functions or when `auto=False`, it returns symbolic RootSum objects that can later be evaluated via `doit()` or `_eval_evalf()`.

## sympy/tensor/array/ndim_array.py
Here is the complete natural-language specification of `sympy/tensor/array/ndim_array.py`:

---

## Module-Level Preamble

### Imports (top-of-file, lines 1–4)
```python
from __future__ import print_function, division
import collections
from sympy import Basic
```

### Imports (bottom-of-file, lines 410–413 — lazy/module-level convenience imports for subclasses and external consumers)
```python
from sympy.core.numbers import Integer
from sympy.core.sympify import sympify
from sympy.core.function import Derivative
from sympy.core.expr import Expr
```

### Constants & Globals
None. No module-level constants or mutable globals are defined.

---

## Code Objects

### Class `NDimArray(object)` (line 7)

**Description:** Abstract base class for N-dimensional symbolic arrays. Provides shape management, element iteration, indexing, arithmetic operators, string representation, and linear-algebra helper methods (`transpose`, `conjugate`, `adjoint`). Subclasses are expected to provide `_loop_size` (total element count), `_shape` (tuple of dimension sizes), `_rank` (number of dimensions), and an iterable data store supporting iteration via `for i in self`.

#### Class-level attributes
None defined at class scope. All attributes are instance-level, set by subclasses during construction.

#### Instance attributes (inherited contract — set by subclass constructors)
- `_loop_size` (`int`): Total number of elements in the flattened array.
- `_shape` (`tuple[int, ...]`): Tuple of dimension sizes for each axis.
- `_rank` (`int`): Number of axes; equals `len(self._shape)`.

#### Methods

##### `__new__(cls, *args, **kwargs)` (line 59)
**Signature:** `def __new__(cls, *args, **kwargs)`

Delegates construction to `ImmutableDenseNDimArray` from `sympy.tensor.array`. Returns an instance of that class regardless of the calling subclass. This makes `NDimArray(...)` a factory alias for `ImmutableDenseNDimArray(...)`.

**Returns:** An `ImmutableDenseNDimArray` instance.

---

##### `_parse_index(self, index)` (line 63)
**Signature:** `def _parse_index(self, index)`

Converts an arbitrary index into a flat integer position within the array's linear storage.

- If `index` is an `int` or `sympy.Integer`: validates that it is less than `self._loop_size`; raises `ValueError("index out of range")` if not; returns `index` unchanged.
- Otherwise (expects a tuple/sequence): checks that `len(index) == self._rank`; raises `ValueError('Wrong number of array axes')` if mismatched. Then validates each component `index[i] < self.shape[i]`; raises `ValueError('Index ' + str(index) + ' out of border')` on violation. Computes the flat index via row-major (C-order) accumulation: `real_index = real_index * self.shape[i] + index[i]` for each axis `i`. Returns the computed flat integer index.

**Returns:** `int` — the flat linear index.

---

##### `_get_tuple_index(self, integer_index)` (line 82)
**Signature:** `def _get_tuple_index(self, integer_index)`

Inverse of `_parse_index`: converts a flat integer position back into an N-dimensional tuple index using row-major decomposition. Iterates over reversed shape dimensions: for each dimension size `sh`, computes `index.append(integer_index % sh)` then `integer_index //= sh`. Reverses the collected list to restore original axis order. Returns `tuple(index)`.

**Returns:** `tuple[int, ...]` — multi-dimensional index tuple.

---

##### `_check_symbolic_index(self, index)` (line 90)
**Signature:** `def _check_symbolic_index(self, index)`

Checks whether any component of the index is a symbolic SymPy expression (`Expr`) that is not a concrete number. Converts `index` to a tuple if it isn't already: `(index if isinstance(index, tuple) else (index,))`. Iterates over each index component and its corresponding dimension size; if any component satisfies `(i < 0) == True` or `(i >= nth_dim) == True`, raises `ValueError("index out of range")`. If all components pass bounds checking and at least one is a non-numeric `Expr`, imports `sympy.tensor.Indexed` and returns `Indexed(self, *tuple_index)` (a symbolic indexed expression). Otherwise returns `None`.

**Returns:** `Indexed | None` — an `Indexed` object if any index component is symbolic; `None` otherwise.

---

##### `_setter_iterable_check(self, value)` (line 101)
**Signature:** `def _setter_iterable_check(self, value)`

Placeholder validation method. If `value` is a `collections.Iterable`, `MatrixBase`, or `NDimArray`, raises `NotImplementedError`. Intended to be overridden by subclasses for element-setting logic; the base implementation rejects iterable assignments.

**Raises:** `NotImplementedError` when `value` is iterable/matrix/array-like.

---

##### `_scan_iterable_shape(cls, iterable)` (line 106)
**Signature:** `@classmethod def _scan_iterable_shape(cls, iterable)`

Recursively flattens a nested Python iterable and determines its shape. Inner function `f(pointer)`:
- If `pointer` is not a `collections.Iterable`, returns `( [pointer], () )` — a singleton list and empty shape tuple (leaf node).
- Otherwise, recursively calls `f(i)` for each element `i` of `pointer`, collecting results into `elems` and `shapes` tuples via `zip`. If the set of shapes has cardinality > 1 (inconsistent nesting), raises `ValueError("could not determine shape unambiguously")`. Flattens all sub-element lists into a single result list. Returns `(result, (len(shapes),) + shapes[0])` — prepending the branching factor to the common child shape.

**Returns:** `tuple[list, tuple[int, ...]]` — flat element list and shape tuple.

---

##### `_handle_ndarray_creation_inputs(cls, iterable=None, shape=None, **kwargs)` (line 123)
**Signature:** `@classmethod def _handle_ndarray_creation_inputs(cls, iterable=None, shape=None, **kwargs)`

Factory helper that normalizes construction inputs into a `(shape_tuple, iterable_data)` pair. Branches on the combination of `iterable` and `shape`:

1. Both `None`: sets `shape = ()`, `iterable = ()`.
2. `shape is None` and `iterable` is an `NDimArray`: extracts `shape = iterable.shape`, converts data to list via `list(iterable)`.
3. `shape is None` and `iterable` is a `collections.Iterable`: calls `_scan_iterable_shape(iterable)` to get both flattened data and shape.
4. `shape is None` and `iterable` is a `MatrixBase`: sets `shape = iterable.shape` (data extraction deferred to subclass).
5. `shape is None` and `iterable` is an `NDimArray` (duplicate branch): same as case 2.
6. `shape is not None`: passes through unchanged.
7. Fallback: sets `shape = ()`, `iterable = (iterable,)`.

After branching, if `shape` is a single `int` or `Integer`, wraps it into `(shape,)`. Validates that every dimension in `shape` is an `int` or `Integer`; raises `TypeError("Shape should contain integers only.")` otherwise. Returns `(tuple(shape), iterable)`.

**Returns:** `(tuple[int, ...], iterable)` — normalized shape and data.

---

##### `__len__(self)` (line 161)
**Signature:** `def __len__(self)`

Returns `self._loop_size`, the total number of elements in the array.

**Returns:** `int`.

---

##### `shape` property (line 177)
**Signature:** `@property def shape(self)`

Returns `self._shape`.

**Returns:** `tuple[int, ...]`.

---

##### `rank(self)` (line 193)
**Signature:** `def rank(self)`

Returns `self._rank`, the number of axes.

**Returns:** `int`.

---

##### `diff(self, *args)` (line 208)
**Signature:** `def diff(self, *args)`

Computes the derivative of every element in the array with respect to the given arguments. Maps `lambda x: x.diff(*args)` over all elements of `self`, then constructs a new array of the same type using the mapped results and `self.shape`.

**Returns:** A new NDimArray instance (same concrete subclass) containing differentiated elements.

---

##### `applyfunc(self, f)` (line 224)
**Signature:** `def applyfunc(self, f)`

Applies a callable `f` to every element of the array. Maps `f` over all elements and constructs a new array of the same type with the transformed data and original shape.

**Returns:** A new NDimArray instance (same concrete subclass).

---

##### `__str__(self)` (line 239)
**Signature:** `def __str__(self)`

Recursively formats the array as a nested Python list-of-lists string representation. Inner function `f(sh, shape_left, i, j)`:
- If `len(shape_left) == 1` (innermost dimension): returns `"[" + ", ".join([str(self[e]) for e in range(i, j)]) + "]"`.
- Otherwise: divides `sh //= shape_left[0]`, then recursively joins sub-blocks: `"[" + ", ".join([f(sh, shape_left[1:], i+e*sh, i+(e+1)*sh) for e in range(shape_left[0])]) + "]"`.

Initial call is `f(self._loop_size, self.shape, 0, self._loop_size)`.

**Returns:** `str` — nested bracket notation string.

---

##### `__repr__(self)` (line 260)
**Signature:** `def __repr__(self)`

Returns `self.__str__()`. Identical to the string representation.

**Returns:** `str`.

---

##### `tolist(self)` (line 263)
**Signature:** `def tolist(self)`

Converts the NDimArray into a nested Python list matching its shape structure. Inner function `f(sh, shape_left, i, j)`:
- If `len(shape_left) == 1` (innermost): returns `[self[e] for e in range(i, j)]`.
- Otherwise: divides `sh //= shape_left[0]`, iterates `e` from `0` to `shape_left[0]-1`, appending recursive calls `f(sh, shape_left[1:], i+e*sh, i+(e+1)*sh)` to a result list.

Initial call is `f(self._loop_size, self.shape, 0, self._loop_size)`.

**Returns:** Nested Python `list` matching the array's dimensionality.

---

##### `__add__(self, other)` (line 290)
**Signature:** `def __add__(self, other)`

Element-wise addition of two NDimArrays. Validates that `other` is an `NDimArray`; raises `TypeError(str(other))` otherwise. Checks shape equality; raises `ValueError("array shape mismatch")` if shapes differ. Computes `[i + j for i, j in zip(self, other)]`. Returns a new array of type `type(self)` with the result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).
**Raises:** `TypeError`, `ValueError`.

---

##### `__sub__(self, other)` (line 300)
**Signature:** `def __sub__(self, other)`

Element-wise subtraction. Same validation as `__add__`: checks `isinstance(other, NDimArray)`, raises `TypeError` if not; checks shape equality, raises `ValueError("array shape mismatch")` if not. Computes `[i - j for i, j in zip(self, other)]`. Returns new array of type `type(self)` with result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).
**Raises:** `TypeError`, `ValueError`.

---

##### `__mul__(self, other)` (line 310)
**Signature:** `def __mul__(self, other)`

Scalar multiplication. Imports `MatrixBase` from `sympy.matrices.matrices`. If `other` is a `collections.Iterable`, `NDimArray`, or `MatrixBase`, raises `ValueError("scalar expected, use tensorproduct(...) for tensorial product")`. Sympifies `other` via `sympify(other)`. Computes `[i * other for i in self]`. Returns new array of type `type(self)` with result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).
**Raises:** `ValueError`.

---

##### `__rmul__(self, other)` (line 319)
**Signature:** `def __rmul__(self, other)`

Reverse scalar multiplication. Same iterable/matrix check as `__mul__`, raising the same `ValueError`. Sympifies `other`. Computes `[other * i for i in self]`. Returns new array of type `type(self)` with result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).
**Raises:** `ValueError`.

---

##### `__div__(self, other)` (line 328)
**Signature:** `def __div__(self, other)`

Element-wise scalar division. Same iterable/matrix check as `__mul__`, raising `ValueError("scalar expected")` if violated. Sympifies `other`. Computes `[i / other for i in self]`. Returns new array of type `type(self)` with result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).
**Raises:** `ValueError`.

---

##### `__rdiv__(self, other)` (line 337)
**Signature:** `def __rdiv__(self, other)`

Always raises `NotImplementedError('unsupported operation on NDimArray')`. Reverse division is not supported.

**Raises:** `NotImplementedError`.

---

##### `__neg__(self)` (line 340)
**Signature:** `def __neg__(self)`

Element-wise negation. Computes `[-i for i in self]`. Returns new array of type `type(self)` with result list and `self.shape`.

**Returns:** New NDimArray instance (same concrete subclass).

---

##### `__eq__(self, other)` (line 344)
**Signature:** `def __eq__(self, other)`

Equality comparison. If `other` is not an `NDimArray`, returns `False`. Otherwise checks that both shapes are equal and the flattened element lists are identical: `(self.shape == other.shape) and (list(self) == list(other))`.

**Returns:** `bool`.

---

##### `__ne__(self, other)` (line 369)
**Signature:** `def __ne__(self, other)`

Returns `not self.__eq__(other)`.

**Returns:** `bool`.

---

##### `__truediv__ = __div__` (line 372)
Python 3 division alias. Maps `/` operator to `__div__`.

##### `__rtruediv__ = __rdiv__` (line 373)
Python 3 reverse division alias. Maps `__rtruediv__` to `__rdiv__`.

---

##### `_eval_diff(self, *args, **kwargs)` (line 375)
**Signature:** `def _eval_diff(self, *args, **kwargs)`

SymPy differentiation hook. Pops `"evaluate"` from `kwargs`, defaulting to `True`. If `evaluate` is truthy, returns `self.diff(*args)`. Otherwise returns `Derivative(self, *args, **kwargs)` (unevaluated derivative object).

**Returns:** Evaluated NDimArray or unevaluated `Derivative` object.

---

##### `_eval_transpose(self)` (line 381)
**Signature:** `def _eval_transpose(self)`

Matrix transpose for rank-2 arrays only. Checks that `self.rank() == 2`; raises `ValueError("array rank not 2")` otherwise. Imports `permutedims` from `.arrayop` and returns `permutedims(self, (1, 0))`, which swaps the two axes.

**Returns:** Permuted NDimArray instance.
**Raises:** `ValueError`.

---

##### `transpose(self)` (line 387)
**Signature:** `def transpose(self)`

Delegates to `self._eval_transpose()`. Returns the result directly.

**Returns:** Transposed NDimArray instance.

---

##### `_eval_conjugate(self)` (line 390)
**Signature:** `def _eval_conjugate(self)`

Element-wise complex conjugation. Calls `i.conjugate()` on each element, then constructs a new array via `self.func([...], self.shape)` — using the subclass's constructor (`func`) with the conjugated list and original shape.

**Returns:** New NDimArray instance (same concrete subclass) with conjugated elements.

---

##### `conjugate(self)` (line 393)
**Signature:** `def conjugate(self)`

Delegates to `self._eval_conjugate()`. Returns the result directly.

**Returns:** Conjugated NDimArray instance.

---

##### `_eval_adjoint(self)` (line 396)
**Signature:** `def _eval_adjoint(self)`

Adjoint (conjugate transpose). Calls `self.transpose().conjugate()` — first transposes, then conjugates each element of the result.

**Returns:** Adjoint NDimArray instance.

---

##### `adjoint(self)` (line 399)
**Signature:** `def adjoint(self)`

Delegates to `self._eval_adjoint()`. Returns the result directly.

**Returns:** Adjoint NDimArray instance.

---

### Class `ImmutableNDimArray(NDimArray, Basic)` (line 403)

**Description:** Immutable variant of NDimArray that also inherits from SymPy's `Basic` expression base class. Provides hashability and integration with SymPy's symbolic expression system.

#### Class-level attributes
- `_op_priority = 11.0` (`float`) — Priority value for operator overloading resolution within SymPy's expression system.

#### Instance attributes
Inherits all instance attribute contracts from `NDimArray`: `_loop_size`, `_shape`, `_rank`.

#### Methods

##### `__hash__(self)` (line 406)
**Signature:** `def __hash__(self)`

Delegates to `Basic.__hash__(self)`, enabling the array to be used as a dictionary key or in sets.

**Returns:** `int` — hash value from SymPy's Basic class.

---

## sympy/utilities/enumerative.py
I now have the complete source file (lines 1–1150). Here is the natural-language specification:

---

## Module-Level Preamble

### Imports
- `from __future__ import print_function, division`
- `from sympy.core.compatibility import range`

### Constants & Globals
None. All constants are local to functions or classes.

---

## Code Objects

### Class `PartComponent(object)`

**Header:** A plain Python class with no base classes (inherits from `object`) and no metaclass.

**Attributes (instance, initialized in `__init__`):**
- `c` (int): Component number — the index of a multiset component within that part. Initialized to `0`.
- `u` (int): The as-yet-unpartitioned amount for component `c` before this triple is allocated. Initialized to `0`.
- `v` (int): Amount of component `c` in the current part (`v <= u`). An invariant: the next higher triple for this component (if any) will have its `u` attribute equal to `self.u - self.v`.

**Methods:**

1. **`__init__(self)`** — Initializes all three attributes (`c`, `u`, `v`) to `0`.

2. **`__repr__(self)`** — Returns the string `'c:%d u:%d v:%d' % (self.c, self.u, self.v)`. Used for debugging/algorithm animation only.

3. **`__eq__(self, other)`** — Value-oriented equality: returns `True` if `other` is an instance of `PartComponent` and all three attributes (`c`, `u`, `v`) match; otherwise `False`.

4. **`__ne__(self, other)`** — Returns the negation of `self.__eq__(other)`. Defined for consistency with `__eq__`.

---

### Function `multiset_partitions_taocp(multiplicities)`

**Header:** A generator function taking one parameter:
- `multiplicities` (list[int]): List of integer multiplicities of the components of a multiset.

**Yields:** `state` — a 3-element list `[f, lpart, pstack]`, where:
- `f` is a frame array that segments `pstack` into parts.
- `lpart` (int) points to the base of the topmost part.
- `pstack` is a list of `PartComponent` objects.

The state object must be treated as read-only and consumed immediately via a visitor function at each iteration; accumulating states for later processing will not work because the state is modified in place.

**Implementation Logic (Knuth's algorithm 7.1.2.5M):**
1. Compute `m = len(multiplicities)` (number of distinct components) and `n = sum(multiplicities)` (total cardinality).
2. Allocate `pstack` as a list of `PartComponent()` objects of length `n * m + 1`, and `f` as `[0] * (n + 1)`.
3. **Step M1 (Initialize):** For each component index `j` in `range(m)`, set `pstack[j].c = j`, `pstack[j].u = multiplicities[j]`, `pstack[j].v = multiplicities[j]`. Set `f[0] = 0`, `a = 0`, `lpart = 0`, `f[1] = m`, `b = m` (current stack frame is from index `a` to `b - 1`).
4. **Outer loop (`while True`):**
   - **Step M2 (Subtract v from u):** Set `j = a`, `k = b`, `x = False`. While `j < b`: set `pstack[k].u = pstack[j].u - pstack[j].v`. If `pstack[k].u == 0`, set `x = True`. Else if not `x`: set `pstack[k].c = pstack[j].c`, `pstack[k].v = min(pstack[j].v, pstack[k].u)`, `x = (pstack[k].u < pstack[j].v)`, increment `k`. Else (`x` is True): set `pstack[k].c = pstack[j].c`, `pstack[k].v = pstack[k].u`, increment `k`. Increment `j`.
   - **Step M3 (Push if nonzero):** If `k > b`: set `a = b`, `b = k`, `lpart += 1`, `f[lpart + 1] = k`; loop back to M2. Else: break to M4.
   - **Step M4 (Visit):** Yield `[f, lpart, pstack]`.
   - **Step M5 (Decrease v):** Inner `while True`: set `j = b - 1`. While `pstack[j].v == 0`, decrement `j`. If `j == a` and `pstack[j].v == 1`: go to Step M6. Else: set `pstack[j].v -= 1`; for each `k` in `range(j + 1, b)`, set `pstack[k].v = pstack[k].u`; break back to M2.
   - **Step M6 (Backtrack):** If `lpart == 0`: return (end of enumeration). Else: set `lpart -= 1`, `b = a`, `a = f[lpart]`; loop back to M5.

---

### Function `factoring_visitor(state, primes)`

**Header:** Takes two parameters:
- `state` (list): The state yielded by `multiset_partitions_taocp`.
- `primes` (tuple/list[int]): Prime factors corresponding to the multiplicities used in enumeration.

**Returns:** A list of integers representing one factorization of a number into prime factors, where each integer is a product of primes raised to their multiplicities within that part.

**Implementation Logic:** Unpack `state` as `[f, lpart, pstack]`. For each part index `i` in `range(lpart + 1)`, compute the factor by iterating over `pstack[f[i]: f[i+1]]`; for each `PartComponent` with `ps.v > 0`, multiply into `factor` by `primes[ps.c] ** ps.v`. Append `factor` to the result list. Return the list.

---

### Function `list_visitor(state, components)`

**Header:** Takes two parameters:
- `state` (list): The state yielded by `multiset_partitions_taocp`.
- `components` (str/list/tuple): The actual component values corresponding to indices in the partition representation.

**Returns:** A list of lists representing the multiset partition, where each inner list contains the components belonging to one part.

**Implementation Logic:** Unpack `state` as `[f, lpart, pstack]`. For each part index `i` in `range(lpart + 1)`, build a `part` list by iterating over `pstack[f[i]: f[i+1]]`; for each `PartComponent` with `ps.v > 0`, extend `part` with `[components[ps.c]] * ps.v`. Append `part` to the result. Return the partition list.

---

### Class `MultisetPartitionTraverser()`

**Header:** A class with no base classes and no metaclass.

**Attributes (instance, initialized in `__init__`):**
- `debug` (bool): Debug tracing flag; defaults to `False`.
- `k1`, `k2`, `p1` (int): Tracing/statistics counters for the constrained decrement methods; all default to `0`.

**Methods:**

#### `__init__(self)`
Initializes `debug = False`, `k1 = 0`, `k2 = 0`, `p1 = 0`.

#### `db_trace(self, msg)`
If `self.debug` is True, prints `"DBG:"`, the message, and two representations of the current state: one via `list_visitor(state, 'abcdefghijklmnopqrstuvwxyz')` (mapping component indices to letters) and one via `animation_visitor(state)` (which must be defined externally or is a dead reference).

#### `_initialize_enumeration(self, multiplicities)`
Allocates and initializes the partition stack for enumeration. Sets `num_components = len(multiplicities)`, `cardinality = sum(multiplicities)`. Creates `self.pstack` as `[PartComponent()] * (num_components * cardinality + 1)`, `self.f = [0] * (cardinality + 1)`. Initializes the first part: for each `j` in `range(num_components)`, set `self.pstack[j].c = j`, `.u = multiplicities[j]`, `.v = multiplicities[j]`. Sets `self.f[0] = 0`, `self.f[1] = num_components`, `self.lpart = 0`.

#### `decrement_part(self, part)`
**Parameter:** `part` (list[PartComponent]): A slice of `pstack` representing one part.

**Returns:** `True` if the part was successfully decremented; `False` otherwise.

**Logic:** Treats the `v` values as a multi-digit integer (least significant on the right). Scans from right to left (`range(plen - 1, -1, -1)`). At index `j`: if `(j == 0 and part[j].v > 1) or (j > 0 and part[j].v > 0)`, decrement `part[j].v` by 1; reset all trailing parts (`k` in `range(j + 1, plen)`) to their maximum: `part[k].v = part[k].u`; return `True`. If no such index is found (the part is `[1, 0, ..., 0]`), return `False`.

#### `decrement_part_small(self, part, ub)`
**Parameters:** `part` (list[PartComponent]), `ub` (int): Maximum allowed number of parts.

**Returns:** `True` if successfully decremented; `False` otherwise.

**Logic:** Three pruning tests before attempting decrement:
1. If `self.lpart >= ub - 1`, return `False` (incrementing `p1`).
2. Scan right to left. At index `j == 0`: if `(part[0].v - 1) * (ub - self.lpart) < part[0].u`, return `False` (incrementing `k1`) — this is Knuth's exercise 7.2.1.5.69 answer: the spread would exceed `ub`.
3. When a decrementable index is found, perform the same decrement and trailing reset as `decrement_part`. Then check an oddball case: if `plen > 1` and `part[1].v == 0` and `(part[0].u - part[0].v) == (ub - self.lpart - 1) * part[0].v`, return `False` (incrementing `k2`) — exactly enough room for the leading component but not the second. Otherwise return `True`.
4. If no decrementable index found, return `False`.

#### `decrement_part_large(self, part, amt, lb)`
**Parameters:** `part` (list[PartComponent]), `amt` (int: 0 or 1), `lb` (int): Minimum number of parts must be strictly greater than this value.

**Returns:** `True` if successfully decremented; `False` otherwise.

**Logic:** If `amt == 1`, first call `self.decrement_part(part)` and return its result immediately if it fails. Then enforce the "sufficient unallocated multiplicity" constraint: compute `min_unalloc = lb - self.lpart`. If `min_unalloc <= 0`, return `True`. Compute `total_mult = sum(pc.u for pc in part)`, `total_alloc = sum(pc.v for pc in part)`. If `total_mult <= min_unalloc`, return `False` (not enough multiplicity to ever reach `lb`). Compute `deficit = min_unalloc - (total_mult - total_alloc)`. If `deficit <= 0`, return `True`. Otherwise, scan right to left: at index `i == 0`: if `part[0].v > deficit`, set `part[0].v -= deficit` and return `True`; else return `False`. At `i > 0`: if `part[i].v >= deficit`, set `part[i].v -= deficit` and return `True`; else subtract `part[i].v` from `deficit` and set `part[i].v = 0`.

#### `decrement_part_range(self, part, lb, ub)`
**Parameters:** `part` (list[PartComponent]), `lb` (int), `ub` (int).

**Returns:** `True` if successfully decremented; `False` otherwise.

**Logic:** Returns the result of `self.decrement_part_small(part, ub) and self.decrement_part_large(part, 0, lb)`. The short-circuit evaluation is critical: `_small` must be called first (it performs the actual decrement), then `_large` enforces the lower bound constraint with `amt=0` (no additional decrement).

#### `spread_part_multiplicity(self)`
**Returns:** `True` if a new part was created; `False` otherwise.

**Logic:** Get `j = self.f[self.lpart]` (base of current top part), `k = self.f[self.lpart + 1]` (upper bound / potential base of next part). Save `base = k`. Set `changed = False`. For each index in `range(self.f[self.lpart], self.f[self.lpart + 1])`: set `self.pstack[k].u = self.pstack[j].u - self.pstack[j].v`. If `self.pstack[k].u == 0`, set `changed = True`. Else: set `self.pstack[k].c = self.pstack[j].c`; if `changed` is True, set `self.pstack[k].v = self.pstack[k].u`; else (maintaining ordering): if `self.pstack[k].u < self.pstack[j].v`, set `self.pstack[k].v = self.pstack[k].u` and `changed = True`; else set `self.pstack[k].v = self.pstack[j].v`. Increment `k`. If `k > base`: increment `self.lpart`, set `self.f[self.lpart + 1] = k`, return `True`. Else return `False`.

#### `top_part(self)`
**Returns:** A slice of `pstack` representing the current top part: `self.pstack[self.f[self.lpart]: self.f[self.lpart + 1]]`.

#### `enum_all(self, multiplicities)`
**Parameter:** `multiplicities` (list[int]).

**Yields:** State objects `[self.f, self.lpart, self.pstack]`, same format as `multiset_partitions_taocp`.

**Logic:** Call `_initialize_enumeration(multiplicities)`. Outer `while True`:
- While `self.spread_part_multiplicity()` returns True, loop (spreading unallocated multiplicity into new parts).
- Yield `[self.f, self.lpart, self.pstack]` (visit).
- Inner `while not self.decrement_part(self.top_part())`: if `self.lpart == 0`, return; else decrement `self.lpart`.

#### `enum_small(self, multiplicities, ub)`
**Parameters:** `multiplicities` (list[int]), `ub` (int): Maximum number of parts.

**Yields:** State objects for partitions with at most `ub` parts.

**Logic:** Set `self.discarded = 0`. If `ub <= 0`, return. Call `_initialize_enumeration(multiplicities)`. Outer `while True`:
- `good_partition = True`. While `self.spread_part_multiplicity()`: if `self.lpart >= ub`, set `self.discarded += 1`, `good_partition = False`, `self.lpart = ub - 2`, break.
- If `good_partition`, yield `[self.f, self.lpart, self.pstack]`.
- Inner `while not self.decrement_part_small(self.top_part(), ub)`: if `self.lpart == 0`, return; else decrement `self.lpart`.

#### `enum_large(self, multiplicities, lb)`
**Parameters:** `multiplicities` (list[int]), `lb` (int): Partitions must have more than `lb` parts.

**Yields:** State objects for partitions with strictly more than `lb` parts.

**Logic:** Set `self.discarded = 0`. If `lb >= sum(multiplicities)`, return. Call `_initialize_enumeration(multiplicities)`. Call `self.decrement_part_large(self.top_part(), 0, lb)` to enforce the lower bound on the initial state. Outer `while True`:
- `good_partition = True`. While `self.spread_part_multiplicity()`: if not `self.decrement_part_large(self.top_part(), 0, lb)`, set `self.discarded += 1`, `good_partition = False`, break.
- If `good_partition`, yield `[self.f, self.lpart, self.pstack]`.
- Inner `while not self.decrement_part_large(self.top_part(), 1, lb)`: if `self.lpart == 0`, return; else decrement `self.lpart`.

#### `enum_range(self, multiplicities, lb, ub)`
**Parameters:** `multiplicities` (list[int]), `lb` (int), `ub` (int): Partitions must have strictly more than `lb` and at most `ub` parts.

**Yields:** State objects for partitions with `lb < num(parts) <= ub`.

**Logic:** Set `self.discarded = 0`. If `ub <= 0` or `lb >= sum(multiplicities)`, return. Call `_initialize_enumeration(multiplicities)`. Call `self.decrement_part_large(self.top_part(), 0, lb)` to enforce the lower bound on initial state. Outer `while True`:
- `good_partition = True`. While `self.spread_part_multiplicity()`: if not `self.decrement_part_large(self.top_part(), 0, lb)`, set `self.discarded += 1`, `good_partition = False`, break; elif `self.lpart >= ub`, set `self.discarded += 1`, `good_partition = False`, `self.lpart = ub - 2`, break.
- If `good_partition`, yield `[self.f, self.lpart, self.pstack]`.
- Inner `while not self.decrement_part_range(self.top_part(), lb, ub)`: if `self.lpart == 0`, return; else decrement `self.lpart`.

#### `count_partitions_slow(self, multiplicities)`
**Parameter:** `multiplicities` (list[int]).

**Returns:** An integer — the total number of partitions of the multiset.

**Logic:** Set `self.pcount = 0`. Call `_initialize_enumeration(multiplicities)`. Outer `while True`: while `self.spread_part_multiplicity()`, loop; increment `self.pcount`; inner `while not self.decrement_part(self.top_part())`: if `self.lpart == 0`, return `self.pcount`; else decrement `self.lpart`.

#### `count_partitions(self, multiplicities)`
**Parameter:** `multiplicities` (list[int]).

**Returns:** An integer — the total number of partitions of the multiset. Uses dynamic programming for efficiency.

**Logic:** Set `self.pcount = 0`, `self.dp_stack = []`. If `self` lacks attribute `dp_map`, initialize `self.dp_map = {}` (a dict mapping part keys to counts; persists across calls). Call `_initialize_enumeration(multiplicities)`. Compute initial `pkey = part_key(self.top_part())`; push `[(pkey, 0)]` onto `self.dp_stack`. Outer `while True`:
- While `self.spread_part_multiplicity()`: compute `pkey = part_key(self.top_part())`. If `pkey in self.dp_map`, add `(self.dp_map[pkey] - 1)` to `self.pcount`, decrement `self.lpart`, break (skip the leaf that would have been counted). Else, push `[(pkey, self.pcount)]` onto `self.dp_stack`.
- Increment `self.pcount` (M4: count a leaf partition).
- Inner `while not self.decrement_part(self.top_part())`: pop all `(key, oldcount)` pairs from `self.dp_stack`; for each, set `self.dp_map[key] = self.pcount - oldcount`. If `self.lpart == 0`, return `self.pcount`; else decrement `self.lpart`.
- After successful decrement: compute `pkey = part_key(self.top_part())` and append `(pkey, self.pcount)` to `self.dp_stack[-1]`.

---

### Function `part_key(part)`

**Parameter:** `part` (list[PartComponent]): A slice of `pstack` representing one part.

**Returns:** A tuple of integers — a compact key for memoization in `count_partitions`.

**Logic:** For each `ps` in `part`, append `ps.u` then `ps.v` to a list. Return the resulting tuple as a hashable key. The component number (`c`) is intentionally excluded because it does not affect partition counts (only multiplicities matter).