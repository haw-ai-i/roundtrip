# Implementation target

Write the module at `sympy/physics/units/prefixes.py`.

It is imported across `sympy.physics.units`, so it MUST define all of these
public names (other modules import them directly):

- `class Prefix` (subclass of sympy's `Expr`)
- `def prefix_unit(unit, prefixes)`
- dict `PREFIXES` and dict `BIN_PREFIXES`
- decimal prefix instances: yotta, zetta, exa, peta, tera, giga, mega, kilo,
  hecto, deca, deci, centi, milli, micro, nano, pico, femto, atto, zepto, yocto
- binary prefix instances: kibi, mebi, gibi, tebi, pebi, exbi

Implement them to satisfy the specification. Do not write tests.
