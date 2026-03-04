# SQL Autocomplete Rules

This document defines the autocomplete behavior for each SQL context.

---

## Glossary

This section defines key terms used throughout the document to avoid ambiguity.

### Statement vs Query vs Buffer

- **Buffer**: The entire text content in the SQL editor, potentially containing multiple queries
- **Statement**: A single SQL query separated by the effective statement separator (e.g., `;` or `GO`)
- **Query**: Synonym for statement - a single executable SQL command
- **Current statement**: The statement where the cursor is currently positioned

**Example:**
```sql
SELECT * FROM users;    -- Statement 1
SELECT * FROM orders;   -- Statement 2 (current statement if cursor is here)
SELECT * FROM products; -- Statement 3
```

### Scope and Tables

- **Scope tables**: Tables/CTEs/derived tables that appear in the current statement's FROM/JOIN clauses
  - Includes: physical tables, CTEs (Common Table Expressions), derived tables (subquery aliases)
  - Priority order: derived tables > CTEs > physical tables (see **Tables in Scope Definition** section)
- **In scope**: A table is "in scope" if it appears in the FROM/JOIN of the current statement
- **Out of scope**: A table exists in the database but is not referenced in the current statement's FROM/JOIN
- **DB-wide tables**: All physical tables in the database, regardless of scope
- **CURRENT_TABLE**: The table currently selected in the table editor UI (optional, may be `None`)

### Scope Classification

The scope classification determines which columns are suggested in expression contexts:

- **SCOPED**: Explicit scope exists via FROM/JOIN clauses in the current statement
  - Example: `SELECT id, | FROM users` → scope = `users` table
  - Example: `SELECT * FROM users u JOIN orders o ON u.id = o.user_id; SELECT u.id, |` → scope = `u`, `o` tables
  - Behavior: Suggest only columns from scope tables (qualified if multiple tables, unqualified if single table)

- **VIRTUAL_SCOPED**: Implicit scope inferred from context without FROM/JOIN
  - Via qualified columns: `SELECT users.id, |` → virtual scope = `users` (inferred from qualified column)
  - Via CURRENT_TABLE: `SELECT id, |` with CURRENT_TABLE=users → virtual scope = `users`
  - **Important:** When VIRTUAL_SCOPED via CURRENT_TABLE (no FROM/JOIN), columns MUST be qualified (e.g., `users.id`, not `id`)
  - Behavior: Suggest columns from the inferred table(s), but allow DB-wide suggestions with prefix

- **NO_SCOPED**: No scope information available
  - No FROM/JOIN in current statement
  - No qualified columns to infer scope from
  - No CURRENT_TABLE set
  - Example: `SELECT id, |` with CURRENT_TABLE=null and no qualified columns
  - Behavior: Suggest only functions (no columns without prefix)

### Prefix and Token

- **Token**: A valid SQL identifier matching `^[A-Za-z_][A-Za-z0-9_]*$` (or dialect-equivalent)
  - Must start with letter or underscore (NOT digit)
  - Can contain letters, digits, underscores after first character
  - Dialect-aware: some dialects support `$`, `#`, or unicode in identifiers
- **Prefix**: The token immediately before the cursor, without containing `.`
- **Dot-completion**: When the token before cursor contains `.` (e.g., `users.` or `u.`)

**Examples:**
- `SELECT u|` → prefix = `"u"`, triggers prefix matching
- `SELECT u.i|` → NOT a prefix (contains dot), triggers dot-completion on `u`
- `SELECT ui|` → prefix = `"ui"`, triggers prefix matching
- `SELECT 1|` → NOT a token (starts with digit), no prefix matching

### Context Types

- **Table-selection context**: Context where tables are suggested (FROM_CLAUSE, JOIN_CLAUSE)
- **Expression context**: Context where columns/functions are suggested (SELECT_LIST, WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING)
- **Scope-restricted expression context**: Expression context that MUST limit suggestions to scope tables only (WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING)

### Qualification

- **Qualified column**: Column name prefixed with table/alias (e.g., `users.id` or `u.id`)
- **Unqualified column**: Column name without prefix (e.g., `id`)
- **Alias-first qualification**: Use `alias.column` when alias exists, otherwise `table.column`

---

## Important Note on Column Ordering in Examples

**All column suggestions throughout this document preserve their table definition order (schema order / ordinal_position), NOT alphabetical order.**

Examples may show columns in sequences that appear alphabetical for readability, but the implementation MUST return columns in their actual schema order. When in doubt, the rule is: **preserve schema order, NOT alphabetical order**.

For clarity, examples use the following assumed schema order:
- `users`: id, name, email, password, is_enabled, created_at
- `orders`: id, user_id, total, created_at
- `products`: id, name, unit_price, stock

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
- `u.id, u.name, u.email, u.password, u.is_enabled, u.created_at` (CURRENT_TABLE in scope via alias 'u', schema order)
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
-- Context: WHERE clause (scope-restricted expression context)
-- Scope: orders (from current statement's FROM clause)
-- Prefix: "u"
-- Check aliases: no alias "u" in this statement
-- Generic prefix (scope-restricted): show orders.user_id, UPPER, UUID, etc.
-- DB-wide columns excluded (scope restriction active)
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

**Prefix** = the identifier token immediately before the cursor, matching `^[A-Za-z_][A-Za-z0-9_]*$` (or equivalent for dialect).

**Rules:**
- Must start with letter or underscore (NOT digit)
- Can contain letters, digits, underscores after first character
- Match is case-insensitive
- Output preserves original form (alias/table/column name)
- If token contains `.` → **not a prefix**: triggers Dot-Completion instead

**Cursor Position Handling:**
- **Cursor at end of token** (e.g., `SELECT u|`): prefix = entire token before cursor
- **Cursor in middle of token** (e.g., `SEL|ECT`, `users.na|me`): prefix = partial token before cursor
  - Text after cursor is ignored for matching
  - Selecting a suggestion replaces the entire token (not just the part before cursor)

**Examples:**
```sql
SELECT u|
→ Prefix: "u" (triggers prefix matching)

SELECT u.i|
→ NOT a prefix (contains dot)
→ Triggers Dot-Completion on table/alias "u"

SEL|ECT
→ Prefix: "SEL" (cursor in middle of token)
→ Suggestions: SELECT
→ Selection replaces entire token "SELECT" (removes "ECT")

users.na|me
→ Dot-completion on "users"
→ Prefix: "na" (cursor in middle of token)
→ Suggestions: name
→ Selection replaces entire token "name" (removes "me")

SELECT ui|
→ Prefix: "ui" (triggers prefix matching)
```

**This distinction is critical:**
- `u.i|` → Dot-Completion (show columns of table/alias `u` starting with `i`)
- `ui|` → Prefix matching (show items starting with `ui`)

---

### Column Qualification (table.column vs alias.column)

**Qualification rules:**

1. **Single table in scope (no ambiguity):** 
   - **No prefix:** Use **unqualified** column names (e.g., `id`, `name`)
   - **With prefix:**
     - **Column-name match** (Generic Prefix Matching rule B): Use **unqualified** column names (e.g., `name`)
     - **Table-name expansion** (Generic Prefix Matching rule A): Use **qualified** column names (e.g., `users.id`)
     - **Order when BOTH match:**
       1. Column-name matches **unqualified** (e.g., `id`, `item_name`)
       2. Column-name matches **qualified** (e.g., `items.id`, `items.item_name`)
       3. Table-name expansion remaining columns **qualified** (e.g., `items.*` excluding already shown columns)
       4. Functions
2. **Multiple tables in scope:** Use qualified names with alias-first preference:
   - If alias exists: `alias.column` (e.g., `u.id`)
   - If no alias: `table.column` (e.g., `users.id`)

3. **CRITICAL - Aliased tables:** When a table has an alias, the original table name CANNOT be used for qualification. SQL will reject `table.column` when an alias exists.
   - **Correct:** `FROM users u WHERE u.id = 1` (use alias)
   - **INCORRECT:** `FROM users u WHERE users.id = 1` (SQL error - table name not accessible)
   - **Implication for autocomplete:** If prefix does not match the alias and does not match any column name, return empty suggestions. Do NOT suggest qualified columns with the original table name.
   - **Example:** `FROM users u WHERE us|` → NO suggestions (prefix 'us' does not match alias 'u' or any column)

4. **Consistency rule - Qualified context:** If the query already uses qualified columns (e.g., `users.id`), suggestions should be qualified for consistency, even for single table contexts.
   - This applies when the user has explicitly written `table.column` or `alias.column` in the query
   - Helps maintain consistent code style within the same query

**Rationale:** When only one table is in scope, qualification adds noise without value. However, when prefix matches a table name, qualified names clarify the source of the match and help users discover dot-completion. Column-name matches are prioritized (unqualified) because they are more specific than table-name expansion. When the user has already qualified columns in the query, maintaining that style keeps the code consistent.

**Examples:**
```sql
-- Single table, no prefix: unqualified
SELECT * FROM users WHERE |
→ id, name, email, password, is_enabled, created_at

-- Single table, prefix matches ONLY column name: unqualified
SELECT * FROM users WHERE n|
→ name  (column-name match, unqualified)
→ (functions starting with 'n' if any)

-- Single table, prefix matches ONLY table name: qualified (table-name expansion)
SELECT * FROM users WHERE u|
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at  (table-name expansion, qualified)
→ UPPER, UUID, UNIX_TIMESTAMP  (functions)

-- Single table, prefix matches BOTH column name AND table name: both shown
-- Example: table 'items' with columns: id, item_name, stock, price
SELECT * FROM items WHERE i|
→ id, item_name  (column-name match, unqualified - FIRST)
→ items.id, items.item_name  (column-name match, qualified - SECOND)
→ items.stock, items.price  (table-name expansion remaining, qualified - THIRD)
→ IF, IFNULL  (functions - FOURTH)

-- Single table with alias, no prefix: unqualified
SELECT * FROM users u WHERE |
→ id, name, email

-- Multiple tables: qualified (alias-first)
SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE |
→ u.id, u.name, u.email, o.user_id, o.total, o.created_at

-- Consistency rule: qualified context (single table but query uses qualified)
SELECT * FROM users WHERE users.id = c|
→ users.created_at  (qualified for consistency, even though single table)
→ COALESCE, CONCAT, COUNT  (functions)
```

**Note:** This rule applies to all contexts: SELECT_LIST, WHERE, JOIN ON, ORDER BY, GROUP BY, HAVING.

**Exception:** Dot-completion mode always returns **unqualified** column names (e.g., `id`, `name`), regardless of scope table count. See **Dot-Completion** section for details.

---

### Comma and Whitespace Behavior

**Universal rule for all contexts:**

- **Comma is never suggested** as an autocomplete item
- If the user types `,` → they want another item → apply "next-item" rules for that context (e.g., after comma in SELECT list, show columns/functions)
- If the user types **whitespace** after a completed identifier/expression → treat it as "selection complete" → show only keywords valid in that position (clause keywords or context modifiers like `ASC`, `DESC`, `NULLS FIRST`, etc.)
- **Exception:** If whitespace follows an incomplete/invalid keyword (e.g., `SEL |` where `SEL` is not a recognized keyword) → show nothing (no suggestions)

**Rationale:** Whitespace signals intentional pause/completion. Comma signals continuation. Incomplete keywords with whitespace are ambiguous and should not trigger suggestions. This distinction applies consistently across all SQL contexts.

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

**Special case - Qualified column in SELECT_LIST:**
```sql
SELECT users.id |
→ Whitespace after qualified column → suggest contextual keywords + plain keywords
→ Suggestions: FROM users, AS, FROM

SELECT users.id F|
→ Whitespace after qualified column + prefix 'F'
→ Suggest: FROM {table} (contextual keyword) + FROM (plain keyword)
→ Suggestions: FROM users, FROM

SELECT users.id W|
→ Whitespace after qualified column + prefix 'W'
→ WHERE is syntactically invalid (cannot follow SELECT item directly)
→ Suggestions: [] (empty - no valid suggestions)
```

**Terminology:**
- **Contextual keyword**: A keyword enriched with context-specific information (e.g., `FROM users` where `users` is inferred from the qualified column)
- **Plain keyword**: Generic keyword without context (e.g., `FROM`, `AS`)

**Ordering:** Contextual keywords MUST appear before plain keywords.

**Rationale:** When a qualified column is used (e.g., `users.id`), the table name is already known. Suggesting `FROM {table}` as a contextual keyword helps the user quickly add the FROM clause with the correct table. However, `FROM` plain keyword is also shown because the user might want to use a different table (e.g., `FROM orders AS users`). Contextual keywords are more specific and useful than plain keywords, so they appear first. With prefix, filter contextual keywords + plain keywords by prefix. Some keywords (e.g., WHERE) are syntactically invalid after SELECT item and should not be suggested.

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
- The column **immediately to the LEFT** of the current operator MUST NOT be suggested
- **Rationale:** Suggesting the same column on both sides (e.g., `WHERE users.id = users.id`) is redundant and not useful

**Definition of "column immediately to the LEFT":**
- Parse the expression immediately to the left of the operator using AST
- If the expression root is (or contains as root) a **column reference** (qualified or unqualified):
  - Exclude that column from suggestions
- If the expression root is a **function call, cast, or literal**:
  - Do NOT exclude any columns (even if the function contains columns as arguments)

**Examples:**
```sql
WHERE users.id = |
→ Exclude: users.id (direct column reference)

WHERE (users.id) = |
→ Exclude: users.id (parentheses ignored, root = column reference)

WHERE users.id::int = |
→ Exclude: users.id (cast ignored, root = column reference)

WHERE COALESCE(users.id, 0) = |
→ Do NOT exclude users.id (root = function call, not column reference)

WHERE users.id + 1 = |
→ Exclude: users.id (binary expression, root contains column reference)

WHERE users.id = orders.user_id AND status = |
→ Exclude only: status (immediately left of current operator)
→ Do NOT exclude: users.id, orders.user_id (not immediately left)
```

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
- MUST NOT suggest `CURRENT_TABLE` if it is already present in the current statement
- **Statement definition:** The current query where the cursor is located, separated by the effective statement separator (not the entire buffer)
- Purpose: convenience shortcut for selecting the current table

**Example:**
```sql
SELECT * FROM users; SELECT * FROM |
```
In this case, `users` is NOT present in the current statement (second query), so it MAY be suggested if it is `CURRENT_TABLE`.

---

#### Expression Contexts (JOIN_ON, WHERE, ORDER_BY, GROUP_BY, HAVING)

These are **scope-restricted expression contexts** (see **Scope-Restricted Expression Contexts** section).

These contexts suggest **columns** from scope tables only.

---

#### SELECT_LIST Context (Special Case)

**If statement has NO scope tables (no FROM/JOIN yet):**
- Without prefix: `CURRENT_TABLE` columns MUST be included first (if set)
- With prefix: `CURRENT_TABLE` columns MUST be included ONLY if they match the prefix via:
  - Column-name match (e.g., `SELECT na|` → `name` from CURRENT_TABLE)
  - Table-name expansion (e.g., `SELECT u|` and CURRENT_TABLE is `users` → suggest `users.*` columns)
- Database-wide columns MUST be included ONLY if prefix exists (guardrail: avoid noise when no prefix)
- Functions and keywords are included

**If statement HAS scope tables (FROM/JOIN exists):**
- `CURRENT_TABLE` columns MUST be included ONLY if `CURRENT_TABLE` is in scope
- If `CURRENT_TABLE` is not in scope, it MUST be ignored
- Database-wide columns MUST NOT be suggested
- Scope table columns are included with alias-first qualification
- **Exception:** If prefix matches DB-wide tables but no scope tables/columns, suggest Out-of-Scope Table Hints (see dedicated section)

---

### Dot-Completion (table.column or alias.column)

**Trigger:** After `table.` or `alias.` in any SQL context

**Show:**
- Columns of the specific table/alias (filtered by prefix if present)

**Scope lookup:**
- Dot-completion works for physical tables, aliases, derived tables (subquery aliases), and CTEs
- The table/alias is resolved from the current statement's scope (FROM/JOIN clauses)
- For derived tables and CTEs, columns are shown if their column list is known/parseable
- If table/alias not found in scope, return empty suggestions (see Edge Case #8)

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

-- Dot-completion on CTE alias
WITH active_users AS (SELECT id, name FROM users WHERE status = 'active')
SELECT au.| FROM active_users au
→ id, name  (CTE columns, schema order)

-- Dot-completion on derived table alias
SELECT dt.| FROM (SELECT id, total FROM orders) AS dt
→ id, total  (derived table columns, schema order)
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
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- All functions

**Examples:**
```sql
SELECT * FROM users WHERE id = 1; SELECT |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified)
→ COUNT, SUM, AVG, ...

SELECT * FROM users u JOIN orders o ON u.id = o.user_id; SELECT |
→ u.id, u.name, o.user_id, o.total, ...  (multiple tables: qualified)
→ COUNT, SUM, AVG, ...
```

#### 3b. With prefix

**Show:**
- Columns matching the prefix (see **Generic Prefix Matching for Column Contexts** section)
- Functions matching the prefix
- **Note:** Keywords are NOT included (syntactically invalid in SELECT list, e.g., `SELECT SELECT` or `SELECT UPDATE`)

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
→ users.id, users.name, users.email, ... (CURRENT_TABLE via table-name expansion)
→ user_sessions.* (other tables starting with 'u')
→ orders.user_id, products.unit_price (DB-wide columns starting with 'u')
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
```

**FROM/JOIN exists, CURRENT_TABLE not in scope (CURRENT_TABLE ignored):**
```sql
-- Assume CURRENT_TABLE = users
SELECT u| FROM orders
→ orders.user_id (scope table column starting with 'u')
→ UPPER, UUID, UNIX_TIMESTAMP (functions)
→ users        + Add via FROM/JOIN (Out-of-Scope Table Hint)
→ (CURRENT_TABLE ignored - not in scope)
→ (DB-wide columns excluded - scope restriction active)
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
- All columns (unqualified if single table, qualified with alias-first if multiple tables) (filtered by prefix if present)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- All functions (filtered by prefix if present)

**Special case - previous item is qualified:**
- If the select item immediately before the comma is a qualified column reference (`table.column` or `alias.column`), suggest columns from that same qualifier first.
- This applies even when there is no FROM/JOIN scope and no prefix.
- Do NOT include database-wide columns from other tables unless a prefix exists.

**Rationale:** The user has already chosen a specific table/alias by qualifying the previous select item, so suggesting the remaining columns from the same qualifier is useful and avoids noisy DB-wide suggestions.

**Examples:**
```sql
-- Single table, no prefix: unqualified
SELECT col1, |
→ id, name, email, ...  (single table: unqualified)
→ COUNT, SUM, AVG, ...

-- Single table, no FROM in current statement, no prefix: unqualified
SELECT * FROM users u WHERE id = 1; SELECT id, |
→ id, name, email, ...  (single table: unqualified)
→ COUNT, SUM, AVG, ...

-- Single table, prefix matches column name: unqualified
SELECT id, n|
→ name  (column-name match, unqualified)

-- Single table, prefix matches table name: qualified (table-name expansion)
SELECT * FROM users; SELECT id, u|
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at  (table-name expansion, qualified)
→ UPPER, UUID, UNIX_TIMESTAMP

-- Multiple tables: qualified
SELECT * FROM users u JOIN orders o ON u.id = o.user_id; SELECT u.id, |
→ u.id, u.name, u.email, o.user_id, o.total, o.created_at  (multiple tables: qualified)
→ COUNT, SUM, AVG, ...
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
- `CURRENT_TABLE` (if set and not already present in current statement)

**Prioritization/Filtering:** If SELECT list contains qualified columns (e.g., `SELECT users.id`), suggest ONLY those referenced tables in FROM suggestions. When multiple tables are referenced, follow their left-to-right appearance order in the SELECT list.

**Examples:**
```sql
SELECT * FROM |
→ customers, orders, products, users  (alphabetical - no prioritization)

SELECT users.id FROM |
→ users  (ONLY referenced table from qualified SELECT column)

SELECT orders.total, users.name FROM |
→ orders, users  (ONLY referenced tables, left-to-right from SELECT)

WITH active_users AS (SELECT * FROM users WHERE status = 'active')
SELECT * FROM |
→ active_users, users, orders, products, ...
```

**Note:** Derived tables are not suggested as candidates to type in FROM/JOIN in v1 (they are inline subqueries, not selectable by name); but if present in the query, their alias contributes columns to scope.

**CURRENT_TABLE handling:**

`CURRENT_TABLE` may be suggested if:
- It is set
- It is not already present in the current statement

**Table re-suggestion policy (self-join support):**

Physical tables already present in FROM/JOIN:
- **WITHOUT alias**: MUST NOT be suggested again (e.g., `FROM products, |` → products excluded)
- **WITH alias**: MAY be suggested again for self-join (e.g., `FROM products p, |` → products allowed)

**Rationale:** FROM_CLAUSE is a table-selection context (scope construction). When users explicitly type qualified columns in SELECT, suggesting only referenced tables reduces ambiguous choices (e.g., `product` vs `products`) and avoids accidental wrong-table selection. Tables without aliases cannot be re-used (SQL syntax error), but tables with aliases enable self-join patterns (e.g., `FROM users u1 JOIN users u2`).

#### 4b. With prefix

**Show:**
- CTE names starting with the prefix
- Physical tables starting with the prefix
- `CURRENT_TABLE` (if set, matches prefix, and not already present in current statement)

**Prioritization/Filtering:** Same as 4a - if SELECT list contains qualified columns, filter to ONLY referenced tables, then apply prefix matching within that set. When multiple tables are referenced, follow their left-to-right appearance order in the SELECT list.

**Examples:**
```sql
SELECT * FROM u|
→ users

SELECT users.column FROM u|
→ users (ONLY referenced table matches prefix)

SELECT products.price, users.name FROM u|
→ users (ONLY referenced table matching prefix)

SELECT orders.total, users.name FROM o|
→ orders (ONLY referenced table matching prefix)

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

**Alias detection (best-effort):**
- SQL allows aliases with or without `AS` keyword (e.g., `FROM users u` or `FROM users AS u`)
- Autocomplete should treat both forms as "alias present" to avoid suggesting `AS` when alias already exists
- Detection: if token after table name is a valid identifier (not a keyword), treat it as an alias

**Examples:**
```sql
SELECT * FROM users |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, AS, WHERE, GROUP BY, ORDER BY, LIMIT
   (AS included because no alias defined yet)

SELECT * FROM users AS u |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, WHERE, GROUP BY, ORDER BY, LIMIT
   (AS excluded because alias 'u' already exists)

SELECT * FROM users u |
→ JOIN, INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, WHERE, GROUP BY, ORDER BY, LIMIT
   (AS excluded because alias 'u' already exists, even without AS keyword)
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
- `CURRENT_TABLE` (if set and not already present in current statement)

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

**Table re-suggestion policy (self-join support):**

Physical tables already present in FROM/JOIN:
- **WITHOUT alias**: MUST NOT be suggested again (e.g., `FROM orders JOIN |` → orders excluded)
- **WITH alias**: MAY be suggested again for self-join (e.g., `FROM orders o JOIN |` → orders allowed)

**Rationale:** JOIN_CLAUSE is a table-selection context (scope extension). It follows the same rule as FROM_CLAUSE. Tables without aliases cannot be re-used (SQL syntax error), but tables with aliases enable self-join patterns (e.g., `FROM users u1 JOIN users u2`).

#### 5b. With prefix

**Show:**
- CTE names starting with the prefix
- Physical tables starting with the prefix
- `CURRENT_TABLE` (if set, matches prefix, and not already present in current statement)

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
- `AS` (only if the table doesn't already have an alias)

**Alias detection (best-effort):**
- SQL allows aliases with or without `AS` keyword (e.g., `JOIN orders o` or `JOIN orders AS o`)
- Autocomplete should treat both forms as "alias present" to avoid suggesting `AS` when alias already exists
- Detection: if token after table name is a valid identifier (not a keyword), treat it as an alias

**Examples:**
```sql
SELECT * FROM users JOIN orders |
→ AS, ON, USING
   (AS included because no alias defined yet)

SELECT * FROM users u LEFT JOIN products AS p |
→ ON, USING
   (AS excluded because alias 'p' already exists)

SELECT * FROM users u LEFT JOIN products p |
→ ON, USING
   (AS excluded because alias 'p' already exists, even without AS keyword)
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
- Columns from scope tables only (qualified with alias-first)
- All functions

**Examples:**
```sql
SELECT * FROM users JOIN orders ON |
→ users.id, users.name, users.email, orders.id, orders.user_id, orders.total, orders.created_at
→ COUNT, SUM, AVG, ...

SELECT * FROM users u JOIN orders o ON |
→ u.id, u.name, u.email, o.id, o.user_id, o.total, o.created_at
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
- Columns from scope tables only (unqualified if single table, qualified with alias-first if multiple tables) (filtered by prefix if present)
- All functions (filtered by prefix if present)

**Operator context rule applies:** The column **immediately to the LEFT** of the current operator MUST NOT be suggested (see **Scope-Restricted Expression Contexts** section for details).

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
→ orders.user_id, orders.id, orders.total, orders.created_at, ...  (orders columns prioritized - other-side table)
→ users.name, users.email, users.password, users.is_enabled, users.created_at, ...  (users columns after)
→ (users.id excluded - immediately left of operator)

SELECT * FROM users u JOIN orders o ON u.id = |
→ NULL, TRUE, FALSE
→ o.user_id, o.id, o.total, o.created_at, ...  (orders columns prioritized - other-side table)
→ u.name, u.email, u.password, u.is_enabled, u.created_at, ...  (users columns after)
→ (u.id excluded - immediately left of operator)

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
- All columns (unqualified if single table, qualified with alias-first if multiple tables)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- All functions

**Examples:**
```sql
SELECT * FROM users WHERE |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified, schema order)
→ COUNT, SUM, AVG, ...

SELECT * FROM users u WHERE |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified, schema order)
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
→ Prefix: "u"
→ Column-name match: (none - no columns start with 'u')
→ Table-name expansion: users.* (table name starts with 'u' → all columns qualified)
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at  (schema order)
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ (DB-wide columns excluded - scope restriction active)

SELECT * FROM users WHERE n|
→ Context: WHERE (scope-restricted)
→ Prefix: "n"
→ Column-name match: name (column starting with 'n', single table: unqualified)
→ Functions: (none starting with 'n')

SELECT * FROM items WHERE i|
→ Context: WHERE (scope-restricted)
→ Scope: [items]
→ Prefix: "i"
→ Prefix matches BOTH column names AND table name
→ Column-name match unqualified: id, item_name  (FIRST - schema order)
→ Column-name match qualified: items.id, items.item_name  (SECOND - schema order)
→ Table-name expansion remaining: items.stock, items.price  (THIRD - schema order, excluding id/item_name)
→ Functions: IF, IFNULL  (FOURTH)
```

#### 6c. After comparison operator

**Trigger:** After `=`, `!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `IN`, etc. in WHERE clause

**Show:**
- Literal keywords: `NULL`, `TRUE`, `FALSE`, `CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`
- All columns (unqualified if single table, qualified with alias-first if multiple tables) (filtered by prefix if present)
- All functions (filtered by prefix if present)

**Operator context rule applies:** The column **immediately to the LEFT** of the current operator MUST NOT be suggested (see **Scope-Restricted Expression Contexts** section for details).

**Examples:**
```sql
SELECT * FROM users WHERE id = |
→ NULL, TRUE, FALSE
→ name, email, password, is_enabled, created_at, ...  (single table: unqualified)
→ COUNT, SUM, ...
→ (id excluded - immediately left of operator)

SELECT * FROM users WHERE is_enabled = |
→ NULL, TRUE, FALSE
→ id, name, email, password, created_at, ...  (single table: unqualified)
→ COUNT, SUM, ...
→ (is_enabled excluded - immediately left of operator)

SELECT * FROM users WHERE created_at > |
→ CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP
→ id, name, email, password, is_enabled, ...  (single table: unqualified)
→ (created_at excluded - immediately left of operator)
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

**MUST NOT suggest literals:** Do NOT suggest `NULL`, `TRUE`, `FALSE`, `CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP` in ORDER BY context. Ordering by constants is meaningless as all rows would have the same sort value.

#### 7a. Without prefix

**Show:**
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- Functions

**MUST NOT suggest sort direction keywords:** Do NOT suggest `ASC`, `DESC`, `NULLS FIRST`, `NULLS LAST` in `ORDER BY |` without a column specified. These keywords are only meaningful after a column/expression (see section 7c).

**Ordering:** Columns first, then functions. Users must choose the column before specifying sort direction.

**Examples:**
```sql
SELECT * FROM users ORDER BY |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified, columns first)
→ COUNT, SUM, AVG, ...                         (functions)
→ NOT: ASC, DESC (no column specified yet)

SELECT * FROM users u JOIN orders o ON u.id = o.user_id ORDER BY |
→ u.id, u.name, o.total, o.created_at, ...  (columns first)
→ COUNT, SUM, AVG, ...                      (functions)
→ NOT: ASC, DESC (no column specified yet)
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
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables) (filtered by prefix if present)
- Functions (filtered by prefix if present)

**Examples:**
```sql
SELECT * FROM users ORDER BY created_at DESC, |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified)
→ COUNT, SUM, AVG, ...

SELECT * FROM users u ORDER BY created_at DESC, n|
→ name  (single table: unqualified)
```

---

### 8. GROUP_BY_CLAUSE (After GROUP BY)

**Trigger:** After `GROUP BY`

**Important:** Only show columns from tables specified in FROM and JOIN clauses (using alias if defined, otherwise table name).

#### 8a. Without prefix

**Show:**
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- Functions

**Examples:**
```sql
SELECT COUNT(*) FROM users GROUP BY |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified)
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
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables) (filtered by prefix if present)
  - **MUST NOT suggest columns already present in the GROUP BY clause**
- Functions (filtered by prefix if present)

**Examples:**
```sql
SELECT COUNT(*) FROM users GROUP BY status, |
→ id, name, email, password, is_enabled, created_at, ...  (single table: unqualified)
→ NOT: status (already present in GROUP BY)
→ DATE, YEAR, MONTH, ...

SELECT COUNT(*) FROM users u GROUP BY is_enabled, c|
→ created_at  (single table: unqualified)
→ NOT: is_enabled (already present)
```

---

### 9. HAVING_CLAUSE (After HAVING)

**Trigger:** After `HAVING`

**Important:** Only show columns from tables specified in FROM and JOIN clauses. Focus on aggregate functions.

**Aggregate functions definition:** Predefined set of functions per SQL dialect that perform aggregation operations. Standard set includes: `COUNT`, `SUM`, `AVG`, `MAX`, `MIN`. Vendor-specific additions: `GROUP_CONCAT` (MySQL), `STRING_AGG` (PostgreSQL), `LISTAGG` (Oracle), `ARRAY_AGG`, etc. This list is dialect-dependent and should be maintained as a constant set in the implementation.

#### 9a. Without prefix

**Show:**
- Aggregate functions (prioritized): from the predefined aggregate functions set for current dialect
- Columns in scope (unqualified if single table, qualified with alias-first if multiple tables)
  - **Note:** With prefix, see **Generic Prefix Matching** section for table-name expansion rules
- Other functions (non-aggregate)

**Ordering:** Aggregate functions first (alphabetical), then columns (schema order - NOT alphabetical), then other functions (alphabetical).

**Rationale:** HAVING typically filters aggregates; prioritizing aggregate functions reduces keystrokes and improves UX.

**Note:** Columns preserve their table definition order (ordinal_position), consistent with global ordering rules.

**Examples:**
```sql
SELECT status, COUNT(*) FROM users GROUP BY status HAVING |
→ COUNT, SUM, AVG, MAX, MIN, ...  (aggregate functions first, alphabetical)
→ id, name, email, ...     (single table: unqualified, schema order)
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
→ created_at (single table: unqualified, scope column matching prefix 'c')
→ CONCAT, COALESCE (other functions, alphabetical)
→ (DB-wide columns excluded - HAVING is scope-restricted expression context)
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

**Column display format:** 
- **Single table in scope:** Use unqualified column names (e.g., `id`, `name`)
- **Multiple tables in scope:** Use `alias.column` when the table has an alias in the current statement; otherwise use `table.column`
- **Exception:** Dot-completion always returns unqualified column names (see **Dot-Completion** section)

**Exception:** In HAVING clause context, aggregate functions are prioritized before columns (see section 9a, 9b for details). This is the only context where functions appear before columns.

**Column ordering reminder:** See "Important Note on Column Ordering in Examples" section at the beginning of this document. All columns preserve schema order (ordinal_position), NOT alphabetical order.

1. **Columns from CURRENT_TABLE** (if set in context, e.g., table editor)
   - **Single table in scope:** Unqualified (e.g., `id`, `name`)
   - **Multiple tables in scope:** Use `alias.column` format if the table has an alias in the current query, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.

2. **Columns from tables in FROM clause** (if any)
   - Includes: derived tables (subquery aliases), CTEs, physical tables
   - Priority within FROM: derived tables > CTEs > physical tables (see **Tables in Scope Definition** section)
   - **Single table in scope:** Unqualified (e.g., `id`, `name`)
   - **Multiple tables in scope:** Use `alias.column` format if the table has an alias, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - When multiple FROM tables exist, follow their appearance order in the query; within each table, preserve column definition order.

3. **Columns from tables in JOIN clause** (if any)
   - Includes: derived tables (subquery aliases), CTEs, physical tables
   - Priority within JOIN: derived tables > CTEs > physical tables (see **Tables in Scope Definition** section)
   - **Multiple tables in scope:** Use `alias.column` format if the table has an alias, otherwise `table.column`
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - When multiple JOIN tables exist, follow their appearance order in the query; within each table, preserve column definition order.
   - **Note:** JOIN clause always implies multiple tables in scope (FROM + JOIN), so columns are always qualified

4. **All table.column from database** (all other tables not in FROM/JOIN)
   - **CRITICAL: Group 4 eligibility is context-dependent:**
     - ✅ **Eligible in SELECT_LIST when NO scope tables exist** (and only with prefix - guardrail against noise)
     - ❌ **NOT eligible in SELECT_LIST when scope tables exist** (scope restriction active)
     - ❌ **NOT eligible in scope-restricted expression contexts** (WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING)
     - ❌ **NOT applicable in table-selection contexts** (FROM_CLAUSE, JOIN_CLAUSE suggest tables, not columns)
   - Always use `table.column` format (no aliases for tables not in query)
   - Columns preserve their definition order (ordinal position in the table schema). They must NOT be reordered alphabetically.
   - Database-wide tables follow a deterministic stable order (schema order or internal stable ordering); within each table, preserve column definition order.
   - **Performance guardrail (applies ONLY to this group when eligible):** If no prefix and total suggestions exceed threshold (400 items), skip this group to avoid lag in large databases
   - **No prefix definition:** prefix is `None` OR empty string after trimming whitespace
   - The cap applies only to group 4 (DB-wide columns). Groups 1-3 (CURRENT_TABLE, FROM, JOIN) are always included in full (already loaded/scoped).
   - With prefix: always include this group when eligible (filtered results are manageable)

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
→ Columns: (none - single table, no columns start with 'user')  (single table: unqualified)
→ Functions: (none starting with 'user')
→ (generic prefix matching, NOT alias-prefix)
→ (DB-wide columns excluded - WHERE is scope-restricted)

SELECT * FROM users u WHERE up|
→ token = "up"
→ alias "u" exists but "up" != "u" → no exact match ❌
→ UPPER                      (function starts with 'up')
→ (generic prefix matching - user is typing a function, NOT using the alias)
```

**No alias in query - Generic prefix mode:**
```sql
SELECT * FROM users JOIN orders ON u|
→ token = "u"
→ Context: JOIN_ON (scope-restricted)
→ no aliases defined → generic prefix
→ users.id, users.name, users.email, users.password, users.is_enabled, users.created_at  (multiple tables: qualified)
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

**Return column suggestions that include BOTH:**

**B) Column-name match:**
- For EVERY column C (from all tables in scope and all other database tables) whose column name startswith(P), return it as a column suggestion
- **Qualification:**
  - **Single table in scope:** Unqualified (e.g., `name`)
  - **Multiple tables in scope:** Qualified with `alias.column` if table has alias, otherwise `table.column`

**A) Table-name match expansion:**
- For EVERY table T whose name startswith(P), return ALL columns of T as column suggestions
- **Qualification:** Always qualified with `alias.column` if table has alias, otherwise `table.column` (even for single table)
- **Rationale:** Qualified names indicate the match is from table name, helping users discover dot-completion

**Order when BOTH B and A match (prefix matches both column names AND table name):**
1. **Column-name matches unqualified** (rule B, single table only)
2. **Column-name matches qualified** (same columns as #1, but qualified)
3. **Table-name expansion remaining columns qualified** (rule A, excluding columns already shown in #1 and #2)
4. **Functions**

**Order when ONLY B matches (prefix matches column names but NOT table name):**
1. **Column-name matches** (unqualified if single table, qualified if multiple tables)
2. **Functions**

**Order when ONLY A matches (prefix matches table name but NOT column names):**
1. **Table-name expansion all columns qualified** (rule A)
2. **Functions**

**Scope restriction:**

**Scope-restricted expression contexts (WHERE, JOIN_ON, ORDER_BY, GROUP_BY, HAVING):**

**Hard line:** In scope-restricted expression contexts, both table-name expansion and column-name matching MUST be computed over scope tables only.

See **Scope-Restricted Expression Contexts** section for complete rules.

**SELECT_LIST without scope tables:**
- `CURRENT_TABLE` columns MUST be included first (if set)
- Database-wide table-name expansion and column-name matching are included **ONLY when prefix exists**
- **CRITICAL: When no prefix exists, DB-wide columns MUST NOT be shown (guardrail against noise)**
- **With prefix matching order:**
  1. **CURRENT_TABLE table-name expansion** (if CURRENT_TABLE name matches prefix)
  2. **Other DB-wide table-name expansions** (tables whose names match prefix)
  3. **Column-name matching from all DB tables** (columns whose names match prefix)
  4. **Functions**

**SELECT_LIST with scope tables:**
- `CURRENT_TABLE` columns MUST be included ONLY if `CURRENT_TABLE` is in scope
- Database-wide columns MUST NOT be suggested (regardless of prefix)
- Scope table columns are included with alias-first qualification
- **Exception:** If prefix matches DB-wide tables but no scope tables/columns, suggest Out-of-Scope Table Hints instead

**Important rules:**
- Do NOT suggest bare table names in column-expression contexts; only columns (qualified)
  - **Exception:** Out-of-Scope Table Hints (see **Out-of-Scope Table Hints** section) are a special suggestion kind
- Deduplicate identical suggestions (if a column appears via both A and B, show it once)
- Apply global Ordering Rules (CURRENT_TABLE > FROM > JOIN > DB > FUNCTIONS > TABLE_HINTS > KEYWORDS)
  - **Note:** DB group only applies when no scope exists; TABLE_HINTS only in SELECT_LIST with scope
- Performance guardrail: see Ordering Rules group 4 (applies only to DB-wide columns when no prefix)

**Examples:**

**SELECT_LIST without scope, with CURRENT_TABLE and prefix:**
```sql
-- Assume CURRENT_TABLE = users, prefix = "u"
SELECT u|
→ Prefix: "u"
→ Context: SELECT_LIST (no scope → DB-wide columns allowed with prefix)
→ CURRENT_TABLE table-name expansion: users.id, users.name, users.email, users.status, users.created_at (FIRST)
→ Other table-name expansion: user_sessions.id, user_sessions.user_id, user_sessions.session_token, user_sessions.expires_at (SECOND)
→ Column-name matching: orders.user_id, products.unit_price (THIRD)
→ Functions: UNIX_TIMESTAMP, UPPER, UUID (FOURTH)
```

**SELECT_LIST with scope tables (database-wide columns excluded):**
```sql
SELECT u| FROM orders
→ Prefix: "u"
→ Context: SELECT_LIST (scope exists → database-wide columns excluded)
→ Scope column-name matching: orders.user_id (scope table column starts with 'u')
→ Functions: UPPER, UUID, UNIX_TIMESTAMP
→ Out-of-Scope Table Hints: users        + Add via FROM/JOIN (prefix matches DB table but not in scope)
→ Combined: orders.user_id, UPPER, UUID, UNIX_TIMESTAMP, users (hint)
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
→ Context: SELECT_LIST without scope (no FROM/JOIN)
→ Prefix: "u"
→ users.id          (CURRENT_TABLE column starting with 'u')
→ users.name        (CURRENT_TABLE column - shown for context)
→ orders.user_id    (DB-wide column starting with 'u' - allowed because no scope AND prefix exists)
→ products.unit_price (DB-wide column starting with 'u')
→ UPPER             (function starting with 'u')
→ UUID              (function starting with 'u')
→ UPDATE            (keyword starting with 'u')
```

**Example in multi-query context (CURRENT_TABLE = users, second query has no scope):**
```sql
SELECT * FROM users u WHERE id = 1; SELECT u|
→ Context: SELECT_LIST without scope (second query has no FROM/JOIN)
→ Prefix: "u"
→ users.id          (CURRENT_TABLE column starting with 'u')
→ users.name        (CURRENT_TABLE column - shown for context)
→ orders.user_id    (DB-wide column starting with 'u' - allowed because no scope AND prefix exists)
→ products.unit_price (DB-wide column starting with 'u')
→ UPPER             (function starting with 'u')
→ UUID              (function starting with 'u')
→ UPDATE            (keyword starting with 'u')
```

**Example in query with FROM:**
```sql
SELECT * FROM users WHERE u|
→ Columns: (none - no columns start with 'u')  (single table: unqualified)
→ UPPER             (function starting with 'u')
→ UPDATE            (keyword starting with 'u')
→ (DB-wide columns excluded - WHERE is scope-restricted expression context)
```

**Example in query with JOIN (alias-exact-match mode):**
```sql
SELECT * FROM users u JOIN orders o WHERE u|
→ Context: WHERE (scope-restricted)
→ Prefix: "u"
→ Alias-exact-match mode (u == alias 'u')
→ u.id, u.name, u.email, u.password, u.is_enabled, u.created_at  (all columns from alias 'u', multiple tables: qualified)
→ UPPER, UUID, UNIX_TIMESTAMP  (functions starting with 'u')
→ (DB-wide columns excluded - WHERE is scope-restricted expression context)
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
| **SELECT_LIST (no scope)** | No | Only with prefix | Yes (if set) | No |
| **SELECT_LIST (with scope)** | Yes | No | Only if in scope | Yes (if prefix matches) |
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
- SELECT_LIST without scope: DB-wide columns included only when prefix exists (guardrail against noise)
- SELECT_LIST with scope: DB-wide columns excluded; Out-of-Scope Table Hints shown when prefix matches DB tables but no scope tables/columns
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
    3. CURRENT_TABLE (if set and not already present in current statement) - convenience shortcut
    
    Filtering:
    - If prefix provided, filter by startswith(prefix)
    - Exclude tables already present in the current statement (query separated by separator)
    
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
        * Include database-wide columns (only with prefix - guardrail against noise)
      - If scope tables exist:
        * CURRENT_TABLE included only if in scope; otherwise ignored
        * Include scope table columns
        * Database-wide columns EXCLUDED (scope restriction active)
        * Exception: Out-of-Scope Table Hints if prefix matches DB tables but no scope columns
    
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

**Important:** Scope handling for subqueries and CTEs.

**v1 subquery scope resolution:**
- **v1 supports inner scope when cursor is inside parentheses of a subquery** (sqlglot typically handles this correctly)
- Fallback to outer scope only when parsing/cursor mapping fails
- When subquery has FROM clause, suggest columns from subquery scope (inner scope)
- When cursor is outside subquery parentheses, suggest columns from outer scope

**Examples:**
```sql
-- Cursor outside subquery: outer query scope
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders) AND |
→ Suggests columns from 'users' (outer query scope)

-- Cursor inside subquery: inner query scope (v1 supported)
SELECT * FROM users WHERE id IN (SELECT | FROM orders)
→ Suggests columns from 'orders' (inner query scope - subquery has FROM)

-- Cursor inside subquery WHERE: inner query scope (v1 supported)
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE |)
→ Suggests columns from 'orders' (inner query scope)
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
- **CTE visibility is limited to the statement where they are defined (standard SQL behavior)**

**CTE scope and visibility:**

CTEs follow **standard SQL semantics**: a CTE is visible only within the statement where it is defined. This is the behavior mandated by the SQL standard and implemented by all major databases.

**Example - CTE scope (standard SQL):**
```sql
WITH a AS (...)
SELECT * FROM a;
SELECT * FROM |
→ CTE 'a' is NOT visible here (different statement, separated by `;`)
→ Show only physical tables
```

**Vendor-specific extensions:**

Some databases offer non-standard CTE extensions (e.g., session-scoped CTEs, persistent CTEs). These are **NOT supported in v1**. The autocomplete system follows standard SQL semantics only.

**Advanced CTE features (future enhancement):**
- Recursive CTEs (standard SQL, but complex parsing)
- Multiple CTEs with dependencies (standard SQL)
- CTE column aliasing (standard SQL)

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

**Separator types:**

1. **Single-character separators** (most engines):
   - MySQL, MariaDB, PostgreSQL, SQLite: `";"`
   - User can override with any single character

2. **Multi-character token separators** (SQL Server and similar):
   - SQL Server: `"GO"` (case-insensitive keyword)
   - Must be a standalone token (word boundary required)
   - Example: `SELECT * FROM users GO SELECT * FROM orders` (valid)
   - Example: `SELECT * FROM users_GO SELECT * FROM orders` (invalid - no word boundary)

**Validation:**

1. **Trim whitespace** from `user_override` before validation
2. **Single-character override:** If length == 1 after trimming → valid
3. **Multi-character override:** If length >= 2 after trimming:
   - **Valid:** ONLY if alphanumeric + underscore `[A-Za-z0-9_]+`
   - **Invalid:** If contains symbols (e.g., `//`, `$$`, `GO;`) → reject, fallback to `engine_default`
4. **Invalid override:** If validation fails → ignore override and fallback to `engine_default`

**Valid override examples:**
- `"GO"` → valid (alphanumeric)
- `"BEGIN"` → valid (alphanumeric)
- `";"` → valid (single char)
- `"END_BLOCK"` → valid (alphanumeric + underscore)

**Invalid override examples (rejected, use engine_default):**
- `"//"` → invalid (symbols only)
- `"GO;"` → invalid (mixed alphanumeric + symbol)
- `"$$"` → invalid (symbols only)
- `"GO "` → invalid after trim (contains space before trim)

**Implementation notes:**

- **Single-character separators:** Simple string split with string/comment awareness
- **Multi-character token separators:** Require word boundary detection using regex `\b{separator}\b`
  - Example: `\bGO\b` for SQL Server
  - Word boundary `\b` works correctly because multi-char separators are restricted to `[A-Za-z0-9_]+`
- **Both types MUST respect:**
  - String literals: `'...'`, `"..."`, `` `...` ``
  - Comments: `-- ...`, `/* ... */`
  - Dollar-quoted strings (PostgreSQL): `$$...$$`, `$tag$...$tag$`

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
- For token separators (e.g., GO), cursor on the token itself is treated as "end of previous statement"

**Examples:**

**Single-character separator (`;`):**
```sql
SELECT * FROM users WHERE id = 1;
SELECT * FROM orders WHERE |  ← cursor here
SELECT * FROM products;
```
Context detection should analyze only: `SELECT * FROM orders WHERE |`

**Token separator (`GO` for SQL Server):**
```sql
SELECT * FROM users WHERE id = 1
GO
SELECT * FROM orders WHERE |  ← cursor here
GO
SELECT * FROM products
```
Context detection should analyze only: `SELECT * FROM orders WHERE |`

**Critical:**
- Do NOT use simple `text.split(effective_separator)`
- The separator must be ignored inside:
  - Strings (`'...'`, `"..."`)
  - Comments (`--`, `/* */`)
  - Dollar-quoted strings (PostgreSQL: `$$...$$`)
- For token separators, word boundaries MUST be respected (e.g., `users_GO` is NOT a separator)

**Recommended approach:**
- Use sqlglot lexer/tokenizer to find statement boundaries (handles strings/comments correctly)
- For token separators: use regex with word boundaries (e.g., `\bGO\b` case-insensitive)
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

## Edge Cases

This section documents problematic scenarios and their explicit resolutions.

### 1. Cursor on Separator

**Scenario:** Cursor is positioned exactly on the statement separator.

```sql
SELECT * FROM users;|
SELECT * FROM orders;
```

**Resolution:** Treat as "end of previous statement". Context detection operates on the first statement (`SELECT * FROM users`), suggesting clause keywords like `WHERE`, `ORDER BY`, `LIMIT`.

---

### 2. Empty Statement

**Scenario:** Multiple separators with no content between them.

```sql
SELECT * FROM users;;|
```

**Resolution:** Empty statements are ignored. Fallback to EMPTY context, suggesting primary keywords (`SELECT`, `INSERT`, `UPDATE`, etc.).

---

### 3. Incomplete String Literal

**Scenario:** Cursor inside an unclosed string.

```sql
SELECT * FROM users WHERE name = '|
```

**Resolution:** sqlglot parsing may fail. Fallback to regex-based context detection. Suggest literal keywords (`NULL`, `TRUE`, `FALSE`) and allow user to complete the string.

---

### 4. Separator Inside String/Comment

**Scenario:** Statement separator appears inside a string or comment.

```sql
SELECT * FROM users WHERE note = 'Price: $10; Discount: 20%' AND |
```

**Resolution:** The `;` inside the string MUST be ignored. Use sqlglot lexer/tokenizer or implement string/comment-aware separator detection. Context: WHERE clause.

---

### 5. Ambiguous Alias with Multiple Matches

**Scenario:** Prefix could match multiple aliases if using `startswith`.

```sql
SELECT * FROM users u JOIN user_stats us WHERE u|
```

**Resolution:** Use **exact match** rule. `"u" == "u"` → alias-prefix mode for `u`. If user types `us|`, then `"us" == "us"` → alias-prefix mode for `us`. No ambiguity.

---

### 6. CURRENT_TABLE Not in Scope

**Scenario:** CURRENT_TABLE is set in UI, but not present in query scope.

```sql
-- CURRENT_TABLE = users (in table editor)
SELECT * FROM orders WHERE |
```

**Resolution:** CURRENT_TABLE columns MUST NOT be suggested. Only `orders.*` columns are valid (scope restriction active). CURRENT_TABLE is ignored unless it appears in FROM/JOIN.

---

### 7. Table Name Matches Column Name

**Scenario:** Prefix matches both a table name and column names.

```sql
SELECT u| FROM orders
```

**Resolution:** Context is SELECT_LIST with scope (orders in FROM). Apply scope-restricted prefix matching:
- Column-name matching: `orders.user_id` (scope table column starting with 'u')
- Functions: `UPPER`, `UUID`, `UNIX_TIMESTAMP`
- Out-of-Scope Table Hint: `users + Add via FROM/JOIN` (prefix matches DB table not in scope)
- ❌ DB-wide columns excluded (scope restriction active - no `users.*` expansion)

---

### 8. Dot-Completion on Non-Existent Table

**Scenario:** User types dot after a non-existent table/alias.

```sql
SELECT * FROM users WHERE xyz.|
```

**Resolution:** `xyz` is not a valid table or alias in scope. Return empty suggestions. Optionally show error hint: "Table or alias 'xyz' not found".

---

### 9. Multi-Query with Different Separators

**Scenario:** User has overridden separator, but buffer contains old separator.

```sql
-- effective_separator = "GO"
SELECT * FROM users;
GO
SELECT * FROM orders WHERE |
```

**Resolution:** Only the effective separator (`GO`) is recognized. The `;` is treated as part of the first statement (not a separator). Context detection operates on the second statement.

---

### 10. CTE Referenced Before Definition

**Scenario:** User references CTE before defining it (incomplete query).

```sql
SELECT * FROM active_users WHERE |
WITH active_users AS (SELECT * FROM users WHERE status = 'active')
```

**Resolution:** sqlglot parsing may fail or produce incorrect AST. Fallback to regex-based context detection. CTE `active_users` is not recognized (defined after usage). Treat as physical table or show error hint.

---

### 11. Nested Subquery Context

**Scenario A:** Cursor in SELECT list of subquery (subquery has FROM).

```sql
SELECT * FROM users WHERE id IN (SELECT | FROM orders)
```

**Resolution:** **v1 supported**. Context detection recognizes the subquery scope (cursor inside parentheses). Suggest `orders.*` columns (inner scope). The subquery's FROM clause establishes scope.

**Scenario B:** Cursor in WHERE clause of subquery.

```sql
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE |)
```

**Resolution:** **v1 supported**. Context detection operates on the subquery scope (cursor inside parentheses). Suggest `orders.*` columns (inner scope). The subquery's FROM clause establishes scope.

**Scenario C:** Cursor in subquery without FROM (correlated subquery).

```sql
SELECT * FROM users WHERE id IN (SELECT | WHERE status = 'active')
```

**Resolution:** No FROM in subquery → no inner scope established. Fallback to outer scope (`users.*`) or show error depending on parsing success. This is acceptable behavior for v1.

**Note:** This scenario is **extremely rare** in practice. The vast majority of correlated subqueries still have a table in the FROM clause (e.g., `SELECT user_id FROM orders WHERE orders.user_id = users.id`). Subqueries without FROM are edge cases, making the v1 behavior entirely reasonable.

---

### 12. Column Name Equals Keyword

**Scenario:** Table has a column named after a SQL keyword.

```sql
-- Table: users (columns: id, name, select, from)
SELECT * FROM users WHERE |
```

**Resolution:** Suggest all columns including `users.select` and `users.from`. Column names take precedence over keywords in expression contexts. User must quote if necessary (e.g., `` `select` `` in MySQL).

---

### 13. Alias Shadows Table Name

**Scenario:** Alias has the same name as another table.

```sql
SELECT * FROM users AS orders WHERE |
```

**Resolution:** Alias `orders` shadows the physical table `orders`. Suggest `orders.id, orders.name, ...` (columns from `users` table via alias `orders`). Physical table `orders` is not in scope.

---

### 14. Self-Join with Same Table

**Scenario:** Table joined with itself using different aliases.

```sql
SELECT * FROM users u1 JOIN users u2 ON u1.id = u2.manager_id WHERE |
```

**Resolution:** Suggest columns from both aliases:
- `u1.id, u1.name, u1.email, ...` (first instance)
- `u2.id, u2.name, u2.email, ...` (second instance)

Both are in scope. No deduplication (different aliases = different logical tables).

---

### 15. Whitespace-Only Prefix

**Scenario:** User types only whitespace after a keyword.

```sql
SELECT   |
```

**Resolution:** Whitespace is trimmed. No prefix exists. Show all columns (if scope exists) + functions + keywords.

---

## Spacing After Completion

- **Keywords:** Space added after keywords (e.g., `SELECT `, `FROM `, `WHERE `, `JOIN `, `AS `)
  - Multi-word keywords are treated as keywords for spacing (space appended after `ORDER BY`, `GROUP BY`, `IS NULL`, etc.)
- **Columns:** No space added (e.g., `users.id|` allows immediate `,` or space)
- **Tables:** No space added (e.g., `users|` allows immediate space or alias)
- **Functions:** No space added by default
  - **Future enhancement:** Consider function snippets with cursor positioning (e.g., `COUNT(|)` where `|` is cursor position)
  - This would require snippet support in the autocomplete system
