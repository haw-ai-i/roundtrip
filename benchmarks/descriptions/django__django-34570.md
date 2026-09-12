## django/db/models/sql/query.py
This is a complete natural-language specification of the `django/db/models/sql/query.py` file.

## 1. Module-Level Preamble

### Imports
The module imports standard library utilities (`copy`, `difflib`, `functools`, `sys`, `collections.Counter`, `collections.namedtuple`, `collections.abc.Iterator`, `collections.abc.Mapping`, `itertools.chain`, `itertools.count`, `itertools.product`, `string.ascii_uppercase`).
It imports Django exceptions (`FieldDoesNotExist`, `FieldError`), database utilities (`DEFAULT_DB_ALIAS`, `NotSupportedError`, `connections`), aggregates (`Count`), constants (`LOOKUP_SEP`), expressions, fields, lookups, query utilities (`Q`, `check_rel_lookup_compatibility`), SQL constants (`INNER`, `LOUTER`, `ORDER_DIR`, `SINGLE`), SQL datastructures (`BaseTable`, `Empty`, `Join`, `MultiJoin`), SQL where nodes (`AND`, `OR`, `ExtraWhere`, `NothingNode`, `WhereNode`), and utility functions (`cached_property`, `_lazy_re_compile`, `Node`).

### Constants & Globals
*   `__all__`: `["Query", "RawQuery"]`
*   `FORBIDDEN_ALIAS_PATTERN`: A compiled regex `r"['`\"\]\[;\s]|--|/\*|\*/"` matching forbidden characters in column aliases.
*   `EXPLAIN_OPTIONS_PATTERN`: A compiled regex `r"[\w\-]+"` matching valid explain options.
*   `JoinInfo`: A namedtuple with fields `("joins", "path", "transform_function")`.
*   `ExplainInfo`: A namedtuple with fields `("format", "options")`.

## 2. Module-Level Functions

### `get_field_names_from_opts(opts)`
*   **Signature:** `def get_field_names_from_opts(opts):`
*   **Logic:** Returns a set of field names available on the given `opts` (model `_meta`). If `opts` is `None`, returns an empty set. It iterates over `opts.get_fields()` and yields `f.name` and `f.attname` (if it exists).

### `get_children_from_q(q)`
*   **Signature:** `def get_children_from_q(q):`
*   **Logic:** A generator that yields all children of a `Q` object. If a child is a `Node`, it recursively yields its children. Otherwise, it yields the child itself.

### `rename_prefix_from_q(prefix, replacement, q)`
*   **Signature:** `def rename_prefix_from_q(prefix, replacement, q):`
*   **Logic:** Recursively clones a `Q` object, replacing the given `prefix` with `replacement` in the keys of its children (which are tuples of `(key, value)`).

### `get_order_dir(field, default="ASC")`
*   **Signature:** `def get_order_dir(field, default="ASC"):`
*   **Logic:** Determines the ordering direction for a field string. If `field` starts with `'-'`, returns `(field[1:], 'DESC')`. If it starts with `'+'`, returns `(field[1:], 'ASC')`. Otherwise, returns `(field, default)`.

## 3. Code Objects (Classes)

### `RawQuery`
*   **Header:** `class RawQuery:`
*   **Description:** Represents a single raw SQL query.
*   **Attributes:** `params`, `sql`, `using`, `cursor`, `low_mark`, `high_mark`, `extra_select`, `annotation_select`.
*   **Methods:**
    *   `__init__(self, sql, using, params=())`: Initializes the query.
    *   `chain(self, using)` / `clone(self, using)`: Returns a new `RawQuery` instance with the same SQL and parameters.
    *   `get_columns(self)`: Executes the query if needed and returns the column names from the cursor description.
    *   `__iter__(self)`: Executes the query and yields results. Uses chunked reads if supported by the database.
    *   `__repr__(self)` / `__str__(self)`: String representations.
    *   `params_type` (property): Returns `dict` if `params` is a mapping, `tuple` otherwise.
    *   `_execute_query(self)`: Adapts parameters using the database connection's `adapt_unknown_value` and executes the SQL on a new cursor.

### `Query`
*   **Header:** `class Query(BaseExpression):`
*   **Description:** Represents a single SQL query. This is the core class responsible for constructing SQL queries from Django's ORM syntax.
*   **Key Attributes:** `model`, `alias_refcount`, `alias_map`, `external_aliases`, `table_map`, `default_cols`, `default_ordering`, `standard_ordering`, `used_aliases`, `filter_is_sticky`, `subq_aliases`, `select`, `where`, `where_class`, `group_by`, `order_by`, `low_mark`, `high_mark`, `distinct`, `distinct_fields`, `select_for_update`, `select_for_update_nowait`, `select_for_update_skip_locked`, `select_for_update_of`, `select_for_update_no_key`, `select_related`, `max_depth`, `values_select`, `annotation_select`, `annotation_select_mask`, `combinator`, `combinator_all`, `combined_queries`, `extra_select`, `extra_tables`, `extra_where`, `extra_order_by`, `deferred_loading`, `explain_info`.
*   **Key Methods:**
    *   `__init__(self, model, alias_refcount=None, alias_map=None)`: Initializes the query state.
    *   `sql_with_params(self)`: Returns the SQL and parameters for the query.
    *   `clone(self)`: Returns a deep copy of the query.
    *   `build_filter(self, filter_expr, branch_negated=False, current_negated=False, can_reuse=None, allow_joins=True, split_subq=True, check_filterable=True)`: Parses a filter expression (e.g., `field__lookup=value`) and returns a `WhereNode` and a list of joins.
    *   `add_filter(self, filter_clause)`: Adds a filter to the query's `where` node.
    *   `add_q(self, q_object)`: Adds a `Q` object to the query.
    *   `setup_joins(self, names, opts, alias, can_reuse=None, allow_many=True)`: Resolves a field path (e.g., `author__name`) into a series of SQL joins.
    *   `resolve_lookup_value(self, value, can_reuse, allow_joins)`: Resolves the right-hand side of a lookup.
    *   `solve_lookup_type(self, lookup)`: Extracts the lookup type (e.g., `exact`, `gt`) from a string.
    *   `add_ordering(self, *ordering)`: Adds ordering to the query.
    *   `add_select_related(self, fields)`: Adds fields to be selected in the same query.
    *   `add_annotation(self, annotation, alias, is_summary=False)`: Adds an annotation to the query.
    *   `set_values(self, fields)`: Sets the fields to be returned by a `values()` or `values_list()` call.
    *   `set_limits(self, low=None, high=None)`: Sets the `LIMIT` and `OFFSET` for the query.
    *   `has_results(self, using)`: Checks if the query would return any results.
    *   `combine(self, rhs, connector)`: Combines this query with another using `UNION`, `INTERSECT`, or `EXCEPT`.

### `JoinPromoter`
*   **Header:** `class JoinPromoter:`
*   **Description:** Abstracts away join promotion problems for complex filter conditions (e.g., promoting `INNER JOIN` to `LEFT OUTER JOIN` when using `OR`).
*   **Attributes:** `connector`, `negated`, `effective_connector`, `num_children`, `votes` (a `Counter` mapping table aliases to vote counts).
*   **Methods:**
    *   `__init__(self, connector, num_children, negated)`: Initializes the promoter, calculating the `effective_connector` (flipping `AND`/`OR` if negated).
    *   `add_votes(self, votes)`: Adds votes for table aliases.
    *   `update_join_types(self, query)`: Analyzes the votes and the `effective_connector` to determine which joins should be promoted to `LOUTER` or demoted to `INNER`. Calls `query.promote_joins()` and `query.demote_joins()` accordingly, and returns the set of demoted joins.