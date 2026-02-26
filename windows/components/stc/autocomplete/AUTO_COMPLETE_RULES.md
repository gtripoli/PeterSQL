# SQL Autocomplete Rules

This document defines the autocomplete behavior for each SQL context.

---

## Context Detection

The autocomplete system uses `sqlglot` to parse the SQL query and determine the current context.
Contexts are defined in the `SQLContext` enum.

---

## Key Examples: Scope Restriction in Action

These examples demonstrate the strict separation between table-selection and expression contexts.

**Assume:** `CURRENT_TABLE = users` (set in table editor)

### Example 1: SELECT with no FROM → CURRENT_TABLE + DB-wide allowed

```sql
SELECT u|
```

**Context:** SELECT_LIST, no scope tables exist

**Suggestions:**
- `users.id, users.name, users.email, ...` (CURRENT_TABLE columns first)
- `products.unit_price, ...` (DB-wide columns matching 'u')
- `UPPER, UUID, UNIX_TIMESTAMP` (functions)

**Rationale:** No scope tables exist, so CURRENT_TABLE and DB-wide columns are allowed.

---

### Example 2: FROM/JOIN suggests CURRENT_TABLE as table candidate

```sql
SELECT * FROM orders JOIN |
```

**Context:** JOIN_CLAUSE (table-selection)

**Suggestions:**
- `users` (CURRENT_TABLE as convenience shortcut)
- `products, customers, ...` (other physical tables)
- CTEs (if any)

**Rationale:** JOIN_CLAUSE is table-selection. CURRENT_TABLE may be suggested even though scope tables (orders) already exist. This is how the user brings it into scope.

---

### Example 3: WHERE/JOIN_ON shows only scoped columns (CURRENT_TABLE excluded unless in scope)

```sql
-- Case A: CURRENT_TABLE not in scope
SELECT * FROM orders WHERE u|
```

**Context:** WHERE (expression context), scope = [orders]

**Suggestions:**
- `orders.user_id` (scope table column matching 'u')
- `UPPER, UUID, UNIX_TIMESTAMP` (functions)

**NOT suggested:**
- ❌ `users.*` (CURRENT_TABLE not in scope)
- ❌ `products.unit_price` (DB-wide column)

**Rationale:** WHERE is an expression context with scope tables. CURRENT_TABLE is not in scope, so it MUST be ignored. DB-wide columns MUST NOT be suggested.

```sql
-- Case B: CURRENT_TABLE in scope
SELECT * FROM users u JOIN orders o WHERE u|
```

**Context:** WHERE (expression context), scope = [users (alias u), orders (alias o)]

**Suggestions:**
- `u.id, u.name, u.email, ...` (CURRENT_TABLE in scope via alias 'u')
- `UPPER, UUID, UNIX_TIMESTAMP` (functions)

**Rationale:** CURRENT_TABLE (users) is in scope via alias 'u', so its columns are included.

---

## Precedence Chain

The autocomplete resolution follows this strict precedence order:

1. **Multi-Query Separation**
   - If multiple queries in editor (separated by the effective statement separator), extract the current statement where the cursor is
   - All subsequent rules apply only to current statement

2. **Dot-Completion** (`table.` or `alias.`)
   - If token immediately before cursor contains `.` → Dot-Completion mode
   - Show columns of that table/alias (ignore broader context)
   - Example: `WHERE u.i|` → show columns of `u` starting with `i`

3. **Context Detection** (sqlglot/regex)
   - Determine SQL context: SELECT_LIST, WHERE, JOIN ON, ORDER BY, etc.
   - Use sqlglot parsing (primary) or regex fallback

4. **Within Context: Prefix Rules**
   - If prefix exists (token before cursor without `.`) → apply prefix matching
   - Check for exact alias match first (Alias Prefix Disambiguation)
   - Otherwise generic prefix matching (tables, columns, functions, keywords)

**Example resolution:**
```sql
-- Multi-query: extract current statement
SELECT * FROM users; SELECT * FROM orders WHERE u|

-- No dot → not Dot-Completion
-- Context: WHERE clause
-- Prefix: "u"
-- Check aliases: no alias "u" in this statement
-- Generic prefix: show users.*, orders.user_id, UPPER, etc.
```

**Example with dot:**
```sql
SELECT * FROM users u WHERE u.i|

-- Dot detected → Dot-Completion (precedence 2)
-- Show columns of "u" starting with "i"
-- Context (WHERE) is ignored for this specific resolution
```

This precedence eliminates ambiguity: **Dot-Completion always wins**, then context, then prefix rules.

---

## Universal Rules (Apply to All Contexts)

### Prefix Definition

**Prefix** = the identifier token immediately before the cursor, composed of `[A-Za-z0-9_]+` (or equivalent for dialect).

**Rules:**
- Match is case-insensitive
- Output preserves original form (alias/table/column name)
- If token contains `.` → **not a prefix**: triggers Dot-Completion instead

**Examples:**
```sql
SELECT u|
→ Prefix: "u" (triggers prefix matching)

SELECT u.i|
→ NOT a prefix (contains dot)
→ Triggers Dot-Completion on table/alias "u"

SELECT ui|
→ Prefix: "ui" (triggers prefix matching)
```

**This distinction is critical:**
- `u.i|` → Dot-Completion (show columns of table/alias `u` starting with `i`)
- `ui|` → Prefix matching (show items starting with `ui`)

---

### Column Qualification (table.column vs alias.column)

**Important:** Always prefer `alias.column` format when an alias is defined, otherwise use `table.column`.

**Examples:**
```sql
-- No alias: use table.column
SELECT * FROM users WHERE |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at

-- With alias: use alias.column
SELECT * FROM users u WHERE |
→ u.id, u.name, u.email

-- Multiple tables with aliases
SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE |
→ u.id, u.name, o.user_id, o.total
```

**Note:** This rule applies to all contexts: SELECT_LIST, WHERE, JOIN ON, ORDER BY, GROUP BY, HAVING.

---

### Comma and Whitespace Behavior

**Universal rule for all contexts:**

- **Comma is never suggested** as an autocomplete item
- If the user types `,` → they want another item → apply "next-item" rules for that context (e.g., after comma in SELECT list, show columns/functions)
- If the user types **whitespace** after a completed identifier/expression → treat it as "selection complete" → show only keywords valid in that position (clause keywords or context modifiers like `ASC`, `DESC`, `NULLS FIRST`, etc.)

**Rationale:** Whitespace signals intentional pause/completion. Comma signals continuation. This distinction applies consistently across all SQL contexts.

**Examples:**
```sql
SELECT id, |
→ Comma typed → next-item rules → show columns/functions

SELECT id |
→ Whitespace typed → selection complete → show clause keywords (FROM, WHERE, AS, ...)

ORDER BY created_at, |
→ Comma typed → next-item rules → show columns/functions

ORDER BY created_at |
→ Whitespace typed → selection complete → show ASC, DESC, NULLS FIRST, NULLS LAST
```

---

### Scope-Restricted Expression Contexts

**Definition:** The following contexts are **scope-restricted expression contexts**:
- WHERE
- JOIN_ON
- ORDER_BY
- GROUP_BY
- HAVING

**Scope restriction rules for these contexts:**
- Column suggestions MUST be limited to scope tables only
- Database-wide columns MUST NOT be suggested
- Table-name expansion MUST be limited to scope tables only
- Column-name matching MUST be limited to scope tables only
- `CURRENT_TABLE` columns MUST NOT be suggested unless `CURRENT_TABLE` is in scope

**Operator context rule (WHERE, JOIN_ON):**
- When cursor is after a comparison operator (`=`, `!=`, `<>`, `<`, `>`, `<=`, `>=`, `LIKE`, `IN`, etc.)
- The column on the LEFT side of the operator MUST NOT be suggested
- **Rationale:** Suggesting the same column on both sides (e.g., `WHERE users.id = users.id`) is redundant and not useful
- **Example:** `WHERE users.id = |` should suggest `users.name`, `users.email`, etc., but NOT `users.id`

**Rationale:** These clauses cannot legally reference tables not present in scope.

---

### CURRENT_TABLE Scope Restriction

**Definition:** `CURRENT_TABLE` = UI-selected table from table editor context (optional, may be `None`).

**Scope tables** = tables/CTEs/derived tables that appear in the current statement's FROM/JOIN clauses:
- Physical tables in FROM/JOIN
- CTEs referenced in FROM/JOIN
- Derived tables (subquery aliases) in FROM/JOIN

---

#### Table-Selection Contexts (FROM_CLAUSE, JOIN_CLAUSE)

These contexts suggest **tables**, not columns.

**Rules:**
- `CURRENT_TABLE` MAY be suggested as a table candidate
- Allowed even if scope tables already exist (this is how user brings it into scope)
- MUST NOT suggest `CURRENT_TABLE` if it is already present in the statement
- Purpose: convenience shortcut for selecting the current table

---

#### Expression Contexts (JOIN_ON, WHERE, ORDER_BY, GROUP_BY, HAVING)

These are **scope-restricted expression contexts** (see **Scope-Restricted Expression Contexts** section).

These contexts suggest **columns** from scope tables only.

---

#### SELECT_LIST Context (Special Case)

**If statement has NO scope tables (no FROM/JOIN yet):**
- `CURRENT_TABLE` columns MUST be included first (if set)
- Database-wide columns MAY be included (guardrail applies when no prefix)
- Functions and keywords are included

**If statement HAS scope tables (FROM/JOIN exists):**
- `CURRENT_TABLE` columns MUST be included ONLY if `CURRENT_TABLE` is in scope
- If `CURRENT_TABLE` is not in scope, it MUST be ignored
- Database-wide columns MAY still be included (for table-name expansion and column-name matching)
- Scope table columns are included with alias-first qualification

---

### Dot-Completion (table.column or alias.column)

**Trigger:** After `table.` or `alias.` in any SQL context

**Show:**
- Columns of the specific table (filtered by prefix if present)

**Output format:** Unqualified column names (e.g., `id`, `name`) NOT qualified (e.g., `u.id`, `u.name`). This is an exception to the alias-first rule used elsewhere.

**Ordering:** Dot-completion bypasses global ordering rules and returns only the selected table's columns (table definition order). Columns preserve their ordinal position in the table schema. No functions, keywords, or other tables.

**Filtering:** When a prefix is present after the dot (e.g., `users.i|`), filtering uses `startswith(prefix)` on column name (case-insensitive). NOT contains or fuzzy matching.

**Examples:**
```sql
SELECT users.|
→ id, name, email, password, is_enabled, created_at  (schema order, NOT alphabetical)
→ NOT users.id, users.name, ...

SELECT users.i|
→ id, is_enabled  (columns starting with 'i', in schema order)
→ NOT users.id

WHERE u.|  (where u is alias of users)
→ id, name, email, password, is_enabled, created_at  (schema order)
→ NOT u.id, u.name, ...

ON orders.|
→ id, user_id, total, created_at

ORDER BY users.|
→ id, name, email, password, is_enabled, created_at  (schema order)
```

**Note:** This rule takes precedence over context-specific rules when a dot is detected.

---

## Autocomplete Rules by Context

### 1. EMPTY (Empty editor)

**Trigger:** Completely empty editor

**Show:**
- Primary keywords: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `SHOW`, `DESCRIBE`, `EXPLAIN`, `WITH`, `REPLACE`, `MERGE`

**Examples:**
```sql
|  → SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ...
```

---

### 2. SINGLE_TOKEN (Single token without spaces)

**Trigger:** Single partial token, no spaces

**Important:** Applies only if the entire current statement contains exactly one token (no whitespace). Whitespace includes newline. This avoids misinterpretation when splitting statements/lines.

**Token definition:** A valid identifier matching the pattern `^[A-Za-z_][A-Za-z0-9_]*$` (or dialect-equivalent). This excludes symbols like `(`, `)`, `,`, `.`, etc. Examples: `SEL` ✅, `SEL(` ❌, `SELECT,` ❌.

**Note:** Token matching is dialect-aware; the pattern above is the default baseline. Some dialects may support `$`, `#`, or unicode characters in identifiers.

**Show:**
- All keywords (filtered by prefix)

**Examples:**
```sql
SEL|  → SELECT
INS|  → INSERT
UPD|  → UPDATE
```

**Not SINGLE_TOKEN:**
```sql
SELECT
SEL|
→ This is two tokens (SELECT + SEL), not SINGLE_TOKEN context
→ Use context detection instead
```

---

### 3. SELECT_LIST (Inside SELECT, before FROM)

**Trigger:** After `SELECT` and before `FROM`

**Important:** Column suggestions depend on whether FROM/JOIN are present in the query.

#### 3a. Without prefix (after SELECT, no FROM/JOIN in query)

**Show:**
- Functions
- Keywords (FROM, WHERE, etc.)

**Examples:**
```sql
SELECT |
→ COUNT, SUM, AVG, MAX, MIN, UPPER, LOWER, ...
→ FROM, WHERE, LIMIT, ...
```

#### 3a-bis. Without prefix (after SELECT, with FROM/JOIN in query)

**Show:**
- Columns in scope (qualified, alias-first)
- All functions

**Examples:**
```sql
SELECT * FROM users WHERE id = 1; SELECT |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...
→ COUNT, SUM, AVG, ...

SELECT * FROM users u JOIN orders o ON u.id = o.user_id; SELECT |
→ u.id, u.name, o.user_id, o.total, ...
→ COUNT, SUM, AVG, ...
```

#### 3b. With prefix

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix

**Matching priority:**
1. If prefix exactly equals an alias → Alias-exact-match mode (see **Alias Prefix Disambiguation** section)
2. Otherwise → Generic prefix matching (see **Generic Prefix Matching for Column Contexts** section)

**CURRENT_TABLE handling:**

- **When NO scope tables exist (no FROM/JOIN):**
  - `CURRENT_TABLE` columns MUST be included first (if set)
  - Database-wide table-name expansion and column-name matching are included
  - Functions are included
  
- **When scope tables exist (FROM/JOIN present):**
  - `CURRENT_TABLE` columns MUST be included ONLY if `CURRENT_TABLE` is in scope
  - If `CURRENT_TABLE` is not in scope, it MUST be ignored
  - Scope table columns are included with alias-first qualification
  - **Out-of-Scope Table Hints:** If prefix matches DB-wide tables but no scope tables/columns, suggest table names as hints (see **Out-of-Scope Table Hints** section)

**Examples:**

**No FROM/JOIN (CURRENT_TABLE included):**
```sql
-- Assume CURRENT_TABLE = users
SELECT u|
→ users.id, users.name, users.email, ... (CURRENT_TABLE columns first)
→ Table-name expansion: (other tables starting with 'u')
→ Column-name matching: orders.user_id, products.unit_price (DB-wide columns starting with 'u')
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
```

**FROM/JOIN exists, CURRENT_TABLE not in scope (CURRENT_TABLE ignored):**
```sql
-- Assume CURRENT_TABLE = users
SELECT u| FROM orders
→ Table-name expansion: users.* (DB-wide table starting with 'u')
→ Column-name matching: orders.user_id (scope table column starting with 'u')
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ (CURRENT_TABLE ignored - not in scope)
```

**FROM/JOIN exists, CURRENT_TABLE in scope (CURRENT_TABLE included):**
```sql
-- Assume CURRENT_TABLE = users
SELECT u| FROM users u JOIN orders o
→ Alias-exact-match mode activated (u == alias 'u')
→ u.id, u.name, u.email (CURRENT_TABLE in scope via alias 'u')
→ UPPER, UUID, UNIX_TIMESTAMP (functions)
```

#### 3c. After comma (next column)

**Trigger:** After comma in SELECT list

**Show:**
- All columns (qualified, alias-first) (filtered by prefix if present)
- All functions (filtered by prefix if present)

**Examples:**
```sql
SELECT col1, |
→ users.id, users.name, users.email, orders.total, ...
→ COUNT, SUM, AVG, ...

SELECT * FROM users u WHERE id = 1; SELECT id, |
→ u.id, u.name, u.email, ...
→ COUNT, SUM, AVG, ...

SELECT id, n|
→ users.name, orders.name, ...
```

#### 3d. After complete column (space after column)

**Trigger:** After a complete column name (with or without table prefix) followed by space

**Show:**
- Keywords ONLY: `FROM`, `WHERE`, `AS`, `LIMIT`, `ORDER BY`, `GROUP BY`, `HAVING`
- `AS` only if the current select item has no alias yet
- **IMPORTANT:** NO functions (COUNT, SUM, UPPER, etc.) - user has completed selection

**Note:** If alias presence cannot be reliably detected in incomplete SQL, default to offering `AS` (non-breaking UX).

**Rationale:** Whitespace after a complete column indicates "selection complete" - user wants to move to next clause, not continue with functions.

**Examples:**
```sql
SELECT id |
→ FROM, WHERE, AS, LIMIT, ORDER BY, GROUP BY, HAVING
→ NOT: COUNT, SUM, UPPER, etc.

SELECT id AS user_id |
→ FROM, WHERE, LIMIT, ORDER BY, GROUP BY, HAVING  (AS excluded - alias already present)

SELECT users.id |
→ FROM, WHERE, AS, LIMIT, ORDER BY, GROUP BY, HAVING
→ NOT: COUNT, SUM, UPPER, etc.

SELECT table.column |
→ FROM, WHERE, AS, LIMIT, ORDER BY, GROUP BY, HAVING
→ NOT: functions
```

---

### 4. FROM_CLAUSE (After FROM)

**Trigger:** After `FROM` and before `WHERE`/`JOIN`

#### 4a. Without prefix

**Show:**
- CTE names (if available from WITH clause)
- All physical tables
- `CURRENT_TABLE` (if set and not already in statement)

**Prioritization:** If SELECT list contains qualified columns (e.g., `SELECT users.id`), prioritize those tables first in suggestions, even without prefix.

**Examples:**
```sql
SELECT * FROM |
→ customers, orders, products, users  (alphabetical - no prioritization)

SELECT users.id FROM |
→ users, customers, orders, products  (users FIRST - referenced in SELECT)

SELECT orders.total, users.name FROM |
→ orders, users, customers, products  (orders and users FIRST - both referenced)

WITH active_users AS (SELECT * FROM users WHERE status = 'active')
SELECT * FROM |
→ active_users, users, orders, products, ...
```

**Note:** Derived tables are not suggested as candidates to type in FROM/JOIN in v1 (they are inline subqueries, not selectable by name); but if present in the query, their alias contributes columns to scope.

**CURRENT_TABLE handling:**

`CURRENT_TABLE` may be suggested if:
- It is set
- It is not already present in the current statement

**Rationale:** FROM_CLAUSE is a table-selection context (scope construction). Prioritizing tables already referenced in SELECT improves UX since users typically want to use the same tables. Even if scope already exists elsewhere in the statement (e.g., user editing a completed query), the only restriction is to avoid suggesting tables already present.

#### 4b. With prefix

**Show:**
- CTE names starting with the prefix
- Physical tables starting with the prefix
- `CURRENT_TABLE` (if set, matches prefix, and not already in statement)

**Prioritization:** Same as 4a - if SELECT list contains qualified columns, prioritize those tables first (among matching tables).

**Examples:**
```sql
SELECT * FROM u|
→ users

SELECT users.column FROM u|
→ users (prioritized - already referenced in SELECT)

SELECT products.price FROM u|
→ users (no prioritization - products referenced, not users)

WITH active_users AS (...)
SELECT * FROM a|
→ active_users
```

#### 4c. After comma (multiple tables)

**Trigger:** After comma in FROM clause

**Show:**
- CTE names (if available)
- All physical tables (filtered by prefix if present)

**Examples:**
```sql
SELECT * FROM users, |
→ orders, products, customers, ...

WITH active_users AS (...)
SELECT * FROM users, |
→ active_users, orders, products, ...

SELECT * FROM users, o|
→ orders
```

#### 4d. After table name (space after table)

**Trigger:** After a complete table name followed by space

**Show:**
- Keywords: `JOIN`, `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `CROSS JOIN`, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`
- `AS` (only if the table doesn't already have an alias)

**Examples:**
```sql
SELECT * FROM users |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, AS, WHERE, GROUP BY, ORDER BY, LIMIT
   (AS included because no alias defined yet)

SELECT * FROM users AS u |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, WHERE, GROUP BY, ORDER BY, LIMIT
   (AS excluded because alias 'u' already exists)
```

#### 4e. After AS (alias definition)

**Trigger:** After `AS` keyword in FROM clause

**Show:**
- Nothing (empty list)

**Rationale:** User is typing a custom alias name. No suggestions should interfere with free-form text input.

**Examples:**
```sql
SELECT * FROM users AS |
→ (no suggestions - user types alias freely)

SELECT * FROM users AS u|
→ (no suggestions - user is typing alias name)

SELECT * FROM users AS u |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, WHERE, GROUP BY, ORDER BY, LIMIT
   (alias complete, suggest next clauses)
```

**Note:** Once the alias is complete (followed by space), normal clause keyword suggestions resume.

---

### 5. JOIN_CLAUSE (After JOIN)

**JOIN_CLAUSE is a table-selection context (like FROM).**

It suggests tables, not columns.

**Allowed suggestions:**
- CTE names
- Physical tables
- `CURRENT_TABLE` (as a convenience table candidate, if not already present in the statement)

**Important:** JOIN_CLAUSE is part of scope construction. It may include `CURRENT_TABLE` even if other scope tables already exist. Column suggestion logic must NOT run in this context.

**Trigger:** After `JOIN`, `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, etc.

#### 5a. Without prefix

**Show:**
- CTE names (if available from WITH clause)
- All physical tables
- `CURRENT_TABLE` (if set and not already in statement)

**Examples:**
```sql
SELECT * FROM users JOIN |
→ orders, products, customers, ...

WITH active_users AS (...)
SELECT * FROM users JOIN |
→ active_users, orders, products, ...
```

**Note:** Derived tables are not suggested as candidates to type in FROM/JOIN in v1 (they are inline subqueries, not selectable by name); but if present in the query, their alias contributes columns to scope.

**CURRENT_TABLE handling:**

`CURRENT_TABLE` may be suggested if:
- It is set
- It is not already present in the current statement

**Rationale:** JOIN_CLAUSE is a table-selection context (scope extension). It follows the same rule as FROM_CLAUSE. The only restriction is to avoid suggesting tables already present.

#### 5b. With prefix

**Show:**
- CTE names starting with the prefix
- Physical tables starting with the prefix
- `CURRENT_TABLE` (if set, matches prefix, and not already in statement)

**Examples:**
```sql
SELECT * FROM users JOIN o|
→ orders

WITH active_users AS (...)
SELECT * FROM users u LEFT JOIN a|
→ active_users
```

#### 5c. After table name (space after table)

**Trigger:** After a complete table name in JOIN clause followed by space

**Show:**
- Keywords: `AS`, `ON`, `USING`

**Examples:**
```sql
SELECT * FROM users JOIN orders |
→ AS, ON, USING

SELECT * FROM users u LEFT JOIN products p |
→ ON, USING
```

---

### 5-JOIN_ON. JOIN_ON (Expression Context)

**JOIN_ON is an expression context.**

It suggests columns and functions.

**Column suggestions MUST be restricted strictly to tables in scope:**
- FROM tables
- JOIN tables
- CTEs referenced in the statement
- Derived tables (subquery aliases)

**Critical restrictions:**

See **Scope-Restricted Expression Contexts** section for complete rules.

---

#### 5d. After ON (without prefix)

**Trigger:** After `ON` keyword in JOIN clause

**Show:**
- Columns from scope tables only (qualified, alias-first)
- All functions

**Examples:**
```sql
SELECT * FROM users JOIN orders ON |
→ users.id, orders.user_id, orders.total, ...
→ COUNT, SUM, AVG, ...

SELECT * FROM users u JOIN orders o ON |
→ u.id, o.user_id, o.total, ...
→ COUNT, SUM, AVG, ...
```

#### 5e. After ON (with prefix)

**Trigger:** After `ON` keyword with prefix in JOIN clause

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix

**Examples:**

**Generic prefix (no alias exact match):**
```sql
SELECT * FROM users JOIN orders ON u|
→ Context: JOIN_ON (scope-restricted)
→ Table-name expansion: users.* (all columns from scope table 'users')
→ Column-name matching: orders.user_id (scope table column only)
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ (Database-wide columns excluded - scope restriction active)
```

**Alias exact match:**
```sql
SELECT * FROM users u JOIN orders o ON u|
→ Context: JOIN_ON (scope-restricted)
→ Alias-exact-match mode (u == alias 'u')
→ u.id, u.name, u.email, u.password, u.is_enabled, u.created_at
→ UPPER, UUID, UNIX_TIMESTAMP
```

#### 5f. After comparison operator

**Trigger:** After `=`, `!=`, `<`, `>`, etc. in ON clause

**Show:**
- Literal keywords: `NULL`, `TRUE`, `FALSE`
- Columns from scope tables only (qualified, alias-first) (filtered by prefix if present)
- All functions (filtered by prefix if present)

**Column ranking (HeidiSQL-like UX):**
- Prioritize columns from the **other-side table** (typically the table being joined)
- Then columns from other tables in scope
- This helps users quickly find the matching column

**Other-side table determination:**
- If left side of operator has qualified column (e.g., `u.id = |`) → other-side = all other tables in scope, prioritizing tables introduced by current JOIN
- If left side is from derived table/CTE → other-side = same logic
- If left side is not recognizable → fallback to scope table ordering (FROM > JOIN)

**Critical:** Database-wide columns and `CURRENT_TABLE` are excluded (scope restriction active).

**Examples:**
```sql
SELECT * FROM users JOIN orders ON users.id = |
→ NULL, TRUE, FALSE
→ orders.user_id, orders.id, ...  (orders columns prioritized - other-side table)
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...       (users columns after)

SELECT * FROM users u JOIN orders o ON u.id = |
→ NULL, TRUE, FALSE
→ o.user_id, o.id, ...  (orders columns prioritized - other-side table)
→ u.id, u.name, ...     (users columns after)

SELECT * FROM users u JOIN orders o ON u.id = o|
→ o.user_id, o.id
```

#### 5g. After complete expression (logical operators)

**Trigger:** After a complete condition/expression followed by space in ON clause

**Show:**
- Logical keywords: `AND`, `OR`, `NOT`
- Other keywords: `WHERE`, `ORDER BY`, `GROUP BY`, `LIMIT`

**Examples:**
```sql
SELECT * FROM users JOIN orders ON users.id = orders.user_id |
→ AND, OR, WHERE, ORDER BY, LIMIT

SELECT * FROM users u JOIN orders o ON u.id = o.user_id |
→ AND, OR, NOT, WHERE, ORDER BY, LIMIT
```

---

### 6. WHERE_CLAUSE (After WHERE)

**Trigger:** After `WHERE`, `AND`, `OR`

**Important:** Only show columns from tables specified in FROM and JOIN clauses (using alias if defined, otherwise table name).

#### 6a. Without prefix

**Show:**
- All columns (qualified, alias-first)
- All functions

**Examples:**
```sql
SELECT * FROM users WHERE |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...  (schema order)
→ COUNT, SUM, AVG, ...

SELECT * FROM users u WHERE |
→ u.id, u.name, u.email, u.password, u.is_enabled, u.created_at, ...  (schema order)
→ COUNT, SUM, AVG, ...
```

#### 6b. With prefix

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix

**Examples:**
```sql
SELECT * FROM users WHERE u|
→ Context: WHERE (scope-restricted)
→ Scope: [users]
→ Table-name expansion: users.* (scope table only)
→ Column-name matching: (none - no scope table columns start with 'u' except from table expansion)
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ (DB-wide columns excluded - scope restriction active)

SELECT * FROM users u WHERE u|
→ Context: WHERE (scope-restricted)
→ Alias-exact-match mode (u == alias 'u')
→ u.id, u.name, u.email, u.password, u.is_enabled, u.created_at
→ UPPER, UUID, UNIX_TIMESTAMP
```

#### 6c. After comparison operator

**Trigger:** After `=`, `!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `IN`, etc. in WHERE clause

**Show:**
- Literal keywords: `NULL`, `TRUE`, `FALSE`, `CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`
- All columns (qualified, alias-first) (filtered by prefix if present)
- All functions (filtered by prefix if present)

**Examples:**
```sql
SELECT * FROM users WHERE id = |
→ NULL, TRUE, FALSE
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...
→ COUNT, SUM, ...

SELECT * FROM users WHERE is_enabled = |
→ NULL, TRUE, FALSE
→ users.is_enabled, ...

SELECT * FROM users WHERE created_at > |
→ CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP
→ users.created_at, ...
```

**Note:** User can also type string literals (`'...'`) or numbers directly. Future enhancement: suggest `'...'` as snippet.

#### 6d. After complete expression (logical operators)

**Trigger:** After a complete condition/expression followed by space

**Show:**
- Logical keywords: `AND`, `OR`, `NOT`, `EXISTS`, `IN`, `BETWEEN`, `LIKE`, `IS NULL`, `IS NOT NULL`
- Other keywords: `ORDER BY`, `GROUP BY`, `LIMIT`, `HAVING`

**Examples:**
```sql
SELECT * FROM users WHERE id = 1 |
→ AND, OR, ORDER BY, GROUP BY, LIMIT

SELECT * FROM users WHERE status = 'active' |
→ AND, OR, NOT, ORDER BY, LIMIT

SELECT * FROM users WHERE id > 10 |
→ AND, OR, BETWEEN, ORDER BY, LIMIT
```

---

### 7. ORDER_BY_CLAUSE (After ORDER BY)

**Trigger:** After `ORDER BY`

**Important:** Only show columns from tables specified in FROM and JOIN clauses (using alias if defined, otherwise table name).

#### 7a. Without prefix

**Show:**
- Columns in scope (qualified, alias-first)
- Functions
- Keywords: `ASC`, `DESC`, `NULLS FIRST`, `NULLS LAST`

**Ordering:** Columns first, then functions, then keywords (ASC/DESC). Users typically need to choose the column before specifying sort direction.

**Examples:**
```sql
SELECT * FROM users ORDER BY |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...  (columns first)
→ COUNT, SUM, AVG, ...                         (functions)
→ ASC, DESC, NULLS FIRST, NULLS LAST           (keywords last)

SELECT * FROM users u JOIN orders o ON u.id = o.user_id ORDER BY |
→ u.id, u.name, o.total, o.created_at, ...  (columns first)
→ COUNT, SUM, AVG, ...                      (functions)
→ ASC, DESC                                 (keywords last)
```

#### 7b. With prefix

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix
- Keywords matching the prefix

**Examples:**
```sql
SELECT * FROM users ORDER BY c|
→ Context: ORDER_BY (scope-restricted)
→ Scope: [users]
→ Table-name expansion: (none - no scope table starts with 'c')
→ Column-name matching: users.created_at (scope table column only)
→ Functions: COUNT, CONCAT, COALESCE
→ Keywords: (none starting with 'c')
→ (DB-wide columns excluded - scope restriction active)
```

#### 7c. After column (space after column)

**Show:**
- Keywords: `ASC`, `DESC`, `NULLS FIRST`, `NULLS LAST`

**Examples:**
```sql
SELECT * FROM users ORDER BY created_at |
→ ASC, DESC, NULLS FIRST, NULLS LAST
```

#### 7d. After comma (multiple sort keys)

**Trigger:** After comma in ORDER BY clause

**Show:**
- Columns in scope (qualified, alias-first) (filtered by prefix if present)
- Functions (filtered by prefix if present)

**Examples:**
```sql
SELECT * FROM users ORDER BY created_at DESC, |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...
→ COUNT, SUM, AVG, ...

SELECT * FROM users u ORDER BY u.created_at DESC, n|
→ u.name
```

---

### 8. GROUP_BY_CLAUSE (After GROUP BY)

**Trigger:** After `GROUP BY`

**Important:** Only show columns from tables specified in FROM and JOIN clauses (using alias if defined, otherwise table name).

#### 8a. Without prefix

**Show:**
- Columns in scope (qualified, alias-first)
- Functions

**Examples:**
```sql
SELECT COUNT(*) FROM users GROUP BY |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...
→ DATE, YEAR, MONTH, ...

SELECT COUNT(*) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY |
→ u.id, u.name, u.email, o.status, ...
→ DATE, YEAR, MONTH, ...
```

#### 8b. With prefix

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix

**Examples:**
```sql
SELECT COUNT(*) FROM users GROUP BY s|
→ Table-name expansion: (none - no tables starting with 's')
→ Column-name matching: (none - no columns starting with 's' in users table)
→ Functions: SUM, SUBSTR
```

#### 8c. After comma (multiple group keys)

**Trigger:** After comma in GROUP BY clause

**Show:**
- Columns in scope (qualified, alias-first) (filtered by prefix if present)
- Functions (filtered by prefix if present)

**Examples:**
```sql
SELECT COUNT(*) FROM users GROUP BY status, |
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...
→ DATE, YEAR, MONTH, ...

SELECT COUNT(*) FROM users u GROUP BY u.is_enabled, c|
→ u.created_at
```

---

### 9. HAVING_CLAUSE (After HAVING)

**Trigger:** After `HAVING`

**Important:** Only show columns from tables specified in FROM and JOIN clauses. Focus on aggregate functions.

**Aggregate functions definition:** Predefined set of functions per SQL dialect that perform aggregation operations. Standard set includes: `COUNT`, `SUM`, `AVG`, `MAX`, `MIN`. Vendor-specific additions: `GROUP_CONCAT` (MySQL), `STRING_AGG` (PostgreSQL), `LISTAGG` (Oracle), `ARRAY_AGG`, etc. This list is dialect-dependent and should be maintained as a constant set in the implementation.

#### 9a. Without prefix

**Show:**
- Aggregate functions (prioritized): from the predefined aggregate functions set for current dialect
- Columns in scope (qualified, alias-first)
- Other functions (non-aggregate)

**Ordering:** Aggregate functions first (alphabetical), then columns (schema order - NOT alphabetical), then other functions (alphabetical).

**Rationale:** HAVING typically filters aggregates; prioritizing aggregate functions reduces keystrokes and improves UX.

**Note:** Columns preserve their table definition order (ordinal_position), consistent with global ordering rules.

**Examples:**
```sql
SELECT status, COUNT(*) FROM users GROUP BY status HAVING |
→ COUNT, SUM, AVG, MAX, MIN, ...  (aggregate functions first, alphabetical)
→ users.id, users.name, users.email, ...     (columns in schema order, NOT alphabetical)
→ CONCAT, UPPER, LOWER, ...       (other functions, alphabetical)
```

#### 9b. With prefix

**Show:**
- Aggregate functions matching the prefix (prioritized): from the predefined aggregate functions set for current dialect
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Other functions matching the prefix (non-aggregate)

**Ordering:** Aggregate functions first (alphabetical), then columns (schema order - NOT alphabetical), then other functions (alphabetical).

**Note:** Columns preserve their table definition order (ordinal_position), consistent with global ordering rules.

**Examples:**
```sql
SELECT status, COUNT(*) FROM users GROUP BY status HAVING c|
→ COUNT           (aggregate function first, alphabetical)
→ Table-name expansion: customers.* (columns in schema order)
→ Column-name matching: users.created_at
→ CONCAT, COALESCE (other functions, alphabetical)
```

#### 9c. After comparison operator

**Show:**
- Literal keywords: `NULL`, `TRUE`, `FALSE`
- Aggregate functions
- Columns
- Numbers (user types directly)

**Examples:**
```sql
SELECT status, COUNT(*) FROM users GROUP BY status HAVING COUNT(*) > |
→ NULL, TRUE, FALSE
→ COUNT, SUM, AVG, ...
→ (user can type number)
```

#### 9d. After complete expression (logical operators)

**Trigger:** After a complete condition/expression followed by space

**Show:**
- Logical keywords: `AND`, `OR`, `NOT`, `EXISTS`
- Other keywords: `ORDER BY`, `LIMIT`

**Examples:**
```sql
SELECT status, COUNT(*) FROM users GROUP BY status HAVING COUNT(*) > 10 |
→ AND, OR, ORDER BY, LIMIT

SELECT status, COUNT(*) FROM users GROUP BY status HAVING SUM(total) > 1000 |
→ AND, OR, NOT, ORDER BY, LIMIT
```

---

### 10. LIMIT_OFFSET_CLAUSE (After LIMIT or OFFSET)

**Trigger:** After `LIMIT` or `OFFSET`

**Show:**
- Nothing (user types number directly)

**Examples:**
```sql
SELECT * FROM users LIMIT |
→ (no suggestions - user types number)

SELECT * FROM users LIMIT 10 OFFSET |
→ (no suggestions - user types number)
```

**Note:** No autocomplete suggestions in this context. User types numeric values freely. This avoids noise and keeps the implementation simple.

---

## Ordering Rules

Suggestions are always ordered by priority:

**Ordering Rules apply after applying scope restrictions.**

**CURRENT_TABLE group inclusion is context-dependent:**
- **Expression contexts (JOIN_ON, WHERE, ORDER_BY, GROUP_BY, HAVING):** CURRENT_TABLE group MUST be omitted unless `CURRENT_TABLE` is in scope
- **SELECT_LIST without scope tables:** CURRENT_TABLE group MUST be included (if set)
- **SELECT_LIST with scope tables:** CURRENT_TABLE group MUST be included ONLY if `CURRENT_TABLE` is in scope
- **Table-selection contexts (FROM_CLAUSE, JOIN_CLAUSE):** Not applicable (these suggest tables, not columns)

**Column display format:** Inside every column group, use `alias.column` when the table has an alias in the current statement; otherwise use `table.column`. (Dot-completion returns unqualified column names.)

**Exception:** In HAVING clause context, aggregate functions are prioritized before columns (see section 9a, 9b for details). This is the only context where functions appear before columns.

**Important:** Examples throughout this document may show columns in alphabetical order for readability, but the actual implementation must return columns in their table definition order (ordinal_position from schema). When in doubt, the rule is: preserve schema order, NOT alphabetical order.

1. **Columns from CURRENT_TABLE** (if set in context, e.g., table editor)
   - Use `alias.column` format if the table has an alias in the current query, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.

2. **Columns from tables in FROM clause** (if any)
   - Use `alias.column` format if the table has an alias, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - When multiple FROM tables exist, follow their appearance order in the query; within each table, preserve column definition order.

3. **Columns from tables in JOIN clause** (if any)
   - Use `alias.column` format if the table has an alias, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - When multiple JOIN tables exist, follow their appearance order in the query; within each table, preserve column definition order.

4. **All table.column from database** (all other tables not in FROM/JOIN)
   - Always use `table.column` format (no aliases for tables not in query)
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - Database-wide tables follow a deterministic stable order (schema order or internal stable ordering); within each table, preserve column definition order.
   - **Performance guardrail (applies ONLY to this group):** If no prefix and total suggestions exceed threshold (400 items), skip this group to avoid lag in large databases
   - **No prefix definition:** prefix is `None` OR empty string after trimming whitespace
   - The cap applies only to group 4 (DB-wide columns). Groups 1-3 (CURRENT_TABLE, FROM, JOIN) are always included in full (already loaded/scoped).
   - With prefix: always include this group (filtered results are manageable)

5. **Functions**
   - Alphabetically within this group

6. **Out-of-Scope Table Hints** (SELECT_LIST with scope only)
   - Format: `table_name (+ Add via FROM or JOIN)`
   - Only when prefix matches DB-wide tables but no scope tables/columns
   - See **Out-of-Scope Table Hints** section for details

7. **Keywords**
   - Alphabetically within this group

---

### Alias Prefix Disambiguation

**Applies in expression contexts** (WHERE, ON, ORDER BY, GROUP BY, HAVING, SELECT_LIST)

**Note:** In SELECT_LIST, alias-prefix disambiguation applies only when FROM/JOIN tables are available in the current statement. Without FROM/JOIN, SELECT_LIST shows functions + keywords (see section 3a).

**Note:** In ORDER BY / GROUP BY, exact alias match still activates alias-prefix mode (same as other contexts). However, this is most relevant when the prefix is immediately followed by `.` (dot-completion) or when the typed token exactly equals an alias. Otherwise generic prefix matching applies (column names are common in these contexts).

**Critical: Exact Match Rule**

Alias-prefix mode activates **only if the token exactly equals an alias** (not startswith). This avoids ambiguity with multiple aliases.

**Rule:**
- `token == alias` → alias-prefix mode ✅
- `token.startswith(alias)` → generic prefix mode ❌

**Why exact match?**
- Avoids ambiguity with multiple aliases (e.g., `u` and `us`)
- Prevents false positives (e.g., `user|` should not trigger alias `u`)

**Behavior:**
- If prefix **exactly equals** an alias: show only that alias' columns first (e.g., `u.id`, `u.name`)
- If prefix does NOT exactly match an alias: treat as generic prefix (match table name, column name, or function name)

**Deduplication in alias-exact-match mode:**
- When alias-exact-match mode is active, do NOT also emit the same columns qualified with the base table name
- Deduplicate by underlying column identity (e.g., if showing `u.id`, do not also show `users.id`)
- This avoids redundancy and keeps suggestions clean

**Interaction with CURRENT_TABLE:**
- In alias-prefix mode, CURRENT_TABLE priority is ignored; alias columns are always ranked first
- This avoids unexpected behavior in table editor when using aliases

**Examples:**

**Exact match - Alias-prefix mode:**
```sql
SELECT * FROM users u JOIN orders o WHERE u|
→ token = "u"
→ alias "u" exists → exact match ✅
→ u.id, u.name, u.email, ...  (alias 'u' columns prioritized)
→ UPPER, UUID                 (functions matching 'u')
→ (do not show users.id, users.name - avoid redundancy)
```

**No exact match - Generic prefix mode:**
```sql
SELECT * FROM users u JOIN orders o WHERE us|
→ token = "us"
→ aliases: u, o
→ "us" != "u" and "us" != "o" → no exact match ❌
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...  (table starts with 'us')
→ (generic prefix matching)

SELECT * FROM users u WHERE user|
→ token = "user"
→ alias "u" exists but "user" != "u" → no exact match ❌
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, ...  (table starts with 'user')
→ orders.user_id             (column starts with 'user')
→ (generic prefix matching, NOT alias-prefix)
```

**No alias in query - Generic prefix mode:**
```sql
SELECT * FROM users JOIN orders ON u|
→ token = "u"
→ Context: JOIN_ON (scope-restricted)
→ no aliases defined → generic prefix
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at  (scope table starts with 'u')
→ orders.user_id                     (scope table column starts with 'u')
→ UPPER, UUID                        (functions start with 'u')
→ (Database-wide columns excluded - scope restriction active)
```

**Note:** This rule applies only to tokens without dot. `u.|` triggers Dot-Completion, not alias-prefix disambiguation.

---

### Generic Prefix Matching for Column Contexts

**Applies to all column-expression contexts:** SELECT_LIST, WHERE_CLAUSE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING, and any additional expression contexts where columns can be inserted.

**When NOT in dot-completion and NOT in alias-exact-match mode:**

Given a prefix P (token immediately before cursor, without '.'):

**Return qualified column suggestions that include BOTH:**

**A) Table-name match expansion:**
- For EVERY table T whose name startswith(P), return ALL columns of T as qualified column suggestions
- Qualification: use `alias.column` if table is in current statement scope and has alias, otherwise `table.column`

**B) Column-name match:**
- For EVERY column C (from all tables in scope and all other database tables) whose column name startswith(P), return it as qualified column suggestion
- Qualification: use `alias.column` if table is in current statement scope and has alias, otherwise `table.column`

**Scope restriction:**

**Scope-restricted expression contexts (WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING):**

**Hard line:** In scope-restricted expression contexts, both table-name expansion and column-name matching MUST be computed over scope tables only.

See **Scope-Restricted Expression Contexts** section for complete rules.

**SELECT_LIST without scope tables:**
- `CURRENT_TABLE` columns MUST be included first (if set)
- Database-wide table-name expansion and column-name matching are included

**SELECT_LIST with scope tables:**
- `CURRENT_TABLE` columns MUST be included ONLY if `CURRENT_TABLE` is in scope
- Database-wide table-name expansion and column-name matching are included
- Scope table columns are included with alias-first qualification

**Important rules:**
- Do NOT suggest bare table names in column-expression contexts; only columns (qualified)
- Deduplicate identical suggestions (if a column appears via both A and B, show it once)
- Apply global Ordering Rules (CURRENT_TABLE > FROM > JOIN > DB > FUNCTIONS > KEYWORDS)
- Performance guardrail: see Ordering Rules group 4 (applies only to DB-wide columns when no prefix)

**Examples:**

**SELECT_LIST with scope tables (database-wide columns included):**
```sql
SELECT u| FROM orders
→ Prefix: "u"
→ Context: SELECT_LIST (database-wide columns allowed)
→ Table-name expansion: users table starts with 'u' → users.id, users.name, users.email, users.password, users.is_enabled, users.created_at
→ Column-name matching: orders.user_id (scope table column starts with 'u'), products.unit_price (database-wide column starts with 'u')
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ Combined (deduplicated): users.id, users.name, users.email, users.password, users.is_enabled, users.created_at, orders.user_id, products.unit_price, UPPER, UUID, UNIX_TIMESTAMP
```

**WHERE with scope tables (database-wide columns excluded):**
```sql
SELECT * FROM users u WHERE us|
→ Prefix: "us"
→ Context: WHERE (scope tables exist → database-wide columns disabled)
→ Alias "u" exists but "us" != "u" → NOT alias-exact-match mode
→ Table-name expansion: users table starts with 'us' → u.id, u.name, u.email, u.password, u.is_enabled, u.created_at (uses alias)
→ Column-name matching: restricted to scope tables only (none in this example)
→ Combined: u.id, u.name, u.email, u.password, u.is_enabled, u.created_at
```

**Deduplication example:**
```sql
SELECT u| FROM users
→ Table-name expansion: users.* (all columns)
→ Column-name matching: users.updated_at (if such column exists and starts with 'u')
→ Deduplication: users.updated_at appears in both → show once
```

**Applies to all column contexts:**
- SELECT_LIST: `SELECT u|` or `SELECT u| FROM users`
- WHERE: `SELECT * FROM users WHERE u|`
- JOIN ON: `SELECT * FROM users u JOIN orders o ON u.id = o.u|`
- ORDER BY: `SELECT * FROM users ORDER BY u|`
- GROUP BY: `SELECT * FROM users GROUP BY u|`
- HAVING: `SELECT status, COUNT(*) FROM users GROUP BY status HAVING u|`

**Example - Alias-prefix overrides CURRENT_TABLE:**
```sql
-- CURRENT_TABLE = users (in table editor)
SELECT * FROM users u JOIN orders o WHERE u|
→ token = "u"
→ exact match with alias "u" → alias-prefix mode ✅
→ u.id, u.name, u.email, ...  (alias columns first)
→ CURRENT_TABLE priority ignored in this case
```

**Example in table editor context (CURRENT_TABLE = users, no alias):**
```sql
SELECT u|
→ users.id          (CURRENT_TABLE column)
→ users.name        (CURRENT_TABLE column)
→ orders.user_id    (database column)
→ products.unit     (database column)
→ UPPER             (FUNCTION)
→ UUID              (FUNCTION)
→ UPDATE            (KEYWORD)
```

**Example in table editor context (CURRENT_TABLE = users, with alias 'u'):**
```sql
SELECT * FROM users u WHERE id = 1; SELECT u|
→ u.id              (CURRENT_TABLE column with alias)
→ u.name            (CURRENT_TABLE column with alias)
→ orders.user_id    (database column)
→ products.unit     (database column)
→ UPPER             (FUNCTION)
→ UUID              (FUNCTION)
→ UPDATE            (KEYWORD)
```

**Example in query with FROM:**
```sql
SELECT * FROM users WHERE u|
→ users.id          (FROM table column)
→ users.name        (FROM table column)
→ orders.user_id    (database column)
→ UPPER             (FUNCTION)
→ UPDATE            (KEYWORD)
```

**Example in query with JOIN:**
```sql
SELECT * FROM users u JOIN orders o WHERE u|
→ u.id              (FROM table column with alias)
→ u.name            (FROM table column with alias)
→ o.user_id         (JOIN table column with alias)
→ products.price    (database column)
→ UPPER             (FUNCTION)
→ UPDATE            (KEYWORD)
```

---

### Out-of-Scope Table Hints (SELECT_LIST with Scope)

**Applies ONLY in SELECT_LIST when scope tables already exist (FROM/JOIN present).**

**Purpose:** Keep SELECT scope-safe (no DB-wide columns), while still allowing controlled table discovery.

---

#### Trigger Conditions

In SELECT_LIST with scope tables:

If prefix P satisfies ALL of:
- No alias-exact-match
- No scope table startswith(P)
- No scope column startswith(P)
- BUT one or more physical tables in the database startswith(P)

Then:
- DO NOT suggest DB-wide columns
- Instead, suggest each matching table as an individual hint item

---

#### Suggestion Format

Each table is a separate suggestion item:

```
users        + Add via FROM/JOIN
customers    + Add via FROM/JOIN
```

---

#### Behavior Rules

- Each table is a separate suggestion item
- Suggestion kind: `TABLE_HINT_OUT_OF_SCOPE`
- No column suggestions for out-of-scope tables
- Selecting this item MUST NOT auto-insert JOIN type
- **Minimal v1 behavior:**
  - Either insert just the table name
  - Or act as a non-insert hint (implementation choice)
- JOIN type (INNER/LEFT/RIGHT) remains user decision
- **No badges:** Badges are reserved for column data types (INT, VARCHAR, etc.)

---

#### Ordering (within SELECT_LIST with scope)

1. Scope columns
2. Functions
3. Out-of-scope table hints
4. Keywords

**Important:** Functions MUST appear before table hints.

**Rationale:** When typing `SELECT c| FROM orders`, the user most likely intends `COUNT, COALESCE, CONCAT`, not `customers` (new table). Therefore, functions are prioritized over discovery hints.

---

#### Example

**Assume:**
- Scope = [orders]
- Database tables = [orders, users, customers]

**Query:**
```sql
SELECT u| FROM orders
```

**Suggestions:**
```
→ UPPER
→ UUID
→ users        + Add via FROM/JOIN
→ UPDATE
```

**NOT suggested:**
```
❌ users.id
❌ customers.name
❌ any DB-wide columns
```

---

#### Important Constraints

- Applies ONLY to SELECT_LIST with existing scope
- Does NOT apply to WHERE, JOIN_ON, GROUP_BY, HAVING, ORDER_BY
- Does NOT apply when no scope exists (normal DB-wide allowed case)
- Dot-completion behavior remains unchanged
- Badges are reserved for column data types (INT, VARCHAR, etc.)

---

## Context Rules Summary Matrix

**In case of ambiguity, detailed context sections override this summary matrix.**

This table provides a quick reference for implementers to understand the behavior of each context.

| Context | Scope Required | DB-wide Columns | CURRENT_TABLE | Table Hints |
|---------|---------------|-----------------|---------------|-------------|
| **SELECT_LIST (no scope)** | No | Yes | Yes (if set) | No |
| **SELECT_LIST (with scope)** | Yes | Conditional* | Only if in scope | Yes (if prefix matches) |
| **FROM_CLAUSE** | Scope building | N/A | Yes (if set, not present) | N/A |
| **JOIN_CLAUSE** | Scope extension | N/A | Yes (if set, not present) | N/A |
| **JOIN_ON** | Yes | No | Only if in scope | No |
| **WHERE** | Yes | No | Only if in scope | No |
| **ORDER_BY** | Yes | No | Only if in scope | No |
| **GROUP_BY** | Yes | No | Only if in scope | No |
| **HAVING** | Yes | No | Only if in scope | No |

**Legend:**
- **Scope Required:** Whether the context requires scope tables to exist
- **DB-wide Columns:** Whether columns from tables outside scope can be suggested
- **CURRENT_TABLE:** Whether CURRENT_TABLE columns can be suggested
- **Table Hints:** Whether out-of-scope table hints can be suggested

**Notes:**
- *SELECT_LIST with scope allows DB-wide columns for table-name expansion and column-name matching, but applies Out-of-Scope Table Hints when prefix matches only DB-wide tables
- FROM_CLAUSE and JOIN_CLAUSE are table-selection contexts (scope building/extension), not column contexts
- All scope-restricted expression contexts (JOIN_ON, WHERE, ORDER_BY, GROUP_BY, HAVING) follow the same rules (see **Scope-Restricted Expression Contexts** section)
- Performance guardrail applies only to DB-wide columns group when no prefix (see Ordering Rules group 4)

---

## Implementation Notes

- Context detection uses `sqlglot.parse_one()` with `ErrorLevel.IGNORE` for incomplete SQL
- Dialect is retrieved from `CURRENT_CONNECTION.get_value().engine.value.dialect`
- `CURRENT_TABLE` is an observable: `CURRENT_TABLE.get_value() -> Optional[SQLTable]`
  - Used to prioritize columns from the current table when set
  - Can be `None` if no table is currently selected
- Fallback to regex-based context detection if sqlglot parsing fails

---

### Architecture Notes

**Critical:** Centralize resolution logic to avoid duplication, but distinguish between table-selection and expression contexts.

**Two distinct resolution functions are needed:**

#### 1. Table Selection (FROM_CLAUSE, JOIN_CLAUSE)

```python
def resolve_tables_for_table_selection(
    context: SQLContext,
    scope: QueryScope,
    current_table: Optional[SQLTable] = None,
    prefix: Optional[str] = None
) -> List[TableSuggestion]:
    """
    Resolve table candidates for FROM/JOIN clauses.
    
    Returns tables in priority order:
    1. CTE names (if available from WITH clause)
    2. Physical tables from database
    3. CURRENT_TABLE (if set and not already in statement) - convenience shortcut
    
    Filtering:
    - If prefix provided, filter by startswith(prefix)
    - Exclude tables already present in the statement
    
    Note: This is table-selection, not column resolution.
    CURRENT_TABLE can appear even if scope tables already exist.
    """
    pass
```

#### 2. Expression Contexts (SELECT_LIST, WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING)

```python
def resolve_columns_for_expression(
    context: SQLContext,
    scope: QueryScope,
    current_table: Optional[SQLTable] = None,
    prefix: Optional[str] = None
) -> List[ColumnSuggestion]:
    """
    Resolve columns for expression contexts with scope-aware restrictions.
    
    Behavior depends on context and scope:
    
    SCOPE-RESTRICTED contexts (WHERE, JOIN_ON, HAVING, ORDER_BY, GROUP_BY):
      - See Scope-Restricted Expression Contexts section for complete rules
      - Priority: FROM tables > JOIN tables
    
    SELECT_LIST context:
      - If NO scope tables:
        * Include CURRENT_TABLE columns (if set)
        * Include database-wide columns
      - If scope tables exist:
        * CURRENT_TABLE included only if in scope; otherwise ignored
        * Include scope table columns
        * Include database-wide columns (for table-name expansion and column-name matching)
    
    All columns use alias.column format when alias exists, otherwise table.column.
    """
    pass
```

**Benefits:**
- Clear separation between table-selection and expression contexts
- Enforces scope restriction rules consistently
- Single source of truth for each context type
- Easier to test and maintain
- Avoids logic duplication

**Architectural improvement (optional):**

For cleaner architecture, consider using a `QueryScope` object instead of passing multiple parameters:

```python
@dataclass
class QueryScope:
    from_tables: List[TableReference]
    join_tables: List[TableReference]
    derived_tables: List[DerivedTable]
    ctes: List[CTE]
    current_table: Optional[SQLTable]
    aliases: Dict[str, TableReference]  # alias -> table mapping

def resolve_columns_in_scope(
    scope: QueryScope,
    prefix: Optional[str] = None
) -> List[ColumnSuggestion]:
    """Pure function - no global context dependency."""
    pass
```

This makes the function pure and easier to test.

---

**Tables in Scope Definition (with CTEs and Derived Tables):**

With CTEs and subquery aliases, "tables in scope" is not just physical tables from FROM/JOIN. The priority order is:

```
tables_in_scope = [
    1. Derived tables (subquery alias) in FROM/JOIN
    2. CTEs referenced in FROM/JOIN
    3. Physical tables in FROM/JOIN
]
```

**Column resolution follows this order:**

**Important:** Include CURRENT_TABLE columns only when allowed by context rules:
- SELECT_LIST with no scope tables, OR
- CURRENT_TABLE is in scope (present in FROM/JOIN)

Otherwise omit CURRENT_TABLE entirely.

1. **CURRENT_TABLE columns** (if allowed by context rules) - use alias if table has alias in query
2. **Derived table columns** - use alias (only sensible name)
3. **CTE columns** - use CTE name (acts as alias)
4. **Physical table columns from FROM** - use alias if defined
5. **Physical table columns from JOIN** - use alias if defined
6. **Database columns** (all other tables, with guardrail - only in SELECT_LIST or when no scope restriction)

**Example:**
```sql
WITH active_users AS (SELECT id, name FROM users WHERE status = 'active')
SELECT * FROM (SELECT id, total FROM orders) AS o 
JOIN active_users au ON o.id = au.id
WHERE |
→ o.id, o.total           (derived table, priority 2)
→ au.id, au.name          (CTE, priority 3)
→ (no physical tables in this query)
```

**Note:** Alias-first is fundamental here - for derived tables and CTEs, the alias/CTE name is often the **only** sensible name (no underlying physical table name).

### Scope Handling (Subqueries and CTEs)

**Important:** Scope handling for subqueries and CTEs may be simplified initially.

**Current approach:**
- Use the nearest FROM/JOIN scope of the current statement
- For simple subqueries in WHERE clause (e.g., `WHERE x IN (SELECT ...)`), context detection operates on the outer query scope
- Full nested scope resolution (tracking which tables are available in inner vs outer queries) is a future enhancement

**Examples:**
```sql
-- Simple case: outer query scope
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders) AND |
→ Suggests columns from 'users' (outer query scope)

-- Future enhancement: inner query scope
SELECT * FROM users WHERE id IN (SELECT | FROM orders)
→ Should suggest columns from 'orders' (inner query scope)
→ Initial implementation may use outer scope or simplified logic
```

**CTE Support (WITH clauses):**

CTEs are increasingly common and should be considered for v1 implementation:

```sql
WITH active_users AS (SELECT * FROM users WHERE status = 'active')
SELECT * FROM active_users WHERE |
→ active_users.id, active_users.name, ...  (CTE columns)
```

**Basic CTE support:**
- Treat CTEs as available tables in the query scope
- CTE name acts like a table name in FROM/JOIN contexts
- Columns from CTE should be resolved (if CTE definition is parseable)
- **CTE visibility is limited to the statement where they are defined**

**Example - CTE scope:**
```sql
WITH a AS (...)
SELECT * FROM a;
SELECT * FROM |
→ CTE 'a' is NOT visible here (different statement)
→ Show only physical tables
```

**Advanced CTE features (future enhancement):**
- Recursive CTEs
- Multiple CTEs with dependencies
- CTE column aliasing

**Subquery Aliases (Derived Tables):**

Subqueries with aliases (derived tables) should also be considered for v1:

```sql
SELECT * FROM (SELECT id, name FROM users) AS u WHERE |
→ u.id, u.name  (derived table columns)
```

**Basic support:**
- Treat aliased subquery as a table in scope
- Resolve columns from the subquery SELECT list (if parseable)
- Alias acts like a table name

**Note:** This is similar to CTE support but inline. If CTEs are supported, derived tables should follow the same pattern.

**Window Functions (Future Enhancement):**

Window functions with OVER clause are common in modern SQL:

```sql
SELECT *, ROW_NUMBER() OVER |
→ (PARTITION BY, ORDER BY)

SELECT *, ROW_NUMBER() OVER (PARTITION BY |
→ Columns in scope (qualified, alias-first)

SELECT *, ROW_NUMBER() OVER (PARTITION BY status ORDER BY |
→ Columns in scope (qualified, alias-first)
```

**Future support:**
- Detect OVER clause context
- After `OVER (` suggest keywords: `PARTITION BY`, `ORDER BY`
- After `PARTITION BY` suggest columns in scope
- After `ORDER BY` suggest columns in scope + `ASC`, `DESC`

**Note:** This is a specialized context that can be added after core functionality is stable.

---

### Potential Challenges

**sqlglot Parsing of Incomplete SQL:**

Test thoroughly with partial queries. You might need a hybrid approach that falls back to regex faster than expected.

**Examples of challenging cases:**
```sql
SELECT id, name FROM users WHERE |
→ sqlglot may parse successfully

SELECT id, name FROM users WH|
→ sqlglot may fail, need regex fallback

SELECT * FROM users WHERE status = '|
→ Incomplete string, sqlglot may fail
```

**Recommendation:**
- Use `sqlglot.parse_one()` with `ErrorLevel.IGNORE` as primary approach
- Implement robust regex fallback for common patterns
- Test with many incomplete query variations
- Log parsing failures to identify patterns that need special handling

**Fallback trigger rule:**
- If sqlglot does not produce a useful AST → fallback to regex
- If cursor position cannot be mapped to an AST node → fallback to regex
- Log: `(dialect, snippet_around_cursor, reason)` for building golden test cases

**Example logging:**
```python
if not ast or not can_map_cursor_to_node(ast, cursor_pos):
    logger.debug(
        "sqlglot_fallback",
        dialect=dialect,
        snippet=text[max(0, cursor_pos-50):cursor_pos+50],
        reason="no_useful_ast" if not ast else "cursor_mapping_failed"
    )
    return regex_based_context_detection(text, cursor_pos)
```

**Benefit:** Build real-world golden tests from production edge cases

**Cursor Position Context:**

Make sure context detection knows exactly where the cursor is, not just what's before it.

**Critical distinction:**
```sql
SELECT | FROM users
→ Context: SELECT_LIST (before FROM)
→ Show: columns, functions

SELECT id| FROM users
→ Context: After column name (before FROM)
→ Show: FROM, AS, etc. (comma is never suggested)
```

**Implementation note:**
- Extract text before cursor: `text[:cursor_pos]`
- Extract text after cursor: `text[cursor_pos:]` (for context validation)
- Check if cursor is immediately after a complete token vs in the middle
- Use both left and right context for accurate detection

---

### Performance Optimization

**Large Schemas:**

The 400-item guardrail is good, but additional optimizations are recommended:

**Debouncing:**
- Delay autocomplete trigger by 150-300ms after last keystroke
- Avoids excessive computation while user is typing rapidly
- Cancel pending autocomplete requests if new input arrives

**Caching:**
- Cache database schema (tables, columns) in memory
- Refresh only when schema changes (DDL operations detected)
- Cache parsed query structure for current statement
- Invalidate cache when query changes significantly

**Schema cache invalidation triggers:**
- DDL operations: `CREATE`, `ALTER`, `DROP`, `TRUNCATE`
- Database/schema change (e.g., `USE database`)
- Manual refresh (user-triggered)
- Reconnection to database
- **Best-effort approach:** Some engines (e.g., PostgreSQL) support event listeners for schema changes; if not available, invalidate on DDL keyword detection or periodic refresh

**Lazy Loading:**
- Load column details only when needed (not all upfront)
- For large tables (>100 columns), load columns on-demand
- Consider pagination for very large suggestion lists

**Example implementation:**
```python
class AutocompleteCache:
    def __init__(self):
        self._schema_cache = {}  # {database: {table: [columns]}}
        self._last_query_hash = None
        self._parsed_query_cache = None
    
    def get_columns(self, table: str) -> List[Column]:
        if table not in self._schema_cache:
            self._schema_cache[table] = fetch_columns(table)
        return self._schema_cache[table]
    
    def invalidate_schema(self):
        self._schema_cache.clear()
```

---

### Statement Separator

The statement separator is NOT hardcoded.

It is determined at runtime using:

```
effective_separator = user_override or engine_default
```

Constraints:
- The separator MUST be a single character.
- Multi-character separators (e.g., "GO") are NOT supported.
- Default for all supported engines (MySQL, MariaDB, PostgreSQL, SQLite) is `";"`

Validation:
- If `user_override` is set, it MUST be exactly 1 character after trimming (e.g., `" ; "` is invalid).
- If invalid → ignore override and fallback to `engine_default`.

All multi-query splitting logic MUST use the effective separator.
Hardcoding `";"` is forbidden.

---

### Multi-Query Support

**Important:** When multiple queries are present in the editor (separated by the effective statement separator), context detection must operate on the **current query** (where the cursor is), not the entire buffer.

**Implementation approach:**
1. Find statement boundaries by detecting the effective separator
2. Extract the query containing the cursor position
3. Run context detection only on that query

**Edge cases:**
- If cursor is on the separator, treat it as "end of previous statement".
- Empty statements are ignored (no context); fallback to EMPTY.

**Example:**
```sql
SELECT * FROM users WHERE id = 1;
SELECT * FROM orders WHERE |  ← cursor here
SELECT * FROM products;
```

Context detection should analyze only: `SELECT * FROM orders WHERE |`

**Critical:**
- Do NOT use simple `text.split(effective_separator)`
- The separator must be ignored inside:
  - Strings (`'...'`, `"..."`)
  - Comments (`--`, `/* */`)
  - Dollar-quoted strings (PostgreSQL: `$$...$$`)

**Recommended approach:**
- Use sqlglot lexer/tokenizer to find statement boundaries (handles strings/comments correctly)
- Or implement robust separator detection with string/comment awareness

### Multi-Word Keywords

Multi-word keywords (e.g., `ORDER BY`, `GROUP BY`, `IS NULL`, `IS NOT NULL`, `NULLS FIRST`) are suggested as a single completion item but inserted verbatim.

**Matching rule:** Use `startswith()` on normalized text (single spaces, case-insensitive). Normalize both the user input and the keyword before matching.

**Examples:**
- User types `ORDE|` → normalized input: `"orde"` → matches `ORDER BY` (normalized: `"order by"`) ✅
- User types `ORDER B|` → normalized input: `"order b"` → matches `ORDER BY` (normalized: `"order by"`) ✅
- User types `NULLS L|` → normalized input: `"nulls l"` → matches `NULLS LAST` (normalized: `"nulls last"`) ✅
- User types `IS N|` → normalized input: `"is n"` → matches `IS NULL`, `IS NOT NULL` ✅

---

### Spacing After Completion

- **Keywords:** Space added after keywords (e.g., `SELECT `, `FROM `, `WHERE `, `JOIN `, `AS `)
  - Multi-word keywords are treated as keywords for spacing (space appended after `ORDER BY`, `GROUP BY`, `IS NULL`, etc.)
- **Columns:** No space added (e.g., `users.id|` allows immediate `,` or space)
- **Tables:** No space added (e.g., `users|` allows immediate space or alias)
- **Functions:** No space added by default
  - **Future enhancement:** Consider function snippets with cursor positioning (e.g., `COUNT(|)` where `|` is cursor position)
  - This would require snippet support in the autocomplete system
