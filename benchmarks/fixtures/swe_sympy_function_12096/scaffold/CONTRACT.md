# Implementation target
Write the module at `sympy/core/function.py`.
Other modules import these names from it, so they MUST exist with these exact names:
- `Application`
- `AppliedUndef`
- `ArgumentIndexError`
- `Derivative`
- `Function`
- `FunctionClass`
- `Lambda`
- `PoleError`
- `Subs`
- `UndefinedFunction`
- `WildFunction`
- `_coeff_isneg`
- `_mexpand`
- `count_ops`
- `diff`
- `expand`
- `expand_complex`
- `expand_func`
- `expand_log`
- `expand_mul`
- `expand_multinomial`
- `expand_power_base`
- `expand_power_exp`
- `expand_trig`
- `nfloat`
Implement them to satisfy the specification. Do not write tests.
