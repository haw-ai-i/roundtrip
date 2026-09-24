## django/db/backends/base/features.py
```markdown
# Module-Level Preamble

## Imports
*   `from django.db import ProgrammingError`
*   `from django.utils.functional import cached_property`

# Code Objects

## Class: `BaseDatabaseFeatures`
This class defines the default features and capabilities of a database backend.

### Attributes
*   `minimum_database_version`: `None`
*   `gis_enabled`: `False`
*   `allows_group_by_lob`: `True`
*   `allows_group_by_selected_pks`: `False`
*   `allows_group_by_refs`: `True`
*   `empty_fetchmany_value`: `[]`
*   `update_can_self_select`: `True`
*   `interprets_empty_strings_as_nulls`: `False`
*   `supports_nullable_unique_constraints`: `True`
*   `supports_partially_nullable_unique_constraints`: `True`
*   `supports_deferrable_unique_constraints`: `False`
*   `can_use_chunked_reads`: `True`
*   `can_return_columns_from_insert`: `False`
*   `can_return_rows_from_bulk_insert`: `False`
*   `has_bulk_insert`: `True`
*   `uses_savepoints`: `True`
*   `can_release_savepoints`: `False`
*   `related_fields_match_type`: `False`
*   `allow_sliced_subqueries_with_in`: `True`
*   `has_select_for_update`: `False`
*   `has_select_for_update_nowait`: `False`
*   `has_select_for_update_skip_locked`: `False`
*   `has_select_for_update_of`: `False`
*   `has_select_for_no_key_update`: `False`
*   `select_for_update_of_column`: `False`
*   `test_db_allows_multiple_connections`: `True`
*   `supports_unspecified_pk`: `False`
*   `supports_forward_references`: `True`
*   `truncates_names`: `False`
*   `has_real_datatype`: `False`
*   `supports_subqueries_in_group_by`: `True`
*   `ignores_unnecessary_order_by_in_subqueries`: `True`
*   `has_native_uuid_field`: `False`
*   `has_native_duration_field`: `False`
*   `supports_temporal_subtraction`: `False`
*   `supports_regex_backreferencing`: `True`
*   `supports_date_lookup_using_string`: `True`
*   `supports_timezones`: `True`
*   `has_zoneinfo_database`: `True`
*   `requires_explicit_null_ordering_when_grouping`: `False`
*   `nulls_order_largest`: `False`
*   `supports_order_by_nulls_modifier`: `True`
*   `order_by_nulls_first`: `False`
*   `max_query_params`: `None`
*   `allows_auto_pk_0`: `True`
*   `can_defer_constraint_checks`: `False`
*   `supports_tablespaces`: `False`
*   `supports_sequence_reset`: `True`
*   `can_introspect_default`: `True`
*   `can_introspect_foreign_keys`: `True`
*   `introspected_field_types`: `{"AutoField": "AutoField", "BigAutoField": "BigAutoField", "BigIntegerField": "BigIntegerField", "BinaryField": "BinaryField", "BooleanField": "BooleanField", "CharField": "CharField", "DurationField": "DurationField", "GenericIPAddressField": "GenericIPAddressField", "IntegerField": "IntegerField", "PositiveBigIntegerField": "PositiveBigIntegerField", "PositiveIntegerField": "PositiveIntegerField", "PositiveSmallIntegerField": "PositiveSmallIntegerField", "SmallAutoField": "SmallAutoField", "SmallIntegerField": "SmallIntegerField", "TimeField": "TimeField"}`
*   `supports_index_column_ordering`: `True`
*   `can_introspect_materialized_views`: `False`
*   `can_distinct_on_fields`: `False`
*   `atomic_transactions`: `True`
*   `can_rollback_ddl`: `False`
*   `schema_editor_uses_clientside_param_binding`: `False`
*   `supports_atomic_references_rename`: `True`
*   `supports_combined_alters`: `False`
*   `supports_foreign_keys`: `True`
*   `can_create_inline_fk`: `True`
*   `can_rename_index`: `False`
*   `indexes_foreign_keys`: `True`
*   `supports_column_check_constraints`: `True`
*   `supports_table_check_constraints`: `True`
*   `can_introspect_check_constraints`: `True`
*   `supports_paramstyle_pyformat`: `True`
*   `requires_literal_defaults`: `False`
*   `connection_persists_old_columns`: `False`
*   `closed_cursor_error_class`: `ProgrammingError`
*   `has_case_insensitive_like`: `False`
*   `bare_select_suffix`: `""`
*   `implied_column_null`: `False`
*   `supports_select_for_update_with_limit`: `True`
*   `greatest_least_ignores_nulls`: `False`
*   `can_clone_databases`: `False`
*   `ignores_table_name_case`: `False`
*   `for_update_after_from`: `False`
*   `supports_select_union`: `True`
*   `supports_select_intersection`: `True`
*   `supports_select_difference`: `True`
*   `supports_slicing_ordering_in_compound`: `False`
*   `supports_parentheses_in_compound`: `True`
*   `requires_compound_order_by_subquery`: `False`
*   `supports_aggregate_filter_clause`: `False`
*   `supports_index_on_text_field`: `True`
*   `supports_over_clause`: `False`
*   `supports_frame_range_fixed_distance`: `False`
*   `only_supports_unbounded_with_preceding_and_following`: `False`
*   `supports_cast_with_precision`: `True`
*   `time_cast_precision`: `6`
*   `create_test_procedure_without_params_sql`: `None`
*   `create_test_procedure_with_int_param_sql`: `None`
*   `create_test_table_with_composite_primary_key`: `None`
*   `supports_callproc_kwargs`: `False`
*   `supported_explain_formats`: `set()`
*   `supports_default_in_lead_lag`: `True`
*   `supports_ignore_conflicts`: `True`
*   `supports_update_conflicts`: `False`
*   `supports_update_conflicts_with_target`: `False`
*   `requires_casted_case_in_updates`: `False`
*   `supports_partial_indexes`: `True`
*   `supports_functions_in_partial_indexes`: `True`
*   `supports_covering_indexes`: `False`
*   `supports_expression_indexes`: `True`
*   `collate_as_index_expression`: `False`
*   `allows_multiple_constraints_on_same_fields`: `True`
*   `supports_boolean_expr_in_select_clause`: `True`
*   `supports_comparing_boolean_expr`: `True`
*   `supports_json_field`: `True`
*   `can_introspect_json_field`: `True`
*   `supports_primitives_in_json_field`: `True`
*   `has_native_json_field`: `False`
*   `has_json_operators`: `False`
*   `supports_json_field_contains`: `True`
*   `json_key_contains_list_matching_requires_list`: `False`
*   `has_json_object_function`: `True`
*   `supports_collation_on_charfield`: `True`
*   `supports_collation_on_textfield`: `True`
*   `supports_non_deterministic_collations`: `True`
*   `supports_comments`: `False`
*   `supports_comments_inline`: `False`
*   `supports_logical_xor`: `False`
*   `prohibits_null_characters_in_text_exception`: `None`
*   `supports_unlimited_charfield`: `False`
*   `test_collations`: `{"ci": None, "cs": None, "non_default": None, "swedish_ci": None}`
*   `test_now_utc_template`: `None`
*   `django_test_expected_failures`: `set()`
*   `django_test_skips`: `{}`

### Methods

#### `__init__(self, connection)`
*   **Implementation Logic:**
    *   Assigns the `connection` parameter to `self.connection`.

#### `supports_explaining_query_execution(self)`
*   **Decorators:** `@cached_property`
*   **Implementation Logic:**
    *   Returns `True` if `self.connection.ops.explain_prefix` is not `None`, otherwise `False`.

#### `supports_transactions(self)`
*   **Decorators:** `@cached_property`
*   **Implementation Logic:**
    *   Uses a context manager to get a cursor from `self.connection.cursor()`.
    *   Executes the SQL statement `"CREATE TABLE ROLLBACK_TEST (X INT)"`.
    *   Calls `self.connection.set_autocommit(False)`.
    *   Executes the SQL statement `"INSERT INTO ROLLBACK_TEST (X) VALUES (8)"`.
    *   Calls `self.connection.rollback()`.
    *   Calls `self.connection.set_autocommit(True)`.
    *   Executes the SQL statement `"SELECT COUNT(X) FROM ROLLBACK_TEST"`.
    *   Fetches one row using `cursor.fetchone()` and unpacks it into a `count` variable.
    *   Executes the SQL statement `"DROP TABLE ROLLBACK_TEST"`.
    *   Returns `True` if `count == 0`, otherwise `False`.

#### `allows_group_by_selected_pks_on_model(self, model)`
*   **Implementation Logic:**
    *   If `self.allows_group_by_selected_pks` is `False`, returns `False`.
    *   Otherwise, returns the value of `model._meta.managed`.
```

## django/db/backends/oracle/features.py
```markdown
# Specification for `django/db/backends/oracle/features.py`

## 1. Module-Level Preamble

### Imports
*   `from django.db import DatabaseError, InterfaceError`
*   `from django.db.backends.base.features import BaseDatabaseFeatures`
*   `from django.utils.functional import cached_property`

### Constants & Globals
There are no module-level constants or globals defined outside of the class.

## 2. Code Objects

### Class: `DatabaseFeatures`
**Inheritance:** Inherits from `BaseDatabaseFeatures`.

#### Class Attributes
*   `minimum_database_version`: `(19,)` (tuple)
*   `allows_group_by_lob`: `False` (bool)
*   `allows_group_by_refs`: `False` (bool)
*   `interprets_empty_strings_as_nulls`: `True` (bool)
*   `has_select_for_update`: `True` (bool)
*   `has_select_for_update_nowait`: `True` (bool)
*   `has_select_for_update_skip_locked`: `True` (bool)
*   `has_select_for_update_of`: `True` (bool)
*   `select_for_update_of_column`: `True` (bool)
*   `can_return_columns_from_insert`: `True` (bool)
*   `supports_subqueries_in_group_by`: `False` (bool)
*   `ignores_unnecessary_order_by_in_subqueries`: `False` (bool)
*   `supports_transactions`: `True` (bool)
*   `supports_timezones`: `False` (bool)
*   `has_native_duration_field`: `True` (bool)
*   `can_defer_constraint_checks`: `True` (bool)
*   `supports_partially_nullable_unique_constraints`: `False` (bool)
*   `supports_deferrable_unique_constraints`: `True` (bool)
*   `truncates_names`: `True` (bool)
*   `supports_comments`: `True` (bool)
*   `supports_tablespaces`: `True` (bool)
*   `supports_sequence_reset`: `False` (bool)
*   `can_introspect_materialized_views`: `True` (bool)
*   `atomic_transactions`: `False` (bool)
*   `nulls_order_largest`: `True` (bool)
*   `requires_literal_defaults`: `True` (bool)
*   `closed_cursor_error_class`: `InterfaceError` (class reference)
*   `bare_select_suffix`: `" FROM DUAL"` (str)
*   `supports_select_for_update_with_limit`: `False` (bool)
*   `supports_temporal_subtraction`: `True` (bool)
*   `ignores_table_name_case`: `True` (bool)
*   `supports_index_on_text_field`: `False` (bool)
*   `create_test_procedure_without_params_sql`: (str)
    ```sql
        CREATE PROCEDURE "TEST_PROCEDURE" AS
            V_I INTEGER;
        BEGIN
            V_I := 1;
        END;
    ```
*   `create_test_procedure_with_int_param_sql`: (str)
    ```sql
        CREATE PROCEDURE "TEST_PROCEDURE" (P_I INTEGER) AS
            V_I INTEGER;
        BEGIN
            V_I := P_I;
        END;
    ```
*   `create_test_table_with_composite_primary_key`: (str)
    ```sql
        CREATE TABLE test_table_composite_pk (
            column_1 NUMBER(11) NOT NULL,
            column_2 NUMBER(11) NOT NULL,
            PRIMARY KEY (column_1, column_2)
        )
    ```
*   `supports_callproc_kwargs`: `True` (bool)
*   `supports_over_clause`: `True` (bool)
*   `supports_frame_range_fixed_distance`: `True` (bool)
*   `supports_ignore_conflicts`: `False` (bool)
*   `max_query_params`: `2**16 - 1` (int)
*   `supports_partial_indexes`: `False` (bool)
*   `can_rename_index`: `True` (bool)
*   `supports_slicing_ordering_in_compound`: `True` (bool)
*   `requires_compound_order_by_subquery`: `True` (bool)
*   `allows_multiple_constraints_on_same_fields`: `False` (bool)
*   `supports_boolean_expr_in_select_clause`: `False` (bool)
*   `supports_comparing_boolean_expr`: `False` (bool)
*   `supports_primitives_in_json_field`: `False` (bool)
*   `supports_json_field_contains`: `False` (bool)
*   `supports_collation_on_textfield`: `False` (bool)
*   `test_collations`: (dict)
    ```python
    {
        "ci": "BINARY_CI",
        "cs": "BINARY",
        "non_default": "SWEDISH_CI",
        "swedish_ci": "SWEDISH_CI",
    }
    ```
*   `test_now_utc_template`: `"CURRENT_TIMESTAMP AT TIME ZONE 'UTC'"` (str)
*   `django_test_skips`: (dict)
    ```python
    {
        "Oracle doesn't support SHA224.": {
            "db_functions.text.test_sha224.SHA224Tests.test_basic",
            "db_functions.text.test_sha224.SHA224Tests.test_transform",
        },
        "Oracle doesn't correctly calculate ISO 8601 week numbering before 1583 (the Gregorian calendar was introduced in 1582).": {
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_week_before_1000",
            "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_week_before_1000",
        },
        "Oracle extracts seconds including fractional seconds (#33517).": {
            "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_extract_second_func_no_fractional",
            "db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_second_func_no_fractional",
        },
        "Oracle doesn't support bitwise XOR.": {
            "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor",
            "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor_null",
            "expressions.tests.ExpressionOperatorTests.test_lefthand_bitwise_xor_right_null",
        },
        "Oracle requires ORDER BY in row_number, ANSI:SQL doesn't.": {
            "expressions_window.tests.WindowFunctionTests.test_row_number_no_ordering",
        },
        "Raises ORA-00600: internal error code.": {
            "model_fields.test_jsonfield.TestQuerying.test_usage_in_subquery",
        },
        "Oracle doesn't support changing collations on indexed columns (#33671).": {
            "migrations.test_operations.OperationTests.test_alter_field_pk_fk_db_collation",
        },
    }
    ```
*   `django_test_expected_failures`: (set)
    ```python
    {
        "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions",
        "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions_can_ref_other_functions",
    }
    ```

#### Methods

##### `introspected_field_types(self)`
*   **Signature:** `def introspected_field_types(self)`
*   **Decorators:** `@cached_property`
*   **Implementation Logic:**
    *   Calls `super().introspected_field_types` to get the base dictionary.
    *   Returns a new dictionary that merges the base dictionary with the following specific overrides for Oracle:
        *   `"GenericIPAddressField"`: `"CharField"`
        *   `"PositiveBigIntegerField"`: `"BigIntegerField"`
        *   `"PositiveIntegerField"`: `"IntegerField"`
        *   `"PositiveSmallIntegerField"`: `"IntegerField"`
        *   `"SmallIntegerField"`: `"IntegerField"`
        *   `"TimeField"`: `"DateTimeField"`

##### `supports_collation_on_charfield(self)`
*   **Signature:** `def supports_collation_on_charfield(self)`
*   **Decorators:** `@cached_property`
*   **Implementation Logic:**
    *   Opens a cursor using `with self.connection.cursor() as cursor:`.
    *   Attempts to execute the SQL query: `"SELECT CAST('a' AS VARCHAR2(4001)) FROM dual"`.
    *   If a `DatabaseError` is raised:
        *   Checks if the error code (accessed via `e.args[0].code`) is `910`.
        *   If the code is `910`, returns `False`.
        *   Otherwise, re-raises the exception.
    *   If the query executes successfully without raising an error, returns `True`.
```

## django/db/models/sql/compiler.py
This is a natural-language specification of `django/db/models/sql/compiler.py`.

## Module-Level Preamble

### Imports
*   `collections`, `json`, `re`
*   `functools.partial`, `itertools.chain`
*   `django.core.exceptions`: `EmptyResultSet`, `FieldError`, `FullResultSet`
*   `django.db`: `DatabaseError`, `NotSupportedError`
*   `django.db.models.constants`: `LOOKUP_SEP`
*   `django.db.models.expressions`: `F`, `OrderBy`, `RawSQL`, `Ref`, `Value`
*   `django.db.models.functions`: `Cast`, `Random`
*   `django.db.models.lookups`: `Lookup`
*   `django.db.models.query_utils`: `select_related_descend`
*   `django.db.models.sql.constants`: `CURSOR`, `GET_ITERATOR_CHUNK_SIZE`, `MULTI`, `NO_RESULTS`, `ORDER_DIR`, `SINGLE`
*   `django.db.models.sql.query`: `Query`, `get_order_dir`
*   `django.db.models.sql.where`: `AND`
*   `django.db.transaction`: `TransactionManagementError`
*   `django.utils.functional`: `cached_property`
*   `django.utils.hashable`: `make_hashable`
*   `django.utils.regex_helper`: `_lazy_re_compile`

### Constants & Globals
None explicitly defined at the module level other than imports.

## Code Objects

### `class SQLCompiler`
The base class for compiling Django `Query` objects into SQL strings.

*   **Attributes:**
    *   `ordering_parts`: A compiled regular expression `_lazy_re_compile(r"^(.*)\s(?:ASC|DESC).*")` used to parse ordering clauses.
*   **Implementation Logic:**
    *   Provides the core logic for translating a `Query` object into a `SELECT` statement.
    *   Handles `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, and `ORDER BY` clauses.
    *   Manages database-specific quoting and parameterization via the `connection` object.
    *   Executes the compiled SQL and returns results.

### `class SQLInsertCompiler(SQLCompiler)`
Compiles `INSERT` queries.

*   **Attributes:**
    *   `returning_fields`: Defaults to `None`.
*   **Implementation Logic:**
    *   Overrides `as_sql()` to generate `INSERT INTO ... VALUES ...` statements.
    *   Handles bulk inserts and `RETURNING` clauses if supported by the backend.

### `class SQLDeleteCompiler(SQLCompiler)`
Compiles `DELETE` queries.

*   **Implementation Logic:**
    *   Overrides `as_sql()` to generate `DELETE FROM ... WHERE ...` statements.
    *   Uses a subquery if the query involves joins or limits that the database cannot handle directly in a `DELETE` statement.

### `class SQLUpdateCompiler(SQLCompiler)`
Compiles `UPDATE` queries.

*   **Implementation Logic:**
    *   Overrides `as_sql()` to generate `UPDATE ... SET ... WHERE ...` statements.
    *   Handles updating fields with expressions (e.g., `F()` objects).
    *   Uses subqueries for complex updates involving joins.

### `class SQLAggregateCompiler(SQLCompiler)`
Compiles queries that only return aggregate values.

*   **Implementation Logic:**
    *   Overrides `as_sql()` to generate a query that wraps the original query in a subquery or directly computes aggregates, depending on the complexity of the original query.

### `def cursor_iter(cursor, sentinel, col_count, itersize)`
A generator function that yields rows from a database cursor.

*   **Signature:** `def cursor_iter(cursor, sentinel, col_count, itersize)`
*   **Implementation Logic:**
    *   Iterates over `cursor.fetchmany(itersize)`.
    *   Yields each row until the cursor is exhausted.
    *   Ensures the cursor is closed when iteration is complete or an exception occurs.

## django/db/models/sql/query.py
This is a natural-language specification of `django/db/models/sql/query.py`.

### 1. Module-Level Preamble

**Imports:**
*   Standard library: `copy`, `difflib`, `functools`, `sys`, `Counter`, `namedtuple` from `collections`, `Iterator`, `Mapping` from `collections.abc`, `chain`, `count`, `product` from `itertools`, `ascii_uppercase` from `string`.
*   Django core: `FieldDoesNotExist`, `FieldError` from `django.core.exceptions`.
*   Django DB: `DEFAULT_DB_ALIAS`, `NotSupportedError`, `connections` from `django.db`.
*   Django models: `Count` from `django.db.models.aggregates`, `LOOKUP_SEP` from `django.db.models.constants`, `BaseExpression`, `Col`, `Exists`, `F`, `OuterRef`, `Ref`, `ResolvedOuterRef`, `Value` from `django.db.models.expressions`, `Field` from `django.db.models.fields`, `MultiColSource` from `django.db.models.fields.related_lookups`, `Lookup` from `django.db.models.lookups`, `Q`, `check_rel_lookup_compatibility`, `refs_expression` from `django.db.models.query_utils`.
*   Django SQL: `INNER`, `LOUTER`, `ORDER_DIR`, `SINGLE` from `django.db.models.sql.constants`, `BaseTable`, `Empty`, `Join`, `MultiJoin` from `django.db.models.sql.datastructures`, `AND`, `OR`, `ExtraWhere`, `NothingNode`, `WhereNode` from `django.db.models.sql.where`.
*   Django utils: `cached_property` from `django.utils.functional`, `_lazy_re_compile` from `django.utils.regex_helper`, `Node` from `django.utils.tree`.

**Constants & Globals:**
*   `__all__ = ["Query", "RawQuery"]`
*   `FORBIDDEN_ALIAS_PATTERN`: A compiled regex `r"['`\"\]\[;\s]|--|/\*|\*/"` matching forbidden characters in column aliases.
*   `EXPLAIN_OPTIONS_PATTERN`: A compiled regex `r"[\w\-]+"` matching valid EXPLAIN options.
*   `JoinInfo`: A `namedtuple` with fields `("final_field", "targets", "opts", "joins", "path", "transform_function")`.
*   `ExplainInfo`: A `namedtuple` with fields `("format", "options")`.

### 2. Code Objects

#### `get_field_names_from_opts(opts)`
*   **Signature:** `def get_field_names_from_opts(opts):`
*   **Logic:** Returns a set of field names from the given model options (`opts`). If `opts` is `None`, returns an empty set. Otherwise, iterates over `opts.get_fields()`. For concrete fields, yields both `name` and `attname`; for non-concrete fields, yields only `name`.

#### `get_children_from_q(q)`
*   **Signature:** `def get_children_from_q(q):`
*   **Logic:** A generator that recursively yields all non-`Node` children from a `Q` object (`q`). Iterates over `q.children`; if a child is a `Node`, yields from a recursive call; otherwise, yields the child.

#### `class RawQuery`
*   **Header:** `class RawQuery:`
*   **Attributes:** `params`, `sql`, `using`, `cursor`, `low_mark`, `high_mark`, `extra_select`, `annotation_select`.
*   **Implementation Logic:** Represents a raw SQL query.
    *   `__init__(self, sql, using, params=())`: Initializes attributes. Sets `low_mark` to 0, `high_mark` to `None`, and `extra_select` and `annotation_select` to empty dicts.
    *   `chain(self, using)`: Returns `self.clone(using)`.
    *   `clone(self, using)`: Returns a new `RawQuery` instance with the same `sql` and `params`, but the specified `using` database alias.
    *   `get_columns(self)`: Executes the query (if not already executed) and returns a list of column names from `self.cursor.description`.
    *   `execute(self, using)`: Executes the query on the specified database connection. Instantiates a cursor, executes `self.sql` with `self.params`, and stores the cursor in `self.cursor`.

#### `class Query(BaseExpression)`
*   **Header:** `class Query(BaseExpression):`
*   **Implementation Logic:** Represents a single SQL query. This is a massive class that encapsulates all SQL construction logic for Django QuerySets. It manages SELECT, WHERE, JOIN, ORDER BY, GROUP BY, and HAVING clauses.
    *   It maintains internal state for aliases, joins, annotations, extra selections, and query limits.
    *   It provides methods for cloning (`clone`), combining (`combine`), and resolving expressions (`resolve_expression`).
    *   It handles complex lookup resolution (`build_filter`, `build_lookup`, `setup_joins`) and join promotion (`promote_joins`).
    *   It manages query compilation by delegating to database-specific compilers (`get_compiler`).

#### `get_order_dir(field, default="ASC")`
*   **Signature:** `def get_order_dir(field, default="ASC"):`
*   **Logic:** Determines the ordering direction for a field. If `field` starts with `'-'`, returns the field name without the prefix and `'DESC'`. Otherwise, returns the field name and the `default` direction.

#### `class JoinPromoter`
*   **Header:** `class JoinPromoter:`
*   **Implementation Logic:** A helper class used to determine which joins should be promoted to LEFT OUTER JOINs based on the query structure and nullability of fields.
    *   `__init__(self, connector, num_children, negated)`: Initializes the promoter with the connector type (AND/OR), number of children, and whether the node is negated.
    *   `add_votes(self, votes)`: Accumulates votes for join promotion.
    *   `update_join_types(self, query)`: Updates the join types in the given `query` based on the accumulated votes and the promoter's logic.