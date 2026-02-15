# PeterSQL — Development Roadmap

> **Last Updated:** 2026-02-11  
> **Based on:** PROJECT_STATUS.md analysis

---

## 🎯 Overview

This roadmap organizes remaining development tasks by priority, difficulty, and component. Tasks are structured to be easily trackable with checkboxes and notes.

---

## 📊 Priority Matrix

| Priority | Impact | Effort | Target |
|----------|--------|--------|--------|
| 🔴 **P0 - Critical** | High | Low- Medium | 1-2 weeks |
| 🟡 **P1 - High** | High | Medium | 2-4 weeks |
| 🟢 **P2 - Medium** | Medium | Medium-High | 1-2 months |
| 🔵 **P3 - Low** | Low | High | 2-3 months |

---

## 🔴 P0 - Critical Fixes (1-2 weeks)

### Engine Layer

- [ ] **PostgreSQLFunction Class Implementation**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🟢 Medium
  - **Files:** `structures/engines/postgresql/database.py`
  - **Notes:**
    - Create full CRUD methods (create, read, update, drop)
    - Follow pattern from MySQLFunction/MariaDBFunction
    - Add parameters, returns, deterministic fields
    - Test with real PostgreSQL functions

---

## 🟡 P1 - High Priority (2-4 weeks)

### Engine Parity

#### Check Constraints Implementation
- [ ] **MySQL Check Constraints**
  - **Engine:** MySQL
  - **Difficulty:** 🟢 Medium
  - **Files:** `structures/engines/mysql/database.py`, `structures/engines/mysql/context.py`
  - **Notes:**
    - Implement `get_checks()` method in context
    - Create `MySQLCheck` class
    - Add check constraint introspection queries

- [ ] **MariaDB Check Constraints**
  - **Engine:** MariaDB
  - **Difficulty:** 🟢 Medium
  - **Files:** `structures/engines/mariadb/database.py`, `structures/engines/mariadb/context.py`
  - **Notes:**
    - Similar to MySQL implementation
    - Test with MariaDB-specific syntax

- [ ] **PostgreSQL Check Constraints**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🟢 Medium
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Notes:**
    - Implement `get_checks()` method
    - Create `PostgreSQLCheck` class
    - Handle PostgreSQL check constraint syntax

#### SSH Tunnel Support
- [ ] **MariaDB SSH Tunnel**
  - **Engine:** MariaDB
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `structures/ssh_tunnel.py`, `structures/engines/mariadb/context.py`
  - **Notes:**
    - Follow MySQL SSH tunnel pattern
    - Test with different SSH configurations
    - Add connection timeout handling

- [ ] **PostgreSQL SSH Tunnel**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `structures/ssh_tunnel.py`, `structures/engines/postgresql/context.py`
  - **Notes:**
    - Similar to MariaDB implementation
    - Consider PostgreSQL-specific port requirements

### Procedure Support
- [ ] **Procedure Implementation (All Engines)**
  - **Engine:** MySQL, MariaDB, PostgreSQL
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `structures/engines/*/database.py`
  - **Notes:**
    - Extend base `SQLProcedure` class
    - Implement CRUD methods for each engine
    - Add parameter handling
    - Test with stored procedures

---

## 🟢 P2 - Medium Priority (1-2 months)

### UI Layer - Core Editors

#### View Editor
- [ ] **View Create/Edit Dialog**
  - **UI Component:** View Editor
  - **Difficulty:** 🟢 Medium
  - **Files:** `windows/main/view.py` (new), `windows/main/explorer.py`
  - **Notes:**
    - Create dialog similar to table editor
    - SQL editor with syntax highlighting
    - Preview functionality
    - Validation for view SQL

#### Trigger Editor
- [ ] **Trigger Create/Edit Dialog**
  - **UI Component:** Trigger Editor
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `windows/main/trigger.py` (new), `windows/main/explorer.py`
  - **Notes:**
    - Complex form with timing/event options
    - SQL editor for trigger body
    - Database-specific syntax support
    - Test trigger validation

#### Function Editor
- [ ] **Function Create/Edit Panel**
  - **UI Component:** Function Editor
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `windows/main/function.py` (new)
  - **Notes:**
    - Parameter definition interface
    - Return type selection
    - SQL editor for function body
    - Database-specific options (deterministic, etc.)

#### Procedure Editor
- [ ] **Procedure Create/Edit Panel**
  - **UI Component:** Procedure Editor
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `windows/main/procedure.py` (new)
  - **Notes:**
    - Similar to function editor
    - IN/OUT/INOUT parameter handling
    - SQL editor for procedure body

### Database Management
- [ ] **Database Create/Drop Operations**
  - **UI Component:** Database Management
  - **Difficulty:** 🟢 Medium
  - **Files:** `windows/main/database.py`, `structures/engines/*/context.py`
  - **Notes:**
    - Implement `create_database()` in all engines
    - Add database creation dialog
    - Database drop confirmation
    - Permission checking

---

## 🔵 P3 - Low Priority (2-3 months)

### SSH Tunnel Testing & Performance

#### SSH Tunnel Test Coverage
- [x] **MySQL SSH Tunnel Tests** ✅ COMPLETED
  - **Engine:** MySQL
  - **Difficulty:** 🟢 Medium
  - **Files:** `tests/engines/mysql/test_integration.py`
  - **Status:** ✅ Complete
  - **Notes:**
    - Basic CRUD operations through SSH tunnel
    - Transaction support testing
    - Error handling validation
    - Integration with testcontainers

- [x] **MariaDB SSH Tunnel Tests** ✅ COMPLETED
  - **Engine:** MariaDB
  - **Difficulty:** 🟢 Medium
  - **Files:** `tests/engines/mariadb/test_integration.py`
  - **Status:** ✅ Complete
  - **Notes:**
    - Basic CRUD operations through SSH tunnel
    - Transaction support testing
    - Error handling validation
    - Integration with testcontainers
    - SSH tunnel implementation completed

- [x] **PostgreSQL SSH Tunnel Tests** ✅ COMPLETED
  - **Engine:** PostgreSQL
  - **Difficulty:** 🟢 Medium
  - **Files:** `tests/engines/postgresql/test_integration.py`
  - **Status:** ✅ Complete
  - **Notes:**
    - Basic CRUD operations through SSH tunnel
    - Transaction support testing
    - Error handling validation
    - Integration with testcontainers
    - SSH tunnel implementation completed

#### SSH Tunnel Performance & Reliability
- [ ] **SSH Tunnel Performance Benchmarks**
  - **Feature:** Performance Testing
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `tests/performance/ssh_tunnel_performance.py`
  - **Notes:**
    - Latency measurements
    - Throughput testing
    - Connection pooling impact
    - Resource usage monitoring

- [ ] **SSH Tunnel Error Recovery**
  - **Feature:** Reliability Testing
  - **Difficulty:** 🟡 Medium-High
  - **Files:** `tests/engines/*/test_ssh_tunnel_resilience.py`
  - **Notes:**
    - Network interruption scenarios
    - Connection timeout handling
    - Automatic reconnection testing
    - Graceful degradation

### Advanced Features

#### Schema Management (PostgreSQL)
- [ ] **PostgreSQL Schema CRUD**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🔵 High
  - **Files:** `structures/engines/postgresql/database.py`, `structures/engines/postgresql/context.py`
  - **Notes:**
    - Create `SQLSchema` base class
    - Implement `PostgreSQLSchema` class
    - Schema operations in UI
    - Object movement between schemas

#### Sequence Management (PostgreSQL)
- [ ] **PostgreSQL Sequence CRUD**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🔵 High
  - **Files:** `structures/engines/postgresql/database.py` (new classes)
  - **Notes:**
    - Create `SQLSequence` base class
    - Implement `PostgreSQLSequence`
    - Sequence editor in UI
    - Integration with table columns

#### User/Role Management
- [ ] **User/Role CRUD (All Engines)**
  - **Engine:** All
  - **Difficulty:** 🔵 High
  - **Files:** New files in each engine directory
  - **Notes:**
    - Create `SQLUser`, `SQLRole` base classes
    - Engine-specific implementations
    - User management UI
    - Permission handling

#### Privileges/Grants
- [ ] **Grant Management System**
  - **Engine:** All
  - **Difficulty:** 🔵 High
  - **Files:** New files, UI components
  - **Notes:**
    - Create `SQLGrant` class
    - Grant/revoke operations
    - Permission matrix UI
    - Role-based access control

### Import/Export Features
- [ ] **Database Dump/Restore**
  - **Feature:** Import/Export
  - **Difficulty:** 🔵 High
  - **Files:** New scripts, UI components
  - **Notes:**
    - Support for multiple dump formats
    - Progress indicators
    - Compression options
    - Scheduled exports

- [ ] **Data Import/Export**
  - **Feature:** Data Transfer
  - **Difficulty:** 🔵 High
  - **Files:** New files, UI components
  - **Notes:**
    - CSV/JSON/XML support
    - Bulk operations
    - Data mapping interface
    - Import validation

### Advanced PostgreSQL Features
- [ ] **Materialized Views**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🔵 High
  - **Notes:**
    - Refresh scheduling
    - Performance monitoring

- [ ] **Table Partitioning**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🔵 High
  - **Notes:**
    - Partition strategy UI
    - Partition management

- [ ] **Extensions Management**
  - **Engine:** PostgreSQL
  - **Difficulty:** 🔵 High
  - **Notes:**
    - Extension installation/removal
    - Version management

---

## 🛠️ Development Guidelines

### Task Completion Criteria

For each task, ensure:

- [ ] **Engine Layer**
  - [ ] Dataclass exists with all required fields
  - [ ] CRUD methods implemented and tested
  - [ ] Integration tests pass with real database
  - [ ] Error handling with user-friendly messages

- [ ] **UI Layer**
  - [ ] Object appears in Explorer tree
  - [ ] Create/edit/delete dialogs functional
  - [ ] Changes reflect immediately in UI
  - [ ] Validation and error handling

- [ ] **Cross-Cutting**
  - [ ] Code follows `CODE_STYLE.md`
  - [ ] No regressions in existing tests
  - [ ] Documentation updated
  - [ ] Transaction support where applicable

### Testing Strategy

- **Unit Tests:** Each new class/method
- **Integration Tests:** Real database operations
- **UI Tests:** User interaction workflows
- **Performance Tests:** Large dataset handling

### Review Process

1. **Code Review:** Peer review required
2. **Testing:** All tests must pass
3. **Documentation:** Update relevant docs
4. **Changelog:** Add changes to CHANGELOG.md

---

## 📈 Progress Tracking

### Current Status

- **P0 Tasks:** 1/1 completed (100%)
- **P1 Tasks:** 0/5 completed (0%)
- **P2 Tasks:** 0/6 completed (0%)
- **P3 Tasks:** 3/8 completed (37.5%)

### Recent Progress

- ✅ **MySQL SSH Tunnel Tests** (2026-02-11)
  - Basic CRUD operations through SSH tunnel
  - Transaction support validation
  - Error handling scenarios
  - Integration with testcontainers
  - 3 focused SSH tests added to integration suite

- ✅ **MariaDB SSH Tunnel Implementation** (2026-02-11)
  - SSH tunnel support added to MariaDB context
  - Test-driven development approach
  - 3 SSH tunnel tests implemented
  - Full CRUD operations through SSH tunnel
  - Transaction and error handling validation

- ✅ **PostgreSQL SSH Tunnel Implementation** (2026-02-11)
  - SSH tunnel support added to PostgreSQL context
  - Test-driven development approach
  - 3 SSH tunnel tests implemented
  - Full CRUD operations through SSH tunnel
  - Transaction and error handling validation

### Milestones

- **v0.1.0:** Complete P0 tasks
- **v0.2.0:** Complete P1 tasks
- **v0.3.0:** Complete P2 tasks
- **v1.0.0:** Complete P3 tasks

---

## 📝 Notes

### Difficulty Legend
- 🟢 **Medium:** Well-defined requirements, existing patterns to follow
- 🟡 **Medium-High:** Complex requirements, some research needed
- 🔵 **High:** Complex requirements, significant research/testing

### Dependencies
- UI tasks depend on corresponding engine implementations
- PostgreSQL features may require additional research
- SSH tunnel implementations should follow existing MySQL pattern

### Time Estimates
- Estimates assume 1 developer working full-time
- Buffer time included for testing and debugging
- UI tasks may take longer due to user experience considerations

---

*This roadmap is a living document. Update as priorities change and tasks are completed.*
