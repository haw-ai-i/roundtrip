## django/db/models/fields/related_lookups.py
Now I have the complete file. Here is the full natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import warnings

from django.db.models.lookups import (
    Exact,
    GreaterThan,
    GreaterThanOrEqual,
    In,
    IsNull,
    LessThan,
    LessThanOrEqual,
)
from django.utils.deprecation import RemovedInDjango50Warning
```

### Constants & Globals

None defined at module level. All functionality is encapsulated in one class (`MultiColSource`), one function (`get_normalized_value`), one mixin class (`RelatedLookupMixin`), and five lookup classes that inherit from it plus `RelatedIn`.

---

## Code Objects

### Class: `MultiColSource`

**Base classes:** None (plain object).

**Class attributes:**
- `contains_aggregate = False` — boolean flag indicating no aggregate expressions.
- `contains_over_clause = False` — boolean flag indicating no OVER clause.

**Instance attributes** (set in `__init__`):
- `self.alias` — the table alias string for this source.
- `self.targets` — list of target field objects (one per column involved).
- `self.sources` — list of source field objects corresponding to each target.
- `self.field` — the related field object.
- `self.output_field = self.field` — alias pointing to `field`.

**Methods:**

1. **`__init__(self, alias, targets, sources, field)`**
   - Stores all four arguments as instance attributes in the order: `targets`, `sources`, `field`, `alias`.
   - Sets `output_field = self.field`.

2. **`__repr__(self)`**
   - Returns a string formatted as `"MultiColSource({alias}, {field})"` using `self.__class__.__name__`, `self.alias`, and `self.field`.

3. **`relabeled_clone(self, relabels)`**
   - Creates and returns a new `MultiColSource` instance of the same class.
   - The `alias` is remapped via `relabels.get(self.alias, self.alias)` (falls back to original if not in `relabels`).
   - `targets`, `sources`, and `field` are passed through unchanged.

4. **`get_lookup(self, lookup)`**
   - Delegates to `self.output_field.get_lookup(lookup)` and returns the result.

5. **`resolve_expression(self, *args, **kwargs)`**
   - Returns `self` unchanged (no-op resolution).

---

### Function: `get_normalized_value(value, lhs)`

**Purpose:** Normalizes a value passed as the RHS of a related-field lookup into a tuple suitable for multi-column comparison.

**Parameters:**
- `value` — the raw RHS value (may be a `Model` instance, a scalar, or already a tuple).
- `lhs` — the LHS expression object; must have an `output_field` attribute that has a `path_infos` attribute.

**Logic:**
1. If `value` is an instance of `django.db.models.Model`:
   - If `value.pk is None`, emit a deprecation warning (`RemovedInDjango50Warning`) stating "Passing unsaved model instances to related filters is deprecated." (The code does **not** raise; the comment notes it will be replaced with a `ValueError` when the deprecation ends.)
   - Retrieve the target fields from `lhs.output_field.path_infos[-1].target_fields`.
   - For each `source` in those targets:
     - While `value` is not an instance of `source.model` **and** `source.remote_field` exists, follow the relation chain: set `source = source.remote_field.model._meta.get_field(source.remote_field.field_name)`.
     - Attempt to append `getattr(value, source.attname)` to a list. If this raises `AttributeError`, immediately return `(value.pk,)` as a fallback (handles cases like filtering by a related model's primary key when the relation is a OneToOneField).
   - Return the accumulated list as a tuple.
2. If `value` is not already a tuple, return `(value,)`.
3. Otherwise (`value` is already a tuple), return it unchanged.

**Return value:** A `tuple` of normalized values (one per column in the related lookup).

---

### Class: `RelatedIn(In)`

**Base classes:** Inherits from `In` (from `django.db.models.lookups`).

**Methods:**

1. **`get_prep_lookup(self)`**
   - If `self.lhs` is **not** a `MultiColSource`:
     - If `self.rhs_is_direct_value()` returns `True` (i.e., the RHS is a direct value, not a queryset):
       - Normalize each element of `self.rhs` by calling `get_normalized_value(val, self.lhs)[0]` for every `val` in `self.rhs`, and replace `self.rhs` with the resulting list. This handles single-column relations.
       - If `self.lhs.output_field` has a `path_infos` attribute:
         - Extract the deepest target field: `target_field = self.lhs.output_field.path_infos[-1].target_fields[-1]`.
         - Run each value through `target_field.get_prep_value(v)` and replace `self.rhs` with the validated list. This ensures type validation (e.g., rejecting non-integer strings for an IntegerField target).
     - Else (RHS is a queryset, not a direct value):
       - If the RHS does **not** have `has_select_fields == True` **and** `self.lhs.field.target_field` is **not** a primary key:
         - Clear the RHS's select clause via `self.rhs.clear_select_clause()`.
         - Determine which field to add: if `self.lhs.output_field` has `primary_key == True` **and** `self.lhs.output_field.model == self.rhs.model`, use `self.lhs.field.name`; otherwise, use `self.lhs.field.target_field.name`.
         - Add that single field to the RHS's select list via `self.rhs.add_fields([target_field], True)`.
   - Call and return `super().get_prep_lookup()`.

2. **`as_sql(self, compiler, connection)`**
   - If `self.lhs` **is** a `MultiColSource`:
     - Import `AND`, `OR`, `SubqueryConstraint`, `WhereNode` from `django.db.models.sql.where`.
     - Create a root constraint: `root_constraint = WhereNode(connector=OR)`.
     - If `self.rhs_is_direct_value()`:
       - Normalize each RHS value: `values = [get_normalized_value(value, self.lhs) for value in self.rhs]`.
       - For each normalized `value` tuple:
         - Create a new `WhereNode()` as `value_constraint`.
         - Iterate over `zip(self.lhs.sources, self.lhs.targets, value)` simultaneously.
         - For each `(source, target, val)`:
           - Get the exact lookup class from `target.get_lookup("exact")`.
           - Create a lookup instance: `lookup_class(target.get_col(self.lhs.alias, source), val)`.
           - Add this lookup to `value_constraint` with connector `AND`.
         - Add `value_constraint` to `root_constraint` with connector `OR`. (Each value tuple forms an OR branch; within each branch, all column comparisons are ANDed.)
     - Else (RHS is a queryset):
       - Create a `SubqueryConstraint(self.lhs.alias, [target.column for target in self.lhs.targets], [source.name for source in self.lhs.sources], self.rhs)`.
       - Add it to `root_constraint` with connector `AND`.
     - Return `root_constraint.as_sql(compiler, connection)`.
   - Else (`self.lhs` is not a `MultiColSource`): delegate to `super().as_sql(compiler, connection)`.

---

### Class: `RelatedLookupMixin`

**Purpose:** A mixin that provides multi-column-aware preprocessing and SQL generation for related-field lookups. It is designed to be used as the first base class in multiple inheritance (before the concrete lookup class).

**Methods:**

1. **`get_prep_lookup(self)`**
   - If `self.lhs` is **not** a `MultiColSource` **and** `self.rhs` does not have a `resolve_expression` attribute:
     - Normalize the RHS via `get_normalized_value(self.rhs, self.lhs)[0]` and replace `self.rhs`. This handles single-column relations.
     - If `self.prepare_rhs` is truthy **and** `self.lhs.output_field` has a `path_infos` attribute:
       - Extract the deepest target field: `target_field = self.lhs.output_field.path_infos[-1].target_fields[-1]`.
       - Run `self.rhs` through `target_field.get_prep_value(self.rhs)` and replace it. This performs type validation on the related field's target column.
   - Call and return `super().get_prep_lookup()`.

2. **`as_sql(self, compiler, connection)`**
   - If `self.lhs` **is** a `MultiColSource`:
     - Assert that `self.rhs_is_direct_value()` is `True` (multi-column lookups only support direct values).
     - Normalize the RHS: `self.rhs = get_normalized_value(self.rhs, self.lhs)`.
     - Import `AND`, `WhereNode` from `django.db.models.sql.where`.
     - Create a root constraint: `root_constraint = WhereNode()`.
     - Iterate over `zip(self.lhs.targets, self.lhs.sources, self.rhs)` simultaneously.
     - For each `(target, source, val)`:
       - Get the lookup class for this specific lookup's name: `lookup_class = target.get_lookup(self.lookup_name)`.
       - Create a lookup instance: `lookup_class(target.get_col(self.lhs.alias, source), val)`.
       - Add it to `root_constraint` with connector `AND`. (All column comparisons are ANDed together.)
     - Return `root_constraint.as_sql(compiler, connection)`.
   - Else (`self.lhs` is not a `MultiColSource`): delegate to `super().as_sql(compiler, connection)`.

---

### Class: `RelatedExact(RelatedLookupMixin, Exact)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `Exact` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides exact-equality comparison (`__exact`) for related fields with multi-column support via the mixin.

---

### Class: `RelatedLessThan(RelatedLookupMixin, LessThan)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `LessThan` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides less-than comparison (`<`) for related fields with multi-column support via the mixin.

---

### Class: `RelatedGreaterThan(RelatedLookupMixin, GreaterThan)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `GreaterThan` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides greater-than comparison (`>`) for related fields with multi-column support via the mixin.

---

### Class: `RelatedGreaterThanOrEqual(RelatedLookupMixin, GreaterThanOrEqual)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `GreaterThanOrEqual` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides greater-than-or-equal comparison (`>=`) for related fields with multi-column support via the mixin.

---

### Class: `RelatedLessThanOrEqual(RelatedLookupMixin, LessThanOrEqual)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `LessThanOrEqual` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides less-than-or-equal comparison (`<=`) for related fields with multi-column support via the mixin.

---

### Class: `RelatedIsNull(RelatedLookupMixin, IsNull)`

**Base classes:** Inherits from `RelatedLookupMixin` (first), then `IsNull` (from `django.db.models.lookups`).
**Behavior:** No additional methods or attributes. Provides null-check (`isnull`) for related fields with multi-column support via the mixin.

---

## Summary of Architecture

The file provides Django ORM support for lookups on **related fields**, including both single-column and **multi-column** (e.g., `to_fields` on foreign keys) relations:

- **`MultiColSource`** is a lightweight descriptor wrapping multiple columns from a related table, supporting relabeling and lookup delegation.
- **`get_normalized_value()`** converts model instances or scalars into tuples of values matching the number of columns in a multi-column relation, following relation chains when necessary.
- **`RelatedIn`** overrides both `get_prep_lookup` and `as_sql` to handle the special case of `IN` lookups on related fields: for direct values it builds OR-combined AND-clauses per value; for querysets it uses a `SubqueryConstraint`.
- **`RelatedLookupMixin`** provides shared preprocessing (normalization + type validation) and SQL generation logic that ANDs together per-column lookups when the LHS is a `MultiColSource`, delegating to the parent class otherwise.
- The five concrete classes (`RelatedExact`, `RelatedLessThan`, `RelatedGreaterThan`, `RelatedGreaterThanOrEqual`, `RelatedLessThanOrEqual`, `RelatedIsNull`) are trivial subclasses that combine the mixin with their respective base lookup classes from `django.db.models.lookups`.

## django/db/models/sql/query.py
Now I have read every line of this 2,667-line file. Here is the complete natural-language specification:

---

# Module-Level Preamble

## Imports

```python
import copy
import difflib
import functools
import sys
from collections import Counter, namedtuple
from collections.abc import Iterator, Mapping
from itertools import chain, count, product
from string import ascii_uppercase

from django.core.exceptions import FieldDoesNotExist, FieldError
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections
from django.db.models.aggregates import Count
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression, Col, Exists, F, OuterRef, Ref, ResolvedOuterRef, Value,
)
from django.db.models.fields import Field
from django.db.models.fields.related_lookups import MultiColSource
from django.db.models.lookups import Lookup
from django.db.models.query_utils import (
    Q, check_rel_lookup_compatibility, refs_expression,
)
from django.db.models.sql.constants import INNER, LOUTER, ORDER_DIR, SINGLE
from django.db.models.sql.datastructures import BaseTable, Empty, Join, MultiJoin
from django.db.models.sql.where import AND, OR, ExtraWhere, NothingNode, WhereNode
from django.utils.functional import cached_property
from django.utils.regex_helper import _lazy_re_compile
from django.utils.tree import Node

__all__ = ["Query", "RawQuery"]
```

## Constants & Globals

- **`FORBIDDEN_ALIAS_PATTERN`** — compiled regex `_lazy_re_compile(r"['`\"][\\]\\[;\\s]|--|/\\*|\\*/")`. Matches quotation marks, square brackets, whitespace, semicolons, and SQL comment markers (`--`, `/*`, `*/`). Used to validate column aliases.
- **`EXPLAIN_OPTIONS_PATTERN`** — compiled regex `_lazy_re_compile(r"[\w\-]+")`. Validates EXPLAIN query option names.

## Helper Functions

### `get_field_names_from_opts(opts)`
Returns a set of all field names from the given model Options object. For each concrete field, yields both `(f.name, f.attname)`. For non-concrete fields, yields only `f.name`. Returns empty set if `opts` is None.

### `get_children_from_q(q)`
Recursive generator that walks a Q-tree (`Node`). Yields leaf children (non-Node items); recurses into child Nodes.

## Named Tuples

### `JoinInfo = namedtuple("JoinInfo", ("final_field", "targets", "opts", "joins", "path", "transform_function"))`
Holds join resolution results: the final field, target fields, model Options, list of join aliases, path of PathInfos, and a transform function.

### `ExplainInfo = namedtuple("ExplainInfo", ("format", "options"))`
Stores EXPLAIN query format and options.

---

# Code Objects

## Class `RawQuery`

**Purpose:** Represents a single raw SQL query that can be executed via the database cursor.

### Attributes (set in `__init__`)
- `params` — tuple or dict of query parameters; default `()`
- `sql` — the raw SQL string
- `using` — database connection alias
- `cursor` — initially None, set during execution
- `low_mark` — offset start, always 0
- `high_mark` — limit end, always None
- `extra_select` — empty dict
- `annotation_select` — empty dict

### Methods

#### `__init__(self, sql, using, params=())`
Stores SQL, connection alias, and parameters. Initializes cursor to None and sets pagination/selection attributes to defaults.

#### `chain(self, using)`
Returns a clone with the given database alias. Delegates to `clone(using)`.

#### `clone(self, using)`
Returns a new `RawQuery` with the same SQL and params but the specified connection alias.

#### `get_columns(self)`
If cursor is None, executes `_execute_query()`. Returns list of column names from `cursor.description`, each converted via `connections[self.using].introspection.identifier_converter`.

#### `__iter__(self)`
Always re-executes the query. If the database cannot use chunked reads (`can_use_chunked_reads` feature is False), materializes all results into a list first; otherwise returns the cursor directly. Returns an iterator over rows.

#### `__repr__(self)`
Returns `<RawQuery: <str representation>>`.

#### `params_type (property)`
Returns None if params is None, else returns `dict` if params is a Mapping instance, else `tuple`.

#### `__str__(self)`
If params_type is None, returns raw SQL. Otherwise returns `sql % params_type(params)`.

#### `_execute_query(self)`
Gets the connection for `self.using`, creates a cursor, adapts parameters via `connection.ops.adapt_unknown_value` (tuple or dict depending on params type), and executes `cursor.execute(self.sql, params)`. Raises RuntimeError if params type is unexpected.

---

## Class `Query(BaseExpression)`

**Purpose:** Encapsulates all SQL construction for Django ORM queries. Extends `BaseExpression`.

### Class-Level Attributes
- **`alias_prefix = "T"`** — prefix for generated table aliases
- **`empty_result_set_value = None`** — value returned when aggregation yields no rows
- **`subq_aliases = frozenset(["T"])`** — set of alias prefixes used by subqueries
- **`compiler = "SQLCompiler"`** — compiler class name
- **`base_table_class = BaseTable`** — base table datastructure class
- **`join_class = Join`** — join datastructure class
- **`default_cols = True`** — whether to select default model columns
- **`default_ordering = True`** — whether to use the model's default ordering
- **`standard_ordering = True`** — whether standard ordering applies
- **`filter_is_sticky = False`** — sticky filter flag
- **`subquery = False`** — whether this query is a subquery

### Instance-Level Attributes (set in `__init__`)
- **`model`** — the Django model class; passed to `__init__`
- **`alias_refcount`** — dict mapping alias → reference count, initialized `{}`
- **`alias_map`** — dict mapping alias → Join or BaseTable object; records all joins in the query
- **`alias_cols`** — whether to provide aliases to columns during reference resolving; default `True` (from parameter)
- **`external_aliases`** — dict mapping external table aliases to boolean indicating if aliased
- **`table_map`** — dict mapping table name → list of aliases for that table
- **`used_aliases`** — set of alias strings used by filters; initialized `set()`
- **`where`** — a `WhereNode()` instance (root WHERE clause)
- **`annotations`** — dict mapping annotation alias → Expression object
- **`extra`** — dict mapping col_alias → `(col_sql, params)` tuple for user-supplied SQL fragments
- **`_filtered_relations`** — dict of FilteredRelation instances keyed by alias

### Class-Level Default Attributes (overridden per-instance)
- **`select = ()`** — expressions in the SELECT clause (for values(), subqueries); empty tuple default
- **`group_by`** — None (no GROUP BY), a tuple of expressions, or True (group by all select fields)
- **`order_by = ()`** — ordering specifications; empty tuple default
- **`low_mark = 0`** — offset start for LIMIT/OFFSET
- **`high_mark = None`** — limit end for LIMIT/OFFSET
- **`distinct = False`** — whether DISTINCT is used
- **`distinct_fields = ()`** — fields for DISTINCT ON clause
- **`select_for_update = False`** — FOR UPDATE flag
- **`select_for_update_nowait = False`** — NOWAIT flag
- **`select_for_update_skip_locked = False`** — SKIP LOCKED flag
- **`select_for_update_of = ()`** — OF tables for FOR UPDATE
- **`select_for_no_key_update = False`** — NO KEY UPDATE flag
- **`select_related = False`** — related model selection config (False, True, or nested dict)
- **`max_depth = 5`** — recursion limit for select_related
- **`values_select = ()`** — fields from values()/values_list() excluding annotations and extras
- **`annotation_select_mask = None`** — mask controlling which annotations appear in SELECT; None means all
- **`_annotation_select_cache = None`** — cached annotation_select result
- **`combinator = None`** — UNION/INTERSECT/EXCEPT operator or None
- **`combinator_all = False`** — ALL flag for set operations
- **`combined_queries = ()`** — tuple of Query objects for set operations
- **`extra_select_mask = None`** — mask controlling which extra selects appear; None means all
- **`_extra_select_cache = None`** — cached extra_select result
- **`extra_tables = ()`** — additional tables for EXTRA clause
- **`extra_order_by = ()`** — additional ORDER BY items from EXTRA
- **`deferred_loading = (frozenset(), True)`** — tuple of (field_names, defer_flag); defer=True means "exclude these", False means "only load these"
- **`explain_info = None`** — ExplainInfo namedtuple or None

### Properties

#### `output_field`
If `select` has exactly one element, returns that expression's `target` attribute if present, else its `field`. If select has >1 but `annotation_select` has exactly one, returns that annotation's `output_field`. Otherwise returns None.

#### `has_select_fields`
Returns True if any of `self.select`, `self.annotation_select_mask`, or `self.extra_select_mask` is truthy (non-empty).

#### `base_table (cached_property)`
Iterates over keys in `alias_map` and returns the first one — the initial FROM table alias.

### Methods

#### `__str__(self)`
Returns SQL string with parameter values substituted: calls `sql_with_params()`, then formats as `sql % params`. Note: parameters are not quoted correctly (that happens at execution time).

#### `sql_with_params(self)`
Delegates to `self.get_compiler(DEFAULT_DB_ALIAS).as_sql()` and returns the `(sql, params)` tuple.

#### `__deepcopy__(self, memo)`
Calls `clone()`, stores result in `memo[id(self)]`, returns it. Avoids full deepcopy overhead.

#### `get_compiler(self, using=None, connection=None, elide_empty=True)`
Requires either `using` or `connection`. If `using` is provided, resolves the connection via `connections[using]`. Returns `connection.ops.compiler(self.compiler)(self, connection, using, elide_empty)`. Raises ValueError if neither parameter is given.

#### `get_meta(self)`
Returns `self.model._meta` if model exists; otherwise None. Overridable by subclasses.

#### `clone(self)`
Lightweight copy (not deepcopy). Creates an Empty object, sets its class to self's class, shallow-copies `__dict__`. Then deep-clones mutable structures: `alias_refcount`, `alias_map`, `external_aliases`, `table_map` via `.copy()`, `where` via `.clone()`, `annotations` via `.copy()`, `annotation_select_mask` (if not None) via `.copy()`, `combined_queries` by cloning each element, `extra` via `.copy()`, `extra_select_mask` and `_extra_select_cache` (if not None), `select_related` via `copy.deepcopy()` if it's not False, `subq_aliases` (if present in __dict__), `used_aliases`, `_filtered_relations`. Sets `_annotation_select_cache = None` (must be re-populated). Pops `"base_table"` from cloned `__dict__` to invalidate the cached_property. Returns the clone.

#### `chain(self, klass=None)`
Clones self via `clone()`. If `klass` is given and differs from current class, changes `obj.__class__` to `klass`. Resets `used_aliases = set()` if `filter_is_sticky` is False. Sets `filter_is_sticky = False`. Calls `_setup_query()` if the method exists on the clone. Returns the chain object.

#### `relabeled_clone(self, change_map)`
Clones self then calls `change_aliases(change_map)` on the clone. Returns it.

#### `_get_col(self, target, field, alias)`
If `alias_cols` is False, sets alias to None. Returns `target.get_col(alias, field)`.

#### `rewrite_cols(self, annotation, col_cnt)`
Ensures inner query has columns referenced by an annotation expression. Iterates over source expressions of the annotation:
- If expr is a `Ref`, appends it unchanged.
- If expr is a `WhereNode` or `Lookup`, recursively rewrites and appends result.
- Otherwise, tries to find a matching already-selected annotation in `self.annotation_select`. If found, creates a `Ref(col_alias, expr)`. If not found: if expr is a `Col` or contains an aggregate but isn't a summary expression, increments col_cnt, creates alias `"__col{col_cnt}"`, adds expr to `self.annotations[col_alias]`, appends the alias to annotation mask via `append_annotation_mask()`, and wraps in `Ref(col_alias, expr)`. For other expressions, recursively rewrites sub-expressions. Sets rewritten source expressions on the annotation and returns `(annotation, col_cnt)`.

#### `get_aggregation(self, using, added_aggregate_names)`
Returns a dict of aggregation results keyed by alias. If no annotations exist, returns `{}`. Filters out annotations whose aliases are in `added_aggregate_names`. Determines whether to use a subquery: if group_by is a tuple, query is sliced, there are existing annotations, distinct is True, or combinator exists → wraps in an AggregateQuery subquery. In the subquery path: clones self as inner_query (subquery=True), creates outer AggregateQuery, clears ordering, sets GROUP BY to model PK if default_cols and has aggregate annotations, relabels aliases, moves summary expressions from inner to outer query via `rewrite_cols()`, ensures at least one field is selected. In the direct path: clears select, disables default_cols, clears extra. Clears ordering/limits/select_for_update/select_related on outer_query. Executes via compiler's `execute_sql(SINGLE)`. Returns None as empty_set_value if result is None. Applies converters and returns dict(zip(outer_query.annotation_select, result)).

#### `get_count(self, using)`
Clones self, adds annotation `Count("*")` with alias `"__count"` and `is_summary=True`, calls `get_aggregation(using, ["__count"])["__count"]`. Returns the count.

#### `has_filters(self)`
Returns truthiness of `self.where`.

#### `exists(self, using, limit=True)`
Clones self. If not (distinct and sliced), and group_by is True, adds concrete field columns and disables GROUP BY aliases. Clears select clause. For combined UNION queries, recursively calls exists on each combined query if the backend supports slicing in compound queries. Clears ordering. If limit is True, sets high=1. Adds annotation `Value(1)` with alias `"a"`. Returns the clone (used as a subquery).

#### `has_results(self, using)`
Calls `self.exists(using)`, gets its compiler for `using`, returns `compiler.has_results()`.

#### `explain(self, using, format=None, **options)`
Clones self. Validates each option name against `EXPLAIN_OPTIONS_PATTERN.fullmatch()` and rejects names containing `"--"`, raising ValueError otherwise. Sets `explain_info = ExplainInfo(format, options)`. Gets compiler for `using` and returns `"\n".join(compiler.explain_query())`.

#### `combine(self, rhs, connector)`
Merges the RHS query into self (RHS effects applied to the right). Raises TypeError if models differ, either query is sliced, or distinct/distinct_fields mismatch. Bumps RHS prefix to avoid alias conflicts (excluding initial alias). Determines reuse set: empty for AND (recreate all joins for m2m), full alias_map copy for OR. Creates a `JoinPromoter(connector, 2, False)` and adds votes from self's INNER joins. Iterates over RHS tables (skipping base table): relabels each join via change_map, joins into self with reuse set, tracks new aliases in change_map, unrefs unused aliases. Updates JoinPromoter with RHS votes. Combines subquery aliases (`self.subq_aliases |= rhs.subq_aliases`). Clones and relabels RHS where-clause, adds to self's where with connector. For selection: if RHS has select, sets it (relabeled); else clears self.select. Raises ValueError for OR connector if both sides have extra(select). Updates `self.extra` from RHS. Merges extra_select_mask. Appends RHS extra_tables. Uses RHS order_by unless empty (then keeps self's). Same for extra_order_by.

#### `_get_defer_select_mask(self, opts, mask, select_mask=None)`
Recursively builds a select mask for deferred loading. Adds PK to select_mask. For each concrete field: if not in mask, adds to select_mask; if in mask with truthy value and is_relation, recurses into related model's mask. Remaining mask entries are reverse relationships or filtered relations — resolves them similarly. Returns the select_mask dict.

#### `_get_only_select_mask(self, opts, mask, select_mask=None)`
Recursively builds a select mask for "only load these fields". Adds PK to select_mask. For each field in mask: adds to select_mask; if mask value is truthy and field is relation, recurses into related model's mask. Raises FieldError for non-relation fields with truthy mask values. Returns the select_mask dict.

#### `get_select_mask(self)`
Converts `deferred_loading` data structure into a field selection mask. If no deferred names, returns `{}`. Builds a nested mask dict from field_names split by LOOKUP_SEP. Calls `_get_defer_select_mask` if defer is True (exclude these), else `_get_only_select_mask` (only load these).

#### `table_alias(self, table_name, create=False, filtered_relation=None)`
Returns `(alias, was_created)`. If not creating and an alias list exists for the table in `table_map`, reuses the first alias and increments its refcount. Otherwise: if alias_list exists, generates `"T{len(alias_map)+1}"`; else uses `filtered_relation.alias` or `table_name` directly and creates a new entry in `table_map`. Sets refcount to 1. Returns `(alias, True)`.

#### `ref_alias(self, alias)`
Increments `self.alias_refcount[alias]` by 1.

#### `unref_alias(self, alias, amount=1)`
Decrements `self.alias_refcount[alias]` by amount.

#### `promote_joins(self, aliases)`
Promotes join types to LOUTER for given aliases and their children. Iterates over aliases: skips base table (join_type is None). If parent is LOUTER or the join is nullable and not already LOUTER, promotes via `join.promote()`. Re-examines all child joins that reference this alias. Prevents INNER-after-LOUTER chains by cascading promotion downstream.

#### `demote_joins(self, aliases)`
Demotes LOUTER joins to INNER for given aliases. Iterates: if join is LOUTER, demotes via `join.demote()`. If parent is INNER, adds parent to queue (prevents LOUTER-after-INNER chains).

#### `reset_refcounts(self, to_counts)`
For each alias in alias_refcount, computes unref_amount = current_count - target_count (from to_counts dict), calls `unref_alias(alias, unref_amount)`.

#### `change_aliases(self, change_map)`
Changes aliases per change_map (old → new). Asserts keys and values are disjoint. Relabels: where clause via `relabel_aliases()`, group_by tuple elements, select expressions, annotations. Renames entries in alias_map, alias_refcount, table_map, and external_aliases.

#### `bump_prefix(self, other_query, exclude=None)`
Changes the alias prefix to avoid conflicts with another query's aliases. Generates new prefixes from ascii_uppercase (A, B, ... AA, AB, ...). Skips prefixes already in subq_aliases. Raises RecursionError if depth exceeds `sys.getrecursionlimit() // 16`. Updates both queries' subq_aliases. Relabels all current aliases with the new prefix via `change_aliases()`, excluding specified aliases (e.g., base table).

#### `get_initial_alias(self)`
Returns the first alias in alias_map and increments its refcount. If no alias_map but model exists, joins the base table class using `self.get_meta().db_table`. Returns None if neither exists.

#### `count_active_tables(self)`
Returns count of aliases with non-zero reference count in `alias_refcount`.

#### `join(self, join, reuse=None, reuse_with_filtered_relation=False)`
Returns an alias for the given join object. If `reuse_with_filtered_relation` and reuse set exist, finds matching joins via `.equals()`. Otherwise finds exact matches where alias is in reuse (or all if reuse is None). Reuses the most recent alias of the same table (for m2m), increments refcount, returns it. Otherwise creates a new alias via `table_alias()`. Sets join_type: LOUTER if parent is LOUTER or join is nullable; else INNER. Stores in alias_map and returns the new alias.

#### `join_parent_model(self, opts, model, alias, seen)`
Ensures a parent model is joined for inheritance. If model already in seen, returns its alias. Gets base chain from opts to model. For each intermediate model: if already seen, uses cached alias; if proxy (no parents), skips to next; otherwise sets up joins via the ancestor link field and caches the result. Returns final alias or `seen[None]`.

#### `check_alias(self, alias)`
Raises ValueError if FORBIDDEN_ALIAS_PATTERN matches the alias (forbids whitespace, quotes, semicolons, SQL comments).

#### `add_annotation(self, annotation, alias, is_summary=False, select=True)`
Validates alias. Resolves annotation expression with `allow_joins=True, reuse=None, summarize=is_summary`. If select is True, appends alias to annotation mask; else sets mask to all annotations minus this one. Stores in `self.annotations[alias]`.

#### `resolve_expression(self, query, *args, **kwargs)`
Clones self and bumps prefix for subquery isolation. Sets subquery=True. Resolves where clause, combined queries (if combinator), and annotations against the outer query. Marks outer query's aliases as external if they are Joins to different tables or BaseTables with aliased names. Returns the resolved clone.

#### `get_external_cols(self)`
Collects all Col instances from annotations and where children that have aliases in `external_aliases`. Uses `_gen_cols` recursively with `include_external=True`.

#### `get_group_by_cols(self, alias=None)`
If alias is given, returns `[Ref(alias, self)]`. Otherwise collects external columns; if any are possibly_multivalued, returns `[self]`; else returns the external columns.

#### `as_sql(self, compiler, connection)`
For subqueries on backends that don't ignore unnecessary ORDER BY, clears ordering from self and combined queries. Gets SQL via compiler's as_sql(). Wraps in parentheses if subquery. Returns `(sql, params)`.

#### `resolve_lookup_value(self, value, can_reuse, allow_joins)`
If value has `resolve_expression`, resolves it against self. If list/tuple, recursively resolves each element preserving type (including namedtuple). Otherwise returns value unchanged.

#### `solve_lookup_type(self, lookup)`
Splits lookup by LOOKUP_SEP. Checks if first part matches an annotation name via `refs_expression()` — if so, returns expression lookups and the expression. Otherwise calls `names_to_path()` to resolve field path. Returns `(lookup_parts, field_parts, False)`. Raises FieldError for invalid multi-part lookups with no field parts.

#### `check_query_object_type(self, value, opts, field)`
If value has `_meta`, checks compatibility via `check_rel_lookup_compatibility()`. Raises ValueError if incompatible.

#### `check_related_objects(self, field, value, opts)`
For relation fields: if value is a Query without select fields, checks model compatibility; if value has `_meta`, calls check_query_object_type; if iterable, recursively checks each element.

#### `check_filterable(self, expression)`
Raises NotSupportedError if expression has `filterable=False`. Recursively checks source expressions via `get_source_expressions()`.

#### `build_lookup(self, lookups, lhs, rhs)`
Extracts transforms and final lookup from the lookups list (defaults to "exact"). Applies each transform name via `try_transform()`. Gets lookup class from lhs; if not found and field is relation, raises FieldError. If not found on non-relation, tries interpreting as a transform then exact lookup. Creates Lookup instance. Handles None RHS: for exact/iexact, returns isnull(True); otherwise rejects unless can_use_none_as_rhs. Oracle special case: `__exact=""` converts to isnull(True). Returns the Lookup or None.

#### `try_transform(self, lhs, name)`
Gets transform class from lhs; if found, instantiates and returns it. If not found, suggests similar lookups via difflib. Raises FieldError with suggestion.

#### `build_filter(self, filter_expr, branch_negated=False, current_negated=False, can_reuse=None, allow_joins=True, split_subq=True, reuse_with_filtered_relation=False, check_filterable=True)`
Handles dict (raises FieldError), Q objects (delegates to `_add_q`), and expressions with `resolve_expression`. For non-conditional expressions raises TypeError. For conditional expressions resolves them, wraps in exact lookup if not Lookup, returns WhereNode. Parses filter_expr as `(arg, value)`. Splits into lookups and field parts via `solve_lookup_type()`. Checks filterability. If allow_joins is False and there are join parts, raises FieldError. Records pre-join refcounts. Resolves lookup value. Computes used_joins from changed refcounts. Handles F() expression references (returns WhereNode with lookup). Otherwise resolves field path via `names_to_path()` / `setup_joins()`. Handles MultiJoin by delegating to `split_exclude()`. Trims joins, builds column reference, constructs lookup. Determines if outer join is required for IS NULL checks and negated conditions. Adds extra IS NOT NULL clauses when needed for nullable columns in negated filters. Returns `(WhereNode, used_joins)`.

#### `add_filter(self, filter_lhs, filter_rhs)`
Delegates to `self.add_q(Q((filter_lhs, filter_rhs)))`.

#### `add_q(self, q_object)`
Collects existing INNER join aliases. Calls `_add_q()` with used_aliases. If clause returned, adds it to self.where with AND connector. Demotes the previously-inner joins (they may become outer if needed).

#### `build_where(self, filter_expr)`
Calls `build_filter(filter_expr, allow_joins=False)[0]` — returns just the WhereNode without join tracking.

#### `clear_where(self)`
Replaces self.where with a fresh `WhereNode()`.

#### `_add_q(self, q_object, used_aliases, branch_negated=False, current_negated=False, allow_joins=True, split_subq=True, check_filterable=True)`
Processes Q-object children. Computes effective negation via XOR. Creates target WhereNode with the Q's connector and negation flag. Creates JoinPromoter for join type decisions. For each child: calls `build_filter()`, adds votes to promoter, adds child clause to target with connector. Calls `update_join_types()` on self. Returns `(target_clause, needed_inner)`.

#### `build_filtered_relation_q(self, q_object, reuse, branch_negated=False, current_negated=False)`
Similar to `_add_q` but for FilteredRelation contexts. Recursively processes Node children via itself; leaf children go through `build_filter()` with `reuse_with_filtered_relation=True` and `split_subq=False`. Returns target WhereNode.

#### `add_filtered_relation(self, filtered_relation, alias)`
Sets the relation's alias. Validates that relation_name has no lookups. For each lookup in the condition, validates that nested relations don't exceed the depth of relation_name. Stores in `_filtered_relations[alias]`. Raises ValueError on validation failures.

#### `names_to_path(self, names, opts, allow_many=True, fail_on_missing=False)`
Walks name list building PathInfo tuples. Handles "pk" → pk.name. Resolves field from opts or annotation_select or filtered_relation. For GenericForeignKeys without related_model, raises FieldError. For inheritance, adds path to parent via `get_path_to_parent()`. For relational fields with path_infos: if allow_many is False and any PathInfo is m2m, raises MultiJoin. Extends path and updates final_field/targets/opts. For local non-relational fields: sets final_field/targets, breaks (unless fail_on_missing with more names). Returns `(path, final_field, targets, remaining_names)`.

#### `setup_joins(self, names, opts, alias, can_reuse=None, allow_many=True, reuse_with_filtered_relation=False)`
Computes table joins for the given field path. Builds a transform partial function. Tries progressively shorter name prefixes (from full list down to 1 element) via `names_to_path()` until one succeeds; trailing names become transforms. For each PathInfo in resolved path: creates Join objects with INNER type, nullable determined by `is_nullable()` for direct joins or True for reverse. Joins them into alias_map, tracking aliases. Handles filtered relations by cloning and updating their path. Returns `JoinInfo(final_field, targets, opts, joins, path, final_transformer)`.

#### `trim_joins(self, targets, joins, path)`
Trims unnecessary leading joins from the join chain. Iterates reversed path: stops if only one join left, if not direct, or if filtered_relation present. Checks if target columns are a subset of the join's foreign related fields — if so, can trim. Updates targets via related_fields mapping, unreferences and pops the alias. Returns `(targets, final_alias, remaining_joins)`.

#### `_gen_cols(cls, exprs, include_external=False)`
Class method. Generator yielding Col instances from expressions. Recurses through `get_source_expressions()`. If include_external is True and expression has `get_external_cols`, yields those too.

#### `_gen_col_aliases(cls, exprs)`
Class method. Yields alias attribute from each Col yielded by `_gen_cols(exprs)`.

#### `resolve_ref(self, name, allow_joins=True, reuse=None, summarize=False)`
Resolves a reference name to an expression or column. Checks annotations dict first: if found and not summarizing, returns annotation; if summarizing, checks it's in annotation_select and returns Ref(). If annotation has joins and allow_joins is False, raises FieldError. For non-annotation names: splits by LOOKUP_SEP, tries as annotation prefix with transforms. Otherwise resolves via `setup_joins()` + `trim_joins()`. Raises FieldError for multicolumn references or if allow_joins=False with joins. Applies transform function to final target. Updates reuse set. Returns the resolved expression/column.

#### `split_exclude(self, filter_expr, can_reuse, names_with_path)`
Handles exclude on N-to-many relations via NOT EXISTS subquery. Creates inner Query, copies _filtered_relations. Converts OuterRef/F RHS to OuterRef. Adds filter, clears ordering. Trims start of join path. If the select alias is reusable, bumps prefix and adds a restriction linking outer PK to inner PK via exact lookup; marks as external alias. Adds an EXISTS subquery condition using ResolvedOuterRef on the trimmed prefix. If the prefix contains LEFT OUTER joins, also adds an IS NULL OR condition for correct NOT IN semantics. Returns `(condition, needed_inner)`.

#### `set_empty(self)`
Adds NothingNode to where clause (making query return zero rows). Propagates to all combined_queries.

#### `is_empty(self)`
Returns True if any child of self.where is a NothingNode instance.

#### `set_limits(self, low=None, high=None)`
Adjusts pagination limits. For high: clamps to existing high_mark or adds to low_mark. For low: clamps to high_mark or adds to current low_mark. If low == high after adjustment, calls set_empty().

#### `clear_limits(self)`
Resets low_mark=0, high_mark=None.

#### `is_sliced (property)`
Returns True if low_mark != 0 or high_mark is not None.

#### `has_limit_one(self)`
Returns True if high_mark is not None and (high_mark - low_mark) == 1.

#### `can_filter(self)`
Returns not self.is_sliced — whether further filtering is possible.

#### `clear_select_clause(self)`
Clears select, sets default_cols=False, select_related=False, clears extra mask and annotation mask.

#### `clear_select_fields(self)`
Sets select=() and values_select=().

#### `add_select_col(self, col, name)`
Appends col to select tuple and name to values_select tuple.

#### `set_select(self, cols)`
Sets default_cols=False and select=tuple(cols).

#### `add_distinct_fields(self, *field_names)`
Sets distinct_fields to field_names and distinct=True.

#### `add_fields(self, field_names, allow_m2m=True)`
Adds model fields to the SELECT set in order. Gets initial alias and opts. For each name: splits by LOOKUP_SEP, sets up joins, trims them, collects target columns via transform function. If cols exist, calls set_select(). Catches MultiJoin → FieldError; catches FieldError with re-raising for cross-model lookups or annotation references.

#### `add_ordering(self, *ordering)`
Adds ordering items. For strings: skips "?", strips "-" prefix, checks against annotations and extra (skips if found), validates via names_to_path(). For non-expressions, collects errors. Checks contains_aggregate on each item (raises FieldError if aggregate not in annotate). Appends to order_by; if empty, sets default_ordering=False.

#### `clear_ordering(self, force=False, clear_default=True)`
Clears ordering unless force is False and query is sliced/distinct_fields set/select_for_update. Clears order_by, extra_order_by, and optionally default_ordering.

#### `set_group_by(self, allow_aliases=True)`
Builds GROUP BY from select expressions plus annotation group-by columns. If allow_aliases, collects column names from joined tables to detect alias collisions. Extends group_by list with each annotation's get_group_by_cols(). Sets self.group_by = tuple(group_by).

#### `add_select_related(self, fields)`
Sets up nested dict structure for select_related. If current is bool, starts empty dict. For each field path (split by LOOKUP_SEP), creates nested dicts. Stores as self.select_related.

#### `add_extra(self, select, select_params, where, params, tables, order_by)`
Adds user-supplied SQL fragments. For select: pairs entries with parameters from select_params (handling %s placeholders), stores in extra dict after checking alias validity and converting to str. Adds ExtraWhere for where/params. Appends tables to extra_tables. Sets extra_order_by if provided.

#### `clear_deferred_loading(self)`
Resets deferred_loading to `(frozenset(), True)`.

#### `add_deferred_loading(self, field_names)`
Adds fields to the deferred loading set. If defer is True (exclude mode), unions with existing names. If defer is False (include mode), removes new names from existing; if all removed, clears and sets include-only mode for remaining names.

#### `add_immediate_loading(self, field_names)`
Sets fields to be immediately loaded. Replaces "pk" with actual pk name. If defer was True, removes deferred names from the set before setting as immediate. Otherwise replaces existing immediate names. Stores as `(frozenset(field_names), False)`.

#### `set_annotation_mask(self, names)`
Sets annotation_select_mask: None for all, or a set of names. Clears _annotation_select_cache.

#### `append_annotation_mask(self, names)`
If mask exists, unions it with the given names via set_annotation_mask().

#### `set_extra_mask(self, names)`
Sets extra_select_mask: None for all, or a set of names. Clears _extra_select_cache.

#### `set_values(self, fields)`
Prepares query for values()/values_list() output. Disables select_related, clears deferred loading and select fields. Classifies field names into extra/annotation/field categories based on current state. Sets masks accordingly. If group_by is True, adds concrete fields then clears and rebuilds. Resolves GROUP BY annotation references not in selected set. Sets values_select tuple and calls add_fields().

#### `annotation_select (property)`
Returns cached _annotation_select_cache if available. Returns {} if no annotations. Returns masked subset if annotation_select_mask is set. Otherwise returns all annotations dict.

#### `extra_select (property)`
Returns cached _extra_select_cache if available. Returns {} if no extra. Returns masked subset if extra_select_mask is set. Otherwise returns all extra dict.

#### `trim_start(self, names_with_path)`
Trims joins from the start of the join path for split_exclude optimization. Collects all paths, identifies m2m boundary. Unrefs aliases up to the m2m point. Builds trimmed_prefix string from name/path pairs. If first remaining join is not LOUTER and has no filtered_relation, trims one more level using foreign_related_fields; otherwise uses reverse related fields. Converts first active table back to BaseTable. Sets select to pk columns of the starting point. Returns `(trimmed_prefix, contains_louter)`.

#### `is_nullable(self, field)`
Returns True if field.null is True OR (field.empty_strings_allowed AND the default database interprets empty strings as null). Uses DEFAULT_DB_ALIAS since QuerySet doesn't know which connection will be used.

---

## Function: `get_order_dir(field, default="ASC")`

Parses an ordering specification string. If field starts with "-", returns `(field[1:], dirn[1])` (reversed direction). Otherwise returns `(field, dirn[0])`. Uses ORDER_DIR mapping for the default direction's ascending/descending values.

---

## Class `JoinPromoter`

**Purpose:** Manages join type promotion/demotion decisions for complex filter conditions with AND/OR connectors and negations.

### Attributes (set in `__init__`)
- **`connector`** — the original connector (AND or OR) from the Q-object
- **`negated`** — whether the Q-object is negated
- **`effective_connector`** — if negated: AND→OR, OR→AND; else same as connector. Used for join type decisions since NOT(a AND b) behaves like a OR b for joins.
- **`num_children`** — number of children in the Q-object
- **`votes`** — Counter mapping table alias → vote count (how many filter branches require this join to be INNER)

### Methods

#### `__repr__(self)`
Returns formatted string with connector, num_children, and negated values.

#### `add_votes(self, votes)`
Updates self.votes Counter with one vote per item from the iterable argument.

#### `update_join_types(self, query)`
Decides which joins to promote (to LOUTER) and demote (to INNER):
- **Promote** if effective_connector is OR and votes < num_children: the join isn't present in all branches, so an INNER would incorrectly filter out valid rows.
- **Demote** if effective_connector is AND (any vote suffices — a filter can only match if the row exists) OR if effective_connector is OR and votes == num_children (all branches require this join, so it's safe to be INNER).
Calls `query.promote_joins(to_promote)` then `query.demote_joins(to_demote)`. Returns `to_demote` set.