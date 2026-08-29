## sympy/printing/latex.py
The complete natural-language specification for `sympy/printing/latex.py` has been written to `/tmp/omp_desc_rzeaw169/sympy_printing_latex_spec.md`. It covers all 2,281 lines of the file, including:

- **All imports** (exact order and aliases)
- **All module-level constants**: `accepted_latex_functions`, `tex_greek_dictionary` (37 entries), `other_symbols`, `modifier_dict` (19 modifiers with their lambda implementations), `greek_letters_set`, `_between_two_numbers_p` (2 regex patterns)
- **The `LatexPrinter` class** in full: default settings, `__init__`, all helper methods (`parenthesize`, `doprint`, bracket-checkers, etc.), and every `_print_*` method (~100+ print handlers covering Add, Mul, Pow, functions, matrices, special functions (Bessel, Airy, hypergeometric, Meijer G, elliptic integrals), polynomials, sets, intervals, transforms, category theory objects, differential geometry primitives, number-theoretic functions, and more)
- **The `translate()` function** with its modifier-chain resolution logic
- **The `latex()` and `print_latex()` top-level API functions**

## sympy/printing/pretty/pretty.py
The complete natural-language specification of `sympy/printing/pretty/pretty.py` (2343 lines) has been written to `/tmp/omp_desc_4x98mq9t/spec_pretty.md`. Here's what it covers:

**Structure:**

1. **Module-Level Preamble** — All 17 imports listed precisely, plus the two module-level aliases (`pprint_use_unicode`, `pprint_try_use_unicode`).

2. **Class `PrettyPrinter(Printer)`** — Settings dict with all 6 keys and defaults; `__init__` (emptyPrinter fallback); `_use_unicode` property; `doprint`.

3. **~100+ `_print_*` methods**, organized by domain:
   - Type dispatch/fallback (`_print_Atom`, `_print_stringPict`, etc.) with all aliases
   - Symbols, floats, vector calculus (Cross, Curl, Divergence, Dot, Gradient)
   - Factorials/binomials/subfactorials
   - Relational and boolean operations (And, Or, Xor, Nand, Nor, Implies, Equivalent, Not) — including the private `__print_Boolean` helper
   - Unary functions (conjugate, Abs/Determinant, floor/ceiling)
   - Derivatives and limits with full notation rendering
   - Integral, Product, Sum with ASCII vs unicode sign construction
   - Matrix operations (MatrixBase, Transpose, Adjoint, MatAdd/MatMul, MatPow, HadamardProduct, BlockMatrix, MatrixElement, MatrixSlice, NDimArray)
   - Piecewise and hypergeometric functions (hyper, meijerg) with annotated F/G symbols
   - Gamma/beta/DiracDelta/expint/Elliptic integrals/constants
   - Modulo, Add, Mul, Pow with fraction rendering (`_print_nth_root`, `__print_numer_denom`)
   - Set operations (ProductSet, FiniteSet, Range, Interval, Union, Intersection, Complement, SymmetricDifference, ImageSet, ConditionSet, ComplexRegion)
   - Sequence types (SeqFormula/SeqPer/SeqAdd/SeqMul), list, tuple, dict, set, frozenset
   - Algebraic structures (PolyRing, FracField, PolynomialRing/FractionRing, FiniteField, Integer/Rational/Real/Complex fields, GroebnerBasis)
   - Subs, Euler/Catalan numbers, KroneckerDelta, RandomDomain
   - Category theory objects (Object, Morphism, NamedMorphism, IdentityMorphism, CompositeMorphism, Category, Diagram, DiagramGrid)
   - Module theory (FreeModuleElement, SubModule, FreeModule, ModuleImplementedIdeal)
   - Quotient structures (QuotientRing/Module and their elements)
   - Matrix homomorphism, differential geometry (BaseScalarField, BaseVectorField, Differential)
   - Prime number functions (primenu, primeomega), Quantity

4. **Three standalone functions** — `pretty()`, `pretty_print()` (+ `pprint` alias), `pager_print()` — with full parameter lists and behavior descriptions.

## sympy/printing/str.py
Now I have the full file content (829 lines). Let me compile the comprehensive specification.

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division
from sympy.core import S, Rational, Pow, Basic, Mul
from sympy.core.mul import _keep_coeff
from .printer import Printer
from sympy.printing.precedence import precedence, PRECEDENCE
import mpmath.libmp as mlib
from mpmath.libmp import prec_to_dps
from sympy.utilities import default_sort_key
```

## Constants & Globals

- **`_relationals`** (class attribute of `StrPrinter`): An empty dict `{}` used to map custom relational operators to display strings.

---

# Code Objects

## Class `StrPrinter(Printer)`

### Header

Class `StrPrinter` inherits from `Printer`. Sets `printmethod = "_sympystr"`.

### Default Settings (class attribute)

```python
_default_settings = {
    "order": None,
    "full_prec": "auto",
    "sympy_integers": False,
    "abbrev": False,
}
```

### Attributes

- `_relationals`: dict — initialized as `{}` at class level.
- Inherits `printmethod = "_sympystr"` from parent.
- Inherits `_settings` dict (populated by `Printer.__init__`).
- Inherits `_print_level` counter (used for auto full-precision stripping).

### Methods

#### `parenthesize(self, item, level, strict=False)`

Returns the string representation of `item` wrapped in parentheses if its precedence is less than `level`, or less than or equal to `level` when `strict=False`. Uses `precedence(item)` from `sympy.printing.precedence`. Returns `"(%s)" % self._print(item)` when parenthesization is needed, otherwise returns `self._print(item)`.

#### `stringify(self, args, sep, level=0)`

Joins the string representations of all items in `args` using separator `sep`, with each item parenthesized at the given `level` via `self.parenthesize(item, level)`. Returns a single string.

#### `emptyPrinter(self, expr)`

Fallback for unhandled types:
- If `expr` is a `str`: returns it as-is.
- If `expr` is a `Basic` instance with an `"args"` attribute: returns `repr(expr)`.
- Otherwise: returns `str(expr)`.
- Re-raises the exception if `expr` is a `Basic` without `"args"`.

#### `_print_Add(self, expr, order=None)`

Prints addition expressions. If `self.order == 'none'`, iterates over `list(expr.args)` directly; otherwise calls `self._as_ordered_terms(expr, order=order)`. For each term:
1. Prints the term via `self._print(term)`.
2. Detects leading `'-'` to determine sign (`"-"` or `"+"`).
3. If `precedence(term) < precedence(expr)`, wraps in parentheses.
4. Accumulates `[sign, printed_term]` into list `l`.

Pops the first element (leading sign). If it was `'+'`, replaces with empty string. Returns `sign + ' '.join(l)` — terms separated by spaces with explicit `+`/`-` signs between them.

#### `_print_BooleanTrue(self, expr)` → `"True"`

#### `_print_BooleanFalse(self, expr)` → `"False"`

#### `_print_Not(self, expr)`

Returns `"~%s" % self.parenthesize(expr.args[0], PRECEDENCE["Not"])`.

#### `_print_And(self, expr)`

Returns `self.stringify(expr.args, " & ", PRECEDENCE["BitwiseAnd"])`.

#### `_print_Or(self, expr)`

Returns `self.stringify(expr.args, " | ", PRECEDENCE["BitwiseOr"])`.

#### `_print_AppliedPredicate(self, expr)`

Returns `"%s(%s)" % (expr.func, expr.arg)`.

#### `_print_Basic(self, expr)`

For each arg in `expr.args`, calls `self._print(o)`. Returns `"ClassName(arg1, arg2, ...)"` where `ClassName = expr.__class__.__name__`.

#### `_print_BlockMatrix(self, B)`

If `B.blocks.shape == (1, 1)`, prints `B.blocks[0, 0]` but discards the result. Always returns `self._print(B.blocks)`.

#### `_print_Catalan(self, expr)` → `"Catalan"`

#### `_print_ComplexInfinity(self, expr)` → `"zoo"`

#### `_print_Derivative(self, expr)`

Extracts `dexpr = expr.expr` and builds `dvars`: for each `(var, count)` in `expr.variable_count`, uses just `var` if `count == 1`, otherwise the full tuple. Returns `"Derivative(%s)" % ", ".join(map(self._print, [dexpr] + dvars))`.

#### `_print_dict(self, d)`

Sorts keys by `default_sort_key`. For each key, formats as `"%s: %s" % (self._print(key), self._print(d[key]))`. Returns `"{" + ", ".join(items) + "}"`.

#### `_print_Dict(self, expr)`

Delegates to `self._print_dict(expr)`.

#### `_print_RandomDomain(self, d)`

Three branches:
1. If `d` has `"as_boolean"` attribute: returns `"Domain: " + self._print(d.as_boolean())`.
2. Else if `d` has `"set"` attribute: returns `"Domain: " + self._print(d.symbols) + " in " + self._print(d.set)`.
3. Otherwise: returns `"Domain on " + self._print(d.symbols)`.

#### `_print_Dummy(self, expr)` → `"_%s" % expr.name` (prefixes name with underscore).

#### `_print_EulerGamma(self, expr)` → `"EulerGamma"`

#### `_print_Exp1(self, expr)` → `"E"`

#### `_print_ExprCondPair(self, expr)` → `"(expr, cond)"` using attribute access.

#### `_print_FiniteSet(self, s)`

Sorts elements by `default_sort_key`. If more than 10 elements: shows first 3 + `"..."` + last 3; otherwise all elements. Returns `'{' + ', '.join(...) + '}'`.

#### `_print_Function(self, expr)`

Returns `"func_name(args)"` where func name is `expr.func.__name__`, args joined by `", "` via `self.stringify(expr.args, ", ")`.

#### `_print_GeometryEntity(self, expr)` → `str(expr)`.

#### `_print_GoldenRatio(self, expr)` → `"GoldenRatio"`

#### `_print_ImaginaryUnit(self, expr)` → `"I"`

#### `_print_Infinity(self, expr)` → `"oo"`

#### `_print_Integral(self, expr)`

Inner helper `_xab_tostr(xab)`: if `len(xab) == 1`, returns `self._print(xab[0])`; else returns `self._print((xab[0],) + tuple(xab[1:]))`. Builds limit string by joining `_xab_tostr(l)` for each limit in `expr.limits` with `", "`. Returns `"Integral(%s, %s)" % (self._print(expr.function), L)`.

#### `_print_Interval(self, i)`

Extracts `a, b, l, r = i.args` (a=lower, b=upper, l=left_closed, r=right_closed). Determines suffix `m`:
- Empty string `''` if either endpoint is infinite, or both endpoints are closed.
- `'.open'` if both finite and both open.
- `'.Lopen'` if left open, right closed.
- `'.Ropen'` if left closed, right open.

Returns `"Interval{m}({a}, {b})".format(a=a, b=b, m=m)`.

#### `_print_AccumulationBounds(self, i)` → `"AccumBounds(%s, %s)" % (self._print(i.min), self._print(i.max))`

#### `_print_Inverse(self, I)` → `"%s^-1" % self.parenthesize(I.arg, PRECEDENCE["Pow"])`.

#### `_print_Lambda(self, obj)`

Unpacks `args, expr = obj.args`:
- If `len(args) == 1`: returns `"Lambda(%s, %s)" % (args.args[0], expr)`.
- Otherwise: joins args with `", "`, returns `"Lambda((%s), %s)" % (arg_string, expr)`.

#### `_print_LatticeOp(self, expr)`

Sorts args by `default_sort_key`. Returns `"func_name(%s)" % ", ".join(self._print(arg) for arg in sorted_args)`.

#### `_print_Limit(self, expr)`

Unpacks `e, z, z0, dir = expr.args`:
- If `str(dir) == "+"`: returns `"Limit(%s, %s, %s)" % (e, z, z0)`.
- Otherwise: returns `"Limit(%s, %s, %s, dir='%s')" % (e, z, z0, dir)`.

#### `_print_list(self, expr)` → `"[%s]" % self.stringify(expr, ", ")`.

#### `_print_MatrixBase(self, expr)` → `expr._format_str(self)`.

**Aliases**: `_print_SparseMatrix`, `_print_MutableSparseMatrix`, `_print_ImmutableSparseMatrix`, `_print_Matrix`, `_print_DenseMatrix`, `_print_MutableDenseMatrix`, `_print_ImmutableMatrix`, `_print_ImmutableDenseMatrix` — all point to `_print_MatrixBase`.

#### `_print_MatrixElement(self, expr)`

Returns `parenthesized_parent + "[%s, %s]" % (expr.i, expr.j)`, where parent is parenthesized at `PRECEDENCE["Atom"]` with `strict=True`.

#### `_print_MatrixSlice(self, expr)`

Inner helper `strslice(x)`: converts slice to list `[start, stop, step]`; removes step if 1; removes stop if `stop == start + 1`; replaces start with empty string if 0. Joins remaining parts with `":"`. Returns `"parent[rowslice, colslice]"` where each slice is processed by `strslice`.

#### `_print_DeferredVector(self, expr)` → `expr.name`.

#### `_print_Mul(self, expr)`

1. Gets `prec = precedence(expr)`.
2. Extracts coefficient `c` and rest `e` via `expr.as_coeff_Mul()`. If `c < 0`, rewraps as `_keep_coeff(-c, e)` and sets `sign = "-"`; else `sign = ""`.
3. Initializes numerator list `a` and denominator list `b`.
4. Orders factors: if `self.order not in ('old', 'none')`, uses `expr.as_ordered_factors()`; otherwise `Mul.make_args(expr)`.
5. For each factor:
   - If commutative, is a Pow with rational negative exponent: adds to denominator list `b` (with negated exponent).
   - If Rational and not Infinity: numerator part goes to `a` if `p != 1`; denominator part goes to `b` if `q != 1`.
   - Otherwise: adds to numerator list `a`.
6. Ensures `a = a or [S.One]`.
7. Parenthesizes all items in `a` and `b` at precedence `prec`.
8. Returns:
   - No denominator: `sign + '*'.join(a_str)`.
   - One denominator item: `sign + '*'.join(a_str) + "/" + b_str[0]`.
   - Multiple denominator items: `sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)`.

#### `_print_MatMul(self, expr)` → `"*".join([self.parenthesize(arg, precedence(expr)) for arg in expr.args])`.

#### `_print_HadamardProduct(self, expr)` → `".*".join([self.parenthesize(arg, precedence(expr)) for arg in expr.args])`.

#### `_print_MatAdd(self, expr)` → `" + ".join([self.parenthesize(arg, precedence(expr)) for arg in expr.args])`.

#### `_print_NaN(self, expr)` → `"nan"`.

#### `_print_NegativeInfinity(self, expr)` → `"-oo"`.

#### `_print_Normal(self, expr)` → `"Normal(%s, %s)" % (expr.mu, expr.sigma)`.

#### `_print_Order(self, expr)`

If all point coordinates are zero or no variables:
- If ≤ 1 variable: returns `"O(%s)" % self._print(expr.expr)`.
- Otherwise: returns `"O(%s)" % self.stringify((expr.expr,) + expr.variables, ', ', 0)`.

Else (non-zero point): returns `"O(%s)" % self.stringify(expr.args, ', ', 0)`.

#### `_print_Ordinal(self, expr)` → `expr.__str__()`.

#### `_print_Cycle(self, expr)` → `expr.__str__()`.

#### `_print_Permutation(self, expr)`

Imports `Permutation` and `Cycle` from `sympy.combinatorics.permutations`:
- If `Permutation.print_cyclic` is True:
  - If no size: returns `"()"`.
  - Gets cyclic representation via `Cycle(expr)(expr.size - 1).__repr__()`, strips `"Cycle"` prefix.
  - Finds last `'('`; if not at position 0 and no comma after it, rotates string to start from that bracket.
  - Removes all commas. Returns the result.
- Else (array form):
  - Gets `s = expr.support()`. If empty: returns `"Permutation(%s)" % str(expr.array_form)` if size < 5; else `"Permutation([], size=%s)" % expr.size`.
  - Otherwise: compares trimmed array form (`str(array_form[:support[-1]+1]) + ", size=N"`) with full form; uses shorter. Returns `"Permutation(%s)" % use`.

#### `_print_TensorIndex(self, expr)` → `expr._print()`.

#### `_print_TensorHead(self, expr)` → `expr._print()`.

#### `_print_Tensor(self, expr)` → `expr._print()`.

#### `_print_TensMul(self, expr)` → `expr._print()`.

#### `_print_TensAdd(self, expr)` → `expr._print()`.

#### `_print_PermutationGroup(self, expr)`

Formats each arg as `"    %s" % str(a)`, joins with `",\n"`, wraps in `"PermutationGroup([\n%s])"`.

#### `_print_PDF(self, expr)`

Returns `"PDF(%s, (%s, %s, %s))" % (self._print(expr.pdf.args[1]), self._print(expr.pdf.args[0]), self._print(expr.domain[0]), self._print(expr.domain[1]))`.

#### `_print_Pi(self, expr)` → `"pi"`.

#### `_print_PolyRing(self, ring)`

Returns `"Polynomial ring in %s over %s with %s order" % (", ".join(map(self._print, ring.symbols)), ring.domain, ring.order)`.

#### `_print_FracField(self, field)`

Returns `"Rational function field in %s over %s with %s order" % (", ".join(map(self._print, field.symbols)), field.domain, field.order)`.

#### `_print_FreeGroupElement(self, elm)` → `elm.__str__()`.

#### `_print_PolyElement(self, poly)`

Returns `poly.str(self, PRECEDENCE, "%s**%s", "*")`.

#### `_print_FracElement(self, frac)`

If denominator is 1: returns `self._print(frac.numer)`. Otherwise: parenthesizes numerator at `PRECEDENCE["Mul"]` strict=True and denominator at `PRECEDENCE["Atom"]` strict=True; returns `"numer/denom"`.

#### `_print_Poly(self, expr)`

Sets `ATOM_PREC = PRECEDENCE["Atom"] - 1`. Builds `gens` list by parenthesizing each generator. For each `(monom, coeff)` in `expr.terms()`:
- Builds monomial string: for each exponent > 0, uses `"gen"**exp` if exp > 1, else just `"gen"`. Joins with `"*"`.
- If coefficient is an Add and monomial exists: wraps coefficient in parentheses; otherwise prints directly.
- Special cases: `S.One` → adds `'+'` + monomial (continue); `S.NegativeOne` → adds `'-'` + monomial (continue).
- Combines coeff*monomial or just coeff.
- If term starts with `'-'`, strips sign and prepends `'-'` to terms list; else prepends `'+'`.

After all terms, pops leading modifier (`'+'`/`'-'`). If `'-'`, negates the first remaining term.

Builds format string: `"ClassName(%s, %s"` + either `", modulus=%s" % expr.get_modulus()` or `", domain='%s'" % expr.get_domain()`. Strips outer parens from gens longer than 2 chars. Returns formatted string with terms and gens.

#### `_print_ProductSet(self, p)` → `' x '.join(self._print(set) for set in p.sets)`.

#### `_print_AlgebraicNumber(self, expr)`

If `expr.is_aliased`: returns `self._print(expr.as_poly().as_expr())`; else: returns `self._print(expr.as_expr())`.

#### `_print_Pow(self, expr, rational=False)`

1. Gets `PREC = precedence(expr)`.
2. If exponent is exactly `S.Half` and not in rational mode: returns `"sqrt(%s)" % self._print(expr.base)`.
3. If commutative:
   - If `-expr.exp == S.Half` (not exact equality): returns `"%s/sqrt(%s)" % tuple(map(self._print, (S.One, expr.base)))`.
   - If `expr.exp is -S.One`: returns `'%s/%s' % (self._print(S.One), self.parenthesize(expr.base, PREC))`.
4. Parenthesizes exponent at precedence `PREC`.
5. Special repr mode: if `self.printmethod == '_sympyrepr'` and exp is Rational with non-1 denominator, and parenthesized exp starts with `'(Rational'`, strips outer parens from the result.
6. Returns `'%s**%s' % (parenthesized_base, parenthesized_exp)`.

#### `_print_UnevaluatedExpr(self, expr)` → `self._print(expr.args[0])`.

#### `_print_MatPow(self, expr)`

Returns `'%s**%s' % (self.parenthesize(expr.base, PREC), self.parenthesize(expr.exp, PREC))` where `PREC = precedence(expr)`.

#### `_print_ImmutableDenseNDimArray(self, expr)` → `str(expr)`.

#### `_print_ImmutableSparseNDimArray(self, expr)` → `str(expr)`.

#### `_print_Integer(self, expr)`

If `"sympy_integers"` setting is True: returns `"S(%s)" % (expr)`. Otherwise: returns `str(expr.p)`.

#### `_print_Integers(self, expr)` → `'S.Integers'`.

#### `_print_Naturals(self, expr)` → `'S.Naturals'`.

#### `_print_Naturals0(self, expr)` → `'S.Naturals0'`.

#### `_print_Reals(self, expr)` → `'S.Reals'`.

#### `_print_int(self, expr)` → `str(expr)`.

#### `_print_mpz(self, expr)` → `str(expr)`.

#### `_print_Rational(self, expr)`

If denominator is 1: returns `str(expr.p)`. Otherwise: if `"sympy_integers"` setting True, returns `"S(%s)/%s" % (expr.p, expr.q)`; else `"%s/%s" % (expr.p, expr.q)`.

#### `_print_PythonRational(self, expr)`

If denominator is 1: returns `str(expr.p)`. Otherwise: `"%d/%d" % (expr.p, expr.q)`.

#### `_print_Fraction(self, expr)`

If denominator is 1: returns `str(expr.numerator)`. Otherwise: `"%s/%s" % (expr.numerator, expr.denominator)`.

#### `_print_mpq(self, expr)`

Same logic as `_print_Fraction`: if denominator is 1 → `str(numerator)`; else `"%s/%s" % (numerator, denominator)`.

#### `_print_Float(self, expr)`

1. Gets `prec = expr._prec`. If prec < 5: `dps = 0`; else `dps = prec_to_dps(expr._prec)`.
2. Determines `strip` flag: True if `full_prec is False`, False if `full_prec is True`, or `self._print_level > 1` if `"auto"`.
3. Calls `mlib.to_str(expr._mpf_, dps, strip_zeros=strip)`.
4. Post-processing:
   - If starts with `'-.0'`: replaces with `'-0.' + rv[3:]`.
   - If starts with `'.0'`: replaces with `'0.' + rv[2:]`.
   - If starts with `'+'`: strips the leading `+` (e.g., `'+inf' → 'inf'`).
5. Returns the result string.

#### `_print_Relational(self, expr)`

Defines `charmap = {"==": "Eq", "!=": "Ne", ":=": "Assignment", "+=": "AddAugmentedAssignment", "-=": "SubAugmentedAssignment", "*=": "MulAugmentedAssignment", "/=": "DivAugmentedAssignment", "%=": "ModAugmentedAssignment"}`.

If `expr.rel_op` is in charmap: returns `'%s(%s, %s)' % (charmap[rel_op], expr.lhs, expr.rhs)`. Otherwise: returns `'%s %s %s' % (parenthesized_lhs, rel_op_lookup_or_raw_rel_op, parenthesized_rhs)` where lookup uses `self._relationals.get(expr.rel_op) or expr.rel_op`, and both sides are parenthesized at `precedence(expr)`.

#### `_print_ComplexRootOf(self, expr)` → `"CRootOf(%s, %d)" % (self._print_Add(expr.expr, order='lex'), expr.index)`.

#### `_print_RootSum(self, expr)`

Builds args list: `[self._print_Add(expr.expr, order='lex')]`. If `expr.fun is not S.IdentityFunction`, appends `self._print(expr.fun)`. Returns `"RootSum(%s)" % ", ".join(args)`.

#### `_print_GroebnerBasis(self, basis)`

Class name from `basis.__class__.__name__`. Prints each expression in `basis.exprs` via `_print_Add(arg, order=basis.order)`, wraps in brackets. Prints generators and domain/order as `"domain='%s'"` / `"order='%s'"`. Returns `"ClassName(exprs, gens..., domain='...', order='...')"`.

#### `_print_Sample(self, expr)` → `"Sample([%s])" % self.stringify(expr, ", ", 0)`.

#### `_print_set(self, s)`

Sorts by `default_sort_key`. If empty: returns `"set()"`. Otherwise: `'{' + ', '.join(...) + '}'`.

#### `_print_frozenset(self, s)`

If empty: returns `"frozenset()"`. Otherwise: `"frozenset(%s)" % self._print_set(s)`.

#### `_print_SparseMatrix(self, expr)`

Imports `Matrix` from `sympy.matrices`; returns `self._print(Matrix(expr))` (converts to dense first).

#### `_print_Sum(self, expr)`

Inner helper `_xab_tostr(xab)`: same as in `_print_Integral`. Returns `'Sum(%s, %s)' % (self._print(expr.function), L)`.

#### `_print_Symbol(self, expr)` → `expr.name`.

**Aliases**: `_print_MatrixSymbol = _print_Symbol`, `_print_RandomSymbol = _print_Symbol`.

#### `_print_Identity(self, expr)` → `"I"`.

#### `_print_ZeroMatrix(self, expr)` → `"0"`.

#### `_print_Predicate(self, expr)` → `"Q.%s" % expr.name`.

#### `_print_str(self, expr)` → `expr` (returns the string as-is).

#### `_print_tuple(self, expr)`

If length is 1: returns `"(%s,)" % self._print(expr[0])`. Otherwise: `"(%s)" % self.stringify(expr, ", ")`.

#### `_print_Tuple(self, expr)` → delegates to `self._print_tuple(expr)`.

#### `_print_Transpose(self, T)` → `"%s.T" % self.parenthesize(T.arg, PRECEDENCE["Pow"])`.

#### `_print_Uniform(self, expr)` → `"Uniform(%s, %s)" % (expr.a, expr.b)`.

#### `_print_Union(self, expr)` → `'Union(%s)' %(', '.join([self._print(a) for a in expr.args]))`.

#### `_print_Complement(self, expr)` → `r' \ '.join(self._print(set) for set in expr.args)`.

#### `_print_Quantity(self, expr)`

If `"abbrev"` setting is True: returns `expr.abbrev`; else: returns `expr.name`.

#### `_print_Quaternion(self, expr)`

Parenthesizes each component at `PRECEDENCE["Mul"]` strict=True. First component as-is; remaining components joined with `"*i"`, `"*j"`, or `"*k"` respectively. Joins all with `" + "`.

#### `_print_Dimension(self, expr)` → `str(expr)`.

#### `_print_Wild(self, expr)` → `expr.name + '_'`.

#### `_print_WildFunction(self, expr)` → `expr.name + '_'`.

#### `_print_Zero(self, expr)`

If `"sympy_integers"` setting True: returns `"S(0)"`; else: returns `"0"`.

#### `_print_DMP(self, p)`

Tries to convert via `p.ring.to_sympy(p)` if ring is not None; catches `SympifyError` and falls through. Otherwise: builds `"%s(%s, %s, %s)" % (cls, rep, dom, ring)` where cls = `p.__class__.__name__`, rep = `self._print(p.rep)`, dom = `self._print(p.dom)`, ring = `self._print(p.ring)`.

#### `_print_DMF(self, expr)` → delegates to `self._print_DMP(expr)`.

#### `_print_Object(self, object)` → `'Object("%s")' % object.name`.

#### `_print_IdentityMorphism(self, morphism)` → `'IdentityMorphism(%s)' % morphism.domain`.

#### `_print_NamedMorphism(self, morphism)` → `'NamedMorphism(%s, %s, "%s")' % (morphism.domain, morphism.codomain, morphism.name)`.

#### `_print_Category(self, category)` → `'Category("%s")' % category.name`.

#### `_print_BaseScalarField(self, field)` → `field._coord_sys._names[field._index]`.

#### `_print_BaseVectorField(self, field)` → `"e_%s" % field._coord_sys._names[field._index]`.

#### `_print_Differential(self, diff)`

Gets `field = diff._form_field`:
- If field has `_coord_sys` attribute: returns `'d%s' % field._coord_sys._names[field._index]`.
- Otherwise: returns `"d(%s)" % self._print(field)`.

#### `_print_Tr(self, expr)` → `"%s(%s)" % ("Tr", self._print(expr.args[0])` (with TODO comment about handling indices).

---

## Function `sstr(expr, **settings)`

Creates a `StrPrinter(settings)` instance and calls `p.doprint(expr)`. Returns the resulting string. Supports settings: `order='none'` for speed on large expressions; `abbrev=True` to print units in abbreviated form.

---

## Class `StrReprPrinter(StrPrinter)`

### Header

Inherits from `StrPrinter`.

### Method `_print_str(self, s)`

Returns `repr(s)` instead of the raw string (for repr-style output).

---

## Function `sstrrepr(expr, **settings)`

Creates a `StrReprPrinter(settings)` instance and calls `p.doprint(expr)`. Returns the expression in mixed str/repr form.