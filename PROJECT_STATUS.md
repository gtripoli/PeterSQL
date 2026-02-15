# PeterSQL — Project Status

> **Last Updated:** 2026-02-11  
> **Version:** Based on code inspection

---

## 1. Executive Summary

### ✅ What is Solid and Complete

| Area | Status |
|------|--------|
| **SQLite Engine** | Most mature. Full CRUD for Table, Column, Index, Foreign Key, Record, View, Trigger. Check constraints supported. |
| **MySQL/MariaDB Engines** | Strong parity. Full CRUD for Table, Column, Index, Foreign Key, Record, View, Trigger, Function. |
| **Connection Management** | SSH tunnel support (MySQL, MariaDB, PostgreSQL), session lifecycle, multi-database navigation. |
| **UI Explorer** | Tree navigation for databases, tables, views, triggers, procedures, functions, events. |
| **Table Editor** | Column editor, index editor, foreign key editor with full CRUD. |
| **Record Editor** | Insert, update, delete, duplicate records with filtering support. |
| **SQL Autocomplete** | Keywords, functions, table/column names. |
| **SSH Tunnel Testing** | Comprehensive test coverage for MySQL, MariaDB, and PostgreSQL SSH tunnel functionality. |

### ⚠️ Partially Implemented (Risky)

| Area | Issue |
|------|-------|
| **PostgreSQL Engine** | Schema support incomplete. No Function class. |
| **Procedure/Event UI** | Explorer shows them but no editor panels exist. |

### ❌ Completely Missing

| Area | Notes |
|------|-------|
| **Schema/Namespace Management** | PostgreSQL schemas visible but no CRUD. |
| **User/Role Management** | Not implemented for any engine. |
| **Privileges/Grants** | Not implemented. |
| **Sequences** | Not implemented (PostgreSQL). |
| **Materialized Views** | Not implemented. |
| **Partitioning** | Not implemented. |
| **Import/Export/Dump** | Not implemented. |
| **Database Create/Drop** | Not implemented in UI. |

---

## 2. Engine Capability Matrix

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ DONE | Fully implemented and tested |
| 🟡 PARTIAL | Implemented but incomplete or has issues |
| ❌ NOT IMPL | Not implemented |
| ➖ N/A | Not applicable to this engine |

---

### 2.1 SQLite

| Object Type | Create | Read | Update | Delete | Notes | Evidence |
|-------------|--------|------|--------|--------|-------|----------|
| **Database** | ➖ | ✅ | ➖ | ➖ | Single file = single DB | `SQLiteContext.get_databases()` |
| **Table** | ✅ | ✅ | ✅ | ✅ | Full recreate strategy for ALTER | `SQLiteTable.create/alter/drop()` |
| **Column** | ✅ | ✅ | ✅ | ✅ | Via table recreate | `SQLiteColumn.add/modify/rename/drop()` |
| **Index** | ✅ | ✅ | ✅ | ✅ | PRIMARY handled in table | `SQLiteIndex.create/drop/modify()` |
| **Primary Key** | ✅ | ✅ | ✅ | ✅ | Inline or table constraint | `SQLiteTable.raw_create()` |
| **Foreign Key** | ✅ | ✅ | ✅ | ✅ | Table-level constraints | `SQLiteForeignKey` (passive) |
| **Unique Constraint** | ✅ | ✅ | ✅ | ✅ | Via CREATE UNIQUE INDEX | `SQLiteIndex` |
| **Check Constraint** | ✅ | ✅ | 🟡 | 🟡 | Read works, modify via recreate | `SQLiteCheck`, `get_checks()` |
| **Default** | ✅ | ✅ | ✅ | ✅ | Column attribute | `SQLiteColumn.server_default` |
| **View** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `SQLiteView` |
| **Trigger** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `SQLiteTrigger` |
| **Function** | ➖ | ➖ | ➖ | ➖ | SQLite has no stored functions | — |
| **Procedure** | ➖ | ➖ | ➖ | ➖ | SQLite has no procedures | — |
| **Records** | ✅ | ✅ | ✅ | ✅ | Full DML | `SQLiteRecord.insert/update/delete()` |
| **Transactions** | ✅ | ➖ | ➖ | ➖ | Context manager | `AbstractContext.transaction()` |
| **Collation** | ✅ | ✅ | ➖ | ➖ | Static list | `COLLATIONS` in `__init__.py` |

---

### 2.2 MySQL

| Object Type | Create | Read | Update | Delete | Notes | Evidence |
|-------------|--------|------|--------|--------|-------|----------|
| **Database** | ❌ | ✅ | ❌ | ❌ | Read-only listing | `MySQLContext.get_databases()` |
| **Table** | ✅ | ✅ | ✅ | ✅ | Full support | `MySQLTable` |
| **Column** | ✅ | ✅ | ✅ | ✅ | ADD/MODIFY/RENAME/DROP | `MySQLColumn` |
| **Index** | ✅ | ✅ | ✅ | ✅ | PRIMARY, UNIQUE, INDEX | `MySQLIndex` |
| **Primary Key** | ✅ | ✅ | ✅ | ✅ | Via index | `MySQLIndexType.PRIMARY` |
| **Foreign Key** | ✅ | ✅ | ✅ | ✅ | Full support | `MySQLForeignKey` |
| **Unique Constraint** | ✅ | ✅ | ✅ | ✅ | Via index | `MySQLIndexType.UNIQUE` |
| **Check Constraint** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |
| **Default** | ✅ | ✅ | ✅ | ✅ | Column attribute | `MySQLColumn.server_default` |
| **View** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `MySQLView` |
| **Trigger** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `MySQLTrigger` |
| **Function** | ✅ | ✅ | ✅ | ✅ | Full support | `MySQLFunction` |
| **Procedure** | ❌ | ❌ | ❌ | ❌ | Class exists but empty | `SQLProcedure` base only |
| **Records** | ✅ | ✅ | ✅ | ✅ | Full DML | `MySQLRecord` |
| **Transactions** | ✅ | ➖ | ➖ | ➖ | Context manager | `AbstractContext.transaction()` |
| **Collation** | ✅ | ✅ | ➖ | ➖ | Dynamic from server | `_on_connect()` |
| **Engine** | ✅ | ✅ | ✅ | ➖ | InnoDB, MyISAM, etc. | `MySQLTable.alter_engine()` |

---

### 2.3 MariaDB

| Object Type | Create | Read | Update | Delete | Notes | Evidence |
|-------------|--------|------|--------|--------|-------|----------|
| **Database** | ❌ | ✅ | ❌ | ❌ | Read-only listing | `MariaDBContext.get_databases()` |
| **Table** | ✅ | ✅ | ✅ | ✅ | Full support | `MariaDBTable` |
| **Column** | ✅ | ✅ | ✅ | ✅ | ADD/MODIFY/CHANGE/DROP | `MariaDBColumn` |
| **Index** | ✅ | ✅ | ✅ | ✅ | PRIMARY, UNIQUE, INDEX | `MariaDBIndex` |
| **Primary Key** | ✅ | ✅ | ✅ | ✅ | Via index | `MariaDBIndexType.PRIMARY` |
| **Foreign Key** | ✅ | ✅ | ✅ | ✅ | Full support | `MariaDBForeignKey` |
| **Unique Constraint** | ✅ | ✅ | ✅ | ✅ | Via index | `MariaDBIndexType.UNIQUE` |
| **Check Constraint** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |
| **Default** | ✅ | ✅ | ✅ | ✅ | Column attribute | `MariaDBColumn.server_default` |
| **View** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `MariaDBView` |
| **Trigger** | ✅ | ✅ | ✅ | ✅ | `alter()` implemented | `MariaDBTrigger` |
| **Function** | ✅ | ✅ | ✅ | ✅ | Full support | `MariaDBFunction` |
| **Procedure** | ❌ | ❌ | ❌ | ❌ | Class exists but empty | `SQLProcedure` base only |
| **Records** | ✅ | ✅ | ✅ | ✅ | Full DML | `MariaDBRecord` |
| **Transactions** | ✅ | ➖ | ➖ | ➖ | Context manager | `AbstractContext.transaction()` |
| **Collation** | ✅ | ✅ | ➖ | ➖ | Dynamic from server | `_on_connect()` |
| **Engine** | ✅ | ✅ | ✅ | ➖ | InnoDB, Aria, etc. | `MariaDBTable.alter_engine()` |

---

### 2.4 PostgreSQL

| Object Type | Create | Read | Update | Delete | Notes | Evidence |
|-------------|--------|------|--------|--------|-------|----------|
| **Database** | ❌ | ✅ | ❌ | ❌ | Read-only listing | `PostgreSQLContext.get_databases()` |
| **Schema** | ❌ | 🟡 | ❌ | ❌ | Read via table.schema | `PostgreSQLTable.schema` |
| **Table** | ✅ | ✅ | ✅ | ✅ | Full support | `PostgreSQLTable` |
| **Column** | ✅ | ✅ | ✅ | ✅ | Via table alter | `PostgreSQLColumn` (passive) |
| **Index** | ✅ | ✅ | ✅ | ✅ | PRIMARY, UNIQUE, INDEX, BTREE, etc. | `PostgreSQLIndex` |
| **Primary Key** | ✅ | ✅ | ✅ | ✅ | Via index | `PostgreSQLIndexType.PRIMARY` |
| **Foreign Key** | ✅ | ✅ | ✅ | ✅ | Full support | `PostgreSQLForeignKey` |
| **Unique Constraint** | ✅ | ✅ | ✅ | ✅ | Via index | `PostgreSQLIndexType.UNIQUE` |
| **Check Constraint** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |
| **Default** | ✅ | ✅ | 🟡 | 🟡 | Column attribute | `PostgreSQLColumn.server_default` |
| **View** | ✅ | 🟡 | ✅ | ✅ | `alter()` implemented | `PostgreSQLView` |
| **Trigger** | ✅ | ✅ | ✅ | ✅ | Full support | `PostgreSQLTrigger` |
| **Function** | ❌ | ❌ | ❌ | ❌ | Class not implemented | — |
| **Procedure** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |
| **Sequence** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |
| **Records** | ✅ | ✅ | ✅ | ✅ | Uses parameterized queries | `PostgreSQLRecord` |
| **Transactions** | ✅ | ➖ | ➖ | ➖ | Context manager | `AbstractContext.transaction()` |
| **Collation** | ✅ | ✅ | ➖ | ➖ | Dynamic from server | `_on_connect()` |
| **Custom Types/Enum** | ❌ | ✅ | ❌ | ❌ | Read-only introspection | `_load_custom_types()` |
| **Extension** | ❌ | ❌ | ❌ | ❌ | Not implemented | — |

---

## 3. UI Capability Matrix

| Object Type | Explorer | Create UI | Read/List UI | Update UI | Delete UI | Notes |
|-------------|----------|-----------|--------------|-----------|-----------|-------|
| **Connection** | ✅ | ✅ | ✅ | ✅ | ✅ | `ConnectionsManager` |
| **Database** | ✅ | ❌ | ✅ | ❌ | ❌ | List only |
| **Table** | ✅ | ✅ | ✅ | ✅ | ✅ | Full editor | 
| **Column** | ✅ | ✅ | ✅ | ✅ | ✅ | `TableColumnsController` |
| **Index** | ✅ | ✅ | ✅ | ✅ | ✅ | `TableIndexController` |
| **Foreign Key** | ✅ | ✅ | ✅ | ✅ | ✅ | `TableForeignKeyController` |
| **Check Constraint** | ✅ | 🟡 | ✅ | 🟡 | 🟡 | `TableCheckController` (SQLite only) |
| **View** | ✅ | ❌ | ✅ | ❌ | ✅ | List + delete only |
| **Trigger** | ✅ | ❌ | ✅ | ❌ | ❌ | List only |
| **Function** | ✅ | ❌ | ❌ | ❌ | ❌ | Explorer shows, no editor |
| **Procedure** | ✅ | ❌ | ❌ | ❌ | ❌ | Explorer shows, no editor |
| **Event** | ✅ | ❌ | ❌ | ❌ | ❌ | Explorer shows, no editor |
| **Records** | ✅ | ✅ | ✅ | ✅ | ✅ | `TableRecordsController` |
| **SQL Query** | ✅ | ✅ | ✅ | ➖ | ➖ | Query editor with autocomplete |

### UI Feature Support

| Feature | Status | Evidence |
|---------|--------|----------|
| **Tree Explorer** | ✅ DONE | `TreeExplorerController` |
| **Table Editor** | ✅ DONE | `EditTableModel`, notebook tabs |
| **Column Editor** | ✅ DONE | `TableColumnsController` |
| **Index Editor** | ✅ DONE | `TableIndexController` |
| **Foreign Key Editor** | ✅ DONE | `TableForeignKeyController` |
| **Check Editor** | 🟡 PARTIAL | `TableCheckController` (SQLite) |
| **Record Editor** | ✅ DONE | `TableRecordsController` |
| **SQL Autocomplete** | ✅ DONE | `SQLAutoCompleteController` |
| **Query Log** | ✅ DONE | `sql_query_logs` StyledTextCtrl |
| **DDL Preview** | ✅ DONE | `sql_create_table` with sqlglot |
| **Theme Support** | ✅ DONE | `ThemeManager`, system color change |
| **View Editor** | ❌ NOT IMPL | Panel exists but no create/edit |
| **Trigger Editor** | ❌ NOT IMPL | Panel exists but no create/edit |
| **Function Editor** | ❌ NOT IMPL | No panel |
| **Procedure Editor** | ❌ NOT IMPL | No panel |

---

## 4. Cross-Cutting Gaps

### Features Blocked by Missing Introspection

| Feature | Blocked By |
|---------|------------|
| PostgreSQL Function UI | No `PostgreSQLFunction` class |
| Check Constraint UI (MySQL/MariaDB) | No `get_checks()` implementation |
| Sequence management | No `SQLSequence` class |
| Schema management | No `SQLSchema` class |

### Engine Inconsistencies

| Issue | Engines Affected |
|-------|------------------|
| Check constraints | MySQL, MariaDB, PostgreSQL missing |

### UI Features Waiting on Engine Support

| UI Feature | Waiting On |
|------------|------------|
| View create/edit dialog | UI implementation needed |
| Trigger create/edit dialog | UI implementation needed |
| Function editor | PostgreSQL `PostgreSQLFunction` class |
| Database create/drop | All engines need `create_database()` |

---

## 5. Actionable Backlog

### Priority 1: Critical Fixes

| Item | Object | Operation | Engine(s) | What's Missing |
|------|--------|-----------|-----------|----------------|
| 1.1 | Function | All | PostgreSQL | `PostgreSQLFunction` class missing |

### Priority 2: Engine Parity

| Item | Object | Operation | Engine(s) | What's Missing |
|------|--------|-----------|-----------|----------------|
| 2.1 | Check Constraint | CRUD | MySQL, MariaDB, PostgreSQL | `get_checks()`, `SQLCheck` subclass |
| 2.2 | Procedure | CRUD | All | Only base class exists |
| 2.3 | SSH Tunnel | Connect | MariaDB, PostgreSQL | Only MySQL has it |

### Priority 3: UI Completeness

| Item | Object | Operation | What's Missing |
|------|--------|-----------|----------------|
| 3.1 | View | Create/Edit | Dialog and controller |
| 3.2 | Trigger | Create/Edit | Dialog and controller |
| 3.3 | Function | All | Panel, dialog, controller |
| 3.4 | Procedure | All | Panel, dialog, controller |
| 3.5 | Database | Create/Drop | Dialog and engine methods |

### Priority 4: New Features

| Item | Object | Operation | What's Missing |
|------|--------|-----------|----------------|
| 4.1 | Schema | CRUD | `SQLSchema` class, PostgreSQL support |
| 4.2 | Sequence | CRUD | `SQLSequence` class, PostgreSQL support |
| 4.3 | User/Role | CRUD | `SQLUser`, `SQLRole` classes |
| 4.4 | Privileges | CRUD | `SQLGrant` class |
| 4.5 | Import/Export | Execute | Dump/restore functionality |

---

## 6. Definition of DONE

A CRUD capability is considered **DONE** when:

- [ ] **Engine Layer**
  - [ ] Dataclass exists with all required fields
  - [ ] `create()` method implemented and tested
  - [ ] `read()`/`get_*()` method returns correct data
  - [ ] `update()`/`alter()` method handles all field changes
  - [ ] `delete()`/`drop()` method works correctly
  - [ ] Integration test passes with real database

- [ ] **UI Layer**
  - [ ] Object appears in Explorer tree
  - [ ] Create dialog/panel exists and is functional
  - [ ] Edit dialog/panel exists and is functional
  - [ ] Delete confirmation and action works
  - [ ] Changes reflect immediately in Explorer

- [ ] **Cross-Cutting**
  - [ ] Error handling with user-friendly messages
  - [ ] Transaction support where applicable
  - [ ] No regressions in existing tests
  - [ ] Code follows `CODE_STYLE.md`

---

## Appendix: File Reference

### Engine Layer Files

| Engine | Context | Database | Builder | DataType | IndexType |
|--------|---------|----------|---------|----------|-----------|
| SQLite | `sqlite/context.py` | `sqlite/database.py` | `sqlite/builder.py` | `sqlite/datatype.py` | `sqlite/indextype.py` |
| MySQL | `mysql/context.py` | `mysql/database.py` | `mysql/builder.py` | `mysql/datatype.py` | `mysql/indextype.py` |
| MariaDB | `mariadb/context.py` | `mariadb/database.py` | `mariadb/builder.py` | `mariadb/datatype.py` | `mariadb/indextype.py` |
| PostgreSQL | `postgresql/context.py` | `postgresql/database.py` | `postgresql/builder.py` | `postgresql/datatype.py` | `postgresql/indextype.py` |

### UI Layer Files

| Component | File |
|-----------|------|
| Main Frame | `windows/main/main_frame.py` |
| Explorer | `windows/main/explorer.py` |
| Column Editor | `windows/main/column.py` |
| Index Editor | `windows/main/index.py` |
| Foreign Key Editor | `windows/main/foreign_key.py` |
| Check Editor | `windows/main/check.py` |
| Record Editor | `windows/main/records.py` |
| Table Model | `windows/main/table.py` |
| Database List | `windows/main/database.py` |
| Connection Manager | `windows/connections/manager.py` |
