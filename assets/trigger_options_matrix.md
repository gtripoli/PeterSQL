# Trigger Options Matrix

Legend:
- ✅ Supported
- ❌ Not supported
- ⚠️ Supported with differences / restrictions

Engines covered:
- MySQL
- MariaDB
- PostgreSQL
- Oracle
- SQLite

---

## Core fields (practical UI)

| Field / Option | MySQL | MariaDB | PostgreSQL | Oracle | SQLite |
|---|---:|---:|---:|---:|---:|
| Name | ✅ | ✅ | ✅ | ✅ | ✅ |
| Target object type | Table ✅ | Table ✅ | Table/View/Foreign table ✅ | Table/View/Schema/Database ✅ | Table/View ✅ |
| Schema / owner | ⚠️ database name | ⚠️ database name | ✅ schema | ✅ schema | ✅ schema |
| Timing | BEFORE/AFTER ✅ | BEFORE/AFTER ✅ | BEFORE/AFTER/INSTEAD OF ✅ | BEFORE/AFTER/INSTEAD OF ✅ | BEFORE/AFTER/INSTEAD OF ✅ |
| Events | INSERT/UPDATE/DELETE ✅ | INSERT/UPDATE/DELETE ✅ | INSERT/UPDATE/DELETE/TRUNCATE ✅ | INSERT/UPDATE/DELETE + many DDL/system events ⚠️ | INSERT/UPDATE/DELETE ✅ |
| UPDATE OF columns | ❌ | ❌ | ✅ | ✅ | ✅ |
| Level | ROW only ✅ | ROW only ✅ | ROW or STATEMENT ✅ | ROW or STATEMENT ✅ | ROW only ✅ |
| WHEN condition | ❌ | ❌ | ✅ | ✅ | ✅ |
| Body language | SQL (BEGIN..END) ✅ | SQL (BEGIN..END) ✅ | calls FUNCTION/PROCEDURE ✅ | PL/SQL (or call proc) ✅ | SQL statements in BEGIN..END ✅ |
| Create-if-exists handling | ❌ (use DROP) | ✅ OR REPLACE / IF NOT EXISTS | ✅ OR REPLACE | ✅ OR REPLACE | ✅ IF NOT EXISTS |
| Definer / security context | ✅ DEFINER | ✅ DEFINER | ❌ | ❌ | ❌ |
| Execution order control | ✅ FOLLOWS/PRECEDES | ✅ FOLLOWS/PRECEDES | ❌ (name order) | ✅ FOLLOWS/PRECEDES | ❌ |
| Transition tables / REFERENCING | ❌ | ❌ | ✅ REFERENCING NEW/OLD TABLE | ⚠️ (uses :NEW/:OLD, compound triggers) | ❌ |
| Constraint/deferrable trigger | ❌ | ❌ | ✅ CONSTRAINT + DEFERRABLE | ❌ | ❌ |
| TEMP trigger | ❌ | ❌ | ❌ | ❌ | ✅ TEMP/TEMPORARY |
| Enable/disable at create | ❌ | ❌ | ❌ (enable/disable via ALTER) | ✅ ENABLE/DISABLE | ❌ |

Notes:
- **MySQL triggers are row-level only** (the syntax defines action time BEFORE/AFTER “for each row”).  
- **PostgreSQL supports INSTEAD OF triggers on views** and supports `TRUNCATE` triggers.  
- **SQLite supports TEMP triggers, `IF NOT EXISTS`, `UPDATE OF col...`, `WHEN expr`, and row-level only.**  
- **Oracle has very broad trigger types** (DML, DDL, system/database events, compound triggers, etc.); the UI above is the “DML view” subset unless you decide to expose advanced Oracle-specific triggers.

---

## Engine-specific clauses (what to show/hide)

### MySQL
- `DEFINER = user` ✅  
- `FOLLOWS other_trigger` / `PRECEDES other_trigger` ✅  
- Timing: `BEFORE` / `AFTER` ✅  
- Events: `INSERT` / `UPDATE` / `DELETE` ✅  
- Level: **ROW only** ✅  

### MariaDB
- `DEFINER = ...` ✅  
- `OR REPLACE` ✅ and `IF NOT EXISTS` ✅  
- `FOLLOWS` / `PRECEDES` ✅  
- Timing/events/level like MySQL (ROW only) ✅  

### PostgreSQL
- `CREATE [OR REPLACE] [CONSTRAINT] TRIGGER ...` ✅  
- Timing: `BEFORE` / `AFTER` / `INSTEAD OF` ✅  
- Events: includes `TRUNCATE` ✅  
- `UPDATE OF col...` ✅  
- `FOR EACH ROW` / `FOR EACH STATEMENT` ✅  
- `WHEN (condition)` ✅  
- `REFERENCING ... TABLE AS ...` (transition tables) ✅  
- Deferrable constraint triggers ✅  

### Oracle (DML-focused subset)
- `CREATE OR REPLACE TRIGGER ...` ✅  
- Timing points (row/statement) ✅  
- `INSTEAD OF` triggers on views ✅  
- `FOLLOWS` / `PRECEDES` ✅  
- `ENABLE` / `DISABLE` ✅  
- Plus **many Oracle-only trigger kinds** (schema/database/system/DDL), which you can keep out of the “common UI”.

### SQLite
- `CREATE [TEMP|TEMPORARY] TRIGGER [IF NOT EXISTS] ...` ✅  
- Timing: `BEFORE` / `AFTER` / `INSTEAD OF` ✅  
- `UPDATE OF col...` ✅  
- `FOR EACH ROW` only ✅  
- `WHEN expr` ✅  
- No definer/security/order controls.

---

## Sources (for your SQL generator / docs)
- MySQL `CREATE TRIGGER`: DEFINER, timing/events, and FOLLOWS/PRECEDES order clause.  
- MySQL security note: triggers have no `SQL SECURITY` characteristic; they always execute in definer context.  
- MariaDB `CREATE TRIGGER`: OR REPLACE, IF NOT EXISTS, DEFINER, FOLLOWS/PRECEDES.  
- PostgreSQL `CREATE TRIGGER`: OR REPLACE, CONSTRAINT triggers, TRUNCATE, UPDATE OF, ROW/STATEMENT, WHEN, transition tables.  
- SQLite `CREATE TRIGGER`: TEMP, IF NOT EXISTS, INSTEAD OF, UPDATE OF, FOR EACH ROW, WHEN.

(If you want, I can produce a second MD that includes the exact SQL synopsis blocks per engine.)
