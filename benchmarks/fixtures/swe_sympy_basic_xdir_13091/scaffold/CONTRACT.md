# Implementation target
Write the following 21 modules. They live in the same package and may import each other.

## `sympy/core/basic.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Atom`
- `Basic`
- `_aresame`
- `_atomic`
- `preorder_traversal`

## `sympy/core/exprtools.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Factors`
- `Term`
- `_gcd_terms`
- `_mask_nc`
- `_monotonic_sign`
- `decompose_power`
- `decompose_power_rat`
- `factor_nc`
- `factor_terms`
- `gcd_terms`

## `sympy/core/numbers.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AlgebraicNumber`
- `BIGBITS`
- `Catalan`
- `ComplexInfinity`
- `E`
- `EulerGamma`
- `Exp1`
- `Float`
- `GoldenRatio`
- `Half`
- `I`
- `ImaginaryUnit`
- `Infinity`
- `Integer`
- `IntegerConstant`
- `NaN`
- `NegativeInfinity`
- `NegativeOne`
- `Number`
- `NumberSymbol`
- `One`
- `Pi`
- `Rational`
- `RationalConstant`
- `RealNumber`
- `Zero`
- `_intcache`
- `comp`
- `igcd`
- `igcd_lehmer`
- `igcdex`
- `ilcm`
- `int_trace`
- `mod_inverse`
- `mpf_norm`
- `nan`
- `oo`
- `pi`
- `rnd`
- `seterr`
- `sympify_complex`
- `sympify_fractions`
- `sympify_mpmath`
- `zoo`

## `sympy/geometry/entity.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `GeometryEntity`
- `GeometrySet`
- `ordering_of_classes`
- `rotate`
- `scale`
- `translate`

## `sympy/physics/optics/medium.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Medium`
- `c`

## `sympy/physics/vector/dyadic.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Dyadic`

## `sympy/physics/vector/frame.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CoordinateSym`
- `ReferenceFrame`
- `_check_frame`

## `sympy/physics/vector/vector.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Vector`
- `VectorTypeError`
- `_check_vector`

## `sympy/polys/agca/modules.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FreeModule`
- `FreeModuleElement`
- `FreeModulePolyRing`
- `FreeModuleQuotientRing`
- `Module`
- `ModuleElement`
- `ModuleOrder`
- `QuotientModule`
- `QuotientModuleElement`
- `SubModule`
- `SubModulePolyRing`
- `SubModuleQuotientRing`
- `SubQuotientModule`

## `sympy/polys/domains/domain.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Domain`

## `sympy/polys/domains/expressiondomain.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ExpressionDomain`

## `sympy/polys/domains/pythonrational.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `PythonRational`
- `sympify_pythonrational`

## `sympy/polys/domains/quotientring.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `QuotientRing`
- `QuotientRingElement`

## `sympy/polys/fields.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FracElement`
- `FracField`
- `field`
- `sfield`
- `vfield`
- `xfield`

## `sympy/polys/monomials.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Monomial`
- `MonomialOps`
- `itermonomials`
- `monomial_count`
- `monomial_deg`
- `monomial_div`
- `monomial_divides`
- `monomial_gcd`
- `monomial_lcm`
- `monomial_ldiv`
- `monomial_max`
- `monomial_min`
- `monomial_mul`
- `monomial_pow`
- `term_div`

## `sympy/polys/polyclasses.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ANP`
- `DMF`
- `DMP`
- `GenericPoly`
- `init_normal_ANP`
- `init_normal_DMF`
- `init_normal_DMP`

## `sympy/polys/polytools.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `GroebnerBasis`
- `LC`
- `LM`
- `LT`
- `Poly`
- `PurePoly`
- `_torational_factor_list`
- `cancel`
- `cofactors`
- `compose`
- `content`
- `count_roots`
- `decompose`
- `degree`
- `degree_list`
- `discriminant`
- `div`
- `exquo`
- `factor`
- `factor_list`
- `gcd`
- `gcd_list`
- `gcdex`
- `gff`
- `gff_list`
- `groebner`
- `ground_roots`
- `half_gcdex`
- `intervals`
- `invert`
- `is_zero_dimensional`
- `lcm`
- `lcm_list`
- `monic`
- `nroots`
- `nth_power_roots_poly`
- `parallel_poly_from_expr`
- `pdiv`
- `pexquo`
- `poly`
- `poly_from_expr`
- `pquo`
- `prem`
- `primitive`
- `quo`
- `real_roots`
- `reduced`
- `refine_root`
- `rem`
- `resultant`
- `sqf`
- `sqf_list`
- `sqf_norm`
- `sqf_part`
- `sturm`
- `subresultants`
- `terms_gcd`
- `to_rational_coeffs`
- `trunc`

## `sympy/polys/rings.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `PolyElement`
- `PolyRing`
- `ring`
- `sring`
- `vring`
- `xring`

## `sympy/polys/rootoftools.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CRootOf`
- `ComplexRootOf`
- `RootOf`
- `RootSum`
- `bisect`
- `rootof`

## `sympy/tensor/array/ndim_array.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ImmutableNDimArray`
- `NDimArray`

## `sympy/utilities/enumerative.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `MultisetPartitionTraverser`
- `PartComponent`
- `factoring_visitor`
- `list_visitor`
- `multiset_partitions_taocp`
- `part_key`

Implement them to satisfy the specification. Do not write tests.
