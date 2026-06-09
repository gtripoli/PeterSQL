# Database Options Matrix (Compact)

## Legend

-   ✅ supported
-   ⚠️ partial / indirect
-   ❌ not supported

------------------------------------------------------------------------

## Matrix

  Option              MySQL   MariaDB   PostgreSQL   SQLite
  ------------------- ------- --------- ------------ --------
  Charset             ✅      ✅        ❌           ❌
  Collation           ✅      ✅        ⚠️           ❌
  Encryption          ✅      ❌        ❌           ❌
  Tablespace          ❌      ❌        ✅           ❌
  Connection limit    ❌      ❌        ✅           ❌

------------------------------------------------------------------------

## Notes

### MySQL

-   Focus on:
    -   charset
    -   collation
    -   encryption (Y/N)

### MariaDB

-   Focus on:
    -   charset
    -   collation
-   Encryption NOT supported (MySQL-only syntax)

### PostgreSQL

-   Different model:
    -   tablespace
    -   connection limit
-   Collation: shown in UI but `PostgreSQLDatabase` has no `default_collation` field — not functional yet

### SQLite

-   No real database-level configuration
-   Database = file

------------------------------------------------------------------------

## Important Caveat

Collation in PostgreSQL is NOT equivalent to MySQL:
-   Derived from locale (LC_COLLATE) — not freely alterable like in MySQL/MariaDB
-   Currently not implemented in the app model
