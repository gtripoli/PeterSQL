# Autocomplete Testing

This directory contains golden test cases for SQL autocomplete functionality.

## Test Structure

Tests are organized in JSON files under `cases/` directory. Each file contains test cases for a specific autocomplete scenario.

## Suggestion Ordering Rules

The autocomplete system follows strict ordering rules to ensure predictable and useful suggestions:

### 1. Columns
**Ordered by schema definition** (as they appear in the table structure), NOT alphabetically.

Example: For table `users(id, name, email, status, created_at)`, suggestions appear in that exact order.

### 2. Tables
**Ordered alphabetically** by table name.

Special cases:
- **CTEs (Common Table Expressions)**: Appear first
- **Referenced tables**: Tables used in CTEs or SELECT appear before unreferenced tables
- **Other tables**: Alphabetically sorted

### 3. Functions and Keywords
**Ordered alphabetically** by name.

### 4. Literals
Constants like `NULL`, `TRUE`, `FALSE` appear after columns but before functions.

## Example

For `SELECT * FROM users u JOIN orders o ON |`:

```
Suggestions order:
1. o.id, o.user_id, o.total, o.status, o.created_at  (JOIN table 'orders' columns by schema)
2. u.id, u.name, u.email, u.status, u.created_at     (FROM table 'users' columns by schema)
3. NULL, TRUE, FALSE                                  (literals)
4. AVG, COALESCE, CONCAT, COUNT, ...                 (functions alphabetically)
```

Note: In JOIN ON context, JOIN tables appear before FROM tables. Columns within each table follow schema order.

### JOIN ON Column Filtering Rule

After an operator in JOIN ON clause, only columns from OTHER tables are suggested:

- `FROM users u JOIN orders o ON u.id = |` → Suggest ONLY `o.*` columns (not `u.*`)
- `FROM users u JOIN orders o ON o.user_id = |` → Suggest ONLY `u.*` columns (not `o.*`)

The query can be written both ways:
- `users.id = orders.user_id` ✓
- `orders.user_id = users.id` ✓

The system detects which table is on the left of the operator and filters out ALL columns from that table.

## Test Coverage Matrix

Golden tests organized by SQL query writing flow (184 total tests):

### 1. Query Start & Basic Context
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| EMPTY ![status](https://img.shields.io/badge/status-pass-brightgreen) | 1 | 1 | 0 | 0 | `\|` | Empty editor suggestions |
| SINGLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | 6 | 6 | 0 | 0 | `SEL\|` | Single keyword/token suggestions |
| CURSOR ![status](https://img.shields.io/badge/status-pass-brightgreen) | 1 | 1 | 0 | 0 | `SELECT * FROM users\|` | Cursor position handling |

### 2. SELECT Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| SEL | 7 | 0 | 0 | 0 | `SELECT \|` | Basic SELECT suggestions |
| SELECT_NO_SCOPE | 3 | 0 | 0 | 0 | `SELECT id, \|` | SELECT without FROM clause |
| SELECT_WITH_SCOPE_CURRENT_TABLE | 4 | 0 | 0 | 0 | `SELECT \| FROM users` | SELECT with current table in scope |
| SELECT_QUALIFIED_COLUMN_WHITESPACE | 5 | 0 | 0 | 0 | `SELECT users.id \|` | Qualified columns with whitespace |
| WHITESPACE_COMMA_BEHAVIOR | 6 | 0 | 0 | 0 | `SELECT id,\|` | Comma and whitespace handling |

### 3. FROM Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| FROM | 9 | 0 | 0 | 0 | `SELECT * FROM \|` | Basic FROM clause suggestions |
| FROM_CLAUSE_PRIORITIZATION | 4 | 0 | 0 | 0 | `SELECT id FROM users u WHERE u.id = 1 FROM \|` | Table prioritization in FROM |
| FROM_JOIN_CLAUSE_CURRENT_TABLE | 8 | 0 | 0 | 0 | `SELECT * FROM \|` (current_table=users) | FROM/JOIN with current table |
| DERIVED_TABLES_CTE | 6 | 0 | 0 | 6 | `WITH au AS (SELECT * FROM users) SELECT * FROM \|` | CTEs and derived tables |

### 4. JOIN Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| JOIN | 4 | 0 | 0 | 0 | `SELECT * FROM users \|` | Basic JOIN suggestions |
| ON | 4 | 0 | 0 | 0 | `SELECT * FROM users u JOIN orders o ON \|` | JOIN ON clause suggestions |
| USING | 1 | 0 | 0 | 1 | `SELECT * FROM users JOIN orders USING (\|)` | JOIN USING clause |
| OPERATOR_LEFT_COLUMN_FILTER | 5 | 0 | 0 | 0 | `SELECT * FROM users JOIN orders ON users.id = \|` | Column filtering after operators |
| SCOPE_RESTRICTION_JOIN_ON | 4 | 0 | 0 | 0 | `SELECT * FROM orders o JOIN products p ON p.id = \|` | Scope restriction in JOIN ON |

### 5. WHERE Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| WHERE | 6 | 0 | 0 | 0 | `SELECT * FROM users WHERE \|` | Basic WHERE clause suggestions |
| SCOPE_RESTRICTION_WHERE | 4 | 0 | 0 | 0 | `SELECT * FROM users u WHERE \|` | Scope restriction in WHERE |
| MW | 2 | 0 | 0 | 2 | `SELECT * FROM users WHERE id = 1 WHERE \|` | Multi-WHERE scenarios |

### 6. GROUP BY Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| GROUP | 3 | 0 | 0 | 0 | `SELECT status, COUNT(*) FROM users GROUP BY \|` | GROUP BY suggestions |
| SCOPE_RESTRICTION_ORDER_GROUP | 5 | 0 | 0 | 0 | `SELECT * FROM users u GROUP BY \|` | Scope restriction in GROUP/ORDER |

### 7. HAVING Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| HAVING | 4 | 0 | 0 | 0 | `SELECT status FROM users GROUP BY status HAVING \|` | Basic HAVING clause |
| HAVING_AGGREGATE_PRIORITY | 4 | 0 | 0 | 4 | `SELECT status, COUNT(*) FROM users GROUP BY status HAVING \|` | Aggregate function priority |

### 8. ORDER BY Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| ORDER | 5 | 0 | 0 | 0 | `SELECT * FROM users ORDER BY \|` | ORDER BY suggestions |

### 9. LIMIT Clause
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| LIMIT | 2 | 0 | 0 | 2 | `SELECT * FROM users LIMIT \|` | LIMIT clause suggestions |

### 10. Advanced Features
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| DOT_COMPLETION | 9 | 0 | 0 | 0 | `SELECT users.\|` | Dot completion (table.column) |
| DOT | 6 | 0 | 0 | 0 | `SELECT u.\| FROM users u` | Legacy dot tests |
| ALIAS | 2 | 0 | 0 | 0 | `SELECT * FROM users \|` | Table/column aliases |
| ALIAS_PREFIX_DISAMBIGUATION | 8 | 0 | 0 | 0 | `SELECT u\| FROM users` | Alias prefix disambiguation |
| PREFIX_EXPANSION | 10 | 0 | 0 | 0 | `SELECT us\| FROM users` | Prefix expansion logic |
| SCOPE | 3 | 0 | 0 | 0 | `SELECT * FROM (SELECT id FROM users) AS u WHERE \|` | Scope management |
| FUT | 1 | 0 | 0 | 1 | `SELECT ROW_NUMBER() OVER (\|)` | Window functions |

### 11. Multi-Query & Special Cases
| Test Group | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|-------|---|---|---|---------------|-------------|
| MULTI_QUERY_SUPPORT | 8 | 0 | 0 | 0 | `SELECT * FROM users; SELECT \|` | Multiple queries in editor |
| MQ | 4 | 0 | 0 | 4 | `SELECT * FROM users; \|` | Multi-query scenarios |
| OUT_OF_SCOPE_HINTS | 6 | 0 | 0 | 0 | `SELECT * FROM users WHERE id = \|` | Out-of-scope suggestions |
| CURR | 2 | 0 | 0 | 2 | `SELECT \|` (current_table=users) | Current table handling |
| LEX | 2 | 0 | 0 | 0 | `SELECT * FROM users WHERE name LIKE '%\|'` | Lexical analysis |
| ALX | 6 | 0 | 0 | 0 | `SELECT * FROM users AS u\|` | Advanced lexical |
| PERF | 2 | 0 | 0 | 0 | Large schema performance tests | Performance tests |

### Summary Statistics
- **Total Tests**: 184
- **✅ Passing**: 8 (4%)
- **❌ Failing**: 0 (0%)
- **⚠️ Expected Failures (xfail)**: 58 (32%)
- **⚪ Not Implemented**: 0 (0%)

### Legend
- ✅ **Pass**: Test passes successfully
- ❌ **Fail**: Test fails (needs fixing)
- ⚠️ **XFail**: Expected failure (feature not yet implemented)
- ⚪ **Skip**: Test skipped

## Running Tests

```bash
uv run pytest tests/autocomplete/test_golden_cases.py -v
```

Run specific test:
```bash
uv run pytest tests/autocomplete/test_golden_cases.py -k "test_name"
```

Run specific group:
```bash
uv run pytest tests/autocomplete/test_golden_cases.py -k "ON"
```

## Implementation Notes

### DERIVED_TABLES_CTE (xfail - Future Enhancement)

**Status**: All 6 tests marked as `xfail` (expected failure)

**Feature Description**: Support for Common Table Expressions (CTEs) and derived tables (subqueries in FROM/JOIN clauses). This requires:
1. Extracting column names from CTE and derived table SELECT lists
2. Creating mock table objects with those columns
3. Making CTEs available as table suggestions in FROM/JOIN clauses
4. Providing column suggestions from CTEs and derived tables in expression contexts

**Implementation Attempts**:

1. **Column Extraction (Partially Successful)**
   - Added `_extract_columns_from_select()` in `context_detector.py` using sqlglot parser
   - Successfully parsed SELECT lists to extract column names and aliases
   - Handled `SELECT *` cases (returns empty list, requires full table resolution)
   - Correctly identified CTEs and derived tables in SQL statements

2. **Mock Table Creation (Failed)**
   - Created `_create_mock_table()` to generate `SQLTable`-like objects with columns
   - Initial approach: Used `unittest.mock.Mock(spec=SQLTable)` - failed due to iteration issues
   - Second approach: Created simple Python classes (`MockTable`, `MockColumn`) - still incompatible
   - Problem: Mock objects don't fully implement all methods/properties expected by `suggestion_builder.py`

3. **CTE Suggestion in FROM_CLAUSE (Partially Successful)**
   - Modified `_build_from_clause()` in `suggestion_builder.py` to extract CTEs via regex
   - Successfully added CTEs to table suggestions
   - Implemented prioritization: CTEs first, then referenced tables, then alphabetically
   - This part worked correctly for CTE_004 test

**Final Blocking Issue**:

The implementation fails when `suggestion_builder.py` attempts to iterate over columns from mock tables. The error `AttributeError: 'NoneType' object has no attribute 'items'` occurs because:

1. Mock table objects don't implement all required interfaces
2. The existing code expects real `SQLTable` objects with `ObservableLazyList` for columns
3. Mock objects lack methods like `__iter__`, property getters, and other SQLAlchemy-like behaviors
4. Attempting to make mock objects fully compatible would require reimplementing significant portions of the `SQLTable` class

**Required for Full Implementation**:

1. **Refactor `suggestion_builder.py`**: Make column resolution more defensive and handle mock tables gracefully
2. **Complete Mock Implementation**: Create a full `MockSQLTable` class that implements all required methods and properties
3. **Alternative Approach**: Modify the architecture to use a different abstraction layer that doesn't require full `SQLTable` objects
4. **Testing Infrastructure**: Add unit tests specifically for CTE/derived table column extraction before integration

**Complexity Estimate**: Medium-High (requires architectural changes to column resolution logic)

**Workaround**: Currently, CTEs and derived tables fall back to suggesting all database columns, which is incorrect but doesn't break existing functionality.
