from typing import Optional

import sqlglot


def format_sql(sql: str, dialect: Optional[str] = None) -> str:
    try:
        parsed = sqlglot.parse_one(sql, read=dialect)
        return parsed.sql(pretty=True)
    except Exception:
        return sql
