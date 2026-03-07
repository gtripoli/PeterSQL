# PeterSQL — Project Status

> **Last Updated:** 2026-03-07  
> **Validation Policy:** new engine features are marked **PARTIAL** until broader integration validation is complete.

---

## 1. Executive Summary

### ✅ Solid and Stable Areas

| Area | Status |
|------|--------|
| **SQLite Engine** | Most mature path with complete day-to-day table/record workflows. |
| **MySQL/MariaDB Core** | Strong parity for tables, columns, indexes, foreign keys, records, views, triggers, functions. |
| **UI Core Editors** | Table, columns, indexes, foreign keys, records, and view editor are operational. |
| **Explorer Navigation** | Databases, tables, views, triggers, procedures, functions, and events are visible in tree explorer. |
| **SSH Tunnel Support** | Implemented for MySQL, MariaDB, and PostgreSQL. |

### 🟡 Partial / Under Validation

| Area | Current State |
|------|---------------|
| **MySQL Procedure** | Class + CRUD methods exist, context introspection exists, integration tests added, broader validation still ongoing. |
| **MariaDB Procedure** | Class + CRUD methods exist, context introspection exists, integration tests added, broader validation still ongoing. |
| **PostgreSQL Function** | Class + CRUD methods exist, context introspection exists, still considered under validation. |
| **PostgreSQL Procedure** | Class + CRUD methods exist, context introspection exists, still considered under validation. |
| **Check Constraints (MySQL/MariaDB/PostgreSQL)** | Engine classes and introspection exist, cross-version validation still needed. |
| **Connection Reliability Features** | Persistent connection statistics, empty DB password support, and TLS auto-retry are implemented and need longer real-world validation. |

### ❌ Missing / Not Implemented

| Area | Notes |
|------|-------|
| **Function/Procedure UI Editors** | Explorer lists objects, but dedicated create/edit UI is still missing. |
| **Database Create/Drop UI** | No complete create/drop workflow across engines. |
| **Schema/Sequence Management** | PostgreSQL schema/sequence CRUD is not available. |
| **User/Role/Grants** | Not implemented for any engine. |
| **Import/Export** | Dump/restore and structured data import/export not implemented. |

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
| Database Create/Drop | ❌ | ✅ | ❌ | ❌ | Read-only listing in context. |

---

### 2.3 MariaDB

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Stable core workflow. |
| View / Trigger / Function | ✅ | ✅ | ✅ | ✅ | Implemented in engine layer. |
| Check Constraint | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MariaDBCheck` + `get_checks()`), validation ongoing. |
| Procedure | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`MariaDBProcedure` + `get_procedures()`), broader validation ongoing. |
| Database Create/Drop | ❌ | ✅ | ❌ | ❌ | Read-only listing in context. |

---

### 2.4 PostgreSQL

| Object | Create | Read | Update | Delete | Notes |
|--------|--------|------|--------|--------|-------|
| Table / Column / Index / FK / Record | ✅ | ✅ | ✅ | ✅ | Core operations available. |
| View / Trigger | ✅ | ✅ | ✅ | ✅ | Implemented in engine layer. |
| Function | 🟡 | 🟡 | 🟡 | 🟡 | `PostgreSQLFunction` implemented, still under validation. |
| Procedure | 🟡 | 🟡 | 🟡 | 🟡 | `PostgreSQLProcedure` implemented, still under validation. |
| Check Constraint | 🟡 | 🟡 | 🟡 | 🟡 | Implemented (`PostgreSQLCheck` + `get_checks()`), validation ongoing. |
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
| Trigger | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated trigger editor panel yet. |
| Function | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated editor yet. |
| Procedure | ✅ | ❌ | ❌ | ❌ | Explorer only; no dedicated editor yet. |
| Event | ✅ | ❌ | ❌ | ❌ | Explorer only. |
| Records | ✅ | ✅ | ✅ | ✅ | Insert/update/delete/duplicate in table records tab. |

---

## 4. Cross-Cutting Notes

### Recently Added

- Persistent connection statistics in connection model and dialog.
- Empty database password accepted in connection validation.
- Automatic TLS retry path for MySQL/MariaDB when server requires TLS.
- CI workflow split into `test`, `update` (nightly), and `release` jobs.

### Main Remaining Risks

- Newly implemented PostgreSQL Function/Procedure paths need broader integration validation.
- Check constraints across MySQL/MariaDB/PostgreSQL need more cross-version coverage.
- UI parity lags engine parity for Trigger/Function/Procedure editors.

---

## 5. Actionable Backlog (High Signal)

### Priority A — Validate Newly Implemented Features

1. PostgreSQL Function integration validation (all supported PG variants).
2. PostgreSQL Procedure integration validation (all supported PG variants).
3. Check constraints validation matrix for MySQL, MariaDB, PostgreSQL.
4. Connection statistics + TLS auto-retry robustness checks.

### Priority B — Close Engine Gaps

1. Database create/drop methods in engine contexts.

### Priority C — UI Completeness

1. Trigger create/edit UI.
2. Function create/edit UI.
3. Procedure create/edit UI.

### Priority D — Future Platform Features

1. PostgreSQL schema CRUD.
2. PostgreSQL sequence CRUD.
3. User/role/grants management.
4. Import/export workflows.

---

## 6. Definition of DONE

A capability is treated as **DONE** only when:

- Engine methods are implemented (`create/read/update/delete` where applicable).
- Integration tests pass on target engine versions.
- UI workflow exists (if feature is user-facing in explorer).
- No known regression in existing suites.
- Documentation is updated (`README`, `PROJECT_STATUS`, `ROADMAP`).
