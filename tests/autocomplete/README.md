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

Golden tests organized by SQL query writing flow (180 base tests, executed across 11 engine/version targets):

- mysql: `8`, `9`
- mariadb: `5`, `10`, `11`, `12`
- postgresql: `15`, `16`, `17`, `18`
- sqlite: `3`

### 1. Query Start & Basic Context
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| EMPTY ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/empty.json` | 1 | 1 | 0 | 0 | Entry-point suggestions when the editor is empty. |
| SINGLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/single.json` | 6 | 6 | 0 | 0 | Single-token bootstrap and keyword completion before full parsing. |

### 2. SELECT Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| SEL ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/sel.json` | 4 | 4 | 0 | 0 | Baseline SELECT-list suggestions (functions/keywords) without table scope. |
| SELECT_PREFIX ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/select_prefix.json` | 5 | 5 | 0 | 0 | Prefix filtering in SELECT with and without `current_table` influence. |
| SELECT_COLUMN_BEHAVIOR ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/select_column_behavior.json` | 13 | 13 | 0 | 0 | Comma/whitespace transitions after columns and expression boundaries. |
| SELECT_SCOPED_CURRENT_TABLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/select_scoped_current_table.json` | 3 | 3 | 0 | 0 | Scope-aware SELECT suggestions when FROM/JOIN tables are already known. |

### 3. FROM Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| FROM ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/from.json` | 11 | 11 | 0 | 0 | Table suggestions plus post-table clause transitions (including no-space continuations). |
| FROM_CLAUSE_PRIORITIZATION ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/from_clause_prioritization.json` | 3 | 3 | 0 | 0 | Prioritization when SELECT already references qualified tables. |
| FROM_CLAUSE_CURRENT_TABLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/from_clause_current_table.json` | 1 | 1 | 0 | 0 | FROM behavior when `current_table` is set and should affect choices. |

### 4. JOIN Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| JOIN ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/join.json` | 6 | 6 | 0 | 0 | JOIN table suggestions and join-keyword progression. |
| JOIN_ON ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/join_on.json` | 6 | 6 | 0 | 0 | ON-clause column/function suggestions with correct scope ordering. |
| JOIN_AFTER_TABLE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/join_after_table.json` | 4 | 4 | 0 | 0 | Keyword transitions immediately after a JOIN target table. |
| JOIN_OPERATOR_LEFT_COLUMN_FILTER ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/join_operator_left_column_filter.json` | 6 | 6 | 0 | 0 | Left-side table exclusion after JOIN operators (`=`, `<`, `>`, etc.). |

### 5. WHERE Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| WHERE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/where.json` | 11 | 11 | 0 | 0 | WHERE context, operator, expression follow-up, and qualified-style propagation rules. |
| WHERE_SCOPED ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/where_scoped.json` | 4 | 4 | 0 | 0 | WHERE suggestions constrained to active scope/aliases only. |

### 6. GROUP BY Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| GROUP ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/group.json` | 7 | 7 | 0 | 0 | GROUP BY column suggestions, duplicate filtering, and qualified-style propagation. |

### 7. HAVING Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| HAVING ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/having.json` | 6 | 6 | 0 | 0 | Aggregate-aware HAVING behavior, operators, and qualified-style propagation. |

### 8. ORDER BY Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| ORDER ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/order.json` | 8 | 8 | 0 | 0 | ORDER BY columns, sort-direction keyword flow, and qualified-style propagation. |

### 9. LIMIT Clause
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| LIMIT ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/limit.json` | 3 | 3 | 0 | 0 | LIMIT/OFFSET context behavior and post-number suggestions. |

### 10. Advanced Features
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| DOT_COMPLETION ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/dot_completion.json` | 7 | 7 | 0 | 0 | `table_or_alias.` completion, including prefix filtering after dot. |
| ALIAS ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/alias.json` | 11 | 11 | 0 | 0 | Alias resolution and qualified suggestions in scoped expressions. |
| ALIAS_PREFIX_DISAMBIGUATION ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/alias_prefix_disambiguation.json` | 7 | 7 | 0 | 0 | Exact alias-prefix disambiguation versus generic prefix matching. |
| PREFIX_EXPANSION ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/prefix_expansion.json` | 6 | 6 | 0 | 0 | Prefix expansion behavior across columns, functions, and qualifiers. |
| WINDOW_FUNCTIONS_OVER ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/window_functions_over.json` | 1 | 1 | 0 | 0 | OVER-clause bootstrap suggestions (`PARTITION BY`, `ORDER BY`). |
| CURSOR_IN_TOKEN ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/cursor_in_token.json` | 1 | 1 | 0 | 0 | Correct prefix/context when cursor is inside an existing token. |

### 11. Multi-Query & Special Cases
| Test Group | File | Total | ✅ | ❌ | ⚠️ | Description |
|------------|------|-------|---|---|---|-------------|
| DERIVED_TABLES_CTE ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/derived_tables_cte.json` | 9 | 9 | 0 | 0 | Minimal CTE/derived-table scope extraction for FROM/JOIN/WHERE and dot completion. |
| MULTI_QUERY_SUPPORT ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/multi_query_support.json` | 7 | 7 | 0 | 0 | Statement isolation in multi-query editors with correct active-scope selection. |
| MULTI_QUERY_EDGE_CASES ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/mq.json` | 1 | 1 | 0 | 0 | Separator edge behavior in multi-query parsing. |
| OUT_OF_SCOPE_HINTS ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/out_of_scope_hints.json` | 4 | 4 | 0 | 0 | Scope-first prefix behavior when out-of-scope names also share the prefix. |
| LEX ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/lex.json` | 2 | 2 | 0 | 0 | Lexical resilience with quotes/comments around separators and dots. |
| ALX ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/alx.json` | 5 | 5 | 0 | 0 | Advanced lexical interactions with alias parsing and token boundaries. |
| LARGE_SCHEMA_GUARDRAILS ![status](https://img.shields.io/badge/status-pass-brightgreen) | `cases/perf.json` | 2 | 2 | 0 | 0 | Large-schema guardrails for prefix filtering and noise control. |

### Summary Statistics
- **Total Tests**: 1881 (171 base × 11 engine/version targets)
- **✅ Passing**: 1881 (171 base × 11 targets, 100%)
- **❌ Failing**: 0 (remaining tests, 0%)
- **⚠️ Expected Failures (xfail)**: 0 (0 base × 11 targets, 0%)
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

- `DERIVED_TABLES_CTE` is fully enabled in the current suite with lightweight virtual-table scope resolution.
- Current implementation intentionally targets common patterns (`WITH ... AS (SELECT col1, col2 ...)`, `FROM (SELECT col1, col2 ...) AS alias`) and avoids deep SQL normalization.
- If we later need nested or highly dynamic CTE projection inference, we can extend parsing incrementally without changing the test contract.
