# Engine Specifications

This project stores SQL autocomplete vocabulary in normalized engine specifications under `structures/engines/`.

## How Version Deltas Work

The specification model uses a **base + delta** strategy:

- `common.functions` and `common.keywords` contain the shared baseline for that engine.
- Added support for stored functions in MySQL and MariaDB contexts, including deterministic flag handling.
- `versions.<major>.functions_remove` and `versions.<major>.keywords_remove` remove entries that are not valid for an older major version.

We intentionally keep newer capabilities in `common` and apply only removals for older majors.

## Version Resolution Rule

At runtime, vocabulary resolution uses:

1. exact major match when available;
2. otherwise, the highest configured major version `<=` the server major.

Example: if PostgreSQL server major is `19` and the highest configured major is `18`, version `18` is used.

## Inter-Engine API Differences and Feature Parity

The engine layer exposes a common base API (`SQLTable`, `SQLColumn`, `SQLIndex`, `SQLForeignKey`, `SQLRecord`, `SQLView`, `SQLTrigger`, `SQLCheck`, `SQLFunction`, `SQLProcedure`, `SQLDatabase`). Engines implement this API with the following known variations:

### SQLite

- File-based storage: `SQLiteDatabase.create()`, `alter()`, and `drop()` raise `NotImplementedError` because database lifecycle is managed at the filesystem level, not via SQL DDL.
- Most mature engine path with complete CRUD for tables, columns, indexes, foreign keys, records, views, and triggers.
- Check constraints are **partial**: read/create/delete are implemented; update depends on a recreate strategy.
- Functions and procedures are **not applicable** (N/A).

### MySQL / MariaDB

- Strong parity for tables, columns, indexes, foreign keys, records, views, triggers, and functions.
- Check constraints and procedures are **partial**: engine objects exist (`MySQLCheck`, `MySQLProcedure`, `MariaDBCheck`, `MariaDBProcedure`), but cross-version validation is ongoing.
- Database create/drop lifecycle methods exist at the engine level, but context/UI wiring remains read/list-oriented.

### PostgreSQL

- Core CRUD available for tables, columns, indexes, foreign keys, records, views, and triggers.
- Functions and procedures are **partial**: `PostgreSQLFunction` and `PostgreSQLProcedure` are implemented but still under broader validation.
- Check constraints are **partial**: `PostgreSQLCheck` and `get_checks()` exist; cross-version validation ongoing.
- Database create/drop lifecycle methods exist at the engine level, but context/UI wiring remains read/list-oriented.
- Schema and sequence objects have basic visibility but no CRUD layer yet.

### Shared Base Contracts

- `SQLColumn` and `SQLIndex` are enforced as abstract base classes (`abc.ABC`) with `@abstractmethod` decorators on public methods (`add`, `drop`, `rename`, `modify`, `create`, `raw_create`). Missing implementations are caught at class definition time.
- Equality comparisons (`__eq__`) on `SQLDatabase` and `SQLForeignKey` use identity-based field matching rather than inverted logic.
