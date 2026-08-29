## django/db/backends/base/schema.py
Now I have the complete file. Let me write the specification.

---

## Module-Level Preamble

### Imports

```python
import logging
from datetime import datetime
from django.db.backends.ddl_references import (Columns, Expressions, ForeignKeyName, IndexName, Statement, Table)
from django.db.backends.utils import names_digest, split_identifier
from django.db.models import Deferrable, Index
from django.db.models.sql import Query
from django.db.transaction import TransactionManagementError, atomic
from django.utils import timezone
```

### Constants & Globals

- `logger` — a `logging.Logger` instance created via `logging.getLogger("django.db.backends.schema")`.

### Module-Level Functions

#### `_is_relevant_relation(relation, altered_field)` → `bool`

Determines whether constraints on the model of `relation` must be temporarily dropped when altering `altered_field`. Returns `False` if `relation.field.many_to_many` is true. Returns `True` if `altered_field.primary_key` and `field.to_fields == [None]` (a FK targeting the PK being altered). Otherwise returns whether `altered_field.name in field.to_fields`.

#### `_all_related_fields(model)` → iterable

Returns `model._meta._get_fields(forward=False, reverse=True, include_hidden=True, include_parents=False)`, yielding all reverse non-M2M related objects for the model.

#### `_related_non_m2m_objects(old_field, new_field)` → generator of `(old_rel, new_rel)` tuples

Zips filtered results from `_all_related_fields(old_field.model)` and `_all_related_fields(new_field.model)`, filtering each via `_is_relevant_relation`. For each matching pair `(old_rel, new_rel)`, yields the tuple then recursively yields from `_related_non_m2m_objects(old_rel.remote_field, new_rel.remote_field)`.

---

## Class: `BaseDatabaseSchemaEditor`

### Inheritance & Metaclass

No explicit base class or metaclass.

### SQL Template Attributes (class-level strings)

| Attribute | Value |
|---|---|
| `sql_create_table` | `"CREATE TABLE %(table)s (%(definition)s)"` |
| `sql_rename_table` | `"ALTER TABLE %(old_table)s RENAME TO %(new_table)s"` |
| `sql_retablespace_table` | `"ALTER TABLE %(table)s SET TABLESPACE %(new_tablespace)s"` |
| `sql_delete_table` | `"DROP TABLE %(table)s CASCADE"` |
| `sql_create_column` | `"ALTER TABLE %(table)s ADD COLUMN %(column)s %(definition)s"` |
| `sql_alter_column` | `"ALTER TABLE %(table)s %(changes)s"` |
| `sql_alter_column_type` | `"ALTER COLUMN %(column)s TYPE %(type)s"` |
| `sql_alter_column_null` | `"ALTER COLUMN %(column)s DROP NOT NULL"` |
| `sql_alter_column_not_null` | `"ALTER COLUMN %(column)s SET NOT NULL"` |
| `sql_alter_column_default` | `"ALTER COLUMN %(column)s SET DEFAULT %(default)s"` |
| `sql_alter_column_no_default` | `"ALTER COLUMN %(column)s DROP DEFAULT"` |
| `sql_alter_column_no_default_null` | Same as `sql_alter_column_no_default` |
| `sql_alter_column_collate` | `"ALTER COLUMN %(column)s TYPE %(type)s%(collation)s"` |
| `sql_delete_column` | `"ALTER TABLE %(table)s DROP COLUMN %(column)s CASCADE"` |
| `sql_rename_column` | `"ALTER TABLE %(table)s RENAME COLUMN %(old_column)s TO %(new_column)s"` |
| `sql_update_with_default` | `"UPDATE %(table)s SET %(column)s = %(default)s WHERE %(column)s IS NULL"` |
| `sql_unique_constraint` | `"UNIQUE (%(columns)s)%(deferrable)s"` |
| `sql_check_constraint` | `"CHECK (%(check)s)"` |
| `sql_delete_constraint` | `"ALTER TABLE %(table)s DROP CONSTRAINT %(name)s"` |
| `sql_constraint` | `"CONSTRAINT %(name)s %(constraint)s"` |
| `sql_create_check` | `"ALTER TABLE %(table)s ADD CONSTRAINT %(name)s CHECK (%(check)s)"` |
| `sql_delete_check` | Same as `sql_delete_constraint` |
| `sql_create_unique` | `"ALTER TABLE %(table)s ADD CONSTRAINT %(name)s UNIQUE (%(columns)s)%(deferrable)s"` |
| `sql_delete_unique` | Same as `sql_delete_constraint` |
| `sql_create_fk` | `"ALTER TABLE %(table)s ADD CONSTRAINT %(name)s FOREIGN KEY (%(column)s) REFERENCES %(to_table)s (%(to_column)s)%(deferrable)s"` |
| `sql_create_inline_fk` | `None` (override in subclasses for inline FK syntax) |
| `sql_create_column_inline_fk` | `None` (override in subclasses for inline FK on ADD COLUMN) |
| `sql_delete_fk` | Same as `sql_delete_constraint` |
| `sql_create_index` | `"CREATE INDEX %(name)s ON %(table)s (%(columns)s)%(include)s%(extra)s%(condition)s"` |
| `sql_create_unique_index` | `"CREATE UNIQUE INDEX %(name)s ON %(table)s (%(columns)s)%(include)s%(condition)s"` |
| `sql_delete_index` | `"DROP INDEX %(name)s"` |
| `sql_create_pk` | `"ALTER TABLE %(table)s ADD CONSTRAINT %(name)s PRIMARY KEY (%(columns)s)"` |
| `sql_delete_pk` | Same as `sql_delete_constraint` |
| `sql_delete_procedure` | `"DROP PROCEDURE %(procedure)s"` |

### Instance Attributes (set in `__init__`)

- `connection` — the database connection object.
- `collect_sql` — boolean; if true, SQL is collected rather than executed.
- `collected_sql` — list of collected SQL strings (only when `collect_sql=True`).
- `atomic_migration` — boolean: `self.connection.features.can_rollback_ddl and atomic`.
- `deferred_sql` — list of deferred SQL statements (set in `__enter__`, cleared each entry).
- `atomic` — an `atomic()` context manager instance (only when `atomic_migration=True`).

### Constructor: `__init__(self, connection, collect_sql=False, atomic=True)`

Sets `connection`, `collect_sql`. If `collect_sql`, initializes `collected_sql = []`. Sets `atomic_migration = self.connection.features.can_rollback_ddl and atomic`.

### Context Manager Methods

#### `__enter__(self)` → `self`

Initializes `deferred_sql = []`. If `atomic_migration`, enters an `atomic(self.connection.alias)` context manager, storing it in `self.atomic`. Returns `self`.

#### `__exit__(self, exc_type, exc_value, traceback)`

If no exception (`exc_type is None`), executes all statements in `deferred_sql` via `self.execute(sql)`. Then exits the atomic context manager if present.

### Core Utility Methods

#### `execute(self, sql, params=())` → `None`

Performs a DDL/DML execution with safety checks:
1. If not collecting SQL and inside an atomic block on a database that cannot rollback DDL, raises `TransactionManagementError`.
2. Converts `sql` to string via `str(sql)`.
3. Logs the SQL and params at debug level using `logger.debug("%s; (params %r)", sql, params, extra={"params": params, "sql": sql})`.
4. If collecting SQL: appends the formatted SQL (with params substituted via `self.quote_value`) to `collected_sql`, adding a trailing semicolon if missing. Otherwise: opens a cursor and executes `cursor.execute(sql, params)`.

#### `quote_name(self, name)` → `str`

Delegates to `self.connection.ops.quote_name(name)`.

#### `table_sql(self, model)` → `(sql: str, params: list)`

Generates the full CREATE TABLE SQL for a model:
1. For each tuple in `model._meta.unique_together`, gets the fields and appends `_create_unique_sql(model, fields)` to `deferred_sql`.
2. Iterates over `model._meta.local_fields`:
   - Calls `column_sql(model, field)`; if definition is `None`, skips.
   - Appends check constraint SQL (`sql_check_constraint % db_params`) if present.
   - Appends column type suffix via `field.db_type_suffix(connection=self.connection)`.
   - If the field has a `remote_field` and `db_constraint`: computes target table/column; if `sql_create_inline_fk` is set, appends inline FK SQL; otherwise appends `_create_fk_sql(model, field, "_fk_%(to_table)s_%(to_column)s")` to `deferred_sql`.
   - Appends `"%(column_name) %(definition)"` to `column_sqls`.
   - If the field is an AutoField/BigAutoField/SmallAutoField and `ops.auto_sql()` returns non-empty SQL, extends `deferred_sql` with it.
3. Builds constraint SQL list from `model._meta.constraints` via `constraint.constraint_sql(model, self)`.
4. Formats into `sql_create_table % {"table": quoted table name, "definition": comma-joined column+constraint SQL}`.
5. If `model._meta.db_tablespace` is set and `ops.tablespace_sql()` returns non-empty string, appends it to the SQL.
6. Returns `(sql, params)`.

### Field ↔ Database Mapping Methods

#### `_iter_column_sql(self, column_db_type, params, model, field, include_default)` → generator of str fragments

Yields column definition fragments:
1. Yields `column_db_type`.
2. If the field has a `db_collation`, yields `_collate_sql(collation)`.
3. Determines nullability from `field.null`; if `include_default` is true and not skipped (via `skip_default` and not nullable-with-skip-on-alter), computes `effective_default(field)`; if non-None, yields `"DEFAULT "` + `_column_default_sql(field)`, with params appended unless `requires_literal_defaults` is set (in which case the value is substituted inline via `prepare_default`).
4. If `empty_strings_allowed` and not primary key and `interprets_empty_strings_as_nulls`, forces null=True.
5. Yields `"NOT NULL"` if not null, or `"NULL"` if `implied_column_null` is false.
6. Yields `"PRIMARY KEY"` if primary key, else `"UNIQUE"` if unique.
7. If a tablespace is set and the backend supports it and field is unique, yields the inline tablespace SQL.

#### `column_sql(self, model, field, include_default=False)` → `(definition: str | None, params: list)`

Returns the column definition string for a field (which must have had `set_attributes_from_name()` called):
1. Gets `db_params = field.db_parameters(connection=self.connection)`. If `db_params["type"]` is `None`, returns `(None, None)`.
2. Builds params list and joins `_iter_column_sql(column_db_type, params, model, field, include_default)` with spaces.
3. Returns the joined string and params.

#### `skip_default(self, field)` → `bool`

Returns `False` by default. Override for backends that don't accept defaults on certain column types (e.g., MySQL longtext/longblob).

#### `skip_default_on_alter(self, field)` → `bool`

Returns `False` by default. Override for backends that can't include defaults in ALTER COLUMN statements.

#### `prepare_default(self, value)` → `str`

Must be overridden by subclasses for backends with `requires_literal_defaults`. Raises `NotImplementedError` otherwise.

#### `_column_default_sql(self, field)` → `str`

Returns `"%s"` (a placeholder for the default value). Override in subclasses.

#### `_effective_default(field)` → `default_value | None` *(static method)*

Computes the effective default for a field without needing a connection:
1. If `field.has_default()`, returns `field.get_default()`.
2. Else if not null and blank and empty_strings_allowed: returns `b""` for BinaryField, else `""`.
3. Else if `auto_now` or `auto_now_add`: returns `timezone.now()` for DateTimeField; otherwise `datetime.now().date()` for DateField, `.time()` for TimeField, or `datetime.now()` for others.
4. Otherwise returns `None`.

#### `effective_default(self, field)` → `default_value | None`

Returns `field.get_db_prep_save(self._effective_default(field), self.connection)`.

#### `quote_value(self, value)` → `str`

Must be overridden by subclasses. Returns a quoted version of the value for use in SQL strings. Raises `NotImplementedError` by default.

### Model/Table Action Methods

#### `create_model(self, model)` → `None`

1. Calls `table_sql(model)`, executes via `self.execute(sql, params or None)`.
2. Extends `deferred_sql` with `_model_indexes_sql(model)`.
3. For each local M2M field whose through table is auto-created, calls `create_model(field.remote_field.through)`.

#### `delete_model(self, model)` → `None`

1. For each local M2M field whose through table is auto-created, calls `delete_model(field.remote_field.through)`.
2. Executes `sql_delete_table % {"table": quoted table name}`.
3. Removes from `deferred_sql` any `Statement` objects that reference the deleted table (checked via `sql.references_table(model._meta.db_table)`).

#### `add_index(self, model, index)` → `None | Statement`

If the index contains expressions and the backend doesn't support expression indexes, returns `None`. Otherwise executes `index.create_sql(model, self)` with `params=None` (since create_sql returns pre-interpolated SQL) and returns nothing.

#### `remove_index(self, model, index)` → `None | None`

If the index contains expressions and the backend doesn't support expression indexes, returns `None`. Otherwise executes `index.remove_sql(model, self)`.

#### `add_constraint(self, model, constraint)` → `None`

Calls `constraint.create_sql(model, self)`. If non-empty, executes with `params=None`.

#### `remove_constraint(self, model, constraint)` → `None`

Calls `constraint.remove_sql(model, self)`. If non-empty, executes it.

### Unique/Together Alteration Methods

#### `alter_unique_together(self, model, old_unique_together, new_unique_together)` → `None`

1. Converts both inputs to sets of field-name tuples (`olds`, `news`).
2. For fields in `olds - news`: calls `_delete_composed_index(model, fields, {"unique": True}, self.sql_delete_unique)`.
3. For fields in `news - olds`: gets the fields from model meta and executes `_create_unique_sql(model, fields)`.

#### `alter_index_together(self, model, old_index_together, new_index_together)` → `None`

1. Converts both inputs to sets of field-name tuples (`olds`, `news`).
2. For fields in `olds - news`: calls `_delete_composed_index(model, fields, {"index": True, "unique": False}, self.sql_delete_index)`.
3. For fields in `news - olds`: gets the fields and executes `_create_index_sql(model, fields=fields, suffix="_idx")`.

#### `_delete_composed_index(self, model, fields, constraint_kwargs, sql)` → `None`

1. Collects meta constraint names and index names into a set to exclude.
2. Gets column names for the given field names.
3. Calls `_constraint_names(model, columns, exclude=..., **constraint_kwargs)`. If exactly one name is not found (length != 1), raises `ValueError` with details.
4. Executes `_delete_constraint_sql(sql, model, constraint_names[0])`.

### Table Alteration Methods

#### `alter_db_table(self, model, old_db_table, new_db_table)` → `None`

If names are equal or case-insensitive match (when backend ignores table name case), returns early. Otherwise:
1. Executes `sql_rename_table % {"old_table": quoted old, "new_table": quoted new}`.
2. For each statement in `deferred_sql`, if it's a `Statement` instance, calls `sql.rename_table_references(old_db_table, new_db_table)`.

#### `alter_db_tablespace(self, model, old_db_tablespace, new_db_tablespace)` → `None`

Executes `sql_retablespace_table % {"table": quoted table, "old_tablespace": quoted old, "new_tablespace": quoted new}`.

### Field Addition/Removal Methods

#### `add_field(self, model, field)` → `None`

1. If the field is M2M with an auto-created through table, delegates to `create_model(field.remote_field.through)`.
2. Calls `column_sql(model, field, include_default=True)`. If definition is `None`, returns.
3. Appends check constraint SQL if present.
4. If the field has a remote field and FK support and `db_constraint`: computes target table/column; if `sql_create_column_inline_fk` is set, appends inline FK SQL (using `_fk_constraint_name` for naming); otherwise appends `_create_fk_sql(model, field, constraint_suffix)` to `deferred_sql`.
5. Executes `sql_create_column % {"table": quoted table, "column": quoted column, "definition": definition}` with params.
6. If not skipped on alter and effective default is non-None: calls `_alter_column_default_sql(model, None, field, drop=True)` and executes the resulting SQL to drop the in-database default.
7. Extends `deferred_sql` with `_field_indexes_sql(model, field)`.
8. Closes connection if `connection_persists_old_columns`.

#### `remove_field(self, model, field)` → `None`

1. If M2M with auto-created through table, delegates to `delete_model(field.remote_field.through)`.
2. If the field's db type is `None`, returns.
3. If the field has a remote field: gets FK constraint names via `_constraint_names(model, [field.column], foreign_key=True)` and executes `_delete_fk_sql` for each.
4. Executes `sql_delete_column % {"table": quoted table, "column": quoted column}`.
5. Closes connection if `connection_persists_old_columns`.
6. Removes from `deferred_sql` any `Statement` objects referencing the deleted column (checked via `sql.references_column(model._meta.db_table, field.column)`).

### Field Alteration Methods

#### `alter_field(self, model, old_field, new_field, strict=False)` → `None`

1. If `_field_should_be_altered(old_field, new_field)` is false, returns early.
2. Gets `old_type = old_db_params["type"]` and `new_type = new_db_params["type"]`.
3. Validates: if either type is None without a remote field, raises `ValueError` about badly-written custom field.
4. If both types are None and both have auto-created through models: delegates to `_alter_many_to_many(model, old_field, new_field, strict)`.
5. If both types are None and neither has an auto-created through model: returns (no-op for manual through models).
6. If only one type is None: raises `ValueError` about incompatible M2M/through conversion.
7. Delegates to `_alter_field(model, old_field, new_field, old_type, new_type, old_db_params, new_db_params, strict)`.

#### `_alter_field(self, model, old_field, new_field, old_type, new_type, old_db_params, new_db_params, strict=False)` → `None`

Performs a physical (non-M2M) field update in this sequence:

1. **Drop FK constraints on the old field** (if backend supports FKs and old field has db_constraint): gets constraint names via `_constraint_names(model, [old_field.column], foreign_key=True)`. In strict mode, verifies exactly one exists. Executes `_delete_fk_sql` for each; tracks dropped columns in `fks_dropped = set()`.

2. **Drop unique constraints** if `old_field.unique` and (not `new_field.unique` or field became primary key): gets meta constraint names to exclude, finds matching unique constraints via `_constraint_names(model, [old_field.column], unique=True, primary_key=False, exclude=...)`. In strict mode, verifies exactly one. Executes `_delete_unique_sql` for each.

3. **Drop incoming FK constraints** if the field was a PK or unique target and type is changing (`drop_foreign_keys = supports_fk and ((old_pk and new_pk) or (old_unique and new_unique)) and old_type != new_type`): iterates `_related_non_m2m_objects(old_field, new_field)`; for each related model's FK to the new field, drops via `_delete_fk_sql`.

4. **Drop db_index** if `old_field.db_index and not old_field.unique and (not new_field.db_index or new_field.unique)`: gets meta index names to exclude, finds BTREE indexes via `_constraint_names(model, [old_field.column], index=True, type_=Index.suffix, exclude=...)`. Executes `_delete_index_sql` for each.

5. **Drop check constraints** if `old_db_params["check"] != new_db_params["check"] and old_db_params["check"]`: gets meta constraint names to exclude, finds check constraints via `_constraint_names(model, [old_field.column], check=True, exclude=...)`. In strict mode, verifies exactly one. Executes `_delete_check_sql` for each.

6. **Rename column** if `old_field.column != new_field.column`: executes `_rename_field_sql(table, old_field, new_field, new_type)`. Then iterates `deferred_sql`, calling `sql.rename_column_references(old_table, old_col, new_col)` on each `Statement` instance.

7. **Build action fragments**:
   - Initializes `actions = []`, `null_actions = []`, `post_actions = []`.
   - If collation changed: appends `_alter_column_collation_sql(model, new_field, new_type, new_collation)`.
   - Else if type changed: calls `_alter_column_type_sql(model, old_field, new_field, new_type)`; appends the fragment to `actions`, extends `post_actions` with returned extras.

8. **Handle NULL → NOT NULL with default** (4-way alteration): If `old_field.null and not new_field.null`:
   - Computes `old_default = effective_default(old_field)`, `new_default = effective_default(new_field)`.
   - If not skipped on alter, defaults differ, and new default is non-None: sets `needs_database_default = True` and appends `_alter_column_default_sql(model, old_field, new_field)` to actions.

9. **Handle nullability change**: If `old_field.null != new_field.null`: calls `_alter_column_null_sql(model, old_field, new_field)`. If non-None, appends to `null_actions`.

10. **Execute ALTER COLUMN**:
    - If `actions or null_actions`: if not doing 4-way default alteration, combines `actions + null_actions`; if backend supports combined alters, joins all action SQL with commas and merges params; executes each via `sql_alter_column % {"table": quoted table, "changes": sql}`.
    - If 4-way: first executes the actions (default set), then executes `sql_update_with_default` to update existing NULL rows to new default, then executes null_actions (NOT NULL).

11. **Execute post_actions**: For each `(sql, params)` in `post_actions`, executes directly.

12. **Drop primary key** if old was PK and new is not: calls `_delete_primary_key(model, strict)`.

13. **Add unique constraint** if `_unique_should_be_added(old_field, new_field)`: executes `_create_unique_sql(model, [new_field])`.

14. **Add index** if `(not old_db_index or old_unique) and new_db_index and not new_unique`: executes `_create_index_sql(model, fields=[new_field])`.

15. **Handle PK type change on related columns**: If `drop_foreign_keys` or field became primary key, collects relations from `_related_non_m2m_objects(old_field, new_field)` into `rels_to_update`. For each relation: calls `_alter_column_type_sql(new_rel.related_model, old_rel.field, new_rel.field, rel_type)`, executes the fragment and post-actions on the related model's table.

16. **Add FK constraint** if backend supports FKs and new field has remote_field and (`fks_dropped` or no old FK or old not constrained) and `new_field.db_constraint`: executes `_create_fk_sql(model, new_field, "_fk_%(to_table)s_%(to_column)s")`.

17. **Rebuild dropped FKs** if `drop_foreign_keys`: for each relation in `rels_to_update` where the field is constrained, executes `_create_fk_sql(rel.related_model, rel.field, "_fk")`.

18. **Add check constraints** if `old_db_params["check"] != new_db_params["check"] and new_db_params["check"]`: generates constraint name via `_create_index_name(table, [new_field.column], suffix="_check")`, executes `_create_check_sql(model, constraint_name, new_db_params["check"])`.

19. **Drop in-database default** if `needs_database_default`: calls `_alter_column_default_sql(model, old_field, new_field, drop=True)` and executes it.

20. Closes connection if `connection_persists_old_columns`.

### Column Alteration Hook Methods

#### `_alter_column_null_sql(self, model, old_field, new_field)` → `(sql: str, params: list) | None`

If backend interprets empty strings as nulls and field allows them, returns `None`. Otherwise returns `(sql_alter_column_null if new_field.null else sql_alter_column_not_null) % {"column": quoted column, "type": new_type}, []`.

#### `_alter_column_default_sql(self, model, old_field, new_field, drop=False)` → `(sql: str, params: list)`

Computes `new_default = effective_default(new_field)`, `default = _column_default_sql(new_field)`, `params = [new_default]`. If `drop`: clears params. If not drop and `requires_literal_defaults`: sets default to `prepare_default(new_default)` and clears params. Selects SQL template: if drop, uses `sql_alter_column_no_default_null` (if null) or `sql_alter_column_no_default`; else uses `sql_alter_column_default`. Returns `(template % {"column": quoted column, "type": new_type, "default": default}, params)`.

#### `_alter_column_type_sql(self, model, old_field, new_field, new_type)` → `((sql: str, params: list), post_actions: list)`

Returns a single-element tuple of `(sql_alter_column_type % {"column": quoted column, "type": new_type}, [])` and an empty post-actions list. Override in subclasses for backends with different creation vs alteration types (e.g., PostgreSQL SERIAL).

#### `_alter_column_collation_sql(self, model, new_field, new_type, new_collation)` → `(sql: str, params: list)`

Returns `(sql_alter_column_collate % {"column": quoted column, "type": new_type, "collation": " " + _collate_sql(new_collation) if new_collation else ""}, [])`.

### Many-to-Many Alteration Method

#### `_alter_many_to_many(self, model, old_field, new_field, strict)` → `None`

1. If the through table names differ: calls `alter_db_table(old_through_model, old_table_name, new_table_name)`.
2. Calls `alter_field(new_through_model, old_reverse_field, new_reverse_field)` where reverse fields are obtained via `m2m_reverse_field_name()`.
3. Calls `alter_field(new_through_model, old_self_field, new_self_field)` where self-referential fields are obtained via `m2m_field_name()`.

### Index/Constraint Name Generation Methods

#### `_create_index_name(self, table_name, column_names, suffix="")` → `str`

1. Extracts bare table name via `split_identifier(table_name)`.
2. Computes hash: `names_digest(table_name, *column_names, length=8)` + suffix = `hash_suffix_part`.
3. Gets `max_length = ops.max_name_length() or 200`.
4. Builds candidate: `"%s_%s_%s" % (table_name, "_".join(column_names), hash_suffix_part)`. If within max_length, returns it.
5. Otherwise truncates: if `hash_suffix_part` exceeds `max_length / 3`, truncates to `max_length // 3`; computes `other_length = (max_length - len(hash_suffix_part)) // 2 - 1`; builds with truncated table and column parts.
6. If resulting name starts with `_` or digit, prepends `"D"` and drops last character: `"D%s" % index_name[:-1]`.

#### `_get_index_tablespace_sql(self, model, fields, db_tablespace=None)` → `str`

If `db_tablespace` is None: uses first field's `db_tablespace` if single field, else model's `db_tablespace`. If non-None, returns `" " + ops.tablespace_sql(db_tablespace)`, else `""`.

#### `_index_condition_sql(self, condition)` → `str`

Returns `" WHERE " + condition` if truthy, else `""`.

#### `_index_include_sql(self, model, columns)` → `str | Statement`

If no columns or backend doesn't support covering indexes: returns `""`. Otherwise returns a `Statement(" INCLUDE (%(columns)s)", columns=Columns(model._meta.db_table, columns, self.quote_name))`.

### Index Creation Methods

#### `_create_index_sql(self, model, *, fields=None, name=None, suffix="", using="", db_tablespace=None, col_suffixes=(), sql=None, opclasses=(), condition=None, include=None, expressions=None)` → `Statement`

1. Defaults `fields = []`, `expressions = []`.
2. Creates a `Query(model, alias_cols=False).get_compiler(connection=self.connection)`.
3. Gets `tablespace_sql` via `_get_index_tablespace_sql`.
4. Extracts column names from fields.
5. Selects SQL template: `sql or self.sql_create_index`.
6. Defines inner function `create_index_name(*args, **kwargs)` that auto-generates name via `_create_index_name` if `name is None`, then returns quoted name.
7. Returns a `Statement(sql_create_index, table=Table(table, self.quote_name), name=IndexName(table, columns, suffix, create_index_name), using=using, columns=_index_columns(...) or Expressions(...), extra=tablespace_sql, condition=_index_condition_sql(condition), include=_index_include_sql(model, include))`.

#### `_delete_index_sql(self, model, name, sql=None)` → `Statement`

Returns a `Statement(sql or self.sql_delete_index, table=Table(model._meta.db_table, self.quote_name), name=self.quote_name(name))`.

#### `_index_columns(self, table, columns, col_suffixes, opclasses)` → `Columns`

Returns `Columns(table, columns, self.quote_name, col_suffixes=col_suffixes)`.

#### `_model_indexes_sql(self, model)` → `list[Statement]`

If model is not managed, is a proxy, or is swapped: returns `[]`. Otherwise collects:
1. For each local field: extends with `_field_indexes_sql(model, field)`.
2. For each tuple in `index_together`: creates index SQL via `_create_index_sql(model, fields=fields, suffix="_idx")`.
3. For each `model._meta.indexes`: if no expressions or backend supports expression indexes, appends `index.create_sql(model, self)`.

#### `_field_indexes_sql(self, model, field)` → `list[Statement]`

If `_field_should_be_indexed(model, field)`, returns `[self._create_index_sql(model, fields=[field])]`; else `[]`.

### Field Alteration Decision Methods

#### `_field_should_be_altered(self, old_field, new_field)` → `bool`

Deconstructs both fields. Removes non-database attributes (`blank`, `db_column`, `editable`, `error_messages`, `help_text`, `limit_choices_to`, `on_delete`, `related_name`, `related_query_name`, `validators`) from kwargs. Returns `True` if quoted column names differ or `(old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)`.

#### `_field_should_be_indexed(self, model, field)` → `bool`

Returns `field.db_index and not field.unique`.

#### `_field_became_primary_key(self, old_field, new_field)` → `bool`

Returns `not old_field.primary_key and new_field.primary_key`.

#### `_unique_should_be_added(self, old_field, new_field)` → `bool`

Returns `not new_field.primary_key and new_field.unique and (not old_field.unique or old_field.primary_key)`.

### Field Rename Method

#### `_rename_field_sql(self, table, old_field, new_field, new_type)` → `str`

Returns `sql_rename_column % {"table": quoted table, "old_column": quoted old column, "new_column": quoted new column, "type": new_type}`.

### Foreign Key Methods

#### `_create_fk_sql(self, model, field, suffix)` → `Statement`

Builds a `Statement(sql_create_fk, table=Table(model._meta.db_table, self.quote_name), name=_fk_constraint_name(model, field, suffix), column=Columns(model._meta.db_table, [field.column], self.quote_name), to_table=Table(target_model_meta.db_table, self.quote_name), to_column=Columns(target_model_meta.db_table, [target_field.column], self.quote_name), deferrable=self.connection.ops.deferrable_sql())`.

#### `_fk_constraint_name(self, model, field, suffix)` → `ForeignKeyName`

Returns a `ForeignKeyName(model._meta.db_table, [field.column], split_identifier(target_model_meta.db_table)[1], [target_field.column], suffix, create_fk_name)` where `create_fk_name` calls `_create_index_name` and quotes the result.

#### `_delete_fk_sql(self, model, name)` → `Statement`

Returns `_delete_constraint_sql(self.sql_delete_fk, model, name)`.

### Deferrable Constraint Method

#### `_deferrable_constraint_sql(self, deferrable)` → `str | None`

If `None`: returns `""`. If `Deferrable.DEFERRED`: returns `" DEFERRABLE INITIALLY DEFERRED"`. If `Deferrable.IMMEDIATE`: returns `" DEFERRABLE INITIALLY IMMEDIATE"`. Otherwise returns `None`.

### Unique Constraint Methods

#### `_unique_sql(self, model, fields, name, condition=None, deferrable=None, include=None, opclasses=None, expressions=None)` → `str | None`

If deferrable but backend doesn't support it: returns `None`. If condition/include/opclasses/expressions present: delegates to `_create_unique_sql`, appends result to `deferred_sql` if non-None, returns `None`. Otherwise builds constraint string via `sql_unique_constraint % {"columns": comma-joined quoted column names, "deferrable": _deferrable_constraint_sql(deferrable)}`, wraps in `sql_constraint % {"name": quoted name, "constraint": constraint}`.

#### `_create_unique_sql(self, model, fields, name=None, condition=None, deferrable=None, include=None, opclasses=None, expressions=None)` → `Statement | None`

If any unsupported feature is requested (deferrable without support, condition without partial index support, include without covering index support, expressions without expression index support): returns `None`. Defines inner function `create_unique_name` that auto-generates name via `_create_index_name(table, columns, "_uniq")` and quotes it. Gets compiler from Query. Extracts column names. If no name given, creates `IndexName(table, columns, "_uniq", create_unique_name)`; else uses quoted name. Selects SQL: `sql_create_unique_index` if condition/include/opclasses/expressions present, else `sql_create_unique`. Builds columns via `_index_columns` or `Expressions`. Returns a `Statement(sql, table=Table(...), name=name, columns=columns, condition=_index_condition_sql(condition), deferrable=_deferrable_constraint_sql(deferrable), include=_index_include_sql(model, include))`.

#### `_delete_unique_sql(self, model, name, condition=None, deferrable=None, include=None, opclasses=None, expressions=None)` → `Statement | None`

If any unsupported feature is requested: returns `None`. Selects SQL template: `sql_delete_index` if condition/include/opclasses/expressions present, else `sql_delete_unique`. Returns `_delete_constraint_sql(sql, model, name)`.

### Check Constraint Methods

#### `_check_sql(self, name, check)` → `str`

Returns `sql_constraint % {"name": quoted name, "constraint": sql_check_constraint % {"check": check}}`.

#### `_create_check_sql(self, model, name, check)` → `Statement`

Returns a `Statement(sql_create_check, table=Table(model._meta.db_table, self.quote_name), name=self.quote_name(name), check=check)`.

#### `_delete_check_sql(self, model, name)` → `Statement`

Returns `_delete_constraint_sql(self.sql_delete_check, model, name)`.

### Constraint Deletion Helper

#### `_delete_constraint_sql(self, template, model, name)` → `Statement`

Returns a `Statement(template, table=Table(model._meta.db_table, self.quote_name), name=self.quote_name(name))`.

### Constraint Lookup Method

#### `_constraint_names(self, model, column_names=None, unique=None, primary_key=None, index=None, foreign_key=None, check=None, type_=None, exclude=None)` → `list[str]`

1. If `column_names` is not None: converts each via `connection.introspection.identifier_converter`.
2. Opens a cursor and calls `connection.introspection.get_constraints(cursor, model._meta.db_table)`.
3. Iterates the resulting dict; for each `(name, infodict)`: filters by column match (`column_names is None or == infodict["columns"]`), then by boolean flags (`unique`, `primary_key`, `index`, `check`, `foreign_key` → must have `infodict["foreign_key"]` be truthy), then by `type_`, then excludes names in the `exclude` set.
4. Returns list of matching constraint names.

### Primary Key Methods

#### `_delete_primary_key(self, model, strict=False)` → `None`

Gets PK constraint names via `_constraint_names(model, primary_key=True)`. In strict mode, verifies exactly one exists (raises `ValueError` otherwise). Executes `_delete_primary_key_sql(model, name)` for each.

#### `_create_primary_key_sql(self, model, field)` → `Statement`

Returns a `Statement(sql_create_pk, table=Table(model._meta.db_table, self.quote_name), name=self.quote_name(_create_index_name(table, [field.column], suffix="_pk")), columns=Columns(model._meta.db_table, [field.column], self.quote_name))`.

#### `_delete_primary_key_sql(self, model, name)` → `Statement`

Returns `_delete_constraint_sql(self.sql_delete_pk, model, name)`.

### Collation Helper

#### `_collate_sql(self, collation)` → `str`

Returns `"COLLATE " + self.quote_name(collation)`.

### Procedure Method

#### `remove_procedure(self, procedure_name, param_types=())` → `None`

Builds SQL: `sql_delete_procedure % {"procedure": quoted name, "param_types": ",".join(param_types)}`. Executes it.

## django/db/models/fields/__init__.py
Now I have the full file. Here is the complete specification:

---

# Module-Level Preamble

## Imports

```python
import collections.abc
import copy
import datetime
import decimal
import math
import operator
import uuid
import warnings
from base64 import b64decode, b64encode
from functools import partialmethod, total_ordering

from django import forms
from django.apps import apps
from django.conf import settings
from django.core import checks, exceptions, validators
from django.db import connection, connections, router
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query_utils import DeferredAttribute, RegisterLookupMixin
from django.utils import timezone
from django.utils.datastructures import DictWrapper
from django.utils.dateparse import parse_date, parse_datetime, parse_duration, parse_time
from django.utils.duration import duration_microseconds, duration_string
from django.utils.functional import Promise, cached_property
from django.utils.ipv6 import clean_ipv6_address
from django.utils.itercompat import is_iterable
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
```

## Constants & Globals

- **`__all__`** — list of 32 exported names: `"AutoField"`, `"BLANK_CHOICE_DASH"`, `"BigAutoField"`, `"BigIntegerField"`, `"BinaryField"`, `"BooleanField"`, `"CharField"`, `"CommaSeparatedIntegerField"`, `"DateField"`, `"DateTimeField"`, `"DecimalField"`, `"DurationField"`, `"EmailField"`, `"Empty"`, `"Field"`, `"FilePathField"`, `"FloatField"`, `"GenericIPAddressField"`, `"IPAddressField"`, `"IntegerField"`, `"NOT_PROVIDED"`, `"NullBooleanField"`, `"PositiveBigIntegerField"`, `"PositiveIntegerField"`, `"PositiveSmallIntegerField"`, `"SlugField"`, `"SmallAutoField"`, `"SmallIntegerField"`, `"TextField"`, `"TimeField"`, `"URLField"`, `"UUIDField"`.

- **`BLANK_CHOICE_DASH`** — `[("", "---------")]`; default blank choice for select fields.

## Helper Functions

### `_empty(of_cls)`
Creates an instance of `Empty`, then sets its `__class__` to `of_cls` and returns it. Used as a lightweight object construction in `__copy__` and `__reduce__`.

### `return_None()`
Returns `None`. Used as a callable default for fields that should return None by default.

### `_load_field(app_label, model_name, field_name)`
Looks up the model via `apps.get_model(app_label, model_name)`, then calls `._meta.get_field(field_name)` and returns it. Used during unpickling to restore field references from their model.

### `_to_naive(value)`
If `value` is timezone-aware (`timezone.is_aware(value)`), converts it to naive UTC via `timezone.make_naive(value, datetime.timezone.utc)`. Returns the (possibly converted) value.

### `_get_naive_now()`
Returns `timezone.now()` converted to naive UTC via `_to_naive`.

---

# Code Objects

## Class `Empty`
A trivial marker class with no attributes or methods. Used as a placeholder in `__copy__` and `_empty()`.

## Class `NOT_PROVIDED`
A trivial sentinel class with no attributes or methods. Used as the default value for the `default` parameter of `Field.__init__` to distinguish "no default provided" from an explicit `None` default.

---

## Class `Field(RegisterLookupMixin)` — base class, decorated with `@total_ordering`

### Class Attributes
- **`empty_strings_allowed = True`** — whether empty strings are permitted at the database level.
- **`empty_values = list(validators.EMPTY_VALUES)`** — list of values considered "empty" (e.g., `None`, `""`, `[]`).
- **`creation_counter = 0`** (class-level) / **`auto_creation_counter = -1`** (class-level) — monotonic counters for field ordering. Decremented on each creation.
- **`default_validators = []`** — empty list of default validators.
- **`default_error_messages`** — dict with keys: `"invalid_choice"` (`_("Value %(value)r is not a valid choice.")`), `"null"` (`_("This field cannot be null.")`), `"blank"` (`_("This field cannot be blank.")`), `"unique"` (`_("%(model_name)s with this %(field_label)s already exists.")`), `"unique_for_date"` (`_("%(field_label)s must be unique for %(date_field_label)s %(lookup_type)s.")`).
- **`system_check_deprecated_details = None`** / **`system_check_removed_details = None`** — deprecation/removal metadata.
- **`hidden = False`**, **`many_to_many = None`**, **`many_to_one = None`**, **`one_to_many = None`**, **`one_to_one = None`**, **`related_model = None`**.
- **`descriptor_class = DeferredAttribute`** — the descriptor class used on the model.
- **`description`** — a `property` that calls `_description()`, which returns `_("Field of type: %(field_type)s") % {"field_type": self.__class__.__name__}`.

### Instance Attributes (set in `__init__`)
Set via parameters with these exact defaults:
- `verbose_name=None`, `name=None`, `primary_key=False`, `max_length=None`, `unique=False`, `blank=False`, `null=False`, `db_index=False`, `rel=None`, `default=NOT_PROVIDED`, `editable=True`, `serialize=True`, `unique_for_date=None`, `unique_for_month=None`, `unique_for_year=None`, `choices=None`, `help_text=""`, `db_column=None`, `db_tablespace=None`, `auto_created=False`, `validators=()`, `error_messages=None`.

Inside `__init__`:
- Sets `self.name`, `self.verbose_name`, `self._verbose_name` (original verbose_name for deconstruction), `self.primary_key`, `self.max_length`, `self._unique`, `self.blank`, `self.null`, `self.remote_field = rel`, `self.is_relation = self.remote_field is not None`, `self.default`, `self.editable`, `self.serialize`, `self.unique_for_date/month/year`, `self.choices` (converted to list if it's an iterator), `self.help_text`, `self.db_index`, `self.db_column`, `self._db_tablespace`, `self.auto_created`.
- Manages `creation_counter`: if `auto_created`, uses `Field.auto_creation_counter` and decrements it; otherwise uses `Field.creation_counter` and increments it. Stores the result in `self.creation_counter`.
- Sets `self._validators = list(validators)` and `self._error_messages = error_messages`.

### Methods

#### `__str__(self)`
If the field has a `model` attribute, returns `"%s.%s" % (model._meta.label, self.name)`. Otherwise delegates to `super().__str__()`.

#### `__repr__(self)`
Returns `"<%s: %s>" % (path, name)` where `path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)` and `name = getattr(self, "name", None)`. If no name, returns `"<%s>" % path`.

#### `check(self, **kwargs)`
Returns a list of errors from: `_check_field_name()`, `_check_choices()`, `_check_db_index()`, `_check_null_allowed_for_primary_keys()`, `_check_backend_specific_checks(**kwargs)`, `_check_validators()`, `_check_deprecation_details()`.

#### `_check_field_name(self)`
Validates field name: returns error `fields.E001` if ends with `"_"`; error `fields.E002` if contains `LOOKUP_SEP`; error `fields.E003` if equals `"pk"`. Otherwise empty list.

#### `_choices_is_value(cls, value)` (classmethod)
Returns `True` if `value` is a valid choice value: `isinstance(value, (str, Promise)) or not is_iterable(value)`.

#### `_check_choices(self)`
Validates the `choices` attribute. If no choices, returns `[]`. Checks that choices is iterable and not a string (`fields.E004`). Iterates through groups to validate each `(value, human_name)` pair using `_choices_is_value`. Tracks `choice_max_length` when `self.max_length` is set; if the longest value exceeds `max_length`, returns error `fields.E009`. If any pair fails validation, returns error `fields.E005`.

#### `_check_db_index(self)`
Returns error `fields.E006` if `db_index` is not in `(None, True, False)`. Otherwise empty list.

#### `_check_null_allowed_for_primary_keys(self)`
If `primary_key and null and not connection.features.interprets_empty_strings_as_nulls`, returns error `fields.E007` with hint to set `null=False` or remove `primary_key=True`. Otherwise empty list.

#### `_check_backend_specific_checks(self, databases=None, **kwargs)`
For each database alias in `databases`, if the router allows migration for that app/model, extends errors with results from `connections[alias].validation.check_field(self, **kwargs)`. Returns empty list if `databases` is None.

#### `_check_validators(self)`
Iterates over `self.validators`; if any validator is not callable, returns error `fields.E008` with hint showing the index and repr of the non-callable. Otherwise empty list.

#### `_check_deprecation_details(self)`
If `system_check_removed_details` is not None, returns an Error using its `"msg"`, `"hint"`, and `"id"` (defaulting id to `"fields.EXXX"`). If `system_check_deprecated_details` is not None, returns a Warning similarly. Otherwise empty list.

#### `get_col(self, alias, output_field=None)`
If `alias == self.model._meta.db_table` and (`output_field` is None or equals `self`), returns `self.cached_col`. Otherwise imports `Col` from `django.db.models.expressions` and returns `Col(alias, self, output_field)`.

#### `cached_col` (property, `@cached_property`)
Returns `Col(self.model._meta.db_table, self)` imported from `django.db.models.expressions`.

#### `select_format(self, compiler, sql, params)`
Returns `(sql, params)` unchanged. Overridden by subclasses for GIS columns on MySQL.

#### `deconstruct(self)`
Returns a 4-tuple `(name, path, args, kwargs)`:
- Builds `keywords` dict from `possibles` (all default parameter values). For each, gets the actual value via `getattr`, using `attr_overrides` mapping (`unique→_unique`, `error_messages→_error_messages`, `validators→_validators`, `verbose_name→_verbose_name`, `db_tablespace→_db_tablespace`). If name is `"choices"` and value is iterable, converts to list. For names in `equals_comparison` (`"choices"`, `"validators"`), uses `!=`; otherwise uses `is not`. Only includes keywords whose values differ from defaults.
- Computes `path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)`, then shortens known prefixes: replaces `"django.db.models.fields.related"`, `"django.db.models.fields.files"`, `"django.db.models.fields.json"`, `"django.db.models.fields.proxy"`, or `"django.db.models.fields"` with `"django.db.models"`.
- Returns `(self.name, path, [], keywords)`.

#### `clone(self)`
Calls `deconstruct()`, unpacks to `(name, path, args, kwargs)`, returns `self.__class__(*args, **kwargs)`.

#### `__eq__(self, other)`
If `other` is a `Field`, compares `creation_counter` and `getattr(other, "model", None) == getattr(self, "model", None)`. Returns `NotImplemented` otherwise.

#### `__lt__(self, other)`
If `other` is a `Field`: if creation counters differ or neither has a model, compares by `creation_counter <`. If one has a model and the other doesn't, no-model fields sort first. Otherwise compares `(model._meta.app_label, model._meta.model_name)`. Returns `NotImplemented` otherwise.

#### `__hash__(self)`
Returns `hash(self.creation_counter)`.

#### `__deepcopy__(self, memodict)`
Creates a shallow copy via `copy.copy(self)`. If `remote_field` exists, copies it and fixes the back-reference if needed. Stores in `memodict[id(self)] = obj` and returns it.

#### `__copy__(self)`
Creates an `Empty()` instance, sets its `__class__` to `self.__class__`, copies `__dict__`, and returns it. Avoids `__reduce__`.

#### `__reduce__(self)`
If no `model` attribute: returns `(_empty, (self.__class__,), state)` where `state = self.__dict__.copy()` with `"_get_default"` removed. If model exists: returns `(_load_field, (app_label, object_name, name))`.

#### `get_pk_value_on_save(self, instance)`
If `self.default` is truthy, returns `self.get_default()`. Otherwise returns `None`.

#### `to_python(self, value)`
Returns `value` unchanged. Subclasses override for type conversion. Raises `ValidationError` on failure.

#### `error_messages` (property, `@cached_property`)
Merges `default_error_messages` from all classes in the MRO (reversed), then updates with `self._error_messages or {}`. Returns the merged dict.

#### `validators` (property, `@cached_property`)
Returns `[*self.default_validators, *self._validators]`.

#### `run_validators(self, value)`
If `value in self.empty_values`, returns early. Otherwise iterates over validators; catches `ValidationError`, replaces message using `error_messages[code]` if available, collects errors. If any errors collected, raises `ValidationError(errors)`.

#### `validate(self, value, model_instance)`
If not editable, returns. If choices are set and value is not empty, checks against all option keys (including nested optgroups). Raises `ValidationError("invalid_choice")` on mismatch. If value is None and `not self.null`, raises `"null"`. If value is in empty_values and `not self.blank`, raises `"blank"`.

#### `clean(self, value, model_instance)`
Calls `to_python(value)`, then `validate()`, then `run_validators()`. Returns the converted value. Propagates all validation errors.

#### `db_type_parameters(self, connection)`
Returns `DictWrapper(self.__dict__, connection.ops.quote_name, "qn_")`.

#### `db_check(self, connection)`
Looks up `connection.data_type_check_constraints[self.get_internal_type()]` formatted with db_type_params. Returns None on KeyError.

#### `db_type(self, connection)`
Looks up `connection.data_types[self.get_internal_type()]` formatted with db_type_params. Returns None on KeyError.

#### `rel_db_type(self, connection)`
Returns `self.db_type(connection)`.

#### `cast_db_type(self, connection)`
Looks up `connection.ops.cast_data_types.get(self.get_internal_type())`; if found, formats with db_type_params; otherwise returns `self.db_type(connection)`.

#### `db_parameters(self, connection)`
Returns `{"type": self.db_type(connection), "check": self.db_check(connection)}`.

#### `db_type_suffix(self, connection)`
Returns `connection.data_types_suffix.get(self.get_internal_type())`.

#### `get_db_converters(self, connection)`
If field has `from_db_value`, returns `[self.from_db_value]`; else `[]`.

#### `unique` (property)
Returns `self._unique or self.primary_key`.

#### `db_tablespace` (property)
Returns `self._db_tablespace or settings.DEFAULT_INDEX_TABLESPACE`.

#### `db_returning` (property)
Returns `False`.

#### `set_attributes_from_name(self, name)`
Sets `self.name = self.name or name`, calls `get_attname_column()` to set `self.attname` and `self.column`, sets `self.concrete = self.column is not None`. If verbose_name is None and name exists, sets it to `name.replace("_", " ")`.

#### `contribute_to_class(self, cls, name, private_only=False)`
Calls `set_attributes_from_name(name)`, sets `self.model = cls`, calls `cls._meta.add_field(self, private=private_only)`. If `self.column` exists, sets `setattr(cls, self.attname, self.descriptor_class(self))`. If choices exist and `"get_%s_display" % self.name` not in `cls.__dict__`, sets a `partialmethod(cls._get_FIELD_display, field=self)` as the display method.

#### `get_filter_kwargs_for_object(self, obj)`
Returns `{self.name: getattr(obj, self.attname)}`.

#### `get_attname(self)`
Returns `self.name`.

#### `get_attname_column(self)`
`attname = self.get_attname()`, `column = self.db_column or attname`. Returns `(attname, column)`.

#### `get_internal_type(self)`
Returns `self.__class__.__name__`.

#### `pre_save(self, model_instance, add)`
Returns `getattr(model_instance, self.attname)`.

#### `get_prep_value(self, value)`
If value is a `Promise`, casts it via `value._proxy____cast()`. Returns the (possibly cast) value.

#### `get_db_prep_value(self, value, connection, prepared=False)`
If not prepared, calls `self.get_prep_value(value)`. Returns the result.

#### `get_db_prep_save(self, value, connection)`
Returns `self.get_db_prep_value(value, connection=connection, prepared=False)`.

#### `has_default(self)`
Returns `self.default is not NOT_PROVIDED`.

#### `get_default(self)`
Returns `self._get_default()`.

#### `_get_default` (property, `@cached_property`)
If has default: returns the callable/default value directly. If not and (`not empty_strings_allowed or null and not interprets_empty_strings_as_nulls`), returns `return_None`. Otherwise returns `str` (empty string).

#### `get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, limit_choices_to=None, ordering=())`
If choices are set: builds list from `self.choices`; if include_blank and no blank already in flatchoices, prepends `blank_choice`. Returns. Otherwise (relation field): gets related model, applies `limit_choices_to`, orders by `ordering`, returns `[blank_choice if include_blank else []] + [(choice_func(x), str(x)) for x in qs]` where `choice_func` is `attrgetter(remote_field.get_related_field().attname)` or `"pk"`.

#### `value_to_string(self, obj)`
Returns `str(self.value_from_object(obj))`.

#### `_get_flatchoices(self)` (property helper)
Flattens nested choice groups into a list of `(choice, value)` tuples. Returns empty list if no choices.

#### `flatchoices` (property)
Returns result of `_get_flatchoices()`.

#### `save_form_data(self, instance, data)`
Calls `setattr(instance, self.name, data)`.

#### `formfield(self, form_class=None, choices_form_class=None, **kwargs)`
Builds defaults dict with `required`, `label` (capfirst of verbose_name), `help_text`. If has default: sets `initial` and `show_hidden_initial=True` if callable; else calls `get_default()`. If choices exist: sets include_blank logic, passes choices/coerce/empty_value to TypedChoiceField, strips irrelevant kwargs. Default form_class is `forms.CharField`. Returns the form field instance.

#### `value_from_object(self, obj)`
Returns `getattr(obj, self.attname)`.

---

## Class `BooleanField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…must be either True or False.")`), `"invalid_nullable"` (`_("…must be either True, False, or None.")`).
- **`description = _("Boolean (Either True or False)")`**

### Methods
- **`get_internal_type()`** → `"BooleanField"`.
- **`to_python(self, value)`**: If null and empty, returns `None`. If already bool, returns `bool(value)`. Converts `"t"/"True"/"1"` to `True`, `"f"/"False"/"0"` to `False`. Raises `ValidationError("invalid_nullable" if self.null else "invalid")` otherwise.
- **`get_prep_value(self, value)`**: Calls parent; if None returns None; else calls `to_python(value)`.
- **`formfield(self, **kwargs)`**: If choices set, passes choices via get_choices. Else uses `NullBooleanField` form class if null, `BooleanField` otherwise, with `required=False`. Merges defaults and delegates to parent.
- **`select_format(self, compiler, sql, params)`**: Calls parent; if sql is empty string, replaces with `"1"`. Returns `(sql, params)`.

---

## Class `CharField(Field)`

### Class Attributes
- **`description = _("String (up to %(max_length)s)")`**

### `__init__(self, *args, db_collation=None, **kwargs)`
Calls parent `__init__`, sets `self.db_collation`. If `max_length` is set, appends `validators.MaxLengthValidator(self.max_length)` to validators.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_db_collation(databases)` and `_check_max_length_attribute()`.
- **`_check_max_length_attribute(self, **kwargs)`**: Returns error `fields.E120` if max_length is None; error `fields.E121` if not a positive int (excluding bool). Otherwise empty.
- **`_check_db_collation(self, databases)`**: For each db in databases where router allows the model, checks that either `db_collation` is None or the backend supports collation on char fields. Returns error `fields.E190` if not supported.
- **`cast_db_type(self, connection)`**: If max_length is None, returns `connection.ops.cast_char_field_without_max_length`; else calls parent.
- **`get_internal_type()`** → `"CharField"`.
- **`to_python(self, value)`**: Returns value if str or None; else `str(value)`.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`formfield(self, **kwargs)`**: Sets `max_length`; if null and backend doesn't interpret empty strings as nulls, sets `empty_value=None`. Merges with kwargs. Delegates to parent.
- **`deconstruct(self)`**: Calls parent; if `db_collation` is set, adds it to kwargs. Returns result.

---

## Class `CommaSeparatedIntegerField(CharField)`

### Class Attributes
- **`default_validators = [validators.validate_comma_separated_integer_list]`**
- **`description = _("Comma-separated integers")`**
- **`system_check_removed_details`**: `{"msg": "…removed except for support in historical migrations.", "hint": "Use CharField(validators=[validate_comma_separated_integer_list]) instead.", "id": "fields.E901"}`

No methods of its own; inherits all from `CharField`.

---

## Class `DateTimeCheckMixin`

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_mutually_exclusive_options()` and `_check_fix_default_value()`.
- **`_check_mutually_exclusive_options(self)`**: Checks that at most one of `auto_now_add`, `auto_now`, or a default value is set. Returns error `fields.E160` if more than one enabled.
- **`_check_fix_default_value(self)`**: Returns `[]`. Overridden by subclasses.
- **`_check_if_value_fixed(self, value, now=None)`**: If `now` is None, gets naive UTC now. Computes a 10-second window around it. Converts datetime to date if needed. If value falls within the window, returns warning `fields.W161`. Otherwise empty list.

---

## Class `DateField(DateTimeCheckMixin, Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…invalid date format. YYYY-MM-DD.")`), `"invalid_date"` (`_("…correct format but invalid date.")`).
- **`description = _("Date (without time)")`**

### `__init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs)`
Sets `auto_now`, `auto_now_add`. If either is true, sets `editable=False` and `blank=True` in kwargs. Calls parent `__init__`.

### Methods
- **`_check_fix_default_value(self)`**: If no default, returns `[]`. Converts datetime to date; checks if fixed value using `_check_if_value_fixed()`.
- **`deconstruct(self)`**: Calls parent; adds `auto_now`/`auto_now_add` kwargs if true; removes `editable` and `blank` if either auto flag is set. Returns result.
- **`get_internal_type()`** → `"DateField"`.
- **`to_python(self, value)`**: If None returns None. If datetime: converts to date (aware datetimes converted to default timezone first). If already date, returns it. Tries `parse_date(value)`; raises `ValidationError("invalid_date")` on parse failure, then `"invalid"` on total failure.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets value to `datetime.date.today()` via setattr and returns it. Else calls parent.
- **`contribute_to_class(self, cls, name, **kwargs)`**: Calls parent; if not null, registers `get_next_by_<name>` and `get_previous_by_<name>` as partialmethods on the class.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls `get_prep_value()`. Returns `connection.ops.adapt_datefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `""` if None; else `val.isoformat()`.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.DateField`.

---

## Class `DateTimeField(DateField)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ].")`), `"invalid_date"`, `"invalid_datetime"` (`_("…correct format but invalid date/time.")`).
- **`description = _("Date (with time)")`**

### Methods
- Inherits `__init__` from DateField.
- **`_check_fix_default_value(self)`**: If no default, returns `[]`. If value is datetime or date, calls `_check_if_value_fixed(value)`.
- **`get_internal_type()`** → `"DateTimeField"`.
- **`to_python(self, value)`**: If None returns None. If datetime, returns it. If date: creates datetime from year/month/day; if USE_TZ and naive, warns and makes aware with default timezone. Tries `parse_datetime(value)`, then `parse_date(value)` (wrapping in datetime). Raises appropriate ValidationErrors.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets value to `timezone.now()` via setattr and returns it. Else calls parent.
- Inherits `contribute_to_class` from DateField.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`. If USE_TZ and naive datetime, warns and makes aware with default timezone. Returns result.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls `get_prep_value()`. Returns `connection.ops.adapt_datetimefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `""` if None; else `val.isoformat()`.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.DateTimeField`.

---

## Class `DecimalField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…must be a decimal number.")`).
- **`description = _("Decimal number")`**

### `__init__(self, verbose_name=None, name=None, max_digits=None, decimal_places=None, **kwargs)`
Sets `max_digits`, `decimal_places`. Calls parent.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_decimal_places()`, `_check_max_digits()`, and `_check_decimal_places_and_max_digits()` (only if no digit errors). Returns errors `fields.E130`–`E134`.
- **`_check_decimal_places(self)`**: Must be a non-negative int. Errors E130/E131.
- **`_check_max_digits(self)`**: Must be a positive int. Errors E132/E133.
- **`_check_decimal_places_and_max_digits(self, **kwargs)`**: decimal_places must not exceed max_digits. Error `fields.E134`.
- **`validators` (property)**: Extends parent validators with `validators.DecimalValidator(self.max_digits, self.decimal_places)`.
- **`context` (property)**: Returns `decimal.Context(prec=self.max_digits)`.
- **`deconstruct(self)`**: Calls parent; adds `max_digits`/`decimal_places` to kwargs if not None.
- **`get_internal_type()`** → `"DecimalField"`.
- **`to_python(self, value)`**: If None returns None. If float: checks for NaN (raises error), else converts via `self.context.create_decimal_from_float(value)`. Otherwise tries `decimal.Decimal(value)`, raising `ValidationError("invalid")` on failure.
- **`get_db_prep_save(self, value, connection)`**: Returns `connection.ops.adapt_decimalfield_value(self.to_python(value), self.max_digits, self.decimal_places)`.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`formfield(self, **kwargs)`**: Calls parent with `max_digits`, `decimal_places`, and `form_class=forms.DecimalField`.

---

## Class `DurationField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…[DD] [[HH:]MM:]ss[.uuuuuu]] format.")`).
- **`description = _("Duration")`**

### Methods
- **`get_internal_type()`** → `"DurationField"`.
- **`to_python(self, value)`**: If None returns None. If timedelta, returns it. Tries `parse_duration(value)`, raises `ValidationError("invalid")` on failure.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If native duration field supported, returns value as-is. If not and value is None, returns None. Otherwise returns `duration_microseconds(value)`.
- **`get_db_converters(self, connection)`**: If no native duration support, prepends `connection.ops.convert_durationfield_value`; then extends parent's converters.
- **`value_to_string(self, obj)`**: Returns `""` if None; else `duration_string(val)`.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.DurationField`.

---

## Class `EmailField(CharField)`

### Class Attributes
- **`default_validators = [validators.validate_email]`**
- **`description = _("Email address")`**

### `__init__(self, *args, **kwargs)`
Sets default `max_length=254`. Calls parent.

### Methods
- **`deconstruct(self)`**: Calls parent; always includes max_length in kwargs (even if 254) to allow future default changes.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.EmailField`.

---

## Class `FilePathField(Field)`

### Class Attributes
- **`description = _("File path")`**

### `__init__(self, verbose_name=None, name=None, path="", match=None, recursive=False, allow_files=True, allow_folders=False, **kwargs)`
Sets `path`, `match`, `recursive`, `allow_files`, `allow_folders`. Sets default `max_length=100`. Calls parent.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_allowing_files_or_folders()`. Error `fields.E140` if neither allow_files nor allow_folders is True.
- **`deconstruct(self)`**: Calls parent; conditionally adds `path`, `match`, `recursive`, `allow_files`, `allow_folders`; removes max_length if 100.
- **`get_prep_value(self, value)`**: Calls parent; if not None, returns `str(value)`.
- **`formfield(self, **kwargs)`**: Calls parent with `path` (calling it if callable), `match`, `recursive`, `allow_files`, `allow_folders`, and `form_class=forms.FilePathField`.
- **`get_internal_type()`** → `"FilePathField"`.

---

## Class `FloatField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…must be a float.")`).
- **`description = _("Floating point number")`**

### Methods
- **`get_prep_value(self, value)`**: Calls parent; if None returns None. Tries `float(value)`, re-raising TypeError/ValueError with field-name message.
- **`get_internal_type()`** → `"FloatField"`.
- **`to_python(self, value)`**: If None returns None. Tries `float(value)`, raises `ValidationError("invalid")` on failure.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.FloatField`.

---

## Class `IntegerField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…must be an integer.")`).
- **`description = _("Integer")`**

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_max_length_warning()`. Warning `fields.W122` if max_length is set.
- **`_check_max_length_warning(self)`**: Returns warning W122 if max_length is not None; else empty list.
- **`validators` (property)**: Extends parent validators with `MinValueValidator(min_value)` and `MaxValueValidator(max_value)` from `connection.ops.integer_field_range(internal_type)`, only if no existing validator already covers the range.
- **`get_prep_value(self, value)`**: Calls parent; if None returns None. Tries `int(value)`, re-raising TypeError/ValueError with field-name message.
- **`get_internal_type()`** → `"IntegerField"`.
- **`to_python(self, value)`**: If None returns None. Tries `int(value)`, raises `ValidationError("invalid")` on failure.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.IntegerField`.

---

## Class `BigIntegerField(IntegerField)`

### Class Attributes
- **`description = _("Big (8 byte) integer")`**
- **`MAX_BIGINT = 9223372036854775807`**

### Methods
- **`get_internal_type()`** → `"BigIntegerField"`.
- **`formfield(self, **kwargs)`**: Calls parent with `min_value=-MAX_BIGINT-1`, `max_value=MAX_BIGINT`.

---

## Class `SmallIntegerField(IntegerField)`

### Class Attributes
- **`description = _("Small integer")`**

### Methods
- **`get_internal_type()`** → `"SmallIntegerField"`.

---

## Class `IPAddressField(Field)` (deprecated)

### Class Attributes
- **`empty_strings_allowed = False`**
- **`description = _("IPv4 address")`**
- **`system_check_removed_details`**: `{"msg": "…removed except for support in historical migrations.", "hint": "Use GenericIPAddressField instead.", "id": "fields.E900"}`

### `__init__(self, *args, **kwargs)`
Sets `max_length=15`. Calls parent.

### Methods
- **`deconstruct(self)`**: Calls parent; removes max_length from kwargs.
- **`get_prep_value(self, value)`**: Calls parent; if not None returns `str(value)`.
- **`get_internal_type()`** → `"IPAddressField"`.

---

## Class `GenericIPAddressField(Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`description = _("IP address")`**
- **`default_error_messages = {}`** (populated in `__init__`)

### `__init__(self, verbose_name=None, name=None, protocol="both", unpack_ipv4=False, *args, **kwargs)`
Sets `unpack_ipv4`, `protocol`. Calls `validators.ip_address_validators(protocol, unpack_ipv4)` to set `default_validators` and the `"invalid"` error message. Sets default `max_length=39`. Calls parent.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_blank_and_null_values()`. Error `fields.E150` if blank=True and null=False.
- **`_check_blank_and_null_values(self, **kwargs)`**: Returns error E150 if not null but blank.
- **`deconstruct(self)`**: Calls parent; adds `unpack_ipv4` if not False, `protocol` if not "both"; removes max_length if 39.
- **`get_internal_type()`** → `"GenericIPAddressField"`.
- **`to_python(self, value)`**: If None returns None. Strips whitespace. If contains `":"`, calls `clean_ipv6_address(value, unpack_ipv4, error_msg)`. Otherwise returns the string.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls `get_prep_value()`. Returns `connection.ops.adapt_ipaddressfield_value(value)`.
- **`get_prep_value(self, value)`**: Calls parent; if None returns None. If contains `":"`, tries `clean_ipv6_address`; on failure falls through to `str(value)`. Otherwise returns `str(value)`.
- **`formfield(self, **kwargs)`**: Calls parent with `protocol` and `form_class=forms.GenericIPAddressField`.

---

## Class `NullBooleanField(BooleanField)` (deprecated)

### Class Attributes
- **`default_error_messages`**: `"invalid"` (`_("…None, True or False.")`), `"invalid_nullable"` (same text).
- **`description = _("Boolean (Either True, False or None)")`**
- **`system_check_removed_details`**: `{"msg": "…removed except for support in historical migrations.", "hint": "Use BooleanField(null=True) instead.", "id": "fields.E903"}`

### `__init__(self, *args, **kwargs)`
Sets `null=True`, `blank=True`. Calls parent.

### Methods
- **`deconstruct(self)`**: Calls parent; removes `null` and `blank` from kwargs.

---

## Class `PositiveIntegerRelDbTypeMixin`

### `__init_subclass__(cls, **kwargs)`
If the subclass doesn't already have an `integer_field_class`, finds the first MRO parent (after self) that is a subclass of `IntegerField` and assigns it to `cls.integer_field_class`.

### `rel_db_type(self, connection)`
If `connection.features.related_fields_match_type`, returns `self.db_type(connection)`. Otherwise returns `self.integer_field_class().db_type(connection=connection)`.

---

## Class `PositiveBigIntegerField(PositiveIntegerRelDbTypeMixin, BigIntegerField)`

### Class Attributes
- **`description = _("Positive big integer")`**

### Methods
- **`get_internal_type()`** → `"PositiveBigIntegerField"`.
- **`formfield(self, **kwargs)`**: Calls parent with `min_value=0`.

---

## Class `PositiveIntegerField(PositiveIntegerRelDbTypeMixin, IntegerField)`

### Class Attributes
- **`description = _("Positive integer")`**

### Methods
- **`get_internal_type()`** → `"PositiveIntegerField"`.
- **`formfield(self, **kwargs)`**: Calls parent with `min_value=0`.

---

## Class `PositiveSmallIntegerField(PositiveIntegerRelDbTypeMixin, SmallIntegerField)`

### Class Attributes
- **`description = _("Positive small integer")`**

### Methods
- **`get_internal_type()`** → `"PositiveSmallIntegerField"`.
- **`formfield(self, **kwargs)`**: Calls parent with `min_value=0`.

---

## Class `SlugField(CharField)`

### Class Attributes
- **`default_validators = [validators.validate_slug]`**
- **`description = _("Slug (up to %(max_length)s)")`**

### `__init__(self, *args, max_length=50, db_index=True, allow_unicode=False, **kwargs)`
Sets `allow_unicode`. If True, replaces default_validators with `[validators.validate_unicode_slug]`. Calls parent with `max_length=max_length`, `db_index=db_index`.

### Methods
- **`deconstruct(self)`**: Calls parent; removes max_length if 50; adds db_index only if False; adds allow_unicode if not False.
- **`get_internal_type()`** → `"SlugField"`.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.SlugField`, `allow_unicode=self.allow_unicode`.

---

## Class `TextField(Field)`

### Class Attributes
- **`description = _("Text")`**

### `__init__(self, *args, db_collation=None, **kwargs)`
Calls parent; sets `self.db_collation = db_collation`.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_db_collation(databases)`. Error `fields.E190` if backend doesn't support collation on text fields.
- **`_check_db_collation(self, databases)`**: Same logic as CharField's version but checks for `"supports_collation_on_textfield"`.
- **`get_internal_type()`** → `"TextField"`.
- **`to_python(self, value)`**: Returns value if str or None; else `str(value)`.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`formfield(self, **kwargs)`**: Calls parent with `max_length=self.max_length`; adds `widget=forms.Textarea` unless choices are set.
- **`deconstruct(self)`**: Calls parent; adds `db_collation` if set.

---

## Class `TimeField(DateTimeCheckMixin, Field)`

### Class Attributes
- **`empty_strings_allowed = False`**
- **`default_error_messages`**: `"invalid"` (`_("…HH:MM[:ss[.uuuuuu]] format.")`), `"invalid_time"` (`_("…correct format but invalid time.")`).
- **`description = _("Time")`**

### `__init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs)`
Sets `auto_now`, `auto_now_add`. If either true, sets `editable=False`, `blank=True` in kwargs. Calls parent.

### Methods
- **`_check_fix_default_value(self)`**: If no default, returns `[]`. If datetime value, uses now=None for check. If time value, combines with today's date and calls `_check_if_value_fixed(value, now=now)`. Otherwise empty.
- **`deconstruct(self)`**: Calls parent; adds auto_now/auto_now_add if not False; removes blank/editable if either auto flag is set.
- **`get_internal_type()`** → `"TimeField"`.
- **`to_python(self, value)`**: If None returns None. If time, returns it. If datetime, extracts `.time()`. Tries `parse_time(value)`, raises `ValidationError("invalid_time")` on parse failure, then `"invalid"` on total failure.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets value to `datetime.datetime.now().time()` via setattr and returns it. Else calls parent.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls `get_prep_value()`. Returns `connection.ops.adapt_timefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `""` if None; else `val.isoformat()`.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.TimeField`.

---

## Class `URLField(CharField)`

### Class Attributes
- **`default_validators = [validators.URLValidator()]`**
- **`description = _("URL")`**

### `__init__(self, verbose_name=None, name=None, **kwargs)`
Sets default `max_length=200`. Calls parent.

### Methods
- **`deconstruct(self)`**: Calls parent; removes max_length if 200.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.URLField`.

---

## Class `BinaryField(Field)`

### Class Attributes
- **`description = _("Raw binary data")`**
- **`empty_values = [None, b""]`**

### `__init__(self, *args, **kwargs)`
Sets default `editable=False`. Calls parent. If max_length is set, appends `validators.MaxLengthValidator(self.max_length)`.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_str_default_value()`. Error `fields.E170` if default is a string.
- **`_check_str_default_value(self)`**: Returns error E170 if has default and isinstance(default, str).
- **`deconstruct(self)`**: Calls parent; removes editable from kwargs (since False is the default); adds it only if True.
- **`get_internal_type()`** → `"BinaryField"`.
- **`get_placeholder(self, value, compiler, connection)`**: Returns `connection.ops.binary_placeholder_sql(value)`.
- **`get_default(self)`**: If has non-callable default, returns it directly. Else calls parent; if result is empty string, returns `b""`; otherwise returns the result.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: Calls parent; if not None, returns `connection.Database.Binary(value)`.
- **`value_to_string(self, obj)`**: Returns base64-encoded string of the binary value via `b64encode(val).decode("ascii")`.
- **`to_python(self, value)`**: If str, decodes from base64 and returns a memoryview. Otherwise returns value unchanged.

---

## Class `UUIDField(Field)`

### Class Attributes
- **`default_error_messages`**: `"invalid"` (`_("…is not a valid UUID.")`).
- **`description = _("Universally unique identifier")`**
- **`empty_strings_allowed = False`**

### `__init__(self, verbose_name=None, **kwargs)`
Sets default `max_length=32`. Calls parent.

### Methods
- **`deconstruct(self)`**: Calls parent; removes max_length from kwargs.
- **`get_internal_type()`** → `"UUIDField"`.
- **`get_prep_value(self, value)`**: Calls parent then `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If None returns None. If not already uuid.UUID, calls `to_python()`. If backend has native UUID support, returns the UUID; otherwise returns `value.hex`.
- **`to_python(self, value)`**: If not None and not already uuid.UUID: determines input format (`"int"` if int, `"hex"` otherwise), tries `uuid.UUID(**{input_form: value})`, raises `ValidationError("invalid")` on failure. Returns value (possibly converted) or None.
- **`formfield(self, **kwargs)`**: Calls parent with `form_class=forms.UUIDField`.

---

## Class `AutoFieldMixin`

### Class Attributes
- **`db_returning = True`**

### `__init__(self, *args, **kwargs)`
Sets default `blank=True`. Calls parent.

### Methods
- **`check(self, **kwargs)`**: Extends parent with `_check_primary_key()`. Error `fields.E100` if primary_key is not set.
- **`_check_primary_key(self)`**: Returns error E100 if not self.primary_key; else empty list.
- **`deconstruct(self)`**: Calls parent; removes blank from kwargs; adds `primary_key=True`.
- **`validate(self, value, model_instance)`**: No-op (pass).
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls `get_prep_value()` then `connection.ops.validate_autopk_value(value)`. Returns result.
- **`contribute_to_class(self, cls, name, **kwargs)`**: If `cls._meta.auto_field` exists, raises `ValueError` about duplicate auto fields. Calls parent; sets `cls._meta.auto_field = self`.
- **`formfield(self, **kwargs)`**: Returns `None`.

---

## Class `AutoFieldMeta(type)` — metaclass

### Attributes/Methods
- **`_subclasses` (property)**: Returns `(BigAutoField, SmallAutoField)`.
- **`__instancecheck__(self, instance)`**: Returns True if instance is an instance of `_subclasses` or any parent class.
- **`__subclasscheck__(self, subclass)`**: Returns True if subclass is a subclass of `_subclasses` or any parent class.

---

## Class `AutoField(AutoFieldMixin, IntegerField, metaclass=AutoFieldMeta)`

### Methods
- **`get_internal_type()`** → `"AutoField"`.
- **`rel_db_type(self, connection)`**: Returns `IntegerField().db_type(connection=connection)`.

---

## Class `BigAutoField(AutoFieldMixin, BigIntegerField)`

### Methods
- **`get_internal_type()`** → `"BigAutoField"`.
- **`rel_db_type(self, connection)`**: Returns `BigIntegerField().db_type(connection=connection)`.

---

## Class `SmallAutoField(AutoFieldMixin, SmallIntegerField)`

### Methods
- **`get_internal_type()`** → `"SmallAutoField"`.
- **`rel_db_type(self, connection)`**: Returns `SmallIntegerField().db_type(connection=connection)`.