# PeterSQL — Development Roadmap

> **Last Updated:** 2026-03-10  
> **Status Rule:** newly implemented features are tracked as **PARTIAL** until validated across supported versions.

---

## 🎯 Overview

This roadmap reflects the current project state and separates:

1. features already implemented but still under validation,
2. true implementation gaps,
3. UI parity work.

---

## 📊 Priority Matrix

| Priority | Focus | Target |
|----------|-------|--------|
| 🔴 **P0 - Validation Now** | stabilize newly added engine features | 1-2 weeks |
| 🟡 **P1 - Engine Gaps** | close remaining CRUD parity gaps | 2-4 weeks |
| 🟢 **P2 - UI Completeness** | add missing editors for exposed objects | 1-2 months |
| 🔵 **P3 - Advanced Features** | schema/security/import-export roadmap | 2-3 months |

---

## 🔴 P0 - Validation Now

### Implemented recently (still PARTIAL)

- [x] **PostgreSQL Function engine implementation** (PARTIAL)
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Status:** integration coverage for create/alter/drop is now in place across supported PostgreSQL variants.
  - **Next:** long-run/manual workflow validation + broader regression checks.

- [x] **PostgreSQL Procedure engine implementation** (PARTIAL)
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Status:** integration coverage for create/alter/drop is now in place across supported PostgreSQL variants.
  - **Next:** long-run/manual workflow validation + introspection consistency checks.

- [x] **Check constraint implementations for MySQL/MariaDB/PostgreSQL** (PARTIAL)
  - **Files:**
    - `structures/engines/mysql/database.py`, `structures/engines/mysql/context.py`
    - `structures/engines/mariadb/database.py`, `structures/engines/mariadb/context.py`
    - `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Next:** cross-version validation matrix.

- [x] **Connection reliability updates** (PARTIAL)
  - **Scope:** persistent connection statistics, empty DB password support, TLS auto-retry (MySQL/MariaDB).
  - **Files:**
    - `structures/connection.py`
    - `windows/dialogs/connections/model.py`
    - `windows/dialogs/connections/view.py`
  - **Validation status:** unit tests now cover connection statistics updates, MySQL/MariaDB TLS retry behavior, and SSH tunnel context lifecycle contracts.
  - **Next:** unblock and run SSH testcontainers integration validation (currently skipped) + long-run behavioral validation.

- [x] **SQL dump/backup object-driven flow** (PARTIAL)
  - **Scope:** `SQLDatabase.dump()` now generates SQL dump files through domain objects (`raw_create()`), with ordered schema + records sections.
  - **Files:**
    - `structures/engines/database.py`
    - `structures/engines/dump.py`
    - `structures/engines/mysql/database.py`
    - `structures/engines/mariadb/database.py`
    - `structures/engines/postgresql/database.py`
    - `structures/engines/sqlite/database.py`
  - **Validation status:** unit suite is green in serial and xdist runs.
  - **Next:** cross-engine manual restore/import verification from produced dumps.

---

## 🟡 P1 - Engine Gaps

- [x] **MySQL Procedure implementation** (PARTIAL)
  - **Status:** Engine CRUD + introspection implemented, integration tests added.
  - **Files:** `structures/engines/mysql/context.py`, `structures/engines/mysql/database.py`, `tests/engines/mysql/test_integration_suite.py`, `tests/engines/base_procedure_tests.py`

- [x] **MariaDB Procedure implementation** (PARTIAL)
  - **Status:** Engine CRUD + introspection implemented, integration tests added.
  - **Files:** `structures/engines/mariadb/context.py`, `structures/engines/mariadb/database.py`, `tests/engines/mariadb/test_integration_suite.py`, `tests/engines/base_procedure_tests.py`

- [ ] **Database lifecycle parity (context + UI wiring)**
  - **Current state:** engine database objects expose create/alter/drop, but context/UI workflow remains read/list oriented.
  - **Files:** `structures/engines/*/context.py`

---

## 🟢 P2 - UI Completeness

- [x] **View Create/Edit Dialog**
  - **Status:** DONE
  - **Files:** `windows/main/tabs/view.py`, `helpers/sql.py`

- [ ] **Trigger Create/Edit UI**
  - **Current state:** explorer visibility exists, editor panel missing.

- [ ] **Function Create/Edit UI**
  - **Current state:** explorer visibility exists, editor panel missing.

- [ ] **Procedure Create/Edit UI**
  - **Current state:** explorer visibility exists, editor panel missing.

- [ ] **Database Create/Drop UI**
  - **Dependency:** engine create/drop API parity.

---

## 🔵 P3 - Advanced Features

- [ ] PostgreSQL schema CRUD
- [ ] PostgreSQL sequence CRUD
- [ ] User/role management
- [ ] Privileges/grants management
- [ ] Restore + structured import/export workflows
- [ ] PostgreSQL advanced objects (materialized views, partitioning, extensions)

---

## 🛠️ Validation and Completion Criteria

Before moving a PARTIAL item to DONE:

- [ ] Integration tests pass on supported versions.
- [ ] Behavior is stable in repeated manual workflows.
- [ ] No regressions in current engine/UI suites.
- [ ] Documentation is aligned (`README`, `PROJECT_STATUS`, `ROADMAP`).

---

## 📈 Progress Snapshot

### Current Status

- **P0 implemented (partial):** 5/5
- **P1 gaps closed:** 2/3
- **P2 UI tasks complete:** 1/5
- **P3 advanced tasks complete:** 0/6

### Recent Highlights

- PostgreSQL Function and Procedure engine classes added.
- PostgreSQL Function/Procedure integration tests now include ALTER coverage (create/alter/drop).
- Check constraint support added for MySQL, MariaDB, PostgreSQL.
- Connection statistics and TLS auto-retry behavior added in connection manager.
- SQL dump/backup pipeline refactored to object-driven generation (`SQLDatabase.dump()` + `raw_create()`).
- SSH tunnel unit contract tests added for context lifecycle and process stop behavior.
- CI workflow split into test/nightly-update/release lanes.

---

*This roadmap is a living document and should be updated whenever a PARTIAL item is validated or a new gap is identified.*
