## sympy/physics/quantum/dagger.py
Here is the complete natural-language specification of `sympy/physics/quantum/dagger.py`:

---

## Module-Level Preamble

### Imports

- `from sympy.core import Expr` — imports the base symbolic expression class `Expr`.
- `from sympy.functions.elementary.complexes import adjoint` — imports the existing `adjoint` function (which computes the Hermitian/complex conjugate of an expression).

### Constants & Globals

- `__all__ = ['Dagger']` — a module-level list declaring that only the name `Dagger` is part of this module's public API.

---

## Code Objects

### Class: `Dagger(adjoint)`

**Inheritance:** Subclass of `adjoint` (imported from `sympy.functions.elementary.complexes`).

**Docstring purpose:** Documents that `Dagger` computes the Hermitian conjugate (also called adjoint or Hermitian transpose) of a Sympy expression. For matrices, this is equivalent to taking the complex conjugate followed by the matrix transpose. The docstring includes extensive doctest examples covering quantum objects (`Ket`, `Bra`, `Operator`), inner/outer products, algebraic operations (products, sums, powers), and numeric matrices.

#### Method: `__new__(cls, arg)`

**Signature:** `def __new__(cls, arg)` — where `arg` is a Sympy `Expr` (or any object with compatible methods).

**Implementation logic (step-by-step):**

1. **Check for an explicit `adjoint()` method on `arg`:**
   - If `hasattr(arg, 'adjoint')` is true, call `obj = arg.adjoint()`. This delegates to the argument's own adjoint implementation (used by quantum objects like `Ket`, `Bra`, etc.).

2. **Check for `conjugate()` and `transpose()` methods on `arg`:**
   - If step 1 did not produce a result (`obj` is still unset), check whether `hasattr(arg, 'conjugate')` *and* `hasattr(arg, 'transpose')`.
   - If both are present, compute `obj = arg.conjugate().transpose()` — i.e., take the element-wise complex conjugate first, then transpose. This path handles matrix-like objects (e.g., Sympy `Matrix`).

3. **Return or construct a new symbolic `Dagger` expression:**
   - If `obj is not None` after either of the above checks, return `obj` directly — meaning the adjoint was successfully computed by delegation.
   - Otherwise (`obj is None`, i.e., neither path produced a result), fall back to constructing a symbolic unevaluated `Dagger` expression: call `Expr.__new__(cls, arg)`. This creates an inert `Dagger(arg)` node in the Sympy expression tree that can be simplified later by other rules.

**Return value:**
- A fully evaluated expression (the result of `.adjoint()`, or `.conjugate().transpose()`), **or**
- An unevaluated symbolic `Dagger` object wrapping `arg` if no simplification path was available.

---

### Module-Level Side Effects (after class definition)

1. **`adjoint.__name__ = "Dagger"`** — renames the parent class's display name from `"adjoint"` to `"Dagger"`. This ensures that when Sympy prints or represents instances of `Dagger`, they appear with the correct name rather than inheriting the base class's name.

2. **`adjoint._sympyrepr = lambda a, b: "Dagger(%s)" % b._print(a.args[0])`** — overrides the `_sympyrepr` attribute (used by Sympy's printer infrastructure to produce string representations) with a lambda that formats the output as `Dagger(<printed-arg>)`. The lambda receives two arguments (`a`, `b`) from Sympy's printing machinery and produces a string like `"Dagger(Ket('psi'))"` by calling `b._print()` on the first argument of the expression.

---

## sympy/physics/quantum/operator.py
Now I have all 644 lines read across multiple sections. Let me write the complete specification:

---

# Module-Level Preamble

## Imports

```python
from __future__ import print_function, division
from sympy import Derivative, Expr, Integer, oo, Mul, expand, Add
from sympy.printing.pretty.stringpict import prettyForm
from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.qexpr import QExpr, dispatch_method
from sympy.matrices import eye
```

## Constants & Globals

- **`__all__`**: A list of six strings: `['Operator', 'HermitianOperator', 'UnitaryOperator', 'IdentityOperator', 'OuterProduct', 'DifferentialOperator']`. These are the public exports.

---

# Code Objects

## class Operator(QExpr)

**Header:** Inherits from `QExpr` (a base quantum expression class). No metaclass specified.

**Attributes / Class-level members:**
- `_label_separator = ','` — string used to separate label elements in printing.

### Methods

#### `default_args()` *(classmethod)*
Returns the tuple `("O",)` as the default label argument for subclasses that do not override it.

#### `_print_operator_name(printer, *args)`
Returns `self.__class__.__name__` (the class name string). Used to print the operator's type prefix.

#### `_print_operator_name_latex = _print_operator_name`
Alias: same implementation as `_print_operator_name`. Returns the class name for LaTeX printing.

#### `_print_operator_name_pretty(printer, *args)`
Returns `prettyForm(self.__class__.__name__)`, wrapping the class name in a pretty-formatted string object.

#### `_print_contents(printer, *args)`
If `len(self.label) == 1`: returns `self._print_label(printer, *args)` (just the label). Otherwise: returns `'%s(%s)' % (self._print_operator_name(printer, *args), self._print_label(printer, *args))` — class name followed by parenthesized label.

#### `_print_contents_pretty(printer, *args)`
If `len(self.label) == 1`: returns `self._print_label_pretty(printer, *args)`. Otherwise: creates a prettyForm from the operator name, appends the label wrapped in parentheses via `prettyForm(...).parens(left='(', right=')')`, and concatenates them side-by-side.

#### `_print_contents_latex(printer, *args)`
If `len(self.label) == 1`: returns `self._print_label_latex(printer, *args)`. Otherwise: returns `r'%s\left(%s\right)' % (self._print_operator_name_latex(printer, *args), self._print_label_latex(printer, *args))`.

#### `_eval_commutator(other, **options)`
Delegates to `dispatch_method(self, '_eval_commutator', other, **options)`, which dispatches to the appropriate registered handler. Returns whatever the dispatcher returns (or None if no handler).

#### `_eval_anticommutator(other, **options)`
Same pattern as `_eval_commutator`: calls `dispatch_method(self, '_eval_anticommutator', other, **options)`.

#### `_apply_operator(ket, **options)`
Delegates to `dispatch_method(self, '_apply_operator', ket, **options)`.

#### `matrix_element(*args)`
Always raises `NotImplementedError('matrix_elements is not defined')`.

#### `inverse()`
Returns `self._eval_inverse()`.

#### `inv = inverse`
Alias attribute pointing to the `inverse` method.

#### `_eval_inverse()`
Returns `self**(-1)`, i.e., the operator raised to power -1 via Sympy's power mechanism.

#### `__mul__(self, other)`
If `isinstance(other, IdentityOperator)`: returns `self` (multiplying by identity is a no-op). Otherwise: returns `Mul(self, other)`, creating a Mul expression node representing the product.

---

## class HermitianOperator(Operator)

**Header:** Inherits from `Operator`. No metaclass.

**Attributes / Class-level members:**
- `is_hermitian = True` — boolean flag indicating this operator is self-adjoint.

### Methods

#### `_eval_inverse()`
If `isinstance(self, UnitaryOperator)` (i.e., the instance is also unitary): returns `self`. Otherwise: calls and returns `Operator._eval_inverse(self)`, which produces `self**(-1)`.

#### `_eval_power(exp)`
If `isinstance(self, UnitaryOperator)`:
- If `exp == -1`: returns `Operator._eval_power(self, exp)` (i.e., `self**(-1)`).
- Else if `abs(exp) % 2 == 0` (even absolute exponent): returns `self * Operator._eval_inverse(self)` (which simplifies to the identity for unitary operators).
- Otherwise: returns `self`.
Else (not unitary): calls and returns `Operator._eval_power(self, exp)`, which is `self**exp`.

---

## class UnitaryOperator(Operator)

**Header:** Inherits from `Operator`. No metaclass.

### Methods

#### `_eval_adjoint()`
Returns `self._eval_inverse()`, implementing the unitary property U† = U⁻¹.

---

## class IdentityOperator(Operator)

**Header:** Inherits from `Operator`. No metaclass.

**Attributes / Class-level members:** None beyond those set in `__init__`.

### Methods

#### `dimension` *(property)*
Returns `self.N`, the dimension of the Hilbert space.

#### `default_args()` *(classmethod)*
Returns `(oo,)` — infinity is the default dimension.

#### `__init__(self, *args, **hints)`
If `len(args)` is not 0 or 1: raises `ValueError('0 or 1 parameters expected, got %s' % args)`. Sets `self.N = args[0]` if exactly one argument is provided and it is truthy; otherwise sets `self.N = oo`.

#### `_eval_commutator(other, **hints)`
Returns `Integer(0)` — the identity commutes with everything.

#### `_eval_anticommutator(other, **hints)`
Returns `2 * other` — {I, X} = IX + XI = 2X.

#### `_eval_inverse()`
Returns `self` (the identity is its own inverse).

#### `_eval_adjoint()`
Returns `self` (the identity is self-adjoint).

#### `_apply_operator(ket, **options)`
Returns `ket` unchanged — applying the identity to a state yields the same state.

#### `_eval_power(exp)`
Returns `self` for any exponent — Iⁿ = I.

#### `_print_contents(printer, *args)`
Returns the string `'I'`.

#### `_print_contents_pretty(printer, *args)`
Returns `prettyForm('I')`.

#### `_print_contents_latex(printer, *args)`
Returns `r'{\mathcal{I}}'` — calligraphic I in LaTeX.

#### `__mul__(self, other)`
If `isinstance(other, Operator)`: returns `other` (identity times an operator is that operator). Otherwise: returns `Mul(self, other)`.

#### `_represent_default_basis(**options)`
If `not self.N or self.N == oo`: raises `NotImplementedError('Cannot represent infinite dimensional identity operator as a matrix')`. Gets `format = options.get('format', 'sympy')`; if format is not `'sympy'`, raises `NotImplementedError('Representation in format %s not implemented.' % format)`. Otherwise: returns `eye(self.N)` — an N×N identity matrix from sympy.matrices.

---

## class OuterProduct(Operator)

**Header:** Inherits from `Operator`. No metaclass.

**Attributes / Class-level members:**
- `is_commutative = False`

### Methods

#### `__new__(cls, *args, **old_assumptions)`
Imports `KetBase` and `BraBase` from `sympy.physics.quantum.state`. If `len(args) != 2`: raises `ValueError('2 parameters expected, got %d' % len(args))`. Expands both arguments via `expand()`, producing `ket_expr` and `bra_expr`.

**Case: single ket × single bra (possibly with coefficient):**
If `isinstance(ket_expr, (KetBase, Mul))` and `isinstance(bra_expr, (BraBase, Mul))`: calls `ket_c, kets = ket_expr.args_cnc()` and `bra_c, bras = bra_expr.args_cnc()` to separate coefficients from non-commutative terms. Validates that exactly one KetBase subclass is in `kets` and exactly one BraBase subclass is in `bras`, raising `TypeError` otherwise. Checks that `kets[0].dual_class() == bras[0].__class__` (the bra's dual class matches the ket), raising `TypeError` if not. Creates the object via `Expr.__new__(cls, *(kets[0], bras[0]), **old_assumptions)`, sets `obj.hilbert_space = kets[0].hilbert_space`, and returns `Mul(*(ket_c + bra_c)) * obj` — coefficient times outer product.

**Case: Add (sum) expansion:**
If both are `Add`: iterates over all pairs of terms from each, creating an `OuterProduct(ket_term, bra_term)` for each pair, collecting into `op_terms`. If only ket is `Add`: creates one OuterProduct per ket term with the full bra. If only bra is `Add`: creates one OuterProduct per bra term with the full ket. Returns `Add(*op_terms)`.

**Else:** raises `TypeError('Expected ket and bra expression, got: %r, %r' % (ket_expr, bra_expr))`.

#### `ket` *(property)*
Returns `self.args[0]`, the left-side ket state.

#### `bra` *(property)*
Returns `self.args[1]`, the right-side bra state.

#### `_eval_adjoint()`
Returns `OuterProduct(Dagger(self.bra), Dagger(self.ket))` — swaps and daggers both components (|a⟩⟨b|)† = |b⟩⟨a|.

#### `_sympystr(printer, *args)`
Returns `printer._print(self.ket) + printer._print(self.bra)` — string concatenation of ket and bra representations.

#### `_sympyrepr(printer, *args)`
Returns `'%s(%s,%s)' % (self.__class__.__name__, printer._print(self.ket, *args), printer._print(self.bra, *args))`.

#### `_pretty(printer, *args)`
Creates a prettyForm from the ket's pretty representation and appends the bra's pretty representation to its right.

#### `_latex(printer, *args)`
Returns `printer._print(self.ket, *args) + printer._print(self.bra, *args)` — LaTeX concatenation of ket and bra strings.

#### `_represent(**options)`
Gets matrix representations: `k = self.ket._represent(**options)` and `b = self.bra._represent(**options)`. Returns their product `k * b` (matrix multiplication).

#### `_eval_trace(**kwargs)`
Returns `self.ket._eval_trace(self.bra, **kwargs)` — delegates trace evaluation to the ket's method with the bra as argument.

---

## class DifferentialOperator(Operator)

**Header:** Inherits from `Operator`. No metaclass.

### Properties

#### `variables` *(property)*
Returns `self.args[-1].args` — the tuple of variables (symbols) that the function depends on. For a function like `f(x, y)`, this returns `(x, y)`.

#### `function` *(property)*
Returns `self.args[-1]` — the function expression to be replaced with the wavefunction (e.g., `f(x)`).

#### `expr` *(property)*
Returns `self.args[0]` — the arbitrary Sympy expression containing derivatives and other operations, into which the wavefunction will be substituted.

#### `free_symbols` *(property)*
Returns `self.expr.free_symbols` — the set of free symbols in the expression.

### Methods

#### `_apply_operator_Wavefunction(self, func)`
Imports `Wavefunction` from `sympy.physics.quantum.state`. Extracts `var = self.variables` and `wf_vars = func.args[1:]` (the wavefunction's variables). Gets `f = self.function`. Substitutes the function with the wavefunction evaluated at the differential operator's variables: `new_expr = self.expr.subs(f, func(*var))`. Evaluates derivatives via `new_expr.doit()`. Returns `Wavefunction(new_expr, *wf_vars)`.

#### `_eval_derivative(self, symbol)`
Creates `new_expr = Derivative(self.expr, symbol)` — differentiates the expression with respect to the given symbol. Returns a new `DifferentialOperator(new_expr, self.args[-1])` with the differentiated expression and the same function argument.

#### `_print(printer, *args)`
Returns `'%s(%s)' % (self._print_operator_name(printer, *args), self._print_label(printer, *args))`.

#### `_print_pretty(printer, *args)`
Creates a prettyForm from the operator name, appends the label wrapped in parentheses via `prettyForm(...).parens(left='(', right=')')`, and concatenates them side-by-side. Returns the resulting prettyForm.