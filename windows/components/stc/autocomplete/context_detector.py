import re

from typing import Optional

import sqlglot

from helpers.logger import logger

from windows.components.stc.autocomplete.query_scope import QueryScope, TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase


class ContextDetector:
    _prefix_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
    _join_after_table_pattern = re.compile(
        r"\b(?:(?:INNER|LEFT|RIGHT|FULL|CROSS)(?:\s+OUTER)?\s+)?JOIN\s+([A-Za-z_][A-Za-z0-9_]*)"
        r"\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s*$",
        re.IGNORECASE,
    )
    _join_after_table_keywords = {
        "AS",
        "ON",
        "USING",
        "WHERE",
        "GROUP",
        "ORDER",
        "LIMIT",
        "JOIN",
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "CROSS",
        "OUTER",
    }

    def __init__(self, dialect: Optional[str] = None):
        self._dialect = dialect

    def detect(
        self, text: str, cursor_pos: int, database: Optional[SQLDatabase]
    ) -> tuple[SQLContext, QueryScope, str]:
        left_text = text[:cursor_pos]
        left_text_stripped = left_text.strip()

        if not left_text_stripped:
            return SQLContext.EMPTY, QueryScope.empty(), ""

        if " " not in left_text and "\n" not in left_text:
            return SQLContext.SINGLE_TOKEN, QueryScope.empty(), left_text_stripped

        prefix = self._extract_prefix(text, cursor_pos)

        try:
            context = self._detect_context_with_regex(left_text, prefix)
            scope = self._extract_scope_from_text(text, database)
            return context, scope, prefix
        except Exception as ex:
            logger.debug(f"context detection error: {ex}")
            return SQLContext.UNKNOWN, QueryScope.empty(), prefix

    def _extract_prefix(self, text: str, cursor_pos: int) -> str:
        if cursor_pos == 0:
            return ""

        left_text = text[:cursor_pos]

        if left_text and left_text[-1] in (" ", "\t", "\n"):
            return ""

        match = self._prefix_pattern.search(left_text)
        if match is None:
            return ""
        return match.group(0)

    def _detect_context_with_regex(self, left_text: str, prefix: str) -> SQLContext:
        left_upper = left_text.upper()

        select_pos = left_upper.rfind("SELECT")
        from_pos = left_upper.rfind("FROM")
        where_pos = left_upper.rfind("WHERE")
        join_pos = left_upper.rfind("JOIN")
        on_pos = left_upper.rfind(" ON ")
        order_by_pos = left_upper.rfind("ORDER BY")
        group_by_pos = left_upper.rfind("GROUP BY")
        having_pos = left_upper.rfind("HAVING")
        limit_pos = left_upper.rfind("LIMIT")
        offset_pos = left_upper.rfind("OFFSET")

        if select_pos == -1:
            return SQLContext.UNKNOWN

        max_pos = max(limit_pos, offset_pos)
        if max_pos > select_pos and max_pos != -1:
            if self._is_after_limit_number(left_text, limit_pos, prefix):
                return SQLContext.AFTER_LIMIT_NUMBER
            return SQLContext.LIMIT_OFFSET_CLAUSE

        if having_pos > select_pos and having_pos != -1:
            if having_pos > max(group_by_pos, order_by_pos, -1):
                if self._is_after_having_operator(left_text, having_pos, prefix):
                    return SQLContext.HAVING_AFTER_OPERATOR
                if self._is_after_having_expression(left_text, having_pos, prefix):
                    return SQLContext.HAVING_AFTER_EXPRESSION
                return SQLContext.HAVING_CLAUSE

        if group_by_pos > select_pos and group_by_pos != -1:
            if group_by_pos > max(where_pos, order_by_pos, having_pos, -1):
                return SQLContext.GROUP_BY_CLAUSE

        if order_by_pos > select_pos and order_by_pos != -1:
            if order_by_pos > max(where_pos, group_by_pos, having_pos, -1):
                if self._is_after_order_by_column(left_text, order_by_pos, prefix):
                    return SQLContext.ORDER_BY_AFTER_COLUMN
                return SQLContext.ORDER_BY_CLAUSE

        if on_pos > select_pos and on_pos != -1:
            if on_pos > max(join_pos, from_pos, where_pos, -1):
                if self._is_after_join_on_operator(left_text, on_pos, prefix):
                    return SQLContext.JOIN_ON_AFTER_OPERATOR
                if self._is_after_join_on_expression(left_text, on_pos, prefix):
                    return SQLContext.JOIN_ON_AFTER_EXPRESSION
                return SQLContext.JOIN_ON

        if join_pos > select_pos and join_pos != -1:
            if join_pos > max(from_pos, where_pos, -1):
                if self._is_after_join_table(left_text, prefix):
                    return SQLContext.JOIN_AFTER_TABLE
                return SQLContext.JOIN_CLAUSE

        if where_pos > select_pos and where_pos != -1:
            if where_pos > max(from_pos, order_by_pos, group_by_pos, -1):
                if self._is_after_where_operator(left_text, where_pos, prefix):
                    return SQLContext.WHERE_AFTER_OPERATOR
                if self._is_after_where_is(left_text, where_pos, prefix):
                    return SQLContext.WHERE_AFTER_EXPRESSION
                if self._is_after_where_expression(left_text, where_pos, prefix):
                    return SQLContext.WHERE_AFTER_EXPRESSION
                return SQLContext.WHERE_CLAUSE

        if from_pos > select_pos and from_pos != -1:
            if from_pos > max(where_pos, join_pos, order_by_pos, group_by_pos, -1):
                return SQLContext.FROM_CLAUSE

        return SQLContext.SELECT_LIST

    def _is_after_join_table(self, left_text: str, prefix: str) -> bool:
        if prefix:
            return False

        if not (match := self._join_after_table_pattern.search(left_text.rstrip())):
            return False

        alias = match.group(2)
        if alias and alias.upper() in self._join_after_table_keywords:
            return False

        return True

    @staticmethod
    def _is_after_join_on_expression(left_text: str, on_pos: int, prefix: str) -> bool:
        if prefix:
            return False

        on_clause = left_text[on_pos + 4 :]
        on_clause_stripped = on_clause.strip()
        if not on_clause_stripped:
            return False

        return bool(
            re.search(
                r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
                r"(?:=|!=|<>|<=|>=|<|>)\s*"
                r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*$",
                on_clause_stripped,
                re.IGNORECASE,
            )
        )

    def _is_after_join_on_operator(
        self, left_text: str, on_pos: int, prefix: str
    ) -> bool:
        if prefix:
            return False

        on_clause = left_text[on_pos + 4 :]
        if not (
            match := re.search(
                r"(?:(?P<qualifier>[A-Za-z_][A-Za-z0-9_]*)\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
                r"(?:=|!=|<>|<=|>=|<|>)\s*$",
                on_clause,
                re.IGNORECASE,
            )
        ):
            return False

        left_qualifier = match.group("qualifier")
        if not left_qualifier:
            return False

        from_qualifier = self._extract_from_qualifier(left_text)
        if not from_qualifier:
            return False

        return left_qualifier.lower() == from_qualifier.lower()

    def _is_after_where_operator(
        self, left_text: str, where_pos: int, prefix: str
    ) -> bool:
        if prefix:
            return False

        where_clause = left_text[where_pos + 5 :]
        if not (
            match := re.search(
                r"(?:(?P<qualifier>[A-Za-z_][A-Za-z0-9_]*)\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
                r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|BETWEEN)\s*$",
                where_clause,
                re.IGNORECASE,
            )
        ):
            return False

        return True

    def _is_after_where_expression(
        self, left_text: str, where_pos: int, prefix: str
    ) -> bool:
        if prefix:
            return False

        where_clause = left_text[where_pos + 5 :]
        where_clause_stripped = where_clause.strip()
        if not where_clause_stripped:
            return False

        # Match: column operator value (where value can be column, literal, or function)
        # Note: IS is handled separately by _is_after_where_is
        return bool(
            re.search(
                r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
                r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|BETWEEN)\s*"
                r"(?:[A-Za-z_][A-Za-z0-9_]*|\d+|'[^']*'|\"[^\"]*\"|NULL|TRUE|FALSE|\w+\([^)]*\))\s*$",
                where_clause_stripped,
                re.IGNORECASE,
            )
        )

    def _is_after_where_is(self, left_text: str, where_pos: int, prefix: str) -> bool:
        if prefix:
            return False

        where_clause = left_text[where_pos + 5 :]
        where_clause_stripped = where_clause.strip()
        if not where_clause_stripped:
            return False

        # Match: column IS (with optional NOT) followed by whitespace or end
        return bool(
            re.search(
                r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s+IS(?:\s+NOT)?\s*$",
                where_clause_stripped,
                re.IGNORECASE,
            )
        )

    def _is_after_having_operator(
        self, left_text: str, having_pos: int, prefix: str
    ) -> bool:
        if prefix:
            return False

        having_clause = left_text[having_pos + 6 :]
        return bool(
            re.search(
                r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|NOT\s+IN|BETWEEN)\s*$",
                having_clause,
                re.IGNORECASE,
            )
        )

    def _is_after_having_expression(
        self, left_text: str, having_pos: int, prefix: str
    ) -> bool:
        if prefix:
            return False

        having_clause = left_text[having_pos + 6 :]
        if not having_clause or not having_clause[-1].isspace():
            return False

        clause = having_clause.strip()
        if not clause:
            return False

        if re.search(
            r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|NOT\s+IN|BETWEEN)$", clause, re.IGNORECASE
        ):
            return False

        if re.search(r"(?:AND|OR|NOT|EXISTS|HAVING)\s*$", clause, re.IGNORECASE):
            return False

        return True

    def _extract_from_qualifier(self, left_text: str) -> Optional[str]:
        if not (
            from_match := re.search(
                r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)"
                r"\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?",
                left_text,
                re.IGNORECASE,
            )
        ):
            return None

        table_name = from_match.group(1)
        alias = from_match.group(2)
        if alias and alias.upper() not in self._join_after_table_keywords:
            return alias

        return table_name

    def _extract_scope_from_select(
        self, parsed: sqlglot.exp.Select, database: Optional[SQLDatabase]
    ) -> QueryScope:
        from_tables = []
        join_tables = []
        aliases = {}

        if from_clause := parsed.args.get("from"):
            if isinstance(from_clause, sqlglot.exp.From):
                for table_exp in from_clause.find_all(sqlglot.exp.Table):
                    table_name = table_exp.name
                    alias = (
                        table_exp.alias
                        if hasattr(table_exp, "alias") and table_exp.alias
                        else None
                    )

                    table_obj = (
                        self._find_table_in_database(table_name, database)
                        if database
                        else None
                    )
                    ref = TableReference(name=table_name, alias=alias, table=table_obj)
                    from_tables.append(ref)

                    if alias:
                        aliases[alias.lower()] = ref
                    aliases[table_name.lower()] = ref

        for join_exp in parsed.find_all(sqlglot.exp.Join):
            if table_exp := join_exp.this:
                if isinstance(table_exp, sqlglot.exp.Table):
                    table_name = table_exp.name
                    alias = (
                        table_exp.alias
                        if hasattr(table_exp, "alias") and table_exp.alias
                        else None
                    )

                    table_obj = (
                        self._find_table_in_database(table_name, database)
                        if database
                        else None
                    )
                    ref = TableReference(name=table_name, alias=alias, table=table_obj)
                    join_tables.append(ref)

                    if alias:
                        aliases[alias.lower()] = ref
                    aliases[table_name.lower()] = ref

        return QueryScope(
            from_tables=from_tables,
            join_tables=join_tables,
            current_table=None,
            aliases=aliases,
        )

    def _extract_scope_from_text(
        self, text: str, database: Optional[SQLDatabase]
    ) -> QueryScope:
        sql_keywords = {
            "WHERE",
            "ORDER",
            "GROUP",
            "HAVING",
            "LIMIT",
            "OFFSET",
            "UNION",
            "INTERSECT",
            "EXCEPT",
            "ON",
            "USING",
            "AND",
            "OR",
            "NOT",
            "IN",
            "EXISTS",
            "BETWEEN",
            "LIKE",
            "IS",
            "NULL",
            "ASC",
            "DESC",
            "AS",
            "JOIN",
            "INNER",
            "LEFT",
            "RIGHT",
            "FULL",
            "CROSS",
            "OUTER",
        }

        join_pattern = re.compile(
            r"\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s*(?:\bON\b|\bUSING\b|$)",
            re.IGNORECASE,
        )

        from_tables = []
        join_tables = []
        aliases = {}

        for table_name, alias in self._extract_from_table_tokens(text):
            if table_name.upper() in sql_keywords:
                continue
            if alias and alias.upper() in sql_keywords:
                alias = None

            table_obj = (
                self._find_table_in_database(table_name, database) if database else None
            )
            ref = TableReference(name=table_name, alias=alias, table=table_obj)
            from_tables.append(ref)

            if alias:
                aliases[alias.lower()] = ref
            aliases[table_name.lower()] = ref

        for match in join_pattern.finditer(text):
            table_name = match.group(1)
            alias = match.group(2) if match.group(2) else None

            if table_name.upper() in sql_keywords:
                continue
            if alias and alias.upper() in sql_keywords:
                alias = None

            table_obj = (
                self._find_table_in_database(table_name, database) if database else None
            )
            ref = TableReference(name=table_name, alias=alias, table=table_obj)
            join_tables.append(ref)

            if alias:
                aliases[alias.lower()] = ref
            aliases[table_name.lower()] = ref

        return QueryScope(
            from_tables=from_tables,
            join_tables=join_tables,
            current_table=None,
            aliases=aliases,
        )

    @staticmethod
    def _extract_from_table_tokens(text: str) -> list[tuple[str, Optional[str]]]:
        if not (
            from_match := re.search(
                r"\bFROM\b(?P<section>.*?)(?:\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bHAVING\b|\bLIMIT\b|\bJOIN\b|$)",
                text,
                re.IGNORECASE | re.DOTALL,
            )
        ):
            return []

        from_section = from_match.group("section")
        if not from_section:
            return []

        tables: list[tuple[str, Optional[str]]] = []
        for raw_part in from_section.split(","):
            part = raw_part.strip()
            if not part:
                continue

            if not (
                table_match := re.match(
                    r"(?P<table>[A-Za-z_][A-Za-z0-9_]*)(?:\s+(?:AS\s+)?(?P<alias>[A-Za-z_][A-Za-z0-9_]*))?$",
                    part,
                    re.IGNORECASE,
                )
            ):
                continue

            table_name = table_match.group("table")
            alias = table_match.group("alias") if table_match.group("alias") else None
            tables.append((table_name, alias))

        return tables

    def _find_table_in_database(
        self, table_name: str, database: SQLDatabase
    ) -> Optional:
        try:
            for table in database.tables:
                if table.name.lower() == table_name.lower():
                    return table
        except Exception:
            pass
        return None

    def _is_in_where(self, text: str) -> bool:
        upper = text.upper()
        where_pos = upper.rfind("WHERE")
        if where_pos == -1:
            return False

        after_where = upper[where_pos:]
        return (
            "ORDER BY" not in after_where
            and "GROUP BY" not in after_where
            and "LIMIT" not in after_where
        )

    def _is_after_from(self, text: str) -> bool:
        upper = text.upper()
        from_pos = upper.rfind("FROM")
        if from_pos == -1:
            return False

        after_from = upper[from_pos + 4 :].strip()
        return len(after_from) == 0 or (
            len(after_from) > 0 and after_from[-1] in [" ", "\n", "\t"]
        )

    def _is_after_on(self, text: str) -> bool:
        upper = text.upper()
        on_pos = upper.rfind(" ON ")
        if on_pos == -1:
            return False

        after_on = upper[on_pos + 4 :].strip()
        return len(after_on) == 0 or (
            len(after_on) > 0
            and not after_on.endswith(("WHERE", "ORDER", "GROUP", "LIMIT"))
        )

    def _is_after_order_by(self, text: str) -> bool:
        upper = text.upper()
        order_by_pos = upper.rfind("ORDER BY")
        if order_by_pos == -1:
            return False

        after_order_by = upper[order_by_pos + 8 :].strip()
        return "LIMIT" not in after_order_by

    def _is_after_limit_number(
        self, left_text: str, limit_pos: int, prefix: str
    ) -> bool:
        if limit_pos == -1:
            return False

        after_limit = left_text[limit_pos + 5 :]
        if not after_limit:
            return False

        stripped = after_limit.strip()
        if not stripped:
            return False

        match = re.match(r"^\d+", stripped)
        if match:
            num_end = match.end()
            after_num = stripped[num_end:]
            if not after_num or after_num[0].isspace():
                if prefix:
                    return True
                return after_num.strip() == ""
        return False

    def _is_after_order_by_column(
        self, left_text: str, order_by_pos: int, prefix: str
    ) -> bool:
        if not prefix:
            after_order_by = left_text[order_by_pos + 8 :]
            if not after_order_by or not after_order_by[-1].isspace():
                return False
            after_stripped = after_order_by.strip()
            if not after_stripped:
                return False
            if after_stripped.endswith(","):
                return False
            if after_stripped.upper().endswith(
                ("ASC", "DESC", "NULLS FIRST", "NULLS LAST")
            ):
                return False
            return True

        after_order_by = left_text[order_by_pos + 8 :]
        after_stripped = after_order_by.strip()
        if not after_stripped:
            return False

        column_match = re.match(
            r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s+([A-Za-z_][A-Za-z0-9_]*)?",
            after_stripped,
            re.IGNORECASE,
        )
        if column_match and column_match.group(1):
            return True
        return False

    def _is_after_group_by(self, text: str) -> bool:
        upper = text.upper()
        group_by_pos = upper.rfind("GROUP BY")
        if group_by_pos == -1:
            return False

        after_group_by = upper[group_by_pos + 8 :].strip()
        return (
            "HAVING" not in after_group_by
            and "ORDER BY" not in after_group_by
            and "LIMIT" not in after_group_by
        )

    def _is_in_having(self, text: str) -> bool:
        upper = text.upper()
        having_pos = upper.rfind("HAVING")
        if having_pos == -1:
            return False

        after_having = upper[having_pos:]
        return "ORDER BY" not in after_having and "LIMIT" not in after_having
