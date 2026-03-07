# Engine Specifications

This project stores SQL autocomplete vocabulary in normalized engine specifications under `structures/engines/`.

## How Version Deltas Work

The specification model uses a **base + delta** strategy:

- `common.functions` and `common.keywords` contain the shared baseline for that engine.
- `versions.<major>.functions_remove` and `versions.<major>.keywords_remove` remove entries that are not valid for an older major version.

We intentionally keep newer capabilities in `common` and apply only removals for older majors.

## Version Resolution Rule

At runtime, vocabulary resolution uses:

1. exact major match when available;
2. otherwise, the highest configured major version `<=` the server major.

Example: if PostgreSQL server major is `19` and the highest configured major is `18`, version `18` is used.
