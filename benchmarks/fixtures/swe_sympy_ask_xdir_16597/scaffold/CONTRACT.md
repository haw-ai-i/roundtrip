# Implementation target
Write the following 6 modules. They live in the same package and may import each other.

## `sympy/assumptions/ask.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AssumptionKeys`
- `Q`
- `_extract_facts`
- `ask`
- `ask_full_inference`
- `compute_known_facts`
- `deprecated_predicates`
- `get_known_facts`
- `get_known_facts_keys`
- `predicate_memo`
- `predicate_storage`
- `register_handler`
- `remove_handler`
- `single_fact_lookup`

## `sympy/assumptions/ask_generated.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `get_known_facts_cnf`
- `get_known_facts_dict`

## `sympy/core/assumptions.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ManagedProperties`
- `StdFactKB`
- `as_property`
- `make_property`

## `sympy/core/power.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Pow`
- `integer_log`
- `integer_nthroot`
- `isqrt`

## `sympy/printing/tree.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `pprint_nodes`
- `print_node`
- `print_tree`
- `tree`

## `sympy/tensor/indexed.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Idx`
- `IndexException`
- `Indexed`
- `IndexedBase`

Implement them to satisfy the specification. Do not write tests.
