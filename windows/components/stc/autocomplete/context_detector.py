import re

from typing import Optional

from helpers.logger import logger

from windows.components.stc.autocomplete.query_scope import (
    QueryScope,
    TableReference,
    VirtualColumn,
    VirtualTable,
)
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase, SQLTable


class ContextDetector:
    _prefix_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
    _identifier_segment_pattern = r"(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`|\"[^\"]+\"|\[[^\]]+\])"
    _table_name_pattern = (
        _identifier_segment_pattern + r"(?:\." + _identifier_segment_pattern + r")?"
    )
    _join_after_table_pattern = re.compile(
        r"\b(?:(?:INNER|LEFT|RIGHT|FULL|CROSS)(?:\s+OUTER)?\s+)?JOIN\s+(" + _table_name_pattern + r")"
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
            scope = self._extract_scope_from_text(text, database)
        except Exception:
            scope = QueryScope.empty()

        dot_match = self._check_dot_completion(left_text, prefix)
        if dot_match:
            table_alias = dot_match.group(1)
            column_prefix = dot_match.group(2) if dot_match.group(2) else ""
            return SQLContext.DOT_COMPLETION, scope, column_prefix

        try:
            context = self._detect_context_with_regex(left_text, prefix)
            if context == SQLContext.INSERT_COMPLETE and left_text.rstrip().endswith(")"):
                prefix = ")"
            return context, scope, prefix
        except Exception as ex:
            logger.debug(f"context detection error: {ex}")
            return SQLContext.UNKNOWN, scope, prefix

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

    _dot_pattern = re.compile(
        r"((?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`|\"[^\"]+\"|\[[^\]]+\]))"
        r"\.([A-Za-z_][A-Za-z0-9_]*)?$"
    )

    def _check_dot_completion(self, left_text: str, prefix: str) -> Optional[re.Match]:
        if "." in left_text:
            return self._dot_pattern.search(left_text)
        return None

    def _detect_context_with_regex(self, left_text: str, prefix: str) -> SQLContext:
        left_upper = left_text.upper()
        statement_type, statement_pos = self._detect_statement_type(left_upper)

        if statement_type == "INSERT":
            return self._detect_insert_context(left_text, left_upper, prefix, statement_pos)
        if statement_type == "UPDATE":
            return self._detect_update_context(left_text, left_upper, prefix, statement_pos)
        if statement_type == "DELETE":
            return self._detect_delete_context(left_text, left_upper, prefix, statement_pos)
        if statement_type != "SELECT":
            return SQLContext.UNKNOWN

        return self._detect_select_context(left_text, left_upper, prefix)

    @staticmethod
    def _detect_statement_type(left_upper: str) -> tuple[str, int]:
        statement_positions = {
            "SELECT": left_upper.rfind("SELECT"),
            "INSERT": left_upper.rfind("INSERT"),
            "UPDATE": left_upper.rfind("UPDATE"),
            "DELETE": left_upper.rfind("DELETE"),
        }
        statement_type = max(statement_positions, key=lambda key: statement_positions[key])
        return statement_type, statement_positions[statement_type]

    def _detect_select_context(
        self, left_text: str, left_upper: str, prefix: str
    ) -> SQLContext:
        select_pos = left_upper.rfind("SELECT")
        if select_pos == -1:
            return SQLContext.UNKNOWN

        from_pos = left_upper.rfind("FROM")
        where_pos = left_upper.rfind("WHERE")
        join_pos = left_upper.rfind("JOIN")
        on_pos = left_upper.rfind(" ON ")
        order_by_pos = left_upper.rfind("ORDER BY")
        group_by_pos = left_upper.rfind("GROUP BY")
        having_pos = left_upper.rfind("HAVING")
        limit_pos = left_upper.rfind("LIMIT")
        offset_pos = left_upper.rfind("OFFSET")

        if re.search(r"\bOVER\s*(?:\(\s*)?$", left_text, re.IGNORECASE):
            return SQLContext.WINDOW_OVER

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
                if self._is_inside_string_literal(left_text[where_pos:]):
                    return SQLContext.WHERE_STRING_LITERAL
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

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        normalized = identifier.strip()
        if not normalized:
            return normalized
        if normalized[0] in {'`', '"', '['} and normalized[-1] in {'`', '"', ']'}:
            return normalized[1:-1]
        return normalized

    # ── INSERT ──────────────────────────────────────────────────────

    @staticmethod
    def _is_inside_string_literal(text: str) -> bool:
        count = 0
        i = 0
        while i < len(text):
            if text[i] == "'" and (i == 0 or text[i - 1] != "\\"):
                count += 1
            i += 1
        return count % 2 == 1

    def _detect_insert_context(
        self, left_text: str, left_upper: str, prefix: str, insert_pos: int
    ) -> SQLContext:
        after_insert = left_text[insert_pos:]

        if self._is_inside_string_literal(after_insert):
            return SQLContext.INSERT_STRING_LITERAL

        into_pos = left_upper.rfind("INTO", insert_pos)
        values_pos = left_upper.rfind("VALUES", insert_pos)

        # INSERT INTO table (...) VALUES (...) |
        if values_pos != -1:
            after_values = left_text[values_pos + 6:].strip()
            # Inside VALUES parentheses or after comma between value groups
            if after_values:
                # Check if we have a complete VALUES(...) group
                open_count = after_values.count("(")
                close_count = after_values.count(")")
                if open_count > close_count:
                    # Inside VALUES(...)
                    return SQLContext.INSERT_VALUE_EXPRESSIONS
                if close_count > 0 and after_values.rstrip().endswith(")"):
                    # Cursor right after ) — no space
                    if left_text.endswith(")"):
                        return SQLContext.INSERT_COMPLETE
                    # After complete VALUES(...) with space
                    return SQLContext.INSERT_POST_VALUES
                if after_values.rstrip().endswith(","):
                    # After VALUES(...),
                    return SQLContext.INSERT_VALUE_EXPRESSIONS
            # Just after VALUES keyword
            return SQLContext.INSERT_VALUE_EXPRESSIONS

        if into_pos == -1:
            return SQLContext.INSERT_INTO

        after_into = left_text[into_pos + 4:].strip()
        if not after_into:
            return SQLContext.INSERT_INTO

        # Check if we're inside column list parentheses
        paren_open = after_into.rfind("(")
        paren_close = after_into.rfind(")")
        if paren_open != -1 and paren_close < paren_open:
            # Inside parentheses — column list
            return SQLContext.INSERT_COLUMNS

        if paren_close != -1 and paren_close > paren_open:
            # After closed parentheses — expect VALUES/SELECT
            return SQLContext.INSERT_VALUES

        # After INSERT INTO, check if table name is present
        tokens = after_into.split()
        if not tokens:
            return SQLContext.INSERT_INTO

        # We have at least a table name
        if len(tokens) == 1 and prefix:
            return SQLContext.INSERT_INTO

        return SQLContext.INSERT_INTO

    # ── UPDATE ──────────────────────────────────────────────────────

    def _detect_update_context(
        self, left_text: str, left_upper: str, prefix: str, update_pos: int
    ) -> SQLContext:
        after_update = left_text[update_pos:]

        if self._is_inside_string_literal(after_update):
            where_pos = left_upper.rfind("WHERE", update_pos)
            if where_pos != -1 and self._is_inside_string_literal(left_text[where_pos:]):
                return SQLContext.UPDATE_WHERE_STRING_LITERAL
            return SQLContext.UPDATE_STRING_LITERAL

        set_pos = left_upper.rfind(" SET ", update_pos)
        where_pos = left_upper.rfind("WHERE", update_pos)
        join_pos = left_upper.rfind("JOIN", update_pos)
        on_pos = left_upper.rfind(" ON ", update_pos)

        # WHERE clause
        if where_pos != -1 and where_pos > max(set_pos, on_pos, -1):
            after_where = left_text[where_pos + 5:]
            after_where_stripped = after_where.strip()
            if not after_where_stripped:
                return SQLContext.UPDATE_WHERE_CONDITIONS
            # After value (column op value) — suggest AND/OR
            if self._is_after_complete_condition(after_where, prefix):
                return SQLContext.UPDATE_WHERE_CONDITIONS
            # After column — suggest operators
            if self._is_after_column_name(after_where, prefix):
                return SQLContext.UPDATE_WHERE_OPERATORS
            return SQLContext.UPDATE_WHERE_CONDITIONS

        # ON clause (JOIN)
        if on_pos != -1 and on_pos > max(join_pos, -1) and set_pos == -1:
            after_on = left_text[on_pos + 4:].strip()
            if self._is_after_complete_join_condition(after_on, prefix):
                return SQLContext.UPDATE_SET_CLAUSE
            return SQLContext.UPDATE_JOIN_ON

        # SET clause
        if set_pos != -1:
            after_set = left_text[set_pos + 5:].strip()
            if not after_set:
                return SQLContext.UPDATE_SET_COLUMNS
            # After = operator
            if re.search(r"=\s*$", after_set):
                return SQLContext.UPDATE_SET_EXPRESSIONS
            # After complete assignment (col = value) with trailing space
            if self._is_after_complete_assignment(after_set, prefix):
                if after_set.rstrip().endswith(","):
                    return SQLContext.UPDATE_SET_COLUMNS
                return SQLContext.UPDATE_WHERE_CLAUSE
            # Column prefix
            return SQLContext.UPDATE_SET_COLUMNS

        # After UPDATE keyword — table name
        after_update_keyword = left_text[update_pos + 6:].strip()
        if not after_update_keyword:
            return SQLContext.UPDATE_TABLE

        # After table name — suggest SET or JOINs
        tokens = after_update_keyword.split()
        if len(tokens) >= 1 and not prefix:
            if join_pos != -1 and join_pos > update_pos:
                # After JOIN table — suggest ON or SET
                after_join = left_text[join_pos + 4:].strip()
                join_tokens = after_join.split()
                if len(join_tokens) >= 1:
                    return SQLContext.UPDATE_SET_CLAUSE
                return SQLContext.UPDATE_TABLE
            return SQLContext.UPDATE_SET_CLAUSE

        return SQLContext.UPDATE_TABLE

    # ── DELETE ──────────────────────────────────────────────────────

    def _detect_delete_context(
        self, left_text: str, left_upper: str, prefix: str, delete_pos: int
    ) -> SQLContext:
        after_delete = left_text[delete_pos:]

        if self._is_inside_string_literal(after_delete):
            return SQLContext.DELETE_WHERE_STRING_LITERAL

        from_pos = left_upper.rfind("FROM", delete_pos)
        where_pos = left_upper.rfind("WHERE", delete_pos)
        using_pos = left_upper.rfind("USING", delete_pos)
        join_pos = left_upper.rfind("JOIN", delete_pos)
        on_pos = left_upper.rfind(" ON ", delete_pos)
        in_pos = left_upper.rfind(" IN ", delete_pos)

        # WHERE clause
        if where_pos != -1 and where_pos > max(from_pos, using_pos, on_pos, -1):
            after_where = left_text[where_pos + 5:]
            after_where_stripped = after_where.strip()
            if not after_where_stripped:
                return SQLContext.DELETE_WHERE_CONDITIONS
            # Check for IN ( subquery
            if in_pos != -1 and in_pos > where_pos:
                after_in = left_text[in_pos + 4:].strip()
                if after_in.startswith("(") and after_in.count("(") > after_in.count(")"):
                    return SQLContext.DELETE_SUBQUERY
            # After complete condition
            if self._is_after_complete_condition(after_where, prefix):
                return SQLContext.DELETE_WHERE_CONDITIONS
            # After = operator
            if re.search(r"(?:=|!=|<>|<=|>=|<|>)\s*$", after_where):
                return SQLContext.DELETE_WHERE_EXPRESSIONS
            # After column name
            if self._is_after_column_name(after_where, prefix):
                return SQLContext.DELETE_WHERE_OPERATORS
            return SQLContext.DELETE_WHERE_CONDITIONS

        # ON clause (JOIN)
        if on_pos != -1 and on_pos > max(join_pos, from_pos, -1):
            after_on = left_text[on_pos + 4:].strip()
            if self._is_after_complete_join_condition(after_on, prefix):
                return SQLContext.DELETE_WHERE_CLAUSE
            return SQLContext.DELETE_JOIN_ON

        # USING clause
        if using_pos != -1 and using_pos > max(from_pos, -1):
            after_using = left_text[using_pos + 5:].strip()
            if not after_using:
                return SQLContext.DELETE_USING
            # After USING table — suggest WHERE
            tokens = after_using.split()
            if len(tokens) >= 1 and not prefix:
                return SQLContext.DELETE_WHERE_CLAUSE
            return SQLContext.DELETE_USING

        # FROM clause
        if from_pos != -1 and from_pos > delete_pos:
            after_from = left_text[from_pos + 4:].strip()
            if not after_from:
                return SQLContext.DELETE_FROM

            # After table name
            tokens = after_from.split()
            if len(tokens) >= 1 and not prefix:
                if join_pos != -1 and join_pos > from_pos:
                    after_join = left_text[join_pos + 4:].strip()
                    join_tokens = after_join.split()
                    if len(join_tokens) >= 1:
                        return SQLContext.DELETE_WHERE_CLAUSE
                return SQLContext.DELETE_WHERE_CLAUSE
            return SQLContext.DELETE_FROM

        return SQLContext.DELETE_FROM

    # ── Helpers for INSERT/UPDATE/DELETE ─────────────────────────────

    @staticmethod
    def _is_after_complete_condition(clause: str, prefix: str) -> bool:
        if prefix:
            return False
        # Match: [word] operator value at end
        return bool(re.search(
            r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
            r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|BETWEEN)\s*"
            r"(?:[A-Za-z_][A-Za-z0-9_]*|\d+|'[^']*'|\"[^\"]*\"|NULL|TRUE|FALSE|\w+\([^)]*\))\s*$",
            clause,
            re.IGNORECASE,
        ))

    @staticmethod
    def _is_after_column_name(clause: str, prefix: str) -> bool:
        if prefix:
            return False
        # Match: identifier at end (with optional qualifier), followed by space
        return bool(re.search(
            r"(?:(?:AND|OR)\s+)?(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s+$",
            clause,
            re.IGNORECASE,
        ))

    @staticmethod
    def _is_after_complete_assignment(clause: str, prefix: str) -> bool:
        if prefix:
            return False
        return bool(re.search(
            r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*"
            r"(?:[A-Za-z_][A-Za-z0-9_.]*|\d+|'[^']*'|\"[^\"]*\"|NULL|TRUE|FALSE|\w+\([^)]*\))\s*$",
            clause,
            re.IGNORECASE,
        ))

    @staticmethod
    def _is_after_complete_join_condition(clause: str, prefix: str) -> bool:
        if prefix:
            return False
        return bool(re.search(
            r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
            r"(?:=|!=|<>|<=|>=|<|>)\s*"
            r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*$",
            clause,
            re.IGNORECASE,
        ))

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

    def _extract_scope_from_text(
        self, text: str, database: Optional[SQLDatabase]
    ) -> QueryScope:
        cleaned_text = re.sub(r"--[^\n]*|/\*.*?\*/", " ", text, flags=re.DOTALL)
        cte_tables, cte_end_pos = self._parse_cte_definitions(cleaned_text)
        main_text = cleaned_text[cte_end_pos:] if cte_end_pos else cleaned_text
        cte_lookup = {ref.name.lower(): ref for ref in cte_tables}

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
            r"\bJOIN\s+(" + self._table_name_pattern + r")\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s*(?:\bON\b|\bUSING\b|$)",
            re.IGNORECASE,
        )

        from_tables = []
        join_tables = []
        aliases = {}

        # Extract UPDATE target table into scope (only for UPDATE statements)
        update_match = re.match(
            r"\s*UPDATE\s+(" + self._table_name_pattern + r")"
            r"(?:\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?",
            main_text,
            re.IGNORECASE,
        )
        if update_match:
            table_name = update_match.group(1)
            alias = update_match.group(2) if update_match.group(2) else None
            if alias and alias.upper() in sql_keywords:
                alias = None
            if table_name.upper() not in sql_keywords:
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

        for table_name, alias, projected_columns in self._extract_from_table_tokens(
            main_text
        ):
            if table_name.upper() in sql_keywords:
                continue
            if alias and alias.upper() in sql_keywords:
                alias = None

            table_obj = None
            if projected_columns is not None:
                table_obj = self._build_virtual_table(table_name, projected_columns)
            elif table_name.lower() in cte_lookup:
                table_obj = cte_lookup[table_name.lower()].table
            elif database:
                table_obj = self._find_table_in_database(table_name, database)

            ref = TableReference(name=table_name, alias=alias, table=table_obj)
            from_tables.append(ref)

            if alias:
                aliases[alias.lower()] = ref
            aliases[table_name.lower()] = ref

        for match in join_pattern.finditer(main_text):
            table_name = match.group(1)
            alias = match.group(2) if match.group(2) else None

            if table_name.upper() in sql_keywords:
                continue
            if alias and alias.upper() in sql_keywords:
                alias = None

            if table_name.lower() in cte_lookup:
                table_obj = cte_lookup[table_name.lower()].table
            else:
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
            cte_tables=cte_tables,
        )

    @staticmethod
    def _extract_from_table_tokens(
        text: str,
    ) -> list[tuple[str, Optional[str], Optional[list[str]]]]:
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

        tables: list[tuple[str, Optional[str], Optional[list[str]]]] = []
        for raw_part in ContextDetector._split_top_level_parts(from_section):
            part = raw_part.strip()
            if not part:
                continue

            subquery_match = re.match(
                r"^\((?P<subquery>.+)\)\s*(?:AS\s+)?(?P<alias>[A-Za-z_][A-Za-z0-9_]*)$",
                part,
                re.IGNORECASE | re.DOTALL,
            )
            if subquery_match:
                alias = subquery_match.group("alias")
                columns = ContextDetector._extract_projected_columns(
                    subquery_match.group("subquery")
                )
                tables.append((alias, alias, columns))
                continue

            if not (
                table_match := re.match(
                    r"(?P<table>" + ContextDetector._table_name_pattern + r")(?:\s+(?:AS\s+)?(?P<alias>[A-Za-z_][A-Za-z0-9_]*))?(?:\s+[A-Za-z_][A-Za-z0-9_]*)?$",
                    part,
                    re.IGNORECASE,
                )
            ):
                continue

            table_name = table_match.group("table")
            alias = table_match.group("alias") if table_match.group("alias") else None
            tables.append((table_name, alias, None))

        return tables

    @staticmethod
    def _split_top_level_parts(text: str) -> list[str]:
        parts = []
        start = 0
        depth = 0
        for idx, ch in enumerate(text):
            if ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(text[start:idx])
                start = idx + 1
        parts.append(text[start:])
        return parts

    @staticmethod
    def _extract_projected_columns(subquery_sql: str) -> list[str]:
        match = re.search(
            r"\bSELECT\b\s+(?P<select>.*?)(?:\bFROM\b|$)",
            subquery_sql,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return []

        select_list = match.group("select")
        columns: list[str] = []
        for raw_expr in ContextDetector._split_top_level_parts(select_list):
            expr = raw_expr.strip()
            if not expr or expr == "*":
                continue

            alias_match = re.search(
                r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)$", expr, re.IGNORECASE
            )
            if alias_match:
                col_name = alias_match.group(1)
            else:
                identifier_match = re.match(
                    r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?([A-Za-z_][A-Za-z0-9_]*)$",
                    expr,
                )
                if not identifier_match:
                    continue
                col_name = identifier_match.group(1)

            if col_name not in columns:
                columns.append(col_name)

        return columns

    @staticmethod
    def _build_virtual_table(name: str, columns: list[str]) -> VirtualTable:
        return VirtualTable(
            name=name,
            columns=[VirtualColumn(name=column) for column in columns],
        )

    def _parse_cte_definitions(self, text: str) -> tuple[list[TableReference], int]:
        cte_refs: list[TableReference] = []
        with_match = re.match(r"\s*WITH\s+", text, re.IGNORECASE)
        if not with_match:
            return cte_refs, 0

        pos = with_match.end()
        length = len(text)
        while pos < length:
            while pos < length and text[pos].isspace():
                pos += 1

            name_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", text[pos:])
            if not name_match:
                break
            cte_name = name_match.group(1)
            pos += name_match.end()

            while pos < length and text[pos].isspace():
                pos += 1

            if not re.match(r"AS\b", text[pos:], re.IGNORECASE):
                break
            pos += 2

            while pos < length and text[pos].isspace():
                pos += 1

            if pos >= length or text[pos] != "(":
                break

            pos += 1
            depth = 1
            subquery_start = pos
            while pos < length and depth > 0:
                if text[pos] == "(":
                    depth += 1
                elif text[pos] == ")":
                    depth -= 1
                pos += 1

            if depth != 0:
                break

            subquery_sql = text[subquery_start : pos - 1]
            projected_columns = self._extract_projected_columns(subquery_sql)
            virtual_table = self._build_virtual_table(cte_name, projected_columns)
            cte_ref = TableReference(name=cte_name, alias=None, table=virtual_table)
            cte_refs.append(cte_ref)

            while pos < length and text[pos].isspace():
                pos += 1

            if pos < length and text[pos] == ",":
                pos += 1
                continue
            break

        return cte_refs, pos

    def _find_table_in_database(
        self, table_name: str, database: SQLDatabase
    ) -> Optional[SQLTable]:
        table_name_candidate = table_name.split(".")[-1]
        normalized_candidate = self._normalize_identifier(table_name_candidate)
        normalized_full_name = self._normalize_identifier(table_name)
        try:
            for table in database.tables:
                if table.name.lower() == normalized_full_name.lower():
                    return table
                if table.name.lower() == normalized_candidate.lower():
                    return table
        except Exception:
            pass
        return None

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

