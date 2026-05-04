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
  Encoding            ❌      ❌        ✅           ❌
  Locale (LC\_\*)     ❌      ❌        ✅           ❌
  Owner               ❌      ❌        ✅           ❌
  Template DB         ❌      ❌        ✅           ❌
  Connection limit    ❌      ❌        ✅           ❌
  Allow connections   ❌      ❌        ✅           ❌
  Is template flag    ❌      ❌        ✅           ❌
  Default engine      ✅      ✅        ❌           ❌

------------------------------------------------------------------------

## Notes

### MySQL / MariaDB

-   Focus on:
    -   charset
    -   collation
    -   default engine

### PostgreSQL

-   Different model:
    -   encoding
    -   locale (LC_COLLATE, LC_CTYPE)
    -   owner
    -   template database
    -   connection rules

### SQLite

-   No real database-level configuration
-   Database = file

------------------------------------------------------------------------

## Important Caveat

Collation in PostgreSQL is NOT equivalent to MySQL: - Derived from
locale (LC_COLLATE) - Not freely alterable like in MySQL/MariaDB
