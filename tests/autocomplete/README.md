# Autocomplete Testing

This directory contains golden test cases for SQL autocomplete functionality.

## Design Principles

### Minimum Noise Principle
**Suggest only what is truly useful.**

The autocomplete system prioritizes relevance and context over completeness:
- Without prefix: Show the most useful suggestions for the current context
- With prefix: Filter all available options that match the prefix
- Contextual keywords (e.g., `FROM users`) appear before plain keywords (e.g., `FROM`)
- Plain keywords that guide workflow (e.g., `FROM`, `AS`) are shown even without context
- Avoid redundant suggestions that add noise without value

**Example:**
```sql
SELECT users.id |
→ Suggestions: FROM users, AS, FROM
  (Contextual keyword first, then plain keywords for flexibility)

SELECT users.id F|
→ Suggestions: FROM users, FROM
  (Both match prefix "F")
```

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

Golden tests organized by SQL query writing flow (178 total tests):

### 1. Query Start & Basic Context
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| EMPTY ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/empty.json` | 1 | 1 | 0 | 0 | `\|` | Empty editor suggestions |
| SINGLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/single.json` | 6 | 6 | 0 | 0 | `SEL\|` | Single keyword/token suggestions |

### 2. SELECT Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| SEL ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/sel.json` | 7 | 7 | 0 | 0 | `SELECT \|` | Basic SELECT suggestions |
| SELECT_PREFIX ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/select_prefix.json` | 6 | 6 | 0 | 0 | `SELECT u\|` | SELECT without FROM clause (prefix; with/without CURRENT_TABLE) |
| SELECT_COLUMN_BEHAVIOR ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/select_column_behavior.json` | 9 | 9 | 0 | 0 | `SELECT users.id \|` | Column whitespace and comma behavior |
| SELECT_SCOPED_CURRENT_TABLE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/select_scoped_current_table.json` | 4 | 0 | 0 | 0 | `SELECT \| FROM users` | SELECT with current table in scope |

### 3. FROM Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| FROM ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/from.json` | 9 | 0 | 0 | 0 | `SELECT * FROM \|` | Basic FROM clause suggestions |
| FROM_CLAUSE_PRIORITIZATION ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/from_clause_prioritization.json` | 3 | 0 | 0 | 0 | `SELECT id FROM users u WHERE u.id = 1 FROM \|` | Table prioritization in FROM |
| FROM_CLAUSE_CURRENT_TABLE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/from_clause_current_table.json` | 3 | 0 | 0 | 0 | `SELECT * FROM \|` (current_table=users) | FROM with current table |

### 4. JOIN Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| JOIN ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/join.json` | 6 | 0 | 0 | 0 | `SELECT * FROM users \|` | Basic JOIN suggestions |
| JOIN_ON ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/join_on.json` | 6 | 0 | 0 | 0 | `SELECT * FROM users u JOIN orders o ON \|` | JOIN ON clause suggestions |
| JOIN_AFTER_TABLE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/join_after_table.json` | 4 | 0 | 0 | 0 | `SELECT * FROM users JOIN orders \|` | Keywords after JOIN table |
| JOIN_OPERATOR_LEFT_COLUMN_FILTER ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/join_operator_left_column_filter.json` | 6 | 0 | 0 | 0 | `SELECT * FROM users JOIN orders ON users.id = \|` | Column filtering after operators |

### 5. WHERE Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| WHERE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/where.json` | 11 | 0 | 0 | 0 | `SELECT * FROM users WHERE \|` | Basic WHERE clause suggestions |
| WHERE_SCOPED ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/where_scoped.json` | 4 | 0 | 0 | 0 | `SELECT * FROM users u WHERE \|` | Scope restriction in WHERE |

### 6. GROUP BY Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| GROUP ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/group.json` | 4 | 0 | 0 | 0 | `SELECT status, COUNT(*) FROM users GROUP BY \|` | GROUP BY suggestions |

### 7. HAVING Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| HAVING ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/having.json` | 5 | 0 | 0 | 0 | `SELECT status FROM users GROUP BY status HAVING \|` | Basic HAVING clause |

### 8. ORDER BY Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| ORDER ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/order.json` | 7 | 0 | 0 | 0 | `SELECT * FROM users ORDER BY \|` | ORDER BY suggestions |

### 9. LIMIT Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| LIMIT ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/limit.json` | 3 | 0 | 0 | 0 | `SELECT * FROM users LIMIT \|` | LIMIT clause suggestions |

### 10. Advanced Features
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| DOT_COMPLETION ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/dot_completion.json` | 8 | 0 | 0 | 0 | `SELECT users.\|` | Dot completion (table.column) |
| ALIAS ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/alias.json` | 12 | 0 | 0 | 0 | `SELECT * FROM users \|` | Table/column aliases |
| ALIAS_PREFIX_DISAMBIGUATION ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/alias_prefix_disambiguation.json` | 8 | 0 | 0 | 0 | `SELECT u\| FROM users` | Alias prefix disambiguation |
| PREFIX_EXPANSION ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/prefix_expansion.json` | 6 | 0 | 0 | 0 | `SELECT us\| FROM users` | Prefix expansion logic |
| SCOPE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/scope.json` | 3 | 0 | 0 | 0 | `SELECT * FROM (SELECT id FROM users) AS u WHERE \|` | Scope management |
| WINDOW_FUNCTIONS_OVER ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/window_functions_over.json` | 1 | 0 | 0 | 0 | `SELECT ROW_NUMBER() OVER (\|)` | Window functions OVER clause |
| CURSOR_IN_TOKEN ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/cursor_in_token.json` | 1 | 1 | 0 | 0 | `SELECT na\|me FROM users` | Cursor position handling |

### 11. Multi-Query & Special Cases
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Example Query | Description |
|------------|------|-------|---|---|---|---------------|-------------|
| DERIVED_TABLES_CTE ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/derived_tables_cte.json` | 8 | 0 | 0 | 8 | `WITH au AS (SELECT * FROM users) SELECT * FROM \|` | CTEs and derived tables |
| MULTI_QUERY_SUPPORT ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/multi_query_support.json` | 7 | 0 | 0 | 0 | `SELECT * FROM users; SELECT \|` | Multiple queries in editor |
| MULTI_QUERY_EDGE_CASES ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/mq.json` | 4 | 0 | 0 | 0 | `SELECT * FROM users; SELECT * FROM orders WHERE \|;` | Multi-query lexical edge cases |
| OUT_OF_SCOPE_HINTS ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/out_of_scope_hints.json` | 5 | 0 | 0 | 0 | `SELECT u\| FROM products` | Scoped SELECT prefix and out-of-scope expansions |
| LEX ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/lex.json` | 2 | 0 | 0 | 0 | `SELECT * FROM users WHERE name LIKE '%\|'` | Lexical analysis |
| ALX ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/alx.json` | 6 | 0 | 0 | 0 | `SELECT * FROM users AS u\|` | Advanced lexical |
| LARGE_SCHEMA_GUARDRAILS ![status](https://img.shields.io/badge/status-not_tested-lightgrey) | `cases/perf.json` | 2 | 0 | 0 | 0 | `SELECT * FROM users WHERE col_0\|` | Large schema prefix/scope guardrails |

### Summary Statistics
- **Total Tests**: 178
- **✅ Passing**: 56 (31%)
- **❌ Failing**: 112 (63%)
- **⚠️ Expected Failures (xfail)**: 10 (6%)
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

**Status**: All 8 tests marked as `xfail` (expected failure)

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
