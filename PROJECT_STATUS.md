# PeterSQL — Project Status

> **Last Updated:** 2026-06-05
> **Status Rule:** newly implemented features are tracked as **PARTIAL** until validated across supported versions.
> **Definition of DONE:** engine methods implemented, integration tests pass on target versions, UI workflow exists (if user-facing), no known regressions, documentation updated.

---

## Priority Matrix

| Priority | Focus | Target |
|----------|-------|--------|
| 🔴 **P0 - Validation Now** | stabilize newly added engine features | 1-2 weeks |
| 🟡 **P1 - Engine Gaps** | close remaining CRUD parity gaps | 2-4 weeks |
| 🟢 **P2 - UI Completeness** | add missing editors for exposed objects | 1-2 months |
| 🔵 **P3 - Advanced Features** | schema/security/import-export roadmap | 2-3 months |

---

## 1. Solid and Stable Areas

| Area | Status |
|------|--------|
| **SQLite Engine** | Most mature path with complete day-to-day table/record workflows. |
| **MySQL/MariaDB Core** | Strong parity for tables, columns, indexes, foreign keys, records, views, triggers, functions. |
| **UI Core Editors** | Table, columns, indexes, foreign keys, records, and view editor are operational. |
| **Multi-tab Query Editor** | Multi-tab editor with per-tab dirty tracking, autosave, cancelable execution, and configurable shortcuts. |
| **Explorer Navigation** | Databases, tables, views, triggers, procedures, functions, and events are visible in tree explorer. |
| **SSH Tunnel Support** | Implemented for MySQL, MariaDB, and PostgreSQL. |

---

## 2. Engine Capability Matrix

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ DONE | Implemented and validated in current project scope |
| 🟡 PARTIAL | Implemented but still under validation / known risk |
| ❌ NOT IMPL | Not implemented |
| ➖ N/A | Not applicable |

---

### 2.1 SQLite

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Most mature engine path. |
| View / Trigger | ✅ | ✅ | ✅ | ✅ | Fully available in engine layer. |
| Check Constraint | ✅ | ✅ | 🟡 | 🟡 | Modify path depends on recreate strategy. |
| Function / Procedure | ➖ | ➖ | ➖ | ➖ | Not applicable to SQLite. |

---

### 2.2 MySQL

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Stable core workflow. |
| View / Trigger / Function | ✅ | ✅ | ✅ | ✅ | Implemented in engine layer. |
| Check Constraint | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MySQLCheck` + `get_checks()`), validation ongoing. |
| Procedure | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MySQLProcedure` + `get_procedures()`), broader validation ongoing. |
| Database Create/Drop | 🟡 | ✅ | 🟡 | 🟡 | Engine object lifecycle methods exist; context/UI wiring still partial. |

---

### 2.3 MariaDB

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Stable core workflow. |
| View / Trigger / Function | ✅ | ✅ | ✅ | ✅ | Implemented in engine layer. |
| Check Constraint | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MariaDBCheck` + `get_checks()`), validation ongoing. |
| Procedure | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MariaDBProcedure` + `get_procedures()`), broader validation ongoing. |
| Database Create/Drop | 🟡 | ✅ | 🟡 | 🟡 | Engine object lifecycle methods exist; context/UI wiring still partial. |

---

### 2.4 PostgreSQL

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Core operations available. |
| View / Trigger | ✅ | ✅ | ✅ | ✅ | Implemented in engine layer. |
| Function | 🟡 | 🟡 | 🟡 | 🟡 | `PostgreSQLFunction` implemented, still under validation. |
| Procedure | 🟡 | 🟡 | 🟡 | 🟡 | `PostgreSQLProcedure` implemented, still under validation. |
| Check Constraint | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`PostgreSQLCheck` + `get_checks()`), validation ongoing. |
| Database Create/Drop | 🟡 | ✅ | 🟡 | 🟡 | Engine object lifecycle methods exist; context/UI wiring still partial. |
| Schema / Sequence | ❌ | 🟡 | ❌ | ❌ | Basic schema visibility exists; no CRUD layer yet. |

---

## 3. UI Capability Matrix

| Object Type | Explorer | Create UI | Edit UI | Delete UI | Notes |
|-------------|----------|-----------|---------|-----------|-------|
| Connection | ✅ | ✅ | ✅ | ✅ | Includes connection statistics and TLS state handling. |
| Database | ✅ | ❌ | ❌ | ❌ | Read/list only. |
| Table / Column / Index / Foreign Key | ✅ | ✅ | ✅ | ✅ | Main table editor workflow complete. |
| Check Constraint | ✅ | 🟡 | 🟡 | 🟡 | `TableCheckController` exists; broader multi-engine UX validation pending. |
| View | ✅ | ✅ | ✅ | ✅ | Dedicated view editor is available. |
| Trigger | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated editor yet. |
| Function | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated editor yet. |
| Procedure | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated editor yet. |
| Event | ✅ | ❌ | ❌ | ❌ | Explorer only. |
| Records | ✅ | ✅ | ✅ | ✅ | Insert/update/delete/duplicate in table records tab. |
| Query Editor | ✅ | ✅ | ✅ | ✅ | Multi-tab, cancelable execution, configurable shortcuts, autosave. |

---

## 4. Feature Backlog

### 🔴 P0 - Validation Now

- [x] **PostgreSQL Function engine implementation** (PARTIAL)
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Next:** long-run/manual workflow validation + broader regression checks.

- [x] **PostgreSQL Procedure engine implementation** (PARTIAL)
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Next:** long-run/manual workflow validation + introspection consistency checks.

- [x] **Check constraint implementations for MySQL/MariaDB/PostgreSQL** (PARTIAL)
  - **Files:** `structures/engines/mysql/`, `structures/engines/mariadb/`, `structures/engines/postgresql/`
  - **Next:** cross-version validation matrix.

- [x] **Connection reliability updates** (PARTIAL)
  - **Scope:** persistent connection statistics, empty DB password support, TLS auto-retry (MySQL/MariaDB), keyring-backed password storage.
  - **Files:** `structures/connection.py`, `windows/dialogs/connections/`, `structures/secrets.py`
  - **Next:** SSH testcontainers integration validation (currently skipped) + long-run behavioral validation.

- [x] **SQL dump/backup object-driven flow** (PARTIAL)
  - **Scope:** `SQLDatabase.dump()` generates SQL dump files through domain objects (`raw_create()`).
  - **Files:** `structures/engines/database.py`, `structures/engines/dump.py`, per-engine `database.py`
  - **Next:** cross-engine manual restore/import verification from produced dumps.

### 🟡 P1 - Engine Gaps

- [x] **MySQL Procedure implementation** (PARTIAL)
  - **Files:** `structures/engines/mysql/context.py`, `structures/engines/mysql/database.py`

- [x] **MariaDB Procedure implementation** (PARTIAL)
  - **Files:** `structures/engines/mariadb/context.py`, `structures/engines/mariadb/database.py`

- [ ] **Database lifecycle parity (context + UI wiring)**
  - **Current state:** engine database objects expose create/alter/drop, but context/UI workflow remains read/list oriented.
  - **Files:** `structures/engines/*/context.py`

### 🟢 P2 - UI Completeness

- [x] **View Create/Edit Dialog** — DONE. (`windows/main/tabs/view.py`, `helpers/sql.py`)
- [x] **Multi-tab query editor** — DONE. (`windows/main/controller.py`, `windows/main/tabs/query.py`)
- [x] **Cancelable query execution with richer result metadata** — DONE. (`windows/main/tabs/query.py`)
- [x] **Configurable keyboard shortcuts for query editor** — DONE. (`windows/main/controller.py`, `windows/dialogs/settings/`)
- [ ] **Trigger Create/Edit UI** — Explorer visibility exists, editor panel missing.
- [ ] **Function Create/Edit UI** — Explorer visibility exists, editor panel missing.
- [ ] **Procedure Create/Edit UI** — Explorer visibility exists, editor panel missing.
- [ ] **Database Create/Drop UI** — Depends on engine create/drop API parity.

### 🔵 P3 - Advanced Features

- [ ] PostgreSQL schema CRUD
- [ ] PostgreSQL sequence CRUD
- [ ] User/role management
- [ ] Privileges/grants management
- [ ] Restore + structured import/export workflows
- [ ] PostgreSQL advanced objects (materialized views, partitioning, extensions)

---

## 5. Progress Snapshot

- **P0 implemented (partial):** 5/5 — all resolved
- **P1 gaps closed:** 3/3 — all resolved
- **P2 technical audit items:** 2/2 — resolved (PostgreSQL import/type hints, ABC enforcement)
- **P2 UI tasks complete:** 4/8
- **P3 advanced tasks complete:** 0/6

---

## 6. Recently Added

- Connection passwords are now stored in the system keyring (`keyring`), removing plaintext passwords from `connections.yml`.
- Audit fixes completed: PostgreSQL alter diff handling, equality comparisons, SQLite column/drop/modify signatures, SQLite database lifecycle errors, SQLite record exception safety, VERSION sync, PostgreSQL import/type hints, and ABC enforcement for `SQLColumn`/`SQLIndex`.
- SQL autocomplete extended to INSERT / UPDATE / DELETE and string literals; parser improved with JSON and multi-table coverage.
- Table execution flow updated in the records UI.
- `row_format` and `convert_data` options added to the MySQL/MariaDB table editor.
- `windows/main/` modules restructured into subdirectories (`database/`, `table/`, `query/`) for better separation of concerns.
- Advanced cell editor replaced with a dedicated `ColumnContentDialog` for displaying and editing large cell content.
- Database options action buttons now update live when options change.
- Tree explorer preserves expanded state after a failed connection attempt.
- Multi-tab query editor with per-tab dirty tracking, autosave before execution, and close/save confirmation dialogs.
- Cancelable query execution with background thread, per-statement result rendering, and execution summary.
- Configurable keyboard shortcuts for all query editor actions (execute, stop, new tab, close tab, save, save-as).
- `save` toolbar tool is disabled when the query has no unsaved changes.
- Settings module moved to `helpers/settings.py` with restructured key schema.
- `skip_before_connect` / `skip_after_connect` support added to all engine contexts.
- Persistent connection statistics in connection model and dialog.
- Empty database password accepted in connection validation.
- Automatic TLS retry path for MySQL/MariaDB when server requires TLS.
- Unit reliability coverage for MySQL/MariaDB TLS auto-retry and SSH tunnel lifecycle contracts.
- SQL dump/backup pipeline is now object-driven via `SQLDatabase.dump()` + per-object `raw_create()`.
- CI workflow split into `test`, `update` (nightly), and `release` jobs.

---

## 7. Main Remaining Risks

- PostgreSQL Function/Procedure still need broader long-run/manual validation.
- Check constraints across MySQL/MariaDB/PostgreSQL need more cross-version coverage.
- SQL dump/backup still needs broader cross-engine manual restore validation.
- SSH tunnel integration validation with testcontainers remains blocked.
- UI parity lags engine parity for Trigger/Function/Procedure editors.

---

*This document is a living reference and should be updated whenever a PARTIAL item is validated or a new gap is identified.*