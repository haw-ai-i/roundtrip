## sympy/printing/codeprinter.py
Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
from typing import Any, Dict, Set, Tuple
from functools import wraps
from sympy.core import Add, Expr, Mul, Pow, S, Float, sympify
from sympy.core.basic import Basic
from sympy.core.compatibility import default_sort_key
from sympy.core.function import Lambda
from sympy.core.mul import _keep_coeff
from sympy.core.symbol import Symbol
from sympy.printing.str import StrPrinter
from sympy.printing.precedence import precedence
```

### Constants & Globals

None at module level beyond the classes and functions defined below.

---

## Code Objects

### Class `requires`

**Header:** A decorator class (not a subclass of anything).

**Attributes:**
- `_req`: dict — stores keyword arguments passed to `__init__`.

**Methods:**

1. **`__init__(self, **kwargs)`** — Stores all keyword arguments in `self._req`.

2. **`__call__(self, method)`** — Returns a wrapper function `_method_wrapper(self_, *args, **kwargs)`. When invoked:
   - Iterates over each key-value pair `(k, v)` in `self._req`.
   - Calls `getattr(self_, k).update(v)` for each, merging the requirement sets into the corresponding attribute of the printer instance.
   - Then calls the original `method(self_, *args, **kwargs)`.
   - The wrapper is decorated with `@wraps(method)` to preserve metadata.

---

### Class `AssignmentError(Exception)`

**Header:** A custom exception subclassing `Exception`.

**Purpose:** Raised when an assignment variable for a loop is missing (e.g., when `_doprint_loops` encounters indexed expressions but no `assign_to` target).

---

### Class `CodePrinter(StrPrinter)`

**Header:** Inherits from `StrPrinter`. Base class for language-specific code printers.

#### Class Attributes

- **`_operators: Dict[str, str]`** — Maps logical operator names to their string representations:
  ```python
  {'and': '&&', 'or': '||', 'not': '!'}
  ```

- **`_default_settings: Dict[str, Any]`** — Default printing settings:
  ```python
  {
      'order': None,
      'full_prec': 'auto',
      'error_on_reserved': False,
      'reserved_word_suffix': '_',
      'human': True,
      'inline': False,
      'allow_unknown_functions': False,
  }
  ```

- **`_rewriteable_functions: Dict[str, str]`** — Maps function names to simpler functions they can be rewritten into:
  ```python
  {'erf2': 'erf', 'Li': 'li', 'beta': 'gamma'}
  ```

#### Instance Attributes (initialized in `__init__`)

- **`reserved_words: Set[str]`** — A set of reserved keyword names for the target language. Initialized to an empty set if not already defined on the subclass.

---

#### Methods

1. **`__init__(self, settings=None)`**
   - Calls `super().__init__(settings=settings)`.
   - If the instance does not have a `reserved_words` attribute, sets it to `set()`.

2. **`doprint(self, expr, assign_to=None)`** — Main entry point for code generation.
   - Defines an inner function `_handle_assign_to(expr, assign_to)`:
     - If `assign_to is None`, returns `sympify(expr)`.
     - If `assign_to` is a list/tuple: checks that `len(expr) == len(assign_to)` (raises `ValueError` otherwise); recursively handles each `(lhs, rhs)` pair and returns a `CodeBlock(*assignments)`.
     - If `assign_to` is a string: if `expr.is_Matrix`, wraps it as `MatrixSymbol(assign_to, *expr.shape)`; else wraps as `Symbol(assign_to)`.
     - If `assign_to` is not a `Basic` instance (and not str/list/tuple), raises `TypeError`.
     - Otherwise returns `Assignment(assign_to, expr)`.
   - Applies `_handle_assign_to(expr, assign_to)` to produce the final expression.
   - Initializes `self._not_supported = set()` and `self._number_symbols = set()`.
   - Calls `lines = self._print(expr).splitlines()`.
   - If `self._settings["human"]` is True:
     - Builds `frontlines`: for each expression in sorted `self._not_supported`, appends a comment line `"Not supported in {language}:"` followed by the type name of each unsupported expression.
     - For each `(name, value)` pair in sorted `self._number_symbols`, appends the result of `self._declare_number_const(name, value)`.
     - Prepends `frontlines` to `lines`, formats via `self._format_code(lines)`, joins with newlines.
   - If `human` is False: formats lines, builds `num_syms = {(k, self._print(v)) for k, v in self._number_symbols}`, returns the tuple `(num_syms, self._not_supported, "\n".join(lines))`.
   - Resets `self._not_supported` and `self._number_symbols` to empty sets.
   - Returns the result string (or tuple if `human=False`).

3. **`_doprint_loops(self, expr, assign_to=None)`** — Generates loop-based code for expressions containing `Indexed` objects (tensor/array contractions).
   - If `self._settings.get('contract', True)`:
     - Calls `self._get_expression_indices(expr, assign_to)` to get non-dummy indices.
     - Calls `get_contraction_structure(expr)` to get dummy-index groupings.
   - Else: sets `indices = []` and `dummies = {None: (expr,)}`.
   - Gets loop-opening/closing lines via `self._get_loop_opening_ending(indices)`.
   - If `None in dummies`: prints the sum of terms with no summations using `StrPrinter.doprint(self, Add(*dummies[None]))`; else initializes to `"0"`.
   - Gets `lhs_printed = self._print(assign_to)`.
   - If the printed RHS text differs from `lhs_printed`: extends lines with open-loop lines, appends a statement `"{lhs} = {rhs}"` (via `_get_statement`), then closes loops.
   - For each dummy-index group `d` in `dummies`:
     - If `d` is a tuple: sorts indices via `self._sort_optimized(d, expr)`, gets loop lines for those indices.
     - For each term in `dummies[d]`:
       - If the term itself has internal contractions (detected by checking if it appears as a key in `dummies` with non-None keys), raises `NotImplementedError`.
       - Otherwise: if `assign_to is None`, raises `AssignmentError`; if `term.has(assign_to)`, raises `ValueError`.
       - Extends lines with open-loop, then inner open-loop; appends accumulator statement `"{lhs} = {lhs} + term"` (via `_get_statement`); closes inner loop, then outer loop.
   - Returns `"\n".join(lines)`.

4. **`_get_expression_indices(self, expr, assign_to)`** — Determines the non-dummy indices for tensor contraction.
   - Calls `get_indices(expr)` and `get_indices(assign_to)` to get right-hand-side and left-hand-side index lists.
   - If LHS has indices but RHS does not (scalar broadcast), sets `rinds = linds`.
   - If `rinds != linds`, raises `ValueError` with a message about mismatched non-dummy indices.
   - Returns the sorted indices via `self._sort_optimized(rinds, assign_to)`.

5. **`_sort_optimized(self, indices, expr)`** — Sorts loop indices for optimal memory access order.
   - If no indices, returns `[]`.
   - Initializes a `score_table = {}` mapping each index to score 0.
   - Collects all `Indexed` atoms from the expression.
   - For each indexed array and each position `p` in its indices: adds `self._rate_index_position(p)` to that index's score (catching `KeyError`).
   - Returns indices sorted by ascending score (highest-scored = innermost loop).

6. **`_rate_index_position(self, p)`** — Abstract method. Must be implemented by subclasses. Returns a numeric score for an index at position `p`. Raises `NotImplementedError` in the base class.

7. **`_get_statement(self, codestring)`** — Abstract method. Formats a code string with proper line ending (e.g., semicolon). Raises `NotImplementedError` in the base class.

8. **`_get_comment(self, text)`** — Abstract method. Formats text as a comment. Raises `NotImplementedError`.

9. **`_declare_number_const(self, name, value)`** — Abstract method. Generates a constant declaration line for numeric symbol `name` with float value `value`. Raises `NotImplementedError`.

10. **`_format_code(self, lines)`** — Abstract method. Takes a list of code-line strings and formats them (indentation, wrapping). Raises `NotImplementedError`.

11. **`_get_loop_opening_ending(self, indices)`** — Abstract method. Returns `(open_lines, close_lines)`, each a list of code lines for loop headers/closers. Raises `NotImplementedError`.

12. **`_print_Dummy(self, expr)`** — Prints a `Dummy` symbol:
    - If the name starts with `'Dummy_'`, returns `'_' + expr.name`.
    - Otherwise returns `'{name}_{dummy_index}'`.

13. **`_print_CodeBlock(self, expr)`** — Returns each element of `expr.args` printed and joined by newlines.

14. **`_print_String(self, string)`** — Returns `str(string)`.

15. **`_print_QuotedString(self, arg)`** — Returns `'"{arg.text}"'`.

16. **`_print_Comment(self, string)`** — Returns `self._get_comment(str(string))`.

17. **`_print_Assignment(self, expr)`** — Prints an assignment statement.
    - Imports: `Assignment`, `Piecewise`, `MatrixSymbol`, `IndexedBase`.
    - If RHS is a `Piecewise`: transforms each `(expression, condition)` pair into an `Assignment(lhs, expression)`, creates a new `Piecewise` of these assignments, and recursively prints it via `self._print(temp)`.
    - Else if LHS is a `MatrixSymbol`: iterates over matrix indices via `self._traverse_matrix_indices(lhs)`, creates element-wise `Assignment(lhs[i,j], rhs[i,j])`, prints each, joins with newlines.
    - Else if `'contract'` setting is True and either LHS or RHS has `IndexedBase`: delegates to `self._doprint_loops(rhs, lhs)`.
    - Otherwise: gets `lhs_code = self._print(lhs)` and `rhs_code = self._print(rhs)`, returns `self._get_statement("{lhs} = {rhs}")`.

18. **`_print_AugmentedAssignment(self, expr)`** — Prints an augmented assignment (e.g., `+=`). Returns `"{lhs} {op} {rhs}"` formatted via `_get_statement`, where each component is printed individually.

19. **`_print_FunctionCall(self, expr)`** — Returns `'{name}({args})'` where args are the result of printing each element in `expr.function_args`, joined by `', '`.

20. **`_print_Variable(self, expr)`** — Returns `self._print(expr.symbol)`.

21. **`_print_Statement(self, expr)`** — Prints the single argument of `expr.args` and wraps it via `_get_statement`.

22. **`_print_Symbol(self, expr)`** — Calls parent's `_print_Symbol` to get the name string.
    - If the name is in `self.reserved_words`: if `'error_on_reserved'` setting is True, raises `ValueError`; otherwise returns `name + self._settings['reserved_word_suffix']`.
    - Otherwise returns the name unchanged.

23. **`_print_Function(self, expr)`** — Prints a function call expression.
    - If `expr.func.__name__` is in `self.known_functions`:
      - Gets `cond_func = self.known_functions[expr.func.__name__]`.
      - If it's a string, uses it directly as the function name.
      - If it's a list of `(condition, func_string)` tuples: iterates to find the first condition that matches (called with `*expr.args`), breaks on match.
      - If a function string was found: tries to call `func(*[self.parenthesize(item, 0) for item in expr.args])`; if `TypeError`, falls back to `'{func}({stringified_args})'`.
    - Else if the expression has `_imp_` attribute that is a `Lambda`: returns `self._print(expr._imp_(*expr.args))` (inlined).
    - Else if `expr.func.__name__` is in `_rewriteable_functions` and the target function is in `known_functions`: rewrites via `expr.rewrite(target)` and prints recursively.
    - Else if `allow_unknown_functions` setting is True: returns `'{func_name}({args})'`.
    - Otherwise: calls `self._print_not_supported(expr)`.

24. **`_print_Expr = _print_Function`** — Alias; generic expression printing delegates to `_print_Function`.

25. **`_print_NumberSymbol(self, expr)`** — Handles symbolic constants (Pi, EulerGamma, etc.).
    - If `'inline'` setting is True: returns `self._print(Float(expr.evalf(self._settings["precision"])))`.
    - Else: adds `(expr, Float(expr.evalf(self._settings["precision"])))` to `self._number_symbols`, returns `str(expr)`.

26. **`_print_Catalan(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

27. **`_print_EulerGamma(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

28. **`_print_GoldenRatio(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

29. **`_print_TribonacciConstant(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

30. **`_print_Exp1(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

31. **`_print_Pi(self, expr)`** — Delegates to `_print_NumberSymbol(expr)`.

32. **`_print_And(self, expr)`** — Joins sorted args (sorted by `default_sort_key`) with `' && '`, parenthesizing each at the expression's precedence level.

33. **`_print_Or(self, expr)`** — Same as `_print_And` but with `' || '` separator.

34. **`_print_Xor(self, expr)`** — If `self._operators.get('xor')` is None, calls `_print_not_supported(expr)`. Otherwise joins args with the xor operator string, parenthesizing each at precedence level.

35. **`_print_Equivalent(self, expr)`** — Same as `_print_Xor` but uses `'equivalent'` from operators; falls back to `_print_not_supported` if unavailable.

36. **`_print_Not(self, expr)`** — Returns `'{op}{parenthesized_arg}'` where op is `'!'` and the arg is parenthesized at precedence level.

37. **`_print_Mul(self, expr)`** — Prints a multiplication expression with numerator/denominator handling.
    - Gets precedence.
    - Extracts coefficient `c` via `expr.as_coeff_Mul()`. If `c < 0`: negates the coefficient and sets `sign = "-"`; else `sign = ""`.
    - Initializes lists `a` (numerator), `b` (denominator), `pow_paren` (Powers with exp=-1 and multi-symbol base).
    - Orders factors: if `self.order not in ('old', 'none')`, uses `expr.as_ordered_factors()`; else `Mul.make_args(expr)`.
    - For each item: if it is a commutative Pow with negative rational exponent:
      - If exp != -1, appends `Pow(base, -exp, evaluate=False)` to denominator.
      - If exp == -1 and the base has more than one argument AND is a Mul (to avoid issue #14160), adds to `pow_paren`; otherwise appends `Pow(base, 1)` to denominator.
    - Else: appends to numerator.
    - Ensures `a` is non-empty (`a or [S.One]`).
    - Parenthesizes all numerator and denominator items at the expression's precedence.
    - For each item in `pow_paren` that appears in `b`, wraps its string representation in parentheses.
    - Returns: if no denominator, `'sign *'.join(a_str)`; if one denominator item, `'sign *'.join(a_str) + "/" + b_str[0]`; else `'sign *'.join(a_str) + "/(" + '*'.join(b_str) + ")"`.

38. **`_print_not_supported(self, expr)`** — Adds `expr` to `self._not_supported` (catching `TypeError` if not hashable). Returns `self.emptyPrinter(expr)`.

39. **Unsupported print methods** (all alias `_print_not_supported`):
    - `_print_Basic`, `_print_ComplexInfinity`, `_print_Derivative`, `_print_ExprCondPair`, `_print_GeometryEntity`, `_print_Infinity`, `_print_Integral`, `_print_Interval`, `_print_AccumulationBounds`, `_print_Limit`, `_print_MatrixBase`, `_print_DeferredVector`, `_print_NaN`, `_print_NegativeInfinity`, `_print_Order`, `_print_RootOf`, `_print_RootsOf`, `_print_RootSum`, `_print_Uniform`, `_print_Unit`, `_print_Wild`, `_print_WildFunction`, `_print_Relational`.

---

### Function `ccode(expr, assign_to=None, standard='c99', **settings)`

- Imports `c_code_printers` from `sympy.printing.c`.
- Looks up the printer class by `standard.lower()` in `c_code_printers`.
- Instantiates it with `settings`, calls `.doprint(expr, assign_to)`, and returns the result.

---

### Function `print_ccode(expr, **settings)`

- Calls `ccode(expr, **settings)` and prints the result to stdout.

---

### Function `fcode(expr, assign_to=None, **settings)`

- Imports `FCodePrinter` from `sympy.printing.fortran`.
- Instantiates it with `settings`, calls `.doprint(expr, assign_to)`, and returns the result.

---

### Function `print_fcode(expr, **settings)`

- Calls `fcode(expr, **settings)` and prints the result to stdout.

---

### Function `cxxcode(expr, assign_to=None, standard='c++11', **settings)`

- Imports `cxx_code_printers` from `sympy.printing.cxx`.
- Looks up the printer class by `standard.lower()` in `cxx_code_printers`.
- Instantiates it with `settings`, calls `.doprint(expr, assign_to)`, and returns the result.

## sympy/printing/precedence.py
Here is the complete natural-language specification of `sympy/printing/precedence.py`:

---

## Module-Level Preamble

### Imports
- `from sympy.core.function import _coeff_isneg` — imported for use in `precedence_Mul`.

### Constants & Globals

**`PRECEDENCE`** (dict[str, int]) — Default precedence values keyed by type name strings. Higher numbers bind tighter:

| Key | Value |
|---|---|
| `"Lambda"` | 1 |
| `"Xor"` | 10 |
| `"Or"` | 20 |
| `"And"` | 30 |
| `"Relational"` | 35 |
| `"BitwiseOr"` | 36 |
| `"BitwiseXor"` | 37 |
| `"BitwiseAnd"` | 38 |
| `"Add"` | 40 |
| `"Mul"` | 50 |
| `"Pow"` | 60 |
| `"Func"` | 70 |
| `"Not"` | 100 |
| `"Atom"` | 1000 |

**`PRECEDENCE_VALUES`** (dict[str, int]) — Maps class names to precedence values. These are treated as inheritable: if a class's name or any of its MRO entries' `__name__` appears here, the associated value is returned. Entries:

| Key | Value |
|---|---|
| `"Equivalent"` | `PRECEDENCE["Xor"]` (10) |
| `"Xor"` | `PRECEDENCE["Xor"]` (10) |
| `"Implies"` | `PRECEDENCE["Xor"]` (10) |
| `"Or"` | `PRECEDENCE["Or"]` (20) |
| `"And"` | `PRECEDENCE["And"]` (30) |
| `"Add"` | `PRECEDENCE["Add"]` (40) |
| `"Pow"` | `PRECEDENCE["Pow"]` (60) |
| `"Relational"` | `PRECEDENCE["Relational"]` (35) |
| `"Sub"` | `PRECEDENCE["Add"]` (40) |
| `"Not"` | `PRECEDENCE["Not"]` (100) |
| `"Function"` | `PRECEDENCE["Func"]` (70) |
| `"NegativeInfinity"` | `PRECEDENCE["Add"]` (40) |
| `"MatAdd"` | `PRECEDENCE["Add"]` (40) |
| `"MatPow"` | `PRECEDENCE["Pow"]` (60) |
| `"MatrixSolve"` | `PRECEDENCE["Mul"]` (50) |
| `"TensAdd"` | `PRECEDENCE["Add"]` (40) |
| `"TensMul"` | `PRECEDENCE["Mul"]` (50) |
| `"HadamardProduct"` | `PRECEDENCE["Mul"]` (50) |
| `"HadamardPower"` | `PRECEDENCE["Pow"]` (60) |
| `"KroneckerProduct"` | `PRECEDENCE["Mul"]` (50) |
| `"Equality"` | `PRECEDENCE["Mul"]` (50) |
| `"Unequality"` | `PRECEDENCE["Mul"]` (50) |

**`PRECEDENCE_FUNCTIONS`** (dict[str, Callable[[object], int]]) — Maps class names to functions that compute a dynamic precedence value from an instance. Entries:

| Key | Value |
|---|---|
| `"Integer"` | `precedence_Integer` |
| `"Mul"` | `precedence_Mul` |
| `"Rational"` | `precedence_Rational` |
| `"Float"` | `precedence_Float` |
| `"PolyElement"` | `precedence_PolyElement` |
| `"FracElement"` | `precedence_FracElement` |
| `"UnevaluatedExpr"` | `precedence_UnevaluatedExpr` |

**`PRECEDENCE_TRADITIONAL`** (dict[str, int]) — A copy of `PRECEDENCE` with the following overrides:

| Key | Value |
|---|---|
| `'Integral'` | `PRECEDENCE["Mul"]` (50) |
| `'Sum'` | `PRECEDENCE["Mul"]` (50) |
| `'Product'` | `PRECEDENCE["Mul"]` (50) |
| `'Limit'` | `PRECEDENCE["Mul"]` (50) |
| `'Derivative'` | `PRECEDENCE["Mul"]` (50) |
| `'TensorProduct'` | `PRECEDENCE["Mul"]` (50) |
| `'Transpose'` | `PRECEDENCE["Pow"]` (60) |
| `'Adjoint'` | `PRECEDENCE["Pow"]` (60) |
| `'Dot'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Cross'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Gradient'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Divergence'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Curl'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Laplacian'` | `PRECEDENCE["Mul"] - 1` (49) |
| `'Union'` | `PRECEDENCE['Xor']` (10) |
| `'Intersection'` | `PRECEDENCE['Xor']` (10) |
| `'Complement'` | `PRECEDENCE['Xor']` (10) |
| `'SymmetricDifference'` | `PRECEDENCE['Xor']` (10) |
| `'ProductSet'` | `PRECEDENCE['Xor']` (10) |

---

## Code Objects

### Precedence Functions (module-level)

#### `precedence_Mul(item) → int`
Returns the precedence for a multiplication-like object. If `_coeff_isneg(item)` is truthy, returns `PRECEDENCE["Add"]` (40); otherwise returns `PRECEDENCE["Mul"]` (50).

#### `precedence_Rational(item) → int`
Returns the precedence for a rational number. If `item.p < 0`, returns `PRECEDENCE["Add"]` (40); otherwise returns `PRECEDENCE["Mul"]` (50).

#### `precedence_Integer(item) → int`
Returns the precedence for an integer. If `item.p < 0`, returns `PRECEDENCE["Add"]` (40); otherwise returns `PRECEDENCE["Atom"]` (1000).

#### `precedence_Float(item) → int`
Returns the precedence for a floating-point number. If `item < 0`, returns `PRECEDENCE["Add"]` (40); otherwise returns `PRECEDENCE["Atom"]` (1000).

#### `precedence_PolyElement(item) → int`
Returns the precedence for a polynomial ring element (`PolyElement`). Logic:
- If `item.is_generator` is truthy, returns `PRECEDENCE["Atom"]` (1000).
- Else if `item.is_ground` is truthy, recursively calls `precedence(item.coeff(1))`.
- Else if `item.is_term` is truthy, returns `PRECEDENCE["Mul"]` (50).
- Otherwise (multi-term polynomial), returns `PRECEDENCE["Add"]` (40).

#### `precedence_FracElement(item) → int`
Returns the precedence for a fraction field element (`FracElement`). If `item.denom == 1`, delegates to `precedence_PolyElement(item.numer)`; otherwise returns `PRECEDENCE["Mul"]` (50).

#### `precedence_UnevaluatedExpr(item) → float`
Returns the precedence of the inner expression minus 0.5: `precedence(item.args[0]) - 0.5`.

---

### Core Functions

#### `precedence(item) → int | float`
Returns the precedence for StrPrinter formatting. Algorithm:
1. If `item` has an attribute named `"precedence"`, return it directly (`item.precedence`).
2. Otherwise, attempt to read `item.__class__.__mro__`. If this raises `AttributeError`, return `PRECEDENCE["Atom"]` (1000).
3. Iterate over each class `i` in the MRO list:
   - Let `n = i.__name__`.
   - If `n` is a key in `PRECEDENCE_FUNCTIONS`, call that function with `item` and return its result immediately.
   - Else if `n` is a key in `PRECEDENCE_VALUES`, return the associated value immediately.
4. If no MRO entry matched, return `PRECEDENCE["Atom"]` (1000).

#### `precedence_traditional(item) → int | float`
Returns the precedence for LaTeX and pretty printers according to traditional mathematical notation rules. Algorithm:
1. Import `UnevaluatedExpr` from `sympy.core.expr`.
2. If `isinstance(item, UnevaluatedExpr)` is true, recursively call `precedence_traditional(item.args[0])` and return the result.
3. Let `n = item.__class__.__name__`.
4. If `n` is a key in `PRECEDENCE_TRADITIONAL`, return `PRECEDENCE_TRADITIONAL[n]`.
5. Otherwise, fall back to `precedence(item)` (the StrPrinter precedence) and return that result.