## sympy/assumptions/ask.py
Now I have the full file content (1530 lines). Let me write the comprehensive natural-language specification.

---

# Module Specification: `sympy/assumptions/ask.py`

## 1. Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from sympy.assumptions.assume import (global_assumptions, Predicate, AppliedPredicate)
from sympy.core import sympify
from sympy.core.cache import cacheit
from sympy.core.decorators import deprecated
from sympy.core.relational import Relational
from sympy.logic.boolalg import (to_cnf, And, Not, Or, Implies, Equivalent, BooleanFunction, BooleanAtom)
from sympy.logic.inference import satisfiable
from sympy.utilities.decorator import memoize_property
```

### Constants & Globals

- **`deprecated_predicates`** — A list of three strings: `['bounded', 'infinity', 'infinitesimal']`. These are predicate names that have been superseded by newer predicates.

- **`predicate_storage`** — An empty dict `{}` used as the backing store for memoized Predicate objects, ensuring singleton identity per predicate name.

- **`predicate_memo`** — A `memoize_property` decorator instance wrapping `predicate_storage`. Applied to every property method of `AssumptionKeys` so that each predicate is instantiated exactly once and reused across all accesses.

### Final Import (line 1529–1530)

```python
from sympy.assumptions.ask_generated import (get_known_facts_dict, get_known_facts_cnf)
```

This imports two cached functions from a generated module that are produced by `compute_known_facts()`. These override the local definitions of `get_known_facts_dict` and `get_known_facts_cnf` at runtime.

---

## 2. Code Objects

### Class: `AssumptionKeys(object)`

A class providing all supported assumption predicate keys via property methods decorated with `@predicate_memo`. Each property returns a new `Predicate(name)` instance, memoized so that repeated access yields the same object (critical for handler registration). The class contains **40+** properties organized into logical groups:

#### Number-type predicates

| Property | Predicate name | Returns |
|---|---|---|
| `hermitian` | `'hermitian'` | `Predicate('hermitian')` — x belongs to Hermitian operators |
| `antihermitian` | `'antihermitian'` | `Predicate('antihermitian')` — x is of the form h·I where h is Hermitian |
| `real` | `'real'` | `Predicate('real')` — x ∈ (-∞, ∞); excludes infinities; every real is complex and finite |
| `extended_real` | `'extended_real'` | `Predicate('extended_real')` — x is real or {-∞, +∞} |
| `imaginary` | `'imaginary'` | `Predicate('imaginary')` — x = r·I for some real r; 0 is not imaginary |
| `complex` | `'complex'` | `Predicate('complex')` — x ∈ ℂ; every complex number is finite |
| `algebraic` | `'algebraic'` | `Predicate('algebraic')` — root of some polynomial in ℚ[x] |
| `transcendental` | `'transcendental'` | `Predicate('transcendental')` — not algebraic (real or complex) |
| `integer` | `'integer'` | `Predicate('integer')` — x ∈ ℤ |
| `rational` | `'rational'` | `Predicate('rational')` — x ∈ ℚ |
| `irrational` | `'irrational'` | `Predicate('irrational')` — real but not rational |
| `finite` | `'finite'` | `Predicate('finite')` — neither ∞ nor NaN; bounded absolute value |
| `infinite` | `'infinite'` | `Predicate('infinite')` — \|x\| = ∞ |

#### Deprecated predicates (wrap the above)

| Property | Predicate name | Decorator | Returns |
|---|---|---|---|
| `bounded` | `'finite'` | `@deprecated(useinstead="finite", issue=9425, deprecated_since_version="1.0")` | `Predicate('finite')` |
| `infinity` | `'infinite'` | `@deprecated(useinstead="infinite", issue=9426, deprecated_since_version="1.0")` | `Predicate('infinite')` |
| `infinitesimal` | `'zero'` | `@deprecated(useinstead="zero", issue=9675, deprecated_since_version="1.0")` | `Predicate('zero')` |

#### Sign predicates (all imply `Q.real`)

| Property | Predicate name | Returns |
|---|---|---|
| `positive` | `'positive'` | `Predicate('positive')` — real and x > 0; ∞ is not positive |
| `negative` | `'negative'` | `Predicate('negative')` — real and x < 0; -∞ is not negative |
| `zero` | `'zero'` | `Predicate('zero')` — value of x equals zero |
| `nonzero` | `'nonzero'` | `Predicate('nonzero')` — real and x ≠ 0; equivalent to `positive \| negative` |
| `nonpositive` | `'nonpositive'` | `Predicate('nonpositive')` — real and not positive (i.e., negative or zero) |
| `nonnegative` | `'nonnegative'` | `Predicate('nonnegative')` — real and not negative (i.e., positive or zero) |

#### Number-theoretic predicates

| Property | Predicate name | Returns |
|---|---|---|
| `even` | `'even'` | `Predicate('even')` — even integer |
| `odd` | `'odd'` | `Predicate('odd')` — odd integer |
| `prime` | `'prime'` | `Predicate('prime')` — natural number > 1 with no positive divisors other than 1 and itself |
| `composite` | `'composite'` | `Predicate('composite')` — positive integer with at least one divisor other than 1 and itself |

#### Generic predicate

| Property | Predicate name | Returns |
|---|---|---|
| `is_true` | `'is_true'` | `Predicate('is_true')` — x evaluates to True; only meaningful for predicates |

#### Matrix predicates (all imply square where noted)

| Property | Predicate name | Returns |
|---|---|---|
| `symmetric` | `'symmetric'` | `Predicate('symmetric')` — square matrix equal to its transpose |
| `invertible` | `'invertible'` | `Predicate('invertible')` — square matrix with nonzero determinant |
| `orthogonal` | `'orthogonal'` | `Predicate('orthogonal')` — MᵀM = MMᵀ = I; implies positive_definite and unitary |
| `unitary` | `'unitary'` | `Predicate('unitary')` — MᴴM = MMᴴ = I (conjugate transpose); implies normal, invertible |
| `positive_definite` | `'positive_definite'` | `Predicate('positive_definite')` — ZᵀMZ > 0 for all nonzero real vectors Z; implies invertible |
| `upper_triangular` | `'upper_triangular'` | `Predicate('upper_triangular')` — M[i,j] = 0 for i < j |
| `lower_triangular` | `'lower_triangular'` | `Predicate('lower_triangular')` — M[i,j] = 0 for i > j |
| `diagonal` | `'diagonal'` | `Predicate('diagonal')` — all off-diagonal entries are zero; implies normal, upper/lower triangular, symmetric |
| `fullrank` | `'fullrank'` | `Predicate('fullrank')` — all rows and columns linearly independent |
| `square` | `'square'` | `Predicate('square')` — same number of rows and columns |
| `integer_elements` | `'integer_elements'` | `Predicate('integer_elements')` — all elements are integers; implies real_elements, complex_elements |
| `real_elements` | `'real_elements'` | `Predicate('real_elements')` — all elements are real numbers; implies complex_elements |
| `complex_elements` | `'complex_elements'` | `Predicate('complex_elements')` — all elements are complex numbers |
| `singular` | `'singular'` | `Predicate('singular')` — determinant is 0; equivalent to ~invertible |
| `normal` | `'normal'` | `Predicate('normal')` — commutes with its conjugate transpose; implies square |
| `triangular` | `'triangular'` | `Predicate('triangular')` — either upper or lower triangular |
| `unit_triangular` | `'unit_triangular'` | `Predicate('unit_triangular')` — triangular matrix with 1s on the diagonal |

---

### Module-level instance: `Q = AssumptionKeys()`

A singleton instance of `AssumptionKeys`, providing attribute access to all predicates (e.g., `Q.hermitian`, `Q.real(x)`, etc.).

---

### Function: `_extract_facts(expr, symbol, check_reversed_rel=True)`

**Purpose:** Extract facts relevant to a given `symbol` from an assumption expression.

**Parameters:**
- `expr` — A boolean expression (assumption).
- `symbol` — The target SymPy object/symbol to extract facts about.
- `check_reversed_rel` — Boolean flag; if True and expr is a Relational, also try extracting from the reversed relation.

**Logic:**
1. If `symbol` is a `Relational` and `check_reversed_rel` is True, recursively call `_extract_facts(expr, symbol.reversed, False)`. Return that result if not None.
2. If `expr` is a Python `bool`, return `None` (no facts to extract).
3. If `expr` does not contain `symbol` (`not expr.has(symbol)`), return `None`.
4. If `expr` is an `AppliedPredicate` and its argument equals `symbol`, return `expr.func` (the predicate itself, e.g., `Q.positive`). Otherwise return `None`.
5. If `expr` is a `Not` wrapping an `And` or `Or`, push the negation inward using De Morgan's law: convert to `Or` of negated args if original was `And`, or `And` of negated args if original was `Or`.
6. Recursively extract facts from each sub-argument: `args = [_extract_facts(arg, symbol) for arg in expr.args]`.
7. If `expr` is an `And`, filter out None values; return the And of remaining non-None results (or None if empty).
8. Otherwise, if all args are non-None and at least one exists, return `expr.func(*args)` (reconstructing the original boolean structure with extracted sub-facts).

**Return:** A boolean expression representing the extracted facts about `symbol`, or `None` if no relevant facts found.

---

### Function: `ask(proposition, assumptions=True, context=global_assumptions)`

**Purpose:** Main inference entry point — determine whether a proposition follows from given assumptions and global context.

**Parameters:**
- `proposition` — A boolean expression or `AppliedPredicate` to prove.
- `assumptions` — A boolean expression of assumed facts (default: `True`).
- `context` — Global assumptions from `global_assumptions` (default).

**Logic:**
1. Import `satask` from `sympy.assumptions.satask`.
2. Validate that `proposition` is an instance of `(BooleanFunction, AppliedPredicate, bool, BooleanAtom)`; raise `TypeError` otherwise.
3. Validate that `assumptions` is an instance of `(BooleanFunction, AppliedPredicate, bool, BooleanAtom)`; raise `TypeError` otherwise.
4. If `proposition` is an `AppliedPredicate`, extract `key = proposition.func` and `expr = sympify(proposition.arg)`. Otherwise, set `key = Q.is_true` and `expr = sympify(proposition)`.
5. Combine assumptions with context: `assumptions = And(assumptions, And(*context))`, then convert to CNF via `to_cnf()`.
6. Extract local facts relevant to `expr`: `local_facts = _extract_facts(assumptions, expr)`.
7. Load known facts in CNF form and dictionary lookup: `known_facts_cnf = get_known_facts_cnf()` and `known_facts_dict = get_known_facts_dict()`.
8. If `local_facts` exists and the conjunction of local facts with known facts is unsatisfiable (`satisfiable(And(local_facts, known_facts_cnf)) is False`), raise `ValueError("inconsistent assumptions %s" % assumptions)`.
9. **Direct resolution:** Call `key(expr)._eval_ask(assumptions)` — the predicate's own handler method. If it returns a non-None result, return `bool(res)`.
10. If `local_facts` is None (no facts extracted), delegate to `satask(proposition, assumptions=assumptions, context=context)` and return its result.
11. **Straight-forward conclusion lookup:**
    - If `local_facts.is_Atom`: check if `key ∈ known_facts_dict[local_facts]` → return True; or `Not(key) ∈ known_facts_dict[local_facts]` → return False.
    - If `local_facts` is an `And` and all its args are keys in the dict: for each assum in local_facts.args, if it's an Atom check direct lookup (same as above); if it's a `Not(Atom)`, reverse the logic (key ∈ dict → False; Not(key) ∈ dict → True).
    - If `key` is a Predicate and `local_facts` is `Not(atom)` where atom.is_Atom: if `atom ∈ known_facts_dict[key]` → return False.
12. **Full logical inference:** Call `ask_full_inference(key, local_facts, known_facts_cnf)`. If it returns None (undecidable), delegate to `satask(proposition, assumptions=assumptions, context=context)`. Otherwise return the result.

**Return:** `True`, `False`, or delegated SAT solver result.

---

### Function: `ask_full_inference(proposition, assumptions, known_facts_cnf)`

**Purpose:** Perform full logical inference using satisfiability checking against known facts.

**Parameters:**
- `proposition` — The proposition to prove (a Predicate).
- `assumptions` — Extracted local facts about the expression.
- `known_facts_cnf` — All known implication/equivalence rules in CNF form.

**Logic:**
1. If `satisfiable(And(known_facts_cnf, assumptions, proposition))` is False (i.e., the conjunction is unsatisfiable), return `False` — the proposition cannot be true given the facts.
2. If `satisfiable(And(known_facts_cnf, assumptions, Not(proposition)))` is False (i.e., assuming the negation leads to contradiction), return `True` — the proposition must be true.
3. Otherwise, return `None` — undecidable with current knowledge.

**Return:** `True`, `False`, or `None`.

---

### Function: `register_handler(key, handler)`

**Purpose:** Register an assumption handler for a given predicate key in the ask system.

**Parameters:**
- `key` — A string name of a predicate (e.g., `'mersenne'`) or a `Predicate` object.
- `handler` — A class inheriting from `AskHandler`.

**Logic:**
1. If `key` is already a `Predicate`, extract its name: `key = key.name`.
2. Look up the predicate on Q: `Qkey = getattr(Q, key, None)`.
3. If found (`Qkey is not None`), call `Qkey.add_handler(handler)` to register it.
4. If not found, create a new Predicate and attach it to Q: `setattr(Q, key, Predicate(key, handlers=[handler]))`.

---

### Function: `remove_handler(key, handler)`

**Purpose:** Remove an assumption handler from the ask system.

**Parameters:** Same as `register_handler`.

**Logic:**
1. If `key` is a `Predicate`, extract its name.
2. Call `getattr(Q, key).remove_handler(handler)`.

---

### Function: `single_fact_lookup(known_facts_keys, known_facts_cnf)`

**Purpose:** Compute a quick-lookup mapping from each predicate to all predicates it implies (one-step derivations).

**Parameters:**
- `known_facts_keys` — List of all Predicate objects.
- `known_facts_cnf` — Known facts in CNF form.

**Logic:**
1. Initialize an empty dict `mapping`.
2. For each `key` in `known_facts_keys`: set `mapping[key] = {key}` (reflexive).
3. For every other `other_key` in `known_facts_keys` where `other_key != key`, call `ask_full_inference(other_key, key, known_facts_cnf)`. If it returns True (i.e., key implies other_key), add `other_key` to `mapping[key]`.
4. Return the mapping dict.

**Return:** A dict mapping each Predicate to a set of Predicates it implies (including itself).

---

### Function: `compute_known_facts(known_facts, known_facts_keys)`

**Purpose:** Generate Python source code for a cached module containing pre-compiled known facts in CNF form and a compressed lookup dictionary. This output is written to `sympy/assumptions/ask_generated.py` by the script `./bin/ask_update.py`.

**Parameters:**
- `known_facts` — The conjunction of all implication/equivalence rules (from `get_known_facts()`).
- `known_facts_keys` — List of all Predicate objects (from `get_known_facts_keys()`).

**Logic:**
1. Import `dedent`, `wrap` from `textwrap`.
2. Define a template string `fact_string` containing:
   - A docstring header warning not to manually edit the file.
   - Imports for `cacheit`, `And`, and `Q`.
   - A `@cacheit`-decorated function `get_known_facts_cnf()` returning `And(...)` with CNF args.
   - A `@cacheit`-decorated function `get_known_facts_dict()` returning a dict mapping predicate names to sets of implied predicates.
3. Convert `known_facts` to CNF: `cnf = to_cnf(known_facts)`.
4. Format the CNF args as a comma-separated string with line breaks and indentation.
5. Compute the single-fact lookup mapping via `single_fact_lookup(known_facts_keys, cnf)`.
6. Sort items by string representation; format keys and values (sets of predicate names).
7. Wrap long lines using `textwrap.wrap` with 8-space hanging indent.
8. Substitute the CNF string and dict string into the template via `%` formatting.

**Return:** A formatted Python source code string ready to be written to a file.

---

### Handler Registration Loop (lines 1425–1465)

A list `_handlers` of 38 `(name, handler_module_path)` tuples maps each predicate name to its handler module path under `sympy.assumptions.handlers`. The template is `'sympy.assumptions.handlers.%s'`. After the loop:

```python
for name, value in _handlers:
    register_handler(name, _val_template % value)
```

This registers all built-in handlers at module import time. The mapping is:

| Predicate | Handler Module Path |
|---|---|
| `antihermitian` | `sympy.assumptions.handlers.sets.AskAntiHermitianHandler` |
| `finite` | `sympy.assumptions.handlers.calculus.AskFiniteHandler` |
| `commutative` | `sympy.assumptions.handlers.AskCommutativeHandler` |
| `complex` | `sympy.assumptions.handlers.sets.AskComplexHandler` |
| `composite` | `sympy.assumptions.handlers.ntheory.AskCompositeHandler` |
| `even` | `sympy.assumptions.handlers.ntheory.AskEvenHandler` |
| `extended_real` | `sympy.assumptions.handlers.sets.AskExtendedRealHandler` |
| `hermitian` | `sympy.assumptions.handlers.sets.AskHermitianHandler` |
| `imaginary` | `sympy.assumptions.handlers.sets.AskImaginaryHandler` |
| `integer` | `sympy.assumptions.handlers.sets.AskIntegerHandler` |
| `irrational` | `sympy.assumptions.handlers.sets.AskIrrationalHandler` |
| `rational` | `sympy.assumptions.handlers.sets.AskRationalHandler` |
| `negative` | `sympy.assumptions.handlers.order.AskNegativeHandler` |
| `nonzero` | `sympy.assumptions.handlers.order.AskNonZeroHandler` |
| `nonpositive` | `sympy.assumptions.handlers.order.AskNonPositiveHandler` |
| `nonnegative` | `sympy.assumptions.handlers.order.AskNonNegativeHandler` |
| `zero` | `sympy.assumptions.handlers.order.AskZeroHandler` |
| `positive` | `sympy.assumptions.handlers.order.AskPositiveHandler` |
| `prime` | `sympy.assumptions.handlers.ntheory.AskPrimeHandler` |
| `real` | `sympy.assumptions.handlers.sets.AskRealHandler` |
| `odd` | `sympy.assumptions.handlers.ntheory.AskOddHandler` |
| `algebraic` | `sympy.assumptions.handlers.sets.AskAlgebraicHandler` |
| `is_true` | `sympy.assumptions.handlers.common.TautologicalHandler` |
| `symmetric` | `sympy.assumptions.handlers.matrices.AaskSymmetricHandler` |
| `invertible` | `sympy.assumptions.handlers.matrices.AskInvertibleHandler` |
| `orthogonal` | `sympy.assumptions.handlers.matrices.AskOrthogonalHandler` |
| `unitary` | `sympy.assumptions.handlers.matrices.AskUnitaryHandler` |
| `positive_definite` | `sympy.assumptions.handlers.matrices.AskPositiveDefiniteHandler` |
| `upper_triangular` | `sympy.assumptions.handlers.matrices.AskUpperTriangularHandler` |
| `lower_triangular` | `sympy.assumptions.handlers.matrices.AskLowerTriangularHandler` |
| `diagonal` | `sympy.assumptions.handlers.matrices.AskDiagonalHandler` |
| `fullrank` | `sympy.assumptions.handlers.matrices.AskFullRankHandler` |
| `square` | `sympy.assumptions.handlers.matrices.AskSquareHandler` |
| `integer_elements` | `sympy.assumptions.handlers.matrices.AskIntegerElementsHandler` |
| `real_elements` | `sympy.assumptions.handlers.matrices.AskRealElementsHandler` |
| `complex_elements` | `sympy.assumptions.handlers.matrices.AskComplexElementsHandler` |

---

### Function: `get_known_facts_keys()` (decorated with `@cacheit`)

**Purpose:** Return a list of all Predicate objects corresponding to non-deprecated properties on `AssumptionKeys`.

**Logic:**
1. Iterate over `Q.__class__.__dict__` attribute names.
2. Filter out attributes starting with `'__'` and those in `deprecated_predicates`.
3. For each remaining name, get the predicate via `getattr(Q, attr)`.

**Return:** A list of Predicate objects (all non-deprecated predicates).

---

### Function: `get_known_facts()` (decorated with `@cacheit`)

**Purpose:** Return a single `And` expression containing all known logical facts about assumptions — implications and equivalences between predicates. This is the knowledge base used by the inference engine.

**Contents (28 rules):**

1. `Implies(Q.infinite, ~Q.finite)`
2. `Implies(Q.real, Q.complex)`
3. `Implies(Q.real, Q.hermitian)`
4. `Equivalent(Q.extended_real, Q.real | Q.infinite)`
5. `Equivalent(Q.even | Q.odd, Q.integer)`
6. `Implies(Q.even, ~Q.odd)`
7. `Equivalent(Q.prime, Q.integer & Q.positive & ~Q.composite)`
8. `Implies(Q.integer, Q.rational)`
9. `Implies(Q.rational, Q.algebraic)`
10. `Implies(Q.algebraic, Q.complex)`
11. `Equivalent(Q.transcendental | Q.algebraic, Q.complex)`
12. `Implies(Q.transcendental, ~Q.algebraic)`
13. `Implies(Q.imaginary, Q.complex & ~Q.real)`
14. `Implies(Q.imaginary, Q.antihermitian)`
15. `Implies(Q.antihermitian, ~Q.hermitian)`
16. `Equivalent(Q.irrational | Q.rational, Q.real)`
17. `Implies(Q.irrational, ~Q.rational)`
18. `Implies(Q.zero, Q.even)`
19. `Equivalent(Q.real, Q.negative | Q.zero | Q.positive)`
20. `Implies(Q.zero, ~Q.negative & ~Q.positive)`
21. `Implies(Q.negative, ~Q.positive)`
22. `Equivalent(Q.nonnegative, Q.zero | Q.positive)`
23. `Equivalent(Q.nonpositive, Q.zero | Q.negative)`
24. `Equivalent(Q.nonzero, Q.negative | Q.positive)`
25. `Implies(Q.orthogonal, Q.positive_definite)`
26. `Implies(Q.orthogonal, Q.unitary)`
27. `Implies(Q.unitary & Q.real, Q.orthogonal)`
28. `Implies(Q.unitary, Q.normal)`
29. `Implies(Q.unitary, Q.invertible)`
30. `Implies(Q.normal, Q.square)`
31. `Implies(Q.diagonal, Q.normal)`
32. `Implies(Q.positive_definite, Q.invertible)`
33. `Implies(Q.diagonal, Q.upper_triangular)`
34. `Implies(Q.diagonal, Q.lower_triangular)`
35. `Implies(Q.lower_triangular, Q.triangular)`
36. `Implies(Q.upper_triangular, Q.triangular)`
37. `Implies(Q.triangular, Q.upper_triangular | Q.lower_triangular)`
38. `Implies(Q.upper_triangular & Q.lower_triangular, Q.diagonal)`
39. `Implies(Q.diagonal, Q.symmetric)`
40. `Implies(Q.unit_triangular, Q.triangular)`
41. `Implies(Q.invertible, Q.fullrank)`
42. `Implies(Q.invertible, Q.square)`
43. `Implies(Q.symmetric, Q.square)`
44. `Implies(Q.fullrank & Q.square, Q.invertible)`
45. `Equivalent(Q.invertible, ~Q.singular)`
46. `Implies(Q.integer_elements, Q.real_elements)`
47. `Implies(Q.real_elements, Q.complex_elements)`

**Return:** An `And` of all 47 rules above.

---

### Final Import (overrides local definitions)

```python
from sympy.assumptions.ask_generated import (get_known_facts_dict, get_known_facts_cnf)
```

These two functions are generated by running `compute_known_facts()` and written to `ask_generated.py`. They provide cached versions of the known-facts dictionary lookup map and CNF knowledge base, respectively. At runtime, these imported names shadow any local definitions (there are no local definitions with these exact names — they are only produced as output strings by `compute_known_facts`).

## sympy/assumptions/ask_generated.py
Now I have the full file content. Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports
- `from sympy.core.cache import cacheit` — decorator for memoizing function results.
- `from sympy.logic.boolalg import And` — logical conjunction class used to build CNF expressions.
- `from sympy.assumptions.ask import Q` — the assumption query predicate object; all predicates referenced in this file are attributes of `Q`.

### Constants & Globals
None beyond the two functions defined below. The module is entirely composed of these two cached accessor functions and their docstring.

---

## Code Objects

### Function: `get_known_facts_cnf()`

**Signature:** `def get_known_facts_cnf() -> And`

**Decorator:** `@cacheit` — the result is memoized after first call.

**Docstring (lines 1–7):** States that this file's contents are the return value of `sympy.assumptions.ask.compute_known_facts`. Warns not to manually edit; instead run `./bin/ask_update.py`.

**Implementation Logic:**
Returns a single `And` expression representing all known logical facts about SymPy predicates in **Conjunctive Normal Form (CNF)**. The `And` wraps 72 clauses, each of which is either:
- A binary disjunction `Q.a | Q.b` (meaning "at least one of a or b must hold"), or
- A binary negated disjunction `~Q.a | ~Q.b` (meaning "a and b cannot both be true"), or
- A ternary disjunction `Q.a | Q.b | Q.c`.

The 72 clauses, in source order, are:

1. `Q.invertible | Q.singular` — every matrix is either invertible or singular.
2. `Q.algebraic | ~Q.rational` — if rational then algebraic.
3. `Q.antihermitian | ~Q.imaginary` — if imaginary then antihermitian.
4. `Q.complex | ~Q.algebraic` — if algebraic then complex.
5. `Q.complex | ~Q.imaginary` — if imaginary then complex.
6. `Q.complex | ~Q.real` — if real then complex.
7. `Q.complex | ~Q.transcendental` — if transcendental then complex.
8. `Q.complex_elements | ~Q.real_elements` — if real_elements then complex_elements.
9. `Q.even | ~Q.zero` — zero is even.
10. `Q.extended_real | ~Q.infinite` — infinite implies extended_real.
11. `Q.extended_real | ~Q.real` — if real then extended_real.
12. `Q.fullrank | ~Q.invertible` — invertible implies fullrank.
13. `Q.hermitian | ~Q.real` — if real then hermitian.
14. `Q.integer | ~Q.even` — even implies integer.
15. `Q.integer | ~Q.odd` — odd implies integer.
16. `Q.integer | ~Q.prime` — prime implies integer.
17. `Q.invertible | ~Q.positive_definite` — positive_definite implies invertible.
18. `Q.invertible | ~Q.unitary` — unitary implies invertible.
19. `Q.lower_triangular | ~Q.diagonal` — diagonal implies lower_triangular.
20. `Q.nonnegative | ~Q.positive` — positive implies nonnegative.
21. `Q.nonnegative | ~Q.zero` — zero is nonnegative.
22. `Q.nonpositive | ~Q.negative` — negative implies nonpositive.
23. `Q.nonpositive | ~Q.zero` — zero is nonpositive.
24. `Q.nonzero | ~Q.negative` — negative implies nonzero.
25. `Q.nonzero | ~Q.positive` — positive implies nonzero.
26. `Q.normal | ~Q.diagonal` — diagonal implies normal.
27. `Q.normal | ~Q.unitary` — unitary implies normal.
28. `Q.positive | ~Q.prime` — prime implies positive.
29. `Q.positive_definite | ~Q.orthogonal` — orthogonal implies positive_definite.
30. `Q.rational | ~Q.integer` — integer implies rational.
31. `Q.real | ~Q.irrational` — irrational implies real.
32. `Q.real | ~Q.negative` — negative implies real.
33. `Q.real | ~Q.positive` — positive implies real.
34. `Q.real | ~Q.rational` — rational implies real.
35. `Q.real | ~Q.zero` — zero is real.
36. `Q.real_elements | ~Q.integer_elements` — integer_elements implies real_elements.
37. `Q.square | ~Q.invertible` — invertible implies square.
38. `Q.square | ~Q.normal` — normal implies square.
39. `Q.square | ~Q.symmetric` — symmetric implies square.
40. `Q.symmetric | ~Q.diagonal` — diagonal implies symmetric.
41. `Q.triangular | ~Q.lower_triangular` — lower_triangular implies triangular.
42. `Q.triangular | ~Q.unit_triangular` — unit_triangular implies triangular.
43. `Q.triangular | ~Q.upper_triangular` — upper_triangular implies triangular.
44. `Q.unitary | ~Q.orthogonal` — orthogonal implies unitary.
45. `Q.upper_triangular | ~Q.diagonal` — diagonal implies upper_triangular.
46. `~Q.algebraic | ~Q.transcendental` — algebraic and transcendental are mutually exclusive.
47. `~Q.antihermitian | ~Q.hermitian` — antihermitian and hermitian are mutually exclusive.
48. `~Q.composite | ~Q.prime` — composite and prime are mutually exclusive.
49. `~Q.even | ~Q.odd` — even and odd are mutually exclusive.
50. `~Q.finite | ~Q.infinite` — finite and infinite are mutually exclusive.
51. `~Q.imaginary | ~Q.real` — imaginary and real are mutually exclusive (excluding zero).
52. `~Q.invertible | ~Q.singular` — invertible and singular are mutually exclusive.
53. `~Q.irrational | ~Q.rational` — irrational and rational are mutually exclusive.
54. `~Q.negative | ~Q.positive` — negative and positive are mutually exclusive.
55. `~Q.negative | ~Q.zero` — negative and zero are mutually exclusive.
56. `~Q.positive | ~Q.zero` — positive and zero are mutually exclusive.
57. `Q.algebraic | Q.transcendental | ~Q.complex` — every complex number is either algebraic or transcendental.
58. `Q.even | Q.odd | ~Q.integer` — every integer is even or odd.
59. `Q.infinite | Q.real | ~Q.extended_real` — every extended_real is infinite or real.
60. `Q.irrational | Q.rational | ~Q.real` — every real is irrational or rational.
61. `Q.lower_triangular | Q.upper_triangular | ~Q.triangular` — every triangular matrix is lower or upper triangular.
62. `Q.negative | Q.positive | ~Q.nonzero` — every nonzero number is negative or positive.
63. `Q.negative | Q.zero | ~Q.nonpositive` — every nonpositive is negative or zero.
64. `Q.positive | Q.zero | ~Q.nonnegative` — every nonnegative is positive or zero.
65. `Q.diagonal | ~Q.lower_triangular | ~Q.upper_triangular` — a diagonal matrix is both lower and upper triangular.
66. `Q.invertible | ~Q.fullrank | ~Q.square` — an invertible matrix must be fullrank and square.
67. `Q.orthogonal | ~Q.real | ~Q.unitary` — an orthogonal matrix is real and unitary.
68. `Q.negative | Q.positive | Q.zero | ~Q.real` — every real number is negative, positive, or zero.
69. `Q.composite | Q.prime | ~Q.integer | ~Q.positive` — every positive integer is composite or prime.

**Return value:** An `And` object containing all 72 clauses conjoined together. The result is cached after the first invocation.

---

### Function: `get_known_facts_dict()`

**Signature:** `def get_known_facts_dict() -> dict[Q, set[Q]]`

**Decorator:** `@cacheit` — the result is memoized after first call.

**Docstring:** None (no docstring).

**Implementation Logic:**
Returns a dictionary mapping each known predicate `Q.<name>` to a **set of predicates that are implied by it**. In other words, for key `k`, every element in `d[k]` is a logical consequence of assuming `k`. The dictionary contains 40 entries:

| Key (assumed true) | Implied predicates (set membership) |
|---|---|
| `Q.algebraic` | `{algebraic, complex}` |
| `Q.antihermitian` | `{antihermitian}` |
| `Q.commutative` | `{commutative}` |
| `Q.complex` | `{complex}` |
| `Q.complex_elements` | `{complex_elements}` |
| `Q.composite` | `{composite}` |
| `Q.diagonal` | `{diagonal, lower_triangular, normal, square, symmetric, triangular, upper_triangular}` |
| `Q.even` | `{algebraic, complex, even, extended_real, hermitian, integer, rational, real}` |
| `Q.extended_real` | `{extended_real}` |
| `Q.finite` | `{finite}` |
| `Q.fullrank` | `{fullrank}` |
| `Q.hermitian` | `{hermitian}` |
| `Q.imaginary` | `{antihermitian, complex, imaginary}` |
| `Q.infinite` | `{extended_real, infinite}` |
| `Q.integer` | `{algebraic, complex, extended_real, hermitian, integer, rational, real}` |
| `Q.integer_elements` | `{complex_elements, integer_elements, real_elements}` |
| `Q.invertible` | `{fullrank, invertible, square}` |
| `Q.irrational` | `{complex, extended_real, hermitian, irrational, nonzero, real}` |
| `Q.is_true` | `{is_true}` |
| `Q.lower_triangular` | `{lower_triangular, triangular}` |
| `Q.negative` | `{complex, extended_real, hermitian, negative, nonpositive, nonzero, real}` |
| `Q.nonnegative` | `{complex, extended_real, hermitian, nonnegative, real}` |
| `Q.nonpositive` | `{complex, extended_real, hermitian, nonpositive, real}` |
| `Q.nonzero` | `{complex, extended_real, hermitian, nonzero, real}` |
| `Q.normal` | `{normal, square}` |
| `Q.odd` | `{algebraic, complex, extended_real, hermitian, integer, nonzero, odd, rational, real}` |
| `Q.orthogonal` | `{fullrank, invertible, normal, orthogonal, positive_definite, square, unitary}` |
| `Q.positive` | `{complex, extended_real, hermitian, nonnegative, nonzero, positive, real}` |
| `Q.positive_definite` | `{fullrank, invertible, positive_definite, square}` |
| `Q.prime` | `{algebraic, complex, extended_real, hermitian, integer, nonnegative, nonzero, positive, prime, rational, real}` |
| `Q.rational` | `{algebraic, complex, extended_real, hermitian, rational, real}` |
| `Q.real` | `{complex, extended_real, hermitian, real}` |
| `Q.real_elements` | `{complex_elements, real_elements}` |
| `Q.singular` | `{singular}` |
| `Q.square` | `{square}` |
| `Q.symmetric` | `{square, symmetric}` |
| `Q.transcendental` | `{complex, transcendental}` |
| `Q.triangular` | `{triangular}` |
| `Q.unit_triangular` | `{triangular, unit_triangular}` |
| `Q.unitary` | `{fullrank, invertible, normal, square, unitary}` |
| `Q.upper_triangular` | `{triangular, upper_triangular}` |
| `Q.zero` | `{algebraic, complex, even, extended_real, hermitian, integer, nonnegative, nonpositive, rational, real, zero}` |

**Return value:** A Python `dict` with 40 key-value pairs. Each key is a `Q` predicate attribute; each value is a `set` of `Q` predicates that follow from the key being true. The result is cached after the first invocation.

## sympy/core/assumptions.py
The referenced modules aren't in this working directory, but I have all the information from reading `assumptions.py` itself. Let me now compose the full specification.

---

# Module Specification: `sympy/core/assumptions.py`

## 1. Module-Level Preamble

### Imports
```python
from __future__ import print_function, division
from sympy.core.facts import FactRules, FactKB
from sympy.core.core import BasicMeta
from sympy.core.compatibility import integer_types
from random import shuffle
```

- `FactRules` — a class that parses assumption-rule strings into an inference engine; exposes `.defined_facts` (a set of all fact names mentioned in rules) and `.prereq` (a mapping from each fact to the set of prerequisite facts needed to derive it).
- `FactKB` — a knowledge-base class for storing and deducing boolean/None facts given a rule engine; supports `__contains__`, indexing (`kb[fact]`), iteration, `.get(fact)`, `.deduce_all_facts(iterable)`, `.copy()`, and a `.generator` property.
- `BasicMeta` — the metaclass that all SymPy `Basic` subclasses use as their metaclass base.
- `integer_types` — a tuple of Python integer types (e.g., `(int,)`).

### Constants & Globals

**`_assume_rules: FactRules`**

A `FactRules` instance constructed from 38 rule strings that define the assumption inference system. Each rule is one of three forms:
- **Implication (`->`)**: a single fact implies another (e.g., `'integer -> rational'`).
- **Equivalence (`==`)**: two sides are logically equivalent; each side may be a conjunction (`&`) or disjunction (`|`) of facts.
- **Negation (`!`)**: used within rules to negate a fact.

The complete rule set (verbatim):

```
integer        ->  rational
rational       ->  real
rational       ->  algebraic
algebraic      ->  complex
real           ->  complex
real           ->  hermitian
imaginary      ->  complex
imaginary      ->  antihermitian
complex        ->  commutative

odd            ==  integer & !even
even           ==  integer & !odd

real           ==  negative | zero | positive
transcendental ==  complex & !algebraic

negative       ==  nonpositive & nonzero
positive       ==  nonnegative & nonzero
zero           ==  nonnegative & nonpositive

nonpositive    ==  real & !positive
nonnegative    ==  real & !negative

zero           ->  even & finite

prime          ->  integer & positive
composite      ->  integer & positive & !prime
!composite     ->  !positive | !even | prime

irrational     ==  real & !rational

imaginary      ->  !real

infinite       ->  !finite
noninteger     ==  real & !integer
nonzero        ==  real & !zero
```

**`_assume_defined: frozenset[str]`**

The union of `_assume_rules.defined_facts` (all fact names appearing in the rules) plus `'polar'`. This is the complete set of known assumption facts.

---

## 2. Code Objects

### Class `StdFactKB(FactKB)`

A subclass of `FactKB` specialized for SymPy's built-in assumption rules. It is the only kind of `FactKB` that `Basic` objects should use.

#### Attributes
- `_generator: dict[str, bool | None]` — a copy of the facts dictionary used to initialize this knowledge base; preserved so it can be returned via `.generator`.
- All inherited attributes from `FactKB`: internal fact storage, reference to the rule engine (`_rules`).

#### Methods

**`__init__(self, facts=None)`**

1. Calls `super().__init__(_assume_rules)`, initializing the parent with the global `_assume_rules`.
2. Sets up `self._generator`:
   - If `facts is None` or falsy: sets `self._generator = {}`.
   - Else if `facts` is not a `FactKB` instance: copies it via `facts.copy()` into `self._generator`.
   - Else (`facts` is a `FactKB`): assigns `self._generator = facts.generator`.
3. If `facts` is truthy, calls `self.deduce_all_facts(facts)` to propagate all known facts through the rule engine.

**`copy(self) -> StdFactKB`**

Returns a new `StdFactKB` initialized with `self`, which copies both the generator and deduced facts.

**`generator (property) -> dict[str, bool | None]`**

Returns a shallow copy of `self._generator`.

---

### Function `as_property(fact: str) -> str`

Converts an assumption fact name to its corresponding property attribute name by prepending `'is_'`. Returns the string `'is_%s' % fact`.

Examples: `'integer' → 'is_integer'`, `'positive' → 'is_positive'`.

---

### Function `make_property(fact: str) -> property`

Creates a descriptor (`property`) that implements lazy evaluation of an assumption fact on a SymPy object.

The returned property has a single getter method `getit(self)` with the following logic:
1. Attempts to read `self._assumptions[fact]`. If present, returns its value (True/False/None).
2. On `KeyError` (fact not yet cached):
   - Checks whether `self._assumptions is self.default_assumptions`. If so, creates a mutable copy: `self._assumptions = self.default_assumptions.copy()`.
   - Calls `_ask(fact, self)` to compute the fact value. Returns whatever `_ask` returns.

The getter function's name is set to `'is_%s' % fact` via `getit.func_name = as_property(fact)`, so that introspection (e.g., `help()`) shows a clean property name like `is_integer`.

---

### Function `_ask(fact: str, obj: Basic) -> bool | None`

Finds the truth value for an assumption fact on a SymPy object. Called when a requested fact is not yet cached in `obj._assumptions`.

**Logic:**
1. Retrieves `assumptions = obj._assumptions` and `handler_map = obj._prop_handler`.
2. **Prevents infinite recursion**: calls `assumptions._tell(fact, None)` to store `None` for the requested fact, so that any recursive attempt to evaluate the same fact will find it already "in progress."
3. **Tries the direct evaluation handler** (if registered):
   - Looks up `handler_map[fact]`. If found, calls `evaluate(obj)`.
   - If the result is not `None`, calls `assumptions.deduce_all_facts(((fact, a),))` to propagate implications through the rule engine and returns `a` (True or False).
4. **Tries prerequisite facts** (if no direct handler or it returned None):
   - Retrieves `prereq = list(_assume_rules.prereq[fact])`.
   - Shuffles the prerequisites for randomized search order (`shuffle(prereq)`).
   - For each prerequisite `pk`:
     - If `pk` is already in `assumptions`, skips it.
     - If `pk` has a handler in `handler_map`, recursively calls `_ask(pk, obj)`.
     - After the recursive call, checks `assumptions.get(fact)`; if it is not `None`, returns that value immediately (the prerequisite chain may have resolved the original fact).
5. **Fallback**: If no value was found through handlers or prerequisites, returns `None` (fact could not be determined). The `None` remains cached from step 2.

---

### Class `ManagedProperties(BasicMeta)`

Metaclass for classes that use old-style SymPy assumptions. Injects assumption-related properties and handlers into newly created classes at class-definition time.

#### Attributes set on the class during `__init__`:
- `_explicit_class_assumptions: dict[str, bool]` — merged explicit assumption values from bases and local definitions.
- `default_assumptions: StdFactKB` — a knowledge base initialized with `_explicit_class_assumptions`, providing default fact values for all instances of the class.
- `_prop_handler: dict[str, callable]` — maps each defined fact to its `_eval_is_<fact>` method (if present on the class).

#### Methods

**`__init__(cls, *args, **kws)`**

1. Calls `BasicMeta.__init__(cls, *args, **kws)` to perform standard metaclass initialization.
2. **Collects local definitions**: Iterates over every fact in `_assume_defined`. For each:
   - Computes the attribute name via `as_property(k)`.
   - Looks up that name in `cls.__dict__` (not inherited). If found and its value is a `bool`, integer, or `None`:
     - Converts non-None values to `bool`.
     - Adds `{k: v}` to `local_defs`.
3. **Merges base definitions**: Iterates over `cls.__bases__` in reverse order. For each base, retrieves `_explicit_class_assumptions` (if present) and updates a `defs` dict with its contents. Then updates `defs` with `local_defs`, so local class-level values override inherited ones.
4. **Stores merged assumptions**: Sets `cls._explicit_class_assumptions = defs`.
5. **Creates default knowledge base**: Sets `cls.default_assumptions = StdFactKB(defs)`.
6. **Registers evaluation handlers**: Initializes `cls._prop_handler = {}`. For each fact in `_assume_defined`, looks for a method named `'_eval_is_%s' % k` on the class; if found, stores it as `cls._prop_handler[k]`.
7. **Injects definite results into class dict** (optimization): For every `(k, v)` pair in `cls.default_assumptions.items()`, sets `setattr(cls, as_property(k), v)`. This makes class-level assumption attributes directly accessible as plain values rather than properties when they are known at class-definition time.
8. **Propagates inherited facts to subclasses**: Collects all fact names from the `default_assumptions` of each base into `derived_from_bases`. For every fact in `derived_from_bases - set(cls.default_assumptions)` (i.e., facts that bases have but this class does not): if the property name is not already in `cls.__dict__`, sets it via `setattr(cls, pname, make_property(fact))`. This ensures subclasses inherit assumption properties from parent classes.
9. **Adds missing automagic properties**: For every fact in `_assume_defined`, if the class does not yet have an attribute with that property name (checked via `hasattr`), creates and sets it via `setattr(cls, pname, make_property(fact))`. This guarantees that all assumption facts are accessible as `.is_<fact>` attributes on any class using this metaclass.

## sympy/core/power.py
I now have the full source code. Here is the complete specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import print_function, division
from math import log as _log
from .sympify import _sympify
from .cache import cacheit
from .singleton import S
from .expr import Expr
from .evalf import PrecisionExhausted
from .function import (_coeff_isneg, expand_complex, expand_multinomial, expand_mul)
from .logic import fuzzy_bool, fuzzy_not
from .compatibility import as_int, range
from .evaluate import global_evaluate
from sympy.utilities.iterables import sift
from mpmath.libmp import sqrtrem as mpmath_sqrtrem
from math import sqrt as _sqrt
```

Later (lines 1673–1676), additional imports are used by `Pow` methods:
```python
from .add import Add
from .numbers import Integer
from .mul import Mul, _keep_coeff
from .symbol import Symbol, Dummy, symbols
```

### Constants & Globals

No module-level constants or globals beyond the imported names. The only notable module-level constructs are three functions (`isqrt`, `integer_nthroot`, `integer_log`) and one class (`Pow`).

---

## Code Objects

### Function: `isqrt(n)`

**Signature:** `def isqrt(n):` — no type hints; parameter `n` expected to be a non-negative integer or numeric.

**Logic:**
1. If `n < 17984395633462800708566937239552`, return `int(_sqrt(n))` (using the fast C-level `math.sqrt`).
2. Otherwise, call `integer_nthroot(int(n), 2)[0]` and return its first element (the integer root).

**Return:** The largest integer ≤ √n.

---

### Function: `integer_nthroot(y, n)`

**Signature:** `def integer_nthroot(y, n):` — returns `(x, exact)`.

**Logic:**
1. Convert both arguments via `as_int(y), as_int(n)`.
2. If `y < 0`, raise `ValueError("y must be nonnegative")`.
3. If `n < 1`, raise `ValueError("n must be positive")`.
4. If `y` is 0 or 1, return `(y, True)` (exact).
5. If `n == 1`, return `(y, True)`.
6. If `n == 2`, call `mpmath_sqrtrem(y)` which returns `(x, rem)`; return `(int(x), not rem)`.
7. If `n > y`, return `(1, False)`.
8. Compute an initial guess: try `guess = int(y**(1./n) + 0.5)`. On `OverflowError`:
   - Compute `exp = _log(y, 2)/n`.
   - If `exp > 53`, set `shift = int(exp - 53)` and `guess = int(2.0**(exp - shift) + 1) << shift`.
   - Otherwise, `guess = int(2.0**exp)`.
9. If `guess > 2**50`, perform Newton iteration: initialize `xprev = -1, x = guess`; loop computing `t = x**(n-1)` then `xprev, x = x, ((n-1)*x + y//t)//n` until `abs(x - xprev) < 2`.
   - Otherwise (guess ≤ 2⁵⁰), set `x = guess`.
10. Compensate: compute `t = x**n`; while `t < y`, increment `x` and recompute `t`; while `t > y`, decrement `x` and recompute `t`.
11. Return `(int(x), t == y)`.

**Return:** Tuple `(x, exact)` where `x = floor(y^(1/n))` and `exact` is `True` iff `x^n == y`.

---

### Function: `integer_log(y, x)`

**Signature:** `def integer_log(y, x):` — returns `(e, exact)`.

**Logic:**
1. If `x == 1`, raise `ValueError('x cannot take value as 1')`.
2. If `y == 0`, raise `ValueError('y cannot take value as 0')`.
3. If `x` is `-2` or `2`: convert `x = int(x)`, `y = as_int(y)`; compute `e = y.bit_length() - 1`; return `(e, x**e == y)`.
4. If `x < 0`: recursively call `integer_log(y if y > 0 else -y, -x)` to get `(n, b)`; return `(n, b and bool(n % 2 if y < 0 else not n % 2))` (the exactness bit is true only when the recursive result was exact AND the parity of `n` matches the sign of `y`).
5. Convert both: `x = as_int(x)`, `y = as_int(y)`. Initialize `r = e = 0`.
6. Outer loop while `y >= x`: set `d = x, m = 1`; inner loop while `y >= d`: compute `(y, rem) = divmod(y, d)`; update `r = r or rem`, `e += m`; if `y > d`, square `d` and double `m`.
7. Return `(e, r == 0 and y == 1)`.

**Return:** Tuple `(e, exact)` where `e` is the largest nonnegative integer such that |y| ≥ |x^e|, and `exact` is `True` iff `y == x^e`.

---

### Class: `Pow(Expr)`

**Inheritance:** `class Pow(Expr)`. No metaclass.

**Class attribute:**
- `is_Pow = True`

**`__slots__`:** `['is_commutative']` — a single mutable slot set in `__new__`.

---

#### Method: `Pow.__new__(cls, b, e, evaluate=None)` *(classmethod via Expr pattern; decorated with `@cacheit`)*

**Signature:** `def __new__(cls, b, e, evaluate=None):`

**Logic (when `evaluate` is truthy):**
1. If `e is S.ComplexInfinity`, return `S.NaN`.
2. If `e is S.Zero`, return `S.One`.
3. If `e is S.One`, return `b`.
4. If `(b.is_Symbol or b.is_number) and (e.is_Symbol or e.is_number)` and `e.is_integer` and `_coeff_isneg(b)`: if `e.is_even`, set `b = -b`; else if `e.is_odd`, return `-Pow(-b, e)`.
5. If `S.NaN in (b, e)`, return `S.NaN`.
6. If `b is S.One`: if `abs(e).is_infinite` return `S.NaN`; otherwise return `S.One`.
7. Otherwise, attempt to recognize the base as Euler's number `E`:
   - If `e` is not an atom and `b` is not `S.Exp1` and `b` is not an instance of `exp_polar`, import `numer, denom, log, sign, im, factor_terms`. Factor `e` to get `(c, ex) = factor_terms(e).as_coeff_Mul()`. Get `den = denom(ex)`.
   - If `den` is a `log` and its argument equals `b`, return `S.Exp1**(c*numer(ex))`.
   - If `den` is an `Add`: compute `s = sign(im(b))`; if `s` is a Number, nonzero, and `den == log(-factor_terms(b, sign=False)) + s*S.ImaginaryUnit*S.Pi`, return `S.Exp1**(c*numer(ex))`.
8. Call `obj = b._eval_power(e)`. If it returns non-None, return that result.

**Logic (always executed after evaluate block):**
9. Create via `Expr.__new__(cls, b, e)`. Run `_exec_constructor_postprocessors(obj)`. If the result is not a `Pow` instance, return it directly.
10. Set `obj.is_commutative = (b.is_commutative and e.is_commutative)`.
11. Return `obj`.

---

#### Property: `base`

Returns `self._args[0]`.

#### Property: `exp`

Returns `self._args[1]`.

#### Method: `Pow.class_key(cls)` *(classmethod)*

Returns `(3, 2, cls.__name__)`.

---

#### Method: `Pow._eval_refine(self, assumptions)`

**Logic:**
1. Get `(b, e) = self.as_base_exp()`.
2. If `ask(Q.integer(e), assumptions)` and `_coeff_isneg(b)`: if `ask(Q.even(e), assumptions)`, return `Pow(-b, e)`; else if `ask(Q.odd(e), assumptions)`, return `-Pow(-b, e)`.

**Return:** Refined expression or nothing (implicit None).

---

#### Method: `Pow._eval_power(self, other)`

Computes `(self.base ** self.exp) ** other` with simplification rules.

**Logic:**
1. Get `(b, e) = self.as_base_exp()`. If `b is S.NaN`, delegate to `__new__`: return `(b**e)**other`.
2. Initialize `s = None`.
3. If `other.is_integer` or `b.is_polar`, set `s = 1`.
4. Else if `e.is_real is not None`: define two helper closures:
   - `_half(e)`: returns `True` if the exponent has literal denominator 2 (checked via `getattr(e, 'q', None) == 2` or `n, d = e.as_numer_denom()` with `n.is_integer and d == 2`); else `None`.
   - `_n2(e)`: evaluates `e.evalf(2, strict=True)`; returns the Number result or `None` on `PrecisionExhausted`.

   **If `e.is_real`:**
   - If `e == -1`: if `_half(other)` and `b.is_negative is True`, return `S.NegativeOne**other * Pow(-b, e*other)`. If `b.is_real is False`, return `Pow(b.conjugate()/Abs(b)**2, other)`.
   - If `e.is_even` and `b.is_real`: set `b = abs(b)`. If `b.is_imaginary`: set `b = abs(im(b)) * S.ImaginaryUnit`.
   - If `(abs(e) < 1) == True or e == 1`, set `s = 1`.
   - Else if `b.is_nonnegative`, set `s = 1`.
   - Else if `re(b).is_nonnegative and (abs(e) < 2) == True`, set `s = 1`.
   - Else if `fuzzy_not(im(b).is_zero) and abs(e) == 2`, set `s = 1`.
   - Else if `_half(other)` is truthy: compute `s = exp(2*S.Pi*S.ImaginaryUnit*other*floor(S.Half - e*arg(b)/(2*S.Pi)))`; if `s.is_real and _n2(sign(s) - s) == 0`, set `s = sign(s)`; else `s = None`.

   **Else (`e.is_real is False`):**
   - Try: compute `s = exp(2*S.ImaginaryUnit*S.Pi*other * floor(S.Half - im(e*log(b))/2/S.Pi))`; if `s.is_real and _n2(sign(s) - s) == 0`, set `s = sign(s)`; else `s = None`. On `PrecisionExhausted`, `s = None`.

5. If `s is not None`, return `s * Pow(b, e*other)`. Otherwise returns nothing (implicit None).

---

#### Method: `Pow._eval_Mod(self, q)`

**Logic:**
1. If `self.exp.is_integer and self.exp.is_positive` and `q.is_integer` and `self.base % q == 0`, return `S.Zero`.
2. If `self.base.is_Integer and self.exp.is_Integer and q.is_Integer`: let `(b, e, m) = (int(self.base), int(self.exp), int(q))`. Compute `mb = m.bit_length()`. If `mb <= 80` and `e >= mb` and `e.bit_length()**4 >= m`, import `totient`; compute `phi = totient(m)`; return `pow(b, phi + e%phi, m)`. Otherwise return `pow(b, e, m)`.

---

#### Method: `Pow._eval_is_even(self)`

If `self.exp.is_integer and self.exp.is_positive`, return `self.base.is_even`.

---

#### Method: `Pow._eval_is_positive(self)`

**Logic:**
1. If `self.base == self.exp` and `self.base.is_nonnegative`, return `True`.
2. Else if `self.base.is_positive` and `self.exp.is_real`, return `True`.
3. Else if `self.base.is_negative`: if `self.exp.is_even`, return `True`; else if `self.exp.is_odd`, return `False`.
4. Else if `self.base.is_zero`: if `self.exp.is_real`, return `self.exp.is_zero`.
5. Else if `self.base.is_nonpositive` and `self.exp.is_odd`, return `False`.
6. Else if `self.base.is_imaginary`: if `self.exp.is_integer`, compute `m = self.exp % 4`; if `m.is_zero`, return `True`; else if `m.is_integer and m.is_zero is False`, return `False`. If `self.exp.is_imaginary`, return `log(self.base).is_imaginary`.

---

#### Method: `Pow._eval_is_negative(self)`

**Logic:**
1. If `self.base.is_negative`: if `self.exp.is_odd`, return `True`; else if `self.exp.is_even`, return `False`.
2. Else if `self.base.is_positive` and `self.exp.is_real`, return `False`.
3. Else if `self.base.is_zero` and `self.exp.is_real`, return `False`.
4. Else if `self.base.is_nonnegative` and `self.exp.is_nonnegative`, return `False`.
5. Else if `self.base.is_nonpositive` and `self.exp.is_even`, return `False`.
6. Else if `self.base.is_real` and `self.exp.is_even`, return `False`.

---

#### Method: `Pow._eval_is_zero(self)`

**Logic:**
1. If `self.base.is_zero`: if `self.exp.is_positive`, return `True`; else if `self.exp.is_nonpositive`, return `False`.
2. Else if `self.base.is_zero is False`: if `self.exp.is_finite`, return `False`; else if `self.exp.is_infinite`: if `(1 - abs(self.base)).is_positive`, return `self.exp.is_positive`; else if `(1 - abs(self.base)).is_negative`, return `self.exp.is_negative`.
3. Else (base is zero-unknown), return `None`.

---

#### Method: `Pow._eval_is_integer(self)`

**Logic:**
1. If `b.is_rational` and `b.is_integer is False` and `e.is_positive`, return `False`.
2. If `b.is_integer and e.is_integer`: if `b is S.NegativeOne`, return `True`; else if `e.is_nonnegative or e.is_positive`, return `True`.
3. If `b.is_integer and e.is_negative` and `(e.is_finite or e.is_integer)`: if `fuzzy_not((b-1).is_zero)` and `fuzzy_not((b+1).is_zero)`, return `False`.
4. If `b.is_Number and e.is_Number`: evaluate `check = self.func(*self.args)`; return `check.is_Integer`.

---

#### Method: `Pow._eval_is_real(self)`

**Logic:**
1. Get `real_b = self.base.is_real`, `real_e = self.exp.is_real`. If either is `None`, return early (None).
2. If both real and true: if `self.base.is_positive`, return `True`; else if `self.base.is_nonnegative` and `self.exp.is_nonnegative`, return `True`; else if not positive/nonnegative, if `self.exp.is_integer`, return `True`.
3. If `real_e` is True but `self.base.is_negative`: if `self.exp.is_Rational`, return `False`.
4. If `real_e and self.exp.is_negative`, return `Pow(self.base, -self.exp).is_real`.
5. Get `im_b = self.base.is_imaginary`, `im_e = self.exp.is_imaginary`.
6. If `im_b`: if `self.exp.is_integer`: if even return `True`; if odd return `False`. Else if `im_e and log(self.base).is_imaginary`, return `True`. Else if `self.exp.is_Add`: get `(c, a) = self.exp.as_coeff_Add()`; if `c` exists and is an Integer, return `Mul(self.base**c, self.base**a, evaluate=False).is_real`. Else if `self.base in (-S.ImaginaryUnit, S.ImaginaryUnit)` and `(self.exp/2).is_integer is False`, return `False`.
7. If `real_b and im_e`: if `self.base is S.NegativeOne`, return `True`; else get `c = self.exp.coeff(S.ImaginaryUnit)`; if `c` exists, compute `ok = (c*log(self.base)/S.Pi).is_Integer`; if `ok is not None`, return `ok`.
8. If `real_b is False`: compute `i = arg(self.base)*self.exp/S.Pi`; return `i.is_integer`.

---

#### Method: `Pow._eval_is_complex(self)`

If all args are complex, return `True`.

---

#### Method: `Pow._eval_is_imaginary(self)`

**Logic:**
1. If `self.base.is_imaginary` and `self.exp.is_integer`: if `odd = self.exp.is_odd` is not None, return `odd`; else return nothing (None).
2. If `self.exp.is_imaginary`: get `imlog = log(self.base).is_imaginary`; if not None, return `False`.
3. If `self.base.is_real and self.exp.is_real`: if `self.base.is_positive`, return `False`; else: if `not self.exp.is_rational`, return that; if `self.exp.is_integer`, return `False`; else get `half = (2*self.exp).is_integer`; if truthy, return `self.base.is_negative`; else return `half`.
4. If `self.base.is_real is False`: compute `i = arg(self.base)*self.exp/S.Pi`; get `isodd = (2*i).is_odd`; if not None, return `isodd`.
5. If `self.exp.is_negative`, return `(1/self).is_imaginary`.

---

#### Method: `Pow._eval_is_odd(self)`

If `self.exp.is_integer`: if positive, return `self.base.is_odd`; else if nonnegative and `self.base.is_odd`, return `True`; else if `self.base is S.NegativeOne`, return `True`.

---

#### Method: `Pow._eval_is_finite(self)`

**Logic:**
1. If `self.exp.is_negative`: if `self.base.is_zero`, return `False`; if `self.base.is_infinite`, return `True`.
2. Get `c1 = self.base.is_finite`, `c2 = self.exp.is_finite`; if either is None, return nothing (None).
3. If both true and (`self.exp.is_nonnegative or fuzzy_not(self.base.is_zero)`), return `True`.

---

#### Method: `Pow._eval_is_prime(self)`

If `self.base.is_integer and self.exp.is_integer and (self.exp - 1).is_positive`, return `False`.

---

#### Method: `Pow._eval_is_composite(self)`

If `(self.base.is_integer and self.exp.is_integer and ((self.base-1).is_positive and (self.exp-1).is_positive) or (self.base+1).is_negative and self.exp.is_positive and self.exp.is_even)`, return `True`.

---

#### Method: `Pow._eval_is_polar(self)`

Returns `self.base.is_polar`.

---

#### Method: `Pow._eval_subs(self, old, new)`

Performs substitution of `old → new` within the power expression. Contains an inner helper `_check(ct1, ct2, old)`:

**Inner function `_check(ct1, ct2, old)`:**
- Takes coefficient/term pairs from exponents. If `terms1 == terms2`: if commutative, compute `pow = coeff1/coeff2`; try `as_int(pow, strict=False)`; if it fails, check whether `Pow(*old.as_base_exp(), evaluate=False)**pow` is a `Pow`, `exp`, or `Symbol`. Returns `(combines, pow, None)`. If noncommutative: ensure all terms are integers; compute integer division with rounding toward zero; return `(True, pow, remainder_pow)` where `remainder_pow = Mul(remainder, *terms1)` if nonzero.

**Logic:**
1. If `old == self.base`, return `new**self.exp._subs(old, new)`.
2. If `old` is a `Pow` and `self.exp == old.exp`: compute `l = log(self.base, old.base)`; if `l.is_Number`, return `Pow(new, l)`.
3. If `old` is a `Pow` and `self.base == old.base`:
   - If `self.exp.is_Add is False`: get `(ct1, ct2) = (self.exp.as_independent(Symbol), old.exp.as_independent(Symbol))`; call `_check(ct1, ct2, old)`; if ok, return `self.func(new, pow)` optionally multiplied by `Pow(old.base, remainder_pow)`.
   - If `self.exp.is_Add`: for each term in the exponent, substitute and check; collect results into `new_l` list; if any substitutions succeeded, build result as `Mul(*new_l)` possibly with a remaining power factor. If noncommutative and any substituted term is not integer, return None.
4. If `old` is an `exp` and `self.exp.is_real and self.base.is_positive`: get coefficient pairs from `old.args[0]` and `self.exp*log(self.base)`; call `_check`; if ok, return `self.func(new, pow)` optionally with remainder factor.

---

#### Method: `Pow.as_base_exp(self)`

Returns `(b, e) = self.args`. If `b.is_Rational and b.p == 1 and b.q != 1`, return `(Integer(b.q), -e)`. Otherwise return `(b, e)`.

---

#### Method: `Pow._eval_adjoint(self)`

**Logic:**
1. Get `i = self.exp.is_integer`, `p = self.base.is_positive`.
2. If `i` is True, return `adjoint(self.base)**self.exp`.
3. If `p` is True, return `self.base**adjoint(self.exp)`.
4. If both are False: expand via `expand_complex(self)`; if result differs from self, return `adjoint(expanded)`.

---

#### Method: `Pow._eval_conjugate(self)`

**Logic:**
1. Get `i = self.exp.is_integer`, `p = self.base.is_positive`.
2. If `i` is True, return `conjugate(self.base)**self.exp`.
3. If `p` is True, return `self.base**conjugate(self.exp)`.
4. If both are False: expand via `expand_complex(self)`; if result differs from self, return `c(expanded)`.
5. If `self.is_real`, return `self`.

---

#### Method: `Pow._eval_transpose(self)`

**Logic:**
1. Get `i = self.exp.is_integer`, `p = self.base.is_complex`.
2. If `p` is True, return `self.base**self.exp`.
3. If `i` is True, return `transpose(self.base)**self.exp`.
4. If both are False: expand via `expand_complex(self)`; if result differs from self, return `transpose(expanded)`.

---

#### Method: `Pow._eval_expand_power_exp(self, **hints)`

Expands `a**(n+m)` → `a**n * a**m`.
1. If `e.is_Add and e.is_commutative`: for each term in `e.args`, create `self.func(b, x)`; return `Mul(*expr)`.
2. Otherwise return `self.func(b, e)`.

---

#### Method: `Pow._eval_expand_power_base(self, **hints)`

Expands `(a*b)**n` → `a**n * b**n`.

**Logic:**
1. Get `force = hints.get('force', False)`. If base is not a `Mul`, return self.
2. Decompose base: `(cargs, nc) = b.args_cnc(split_1=False)`.
3. For noncommutative parts: expand each via `_eval_expand_power_base` if available. If exponent is an integer and positive, return `Mul(*nc*e)`; if negative, return `Mul(*[i**-1 for i in nc[::-1]]*-e)`. If there are commutative args, multiply by `Mul(*cargs)**e`.
4. If no commutative args and noncommutative: return `self.func(Mul(*nc), e, evaluate=False)` if no integer exponent; else handle as above. Otherwise wrap nc into `[Mul(*nc)]`.
5. Sift commutative args: `other, maybe_real = sift(cargs, lambda x: x.is_real is False, binary=True)`. Further sift `maybe_real` by a predicate that classifies `S.ImaginaryUnit`, polar terms, and nonnegative terms into `imag`, `nonneg`, `neg`, `other`.
6. Handle imaginary unit factors (count mod 4): if count mod 4 == 1, append I to other; if == 2, move one negative to nonneg or add -1 to neg; if == 3, similar with an extra I appended to other.
7. If `force or e.is_integer`: all commutatives go into `cargs`; nc goes into `other`. Otherwise (non-integer exponent): handle negatives by making them positive and tracking residual -1 in `other`; `cargs = nonneg`, `other += nc`.
8. Build result: for each base in `cargs`, create `self.func(b, e, evaluate=False)`; multiply into `rv`. If `other` remains, wrap as `self.func(Mul(*other), e, evaluate=False)`.

---

#### Method: `Pow._eval_expand_multinomial(self, **hints)`

Expands `(a + b + ...)**n` via the multinomial theorem.

**Logic:**
1. If `exp.is_Rational and exp.p > 0 and base.is_Add`: if not integer exponent, split into integer part `n = Integer(exp.p // exp.q)` and radical; expand the integer part via `_eval_expand_multinomial`; multiply each term by the radical; return as `Add`.
2. If `exp.is_Rational` (integer case): let `n = int(exp)`.
   - **Commutative base:** separate order terms from other terms. Handle order terms: for n=2, expand `f**2 + 2*f*o`; else expand `f*(f^(n-1)) + n*g*o`. If base is a number (real+imaginary): use efficient complex binomial via `(a+b*I)^n` algorithm with doubling. Otherwise, use `multinomial_coefficients(len(p), n)` and `basic_from_dict`.
   - **Non-commutative base:** for n=2 return `Add(*[f*g for f in base.args for g in base.args])`; else recursively expand `(base**(n-1))` and distribute.
3. If `exp.is_Rational and exp.p < 0 and abs(exp.p) > exp.q`: return `1 / self.func(base, -exp)._eval_expand_multinomial()`.
4. If `exp.is_Add and base.is_Number`: split exponent into number terms (multiply into coeff) and non-number terms (sum into tail); return `coeff * self.func(base, tail)`.
5. Otherwise return the unevaluated result.

---

#### Method: `Pow.as_real_imag(self, deep=True, **hints)`

**Logic:**
1. If `self.exp.is_Integer`: get `(re, im) = self.base.as_real_imag()`. If `im` is zero, return `(self, S.Zero)`. Create dummy symbols `a, b`. If exponent ≥ 0: if both re and im are Numbers, expand via `expand_multinomial`; else use `poly((a+b)**exp)`. If exponent < 0: swap to conjugate form with `mag = re**2 + im**2`, then `poly((a+b)^(-exp))`. Separate even b-powers (real part) and odd b-powers mod 4 == 1 or 3 (imaginary parts); substitute back.
2. If `self.exp.is_Rational`: get `(re, im)` from base. Special case: if `im.is_zero` and `exp is S.Half`, return `(self, S.Zero)` for nonnegative re; return `(S.Zero, (-self.base)**self.exp)` for nonpositive re. Otherwise compute `r = (re² + im²)^(1/2)`, `t = atan2(im, re)`, then return `(r^exp * cos(t*exp), r^exp * sin(t*exp))`.
3. Else: if `deep`, set `hints['complex'] = False`; expand; return `(re(expanded), im(expanded))` or fall back to `(re(self), im(self))`.

---

#### Method: `Pow._eval_derivative(self, s)`

Returns `self * (dexp * log(self.base) + dbase * self.exp/self.base)` where `dbase = self.base.diff(s)` and `dexp = self.exp.diff(s)`.

---

#### Method: `Pow._eval_evalf(self, prec)`

1. Get `(base, exp) = self.as_base_exp()`. Evaluate `base` to precision; if exponent is not an integer, also evaluate it.
2. If `exp.is_negative and base.is_number and base.is_real is False`: set `base = base.conjugate() / (base * base.conjugate())._evalf(prec)`, negate exp, return expanded form.
3. Otherwise return `self.func(base, exp)`.

---

#### Method: `Pow._eval_is_polynomial(self, syms)`

If `self.exp.has(*syms)`, return `False`. If `self.base.has(*syms)`, return `bool(self.base._eval_is_polynomial(syms) and self.exp.is_Integer and (self.exp >= 0))`. Otherwise return `True`.

---

#### Method: `Pow._eval_is_rational(self)`

1. Evaluate `p = self.func(*self.as_base_exp())` (unevaluated if needed). If not a `Pow`, return `p.is_rational`.
2. Get `(b, e) = p.as_base_exp()`. If both are Rational but exponent is not Integer, return `False`.
3. If `e.is_integer`: if `b.is_rational` and (`fuzzy_not(b.is_zero)` or `e.is_nonnegative`), return `True`; else if `b == e`, return `True`. If `b.is_irrational`, return `e.is_zero`.

---

#### Method: `Pow._eval_is_algebraic(self)`

Inner helper `_is_one(expr)`: tries `(expr - 1).is_zero`; returns `False` on ValueError.
1. If base is zero or `_is_one(base)`, return `True`.
2. If `self.exp.is_rational`: if `base.is_algebraic is False`, return `e.is_zero`; else return `base.is_algebraic`.
3. If both base and exponent are algebraic: if (`fuzzy_not(base.is_zero)` and `fuzzy_not(_is_one(base))`) or `base.is_integer is False` or `base.is_irrational`, return `self.exp.is_rational`.

---

#### Method: `Pow._eval_is_rational_function(self, syms)`

If exponent has symbols, return `False`. If base has symbols, return `base._eval_is_rational_function(syms) and self.exp.is_Integer`. Otherwise return `True`.

---

#### Method: `Pow._eval_is_algebraic_expr(self, syms)`

If exponent has symbols, return `False`. If base has symbols, return `base._eval_is_algebraic_expr(syms) and self.exp.is_Rational`. Otherwise return `True`.

---

#### Method: `Pow._eval_rewrite_as_exp(self, base, expo, **kwargs)`

1. If base is zero or either contains `exp`, return `base**expo`.
2. If base has a Symbol (delay evaluation): return `exp(log(base)*expo, evaluate=expo.has(Symbol))`.
3. Otherwise: return `exp((log(abs(base)) + I*arg(base))*expo)`.

---

#### Method: `Pow.as_numer_denom(self)`

1. If not commutative, return `(self, S.One)`.
2. Get `(base, exp) = self.as_base_exp()`. Decompose base into numerator/denominator `(n, d)`. Determine `neg_exp` from `exp.is_negative` or `_coeff_isneg(exp)`.
3. If denominator is not real and exponent is not integer, keep as-is (`d = S.One`). If `dnonpos`, negate both n and d. If `dnonpos is None and not int_exp`, keep as-is.
4. If negative exponent: swap n and d, negate exp. Handle infinite exponents with special cases for unit numerator/denominator. Return `(self.func(n, exp), self.func(d, exp))`.

---

#### Method: `Pow.matches(self, expr, repl_dict={}, old=False)`

1. Sympify `expr`. If `expr is S.One`: try matching `self.exp` against `S.Zero`; return the dict if successful.
2. If `expr` is not an `Expr`, return `None`.
3. Get `(b, e) = expr.as_base_exp()`, `(sb, se) = self.as_base_exp()`. If `sb.is_Symbol and se.is_Integer`: match `sb` against `b**(e/se)` (or `expr**(1/se)`).
4. Copy dict; match `self.base` against `b`; if None, return None. Match `self.exp.xreplace(d)` against `e`; if None, fall back to `Expr.matches(self, expr, repl_dict)`.

---

#### Method: `Pow._eval_nseries(self, x, n, logx)`

Generates a generalized power series expansion (part of the Gruntz limit algorithm).

**Logic:**
1. Get `(b, e) = self.args`. Import `ceiling, collect, exp, log, O, Order, powsimp`.
2. **If `e.is_Integer`:**
   - If positive: expand base via `_eval_nseries`, then multinomial-expand the result.
   - If `e is S.NegativeOne`: compute leading term order; adjust n; rewrite as `1/(1 + x)` series using geometric expansion with binomial-like terms up to order n.
   - Otherwise (negative integer): recursively expand via `(b**(-e))._eval_nseries` then take reciprocal.
3. **If `e.has(Symbol)`:** return `exp(e*log(b))._eval_nseries(x, n=n, logx=logx)`.
4. Simplify base: walk through nested rational powers to find the simplest bx; if `bx == x`, return self.
5. Helper `e2int(e)`: compute limit of e at 0; convert to int with fallback to evalf+1; returns `(n, infinite_flag)`.
6. Compute `b0 = b.limit(x, 0)`. If infinite exponent and `b0 is S.One` or has symbols: check sign of `b-1`; return Infinity/Zero accordingly, or raise ValueError. Return `b0**ei` otherwise.
7. If `b0 is S.Zero or b0.is_infinite`: if not infinite exponent, compute adjusted order; get leading term; correct nuse via Order analysis; expand base and decompose as `lt*(1 + rest)`; return series of `(1+rest)^e`. Handle Add case by substituting dummy for Order terms.
8. **General case** (`b0` bounded but not 0/1, or infinite exponent): compute `z = b/b0 - 1`; determine order via log ratio; if infinite, use `r = 1 + z`; else build Taylor series of `(1+z)^e` using `_taylor_term` for n+2 terms. Return `expand_mul(r*b0**e) + order`.

---

#### Method: `Pow._eval_as_leading_term(self, x)`

If exponent does not contain `x`, return `self.func(self.base.as_leading_term(x), self.exp)`. Otherwise return `exp(self.exp * log(self.base)).as_leading_term(x)`.

---

#### Method: `Pow._taylor_term(self, n, x, *previous_terms)` *(decorated with `@cacheit`)*

Returns `binomial(self.exp, n) * self.func(x, n)` — the nth term of the binomial expansion of `(1+x)^e`.

---

#### Method: `Pow._sage_(self)`

Returns `self.args[0]._sage_()**self.args[1]._sage_()` (Sage interoperability).

---

#### Method: `Pow.as_content_primitive(self, radical=False, clear=True)`

Extracts positive rational content from the power.
1. Get `(b, e) = self.as_base_exp()`. Extract content/primitive from both base and exponent via `_keep_coeff` + recursive `as_content_primitive`.
2. If base is Rational: decompose exponent into integer part `h` and fractional tail `t`; compute `ceh = ce*h`; if the resulting power is not rational, use `divmod(ceh.p, ceh.q)` to separate integer and remainder parts; return `(c, self.func(b, _keep_coeff(ce, t + r/ce/ceh.q)))`.
3. If exponent is Rational and base is a Mul: extract positive content `h` from base; compute `c = self.func(h, e).as_coeff_Mul()` (positive coefficient); return `(c, self.func(_keep_coeff(m, t), e))` where `m` is the primitive part of the coefficient.
4. Otherwise return `(S.One, self)`.

---

#### Method: `Pow.is_constant(self, *wrt, **flags)`

Determines if the expression is constant with respect to given variables.
1. If `simplify` flag is True (default), simplify first.
2. Get `(b, e) = expr.as_base_exp()`. Check if base equals 0; if so, recalculate and recurse.
3. Get `econ = e.is_constant(*wrt)` and `bcon = b.is_constant(*wrt)`.
4. If both constant, return `True`. If base is not zero-constant (and not zero), return `False`. If `bcon is None`, return `None`.
5. Otherwise return `e.equals(0)`.

---

#### Method: `Pow._eval_difference_delta(self, n, step)`

If exponent has `n` but base does not: compute `new_e = e.subs(n, n + step)`; return `(b**(new_e - e) - 1) * self`.

---

### End-of-file imports (lines 1673–1676)

These are imported at module level after the class definition and are used by methods within `Pow`:
```python
from .add import Add
from .numbers import Integer
from .mul import Mul, _keep_coeff
from .symbol import Symbol, Dummy, symbols
```

## sympy/printing/tree.py
Here is the complete natural-language specification of `/tmp/omp_desc_2yk_ne5z/sympy/printing/tree.py`:

---

## Module-Level Preamble

**Imports:** None (no imports at module level).

**Constants & Globals:** None defined.

---

## Code Objects

### Function: `pprint_nodes(subtrees)`

**Signature:** `def pprint_nodes(subtrees):` — takes a single positional parameter `subtrees`, which is an iterable of strings representing already-formatted subtree outputs (each string produced by `tree()`). Returns a single concatenated string.

**Implementation Logic:**
1. Defines an inner helper function `indent(s, type=1)`:
   - Splits the input string `s` on newline characters into a list `x`.
   - Prepends `"+-"` to the first element (`x[0]`) and appends `\n`, forming the root line of this subtree segment.
   - For each remaining element `a` in `x[1:]`:
     - If `a` is an empty string, skip it entirely (no output produced).
     - Otherwise, if `type == 1`, prepend `"| "` to `a` and append `\n`. This produces a vertical-branch connector.
     - If `type != 1` (i.e., `type == 2`), prepend two spaces `"  "` to `a` and append `\n`. This produces an indented continuation without the branch line.
   - Returns the accumulated result string `r`.

2. If `subtrees` is empty (falsy), returns `""` immediately.

3. Initializes an accumulator string `f = ""`.

4. Iterates over all elements of `subtrees` except the last one (`subtrees[:-1]`). For each element, calls `indent(a)` with the default `type=1`, and appends the result to `f`. This means every subtree except the final one gets a `"| "` connector on continuation lines.

5. Processes the **last** element of `subtrees` (`subtrees[-1]`) by calling `indent(subtrees[-1], 2)`, which uses `type=2` (two-space indent instead of `"| "`) for its continuation lines, producing a terminal branch that does not carry a vertical connector downward.

6. Returns the accumulated string `f`.

**Return value:** A single string containing all subtree strings formatted with tree-like indentation using `"+-"` prefixes and either `"| "` or `"  "` connectors on continuation lines. The last subtree uses `"  "` (no branch line); all preceding subtrees use `"| "`.

---

### Function: `print_node(node)`

**Signature:** `def print_node(node):` — takes a single positional parameter `node`, which is expected to be an object with at least the attributes `__class__.__name__`, `str()` representation, and `_assumptions`. Returns a string.

**Implementation Logic:**
1. Constructs the initial line: `"%s: %s\n"` formatted with `node.__class__.__name__` as the class name and `str(node)` as its string representation. Stored in variable `s`.

2. Retrieves `d = node._assumptions`, which is expected to be a dictionary mapping assumption names (strings) to their values (any type, possibly `None`).

3. If `d` is truthy (non-empty):
   - Iterates over the keys of `d` in sorted order (`sorted(d)`).
   - For each key `a`, retrieves its value `v = d[a]`.
   - If `v` is exactly `None`, skips this entry (no output line produced for it).
   - Otherwise, appends `"%s: %s\n"` formatted with the assumption name `a` and its string representation to `s`.

4. Returns the accumulated string `s`.

**Return value:** A multi-line string where the first line is `"ClassName: str(node)\n"`, followed by zero or more lines of `"assumption_name: value\n"` for each non-None assumption, sorted alphabetically by name.

---

### Function: `tree(node)`

**Signature:** `def tree(node):` — takes a single positional parameter `node`. Returns a string representing the full recursive tree visualization of the node and all its descendants.

**Implementation Logic:**
1. Initializes an empty list `subtrees = []`.

2. Iterates over each element in `node.args` (expected to be an iterable/sequence). For each argument:
   - Recursively calls `tree(arg)` on that argument.
   - Appends the returned string to `subtrees`.

3. Calls `print_node(node)` to get the formatted representation of the current node itself.

4. Concatenates the result of `print_node(node)` with the result of `pprint_nodes(subtrees)`, storing in `s`.

5. Returns `s`.

**Return value:** A string starting with the current node's class name and string representation (from `print_node`), followed by all recursively formatted subtrees (from `pprint_nodes`). The structure is a depth-first traversal where each node's children are indented beneath it using tree-drawing characters (`+-`, `| `, `  `).

**Base case:** If `node.args` is empty, the loop produces no entries in `subtrees`; `pprint_nodes([])` returns `""`; the result is just `print_node(node)`.

---

### Function: `print_tree(node)`

**Signature:** `def print_tree(node):` — takes a single positional parameter `node`. Returns nothing (returns `None`).

**Implementation Logic:**
1. Calls `tree(node)` to obtain the full tree string representation.
2. Passes that result to Python's built-in `print()` function, which outputs it to standard output with a trailing newline.

**Return value:** `None` (side-effect only: prints to stdout).

---

## Summary of Data Flow

The module implements a recursive tree-printing system for SymPy expression nodes:
- **`tree(node)`** is the core recursive function that traverses `node.args` depth-first, building up formatted subtree strings.
- **`print_node(node)`** formats a single node's identity (class name + string repr) plus its `_assumptions` dictionary entries.
- **`pprint_nodes(subtrees)`** joins multiple pre-formatted subtree strings with tree-drawing indentation characters (`+-`, `| `, `  `), using `"| "` for intermediate branches and `"  "` for the final branch to avoid dangling vertical lines.
- **`print_tree(node)`** is a convenience wrapper that calls `tree()` and prints the result to stdout.

## sympy/tensor/indexed.py
The specification has been written to `sympy_tensor_indexed_spec.md`. Here's a summary of what it covers:

**Module structure:**
- 3 imports from `sympy.core`, 1 compatibility import, 1 sympify helper, and 1 KroneckerDelta import
- 1 module-level exception class (`IndexException`)

**Three core classes documented in full detail:**

1. **`Indexed(Expr)`** — Represents a complete indexed object like `M[i,j]`. Covers its constructor (with string/Symbol/IndexedBase base handling, index sympification, and NDimArray delegation), derivative evaluation via KroneckerDelta products, properties (`base`, `indices`, `rank`, `shape`, `ranges`), string formatting, and free symbol computation.

2. **`IndexedBase(Expr, NotIterable)`** — Represents the array stem like `M`. Covers its constructor (label type dispatching, shape/strides/offset handling), `__getitem__` for creating `Indexed` objects with rank checking, and properties (`name`, `shape`, `strides`, `offset`, `label`).

3. **`Idx(Expr)`** — Represents an integer index with optional range bounds. Covers its constructor (string-to-Symbol conversion, tuple vs dimension range parsing, assumption setting), properties (`label`, `lower`, `upper`, `name`, `free_symbols`), and all four comparison operators (`__le__`, `__ge__`, `__lt__`, `__gt__`) with range-aware logic.