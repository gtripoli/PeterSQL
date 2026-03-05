import re

from typing import Optional

from windows.components.stc.autocomplete.completion_types import (
    CompletionItem,
    CompletionItemType,
)
from windows.components.stc.autocomplete.query_scope import QueryScope, TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase, SQLTable


class SuggestionBuilder:
    _primary_keywords = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "SHOW",
        "DESCRIBE",
        "EXPLAIN",
        "WITH",
        "REPLACE",
        "MERGE",
    }

    _aggregate_functions = {"COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP_CONCAT"}

    _select_list_excluded_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
    }

    _join_expression_excluded_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "PI",
        "POW",
        "POWER",
    }

    _group_by_excluded_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "PI",
        "POW",
        "POWER",
    }

    _having_excluded_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "PI",
        "POW",
        "POWER",
    }

    _max_database_columns = 400

    _scope_restricted_contexts = {
        SQLContext.WHERE_CLAUSE,
        SQLContext.JOIN_ON,
        SQLContext.JOIN_ON_AFTER_OPERATOR,
        SQLContext.JOIN_ON_AFTER_EXPRESSION,
        SQLContext.ORDER_BY_CLAUSE,
        SQLContext.GROUP_BY_CLAUSE,
        SQLContext.HAVING_CLAUSE,
        SQLContext.HAVING_AFTER_OPERATOR,
        SQLContext.HAVING_AFTER_EXPRESSION,
    }

    def __init__(
        self, database: Optional[SQLDatabase], current_table: Optional[SQLTable]
    ):
        self._database = database
        self._current_table = current_table

    def _is_scope_restricted_context(self, context: SQLContext) -> bool:
        return context in self._scope_restricted_contexts

    def _is_current_table_in_scope(self, scope: QueryScope) -> bool:
        if not self._current_table:
            return False
        current_table_name_lower = self._current_table.name.lower()
        for ref in scope.from_tables + scope.join_tables:
            if ref.name.lower() == current_table_name_lower:
                return True
        return False

    def build(
        self,
        context: SQLContext,
        scope: QueryScope,
        prefix: str,
        statement: str = "",
        cursor_pos: Optional[int] = None,
    ) -> list[CompletionItem]:
        if context == SQLContext.EMPTY:
            return self._build_empty(prefix)

        if context == SQLContext.SINGLE_TOKEN:
            return self._build_single_token(prefix)

        if context == SQLContext.DOT_COMPLETION:
            return self._build_dot_completion(scope, prefix, statement)

        if context == SQLContext.SELECT_LIST:
            return self._build_select_list(scope, prefix, statement, cursor_pos)

        if context == SQLContext.FROM_CLAUSE:
            import re

            statement_upper = statement.upper()

            if re.search(r"\bAS\s+$", statement_upper):
                return []

            if prefix and re.search(r"\bAS\s+\w+$", statement_upper):
                return []

            if (
                prefix
                and scope.from_tables
                and "," not in statement
                and self._is_after_completed_from_table_with_prefix(
                    statement, prefix, scope
                )
            ):
                return self._build_from_followup_keywords(prefix, scope)

            if not prefix and scope.from_tables:
                if "," in statement:
                    in_scope_table_names = {
                        ref.name.lower() for ref in scope.from_tables
                    }
                    try:
                        tables = [
                            CompletionItem(
                                name=table.name, item_type=CompletionItemType.TABLE
                            )
                            for table in self._database.tables
                            if table.name.lower() not in in_scope_table_names
                        ]
                        return sorted(
                            tables, key=lambda x: self._table_name_sort_key(x.name)
                        )
                    except (AttributeError, TypeError):
                        return []
                else:
                    return self._build_from_followup_keywords(prefix, scope)

            return self._build_from_clause(prefix, statement, scope)

        if context == SQLContext.JOIN_CLAUSE:
            return self._build_join_clause(prefix, scope)

        if context == SQLContext.JOIN_AFTER_TABLE:
            return self._build_join_after_table(scope)

        if context == SQLContext.JOIN_ON:
            return self._build_join_on(scope, prefix, statement)

        if context == SQLContext.JOIN_ON_AFTER_OPERATOR:
            return self._build_join_on_after_operator(scope, prefix)

        if context == SQLContext.JOIN_ON_AFTER_EXPRESSION:
            return self._build_join_on_after_expression(prefix)

        if context == SQLContext.WHERE_CLAUSE:
            return self._build_where_clause(scope, prefix, statement)

        if context == SQLContext.WHERE_AFTER_EXPRESSION:
            return self._build_where_after_expression(prefix, statement)

        if context == SQLContext.WHERE_AFTER_OPERATOR:
            return self._build_where_after_operator(scope, prefix, statement)

        if context == SQLContext.ORDER_BY_CLAUSE:
            return self._build_order_by(scope, prefix, statement)

        if context == SQLContext.ORDER_BY_AFTER_COLUMN:
            return self._build_order_by_after_column(prefix)

        if context == SQLContext.GROUP_BY_CLAUSE:
            return self._build_group_by(scope, prefix, statement, cursor_pos)

        if context == SQLContext.HAVING_CLAUSE:
            return self._build_having(scope, prefix, statement)

        if context == SQLContext.HAVING_AFTER_OPERATOR:
            return self._build_having_after_operator(scope, prefix, statement)

        if context == SQLContext.HAVING_AFTER_EXPRESSION:
            return self._build_having_after_expression(prefix)

        if context == SQLContext.WINDOW_OVER:
            return self._build_window_over(prefix)

        if context == SQLContext.LIMIT_OFFSET_CLAUSE:
            return []

        if context == SQLContext.AFTER_LIMIT_NUMBER:
            return self._build_after_limit_number(prefix)

        return self._build_keywords(prefix)

    def _build_empty(self, prefix: str) -> list[CompletionItem]:
        keywords = [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in self._primary_keywords
        ]

        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.name.startswith(prefix_upper)]

        return sorted(keywords, key=lambda x: x.name)

    def _build_dot_completion(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        import re

        cursor_pos = len(statement)
        text_before_cursor = statement[:cursor_pos]

        dot_match = re.search(
            r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)?$",
            text_before_cursor,
        )
        if not dot_match:
            return []

        table_alias = dot_match.group(1)
        column_prefix = dot_match.group(2) if dot_match.group(2) else ""

        resolved_table = self._resolve_table_alias(table_alias, scope, statement)
        if not resolved_table:
            return []

        table_name = resolved_table.name
        columns = resolved_table.columns

        try:
            ordered_columns = self._order_columns_for_dot_completion(columns)
        except (AttributeError, TypeError):
            ordered_columns = []

        column_items = []
        for col in ordered_columns:
            col_name = col.name
            if not column_prefix or col_name.upper().startswith(column_prefix.upper()):
                column_items.append(
                    CompletionItem(name=col_name, item_type=CompletionItemType.COLUMN)
                )

        return column_items

    @staticmethod
    def _order_columns_for_dot_completion(columns: object) -> list[object]:
        columns_list = list(columns)

        def key(item_with_index: tuple[int, object]) -> tuple[int, int]:
            idx, col = item_with_index
            raw_id = getattr(col, "id", None)
            if isinstance(raw_id, int):
                return (0, raw_id)
            if isinstance(raw_id, str) and raw_id.isdigit():
                return (0, int(raw_id))
            return (1, idx)

        return [col for _, col in sorted(enumerate(columns_list), key=key)]

    def _resolve_table_alias(self, table_alias: str, scope: QueryScope, statement: str):
        for ref in scope.from_tables:
            if ref.alias and ref.alias.lower() == table_alias.lower():
                if ref.table is not None:
                    return ref.table
                return self._get_table_by_name(ref.name)
            if ref.name.lower() == table_alias.lower():
                if ref.table is not None:
                    return ref.table
                return self._get_table_by_name(ref.name)

        for ref in scope.join_tables:
            if ref.alias and ref.alias.lower() == table_alias.lower():
                if ref.table is not None:
                    return ref.table
                return self._get_table_by_name(ref.name)
            if ref.name.lower() == table_alias.lower():
                if ref.table is not None:
                    return ref.table
                return self._get_table_by_name(ref.name)

        for ref in scope.cte_tables:
            if ref.name.lower() == table_alias.lower() and ref.table is not None:
                return ref.table

        if (
            scope.current_table
            and scope.current_table.name.lower() == table_alias.lower()
        ):
            return scope.current_table

        return self._get_table_by_name(table_alias)

    def _get_table_by_name(self, table_name: str):
        try:
            for table in self._database.tables:
                if table.name.lower() == table_name.lower():
                    return table
        except (AttributeError, TypeError):
            pass
        return None

    def _build_single_token(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []

        try:
            all_keywords = self._database.context.KEYWORDS
            keywords = [
                CompletionItem(
                    name=str(kw).upper(), item_type=CompletionItemType.KEYWORD
                )
                for kw in all_keywords
            ]
        except (AttributeError, TypeError):
            return []

        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.name.startswith(prefix_upper)]

        return sorted(keywords, key=lambda x: x.name)

    def _build_select_list(
        self,
        scope: QueryScope,
        prefix: str,
        statement: str = "",
        cursor_pos: Optional[int] = None,
    ) -> list[CompletionItem]:
        has_scope = bool(scope.from_tables or scope.join_tables)
        left_statement = statement[:cursor_pos] if cursor_pos is not None else statement

        if self._is_after_completed_select_item(
            left_statement
        ) or self._is_after_completed_select_item_with_prefix(
            left_statement,
            prefix,
        ):
            return self._build_select_completed_item_keywords(
                left_statement, scope, prefix
            )

        if self._is_after_select_comma_context(left_statement, prefix):
            return self._build_select_list_after_comma(
                scope, prefix, left_statement, has_scope
            )

        if prefix:
            if has_scope and (
                single_reference := self._get_single_unaliased_scope_reference(scope)
            ):
                columns = self._build_single_scope_prefix_columns(
                    single_reference, prefix
                )
                items = list(columns)
                items.extend(self._build_select_list_functions(prefix))
                hints = self._get_out_of_scope_table_hints(scope, prefix, columns)
                items.extend(hints)
                return items

            columns = self._resolve_columns_in_scope(
                scope, prefix, SQLContext.SELECT_LIST
            )
            items = list(columns)
            items.extend(self._build_select_list_functions(prefix))
            if has_scope:
                hints = self._get_out_of_scope_table_hints(scope, prefix, columns)
                items.extend(hints)
            return items

        if not has_scope:
            return self._build_select_list_functions(prefix)

        items = self._resolve_columns_in_scope(scope, prefix, SQLContext.SELECT_LIST)
        items.extend(self._build_select_list_functions(prefix))
        return items

    @staticmethod
    def _get_single_unaliased_scope_reference(
        scope: QueryScope,
    ) -> Optional[TableReference]:
        references = scope.from_tables + scope.join_tables
        if len(references) != 1:
            return None

        reference = references[0]
        if reference.alias:
            return None
        if not reference.table:
            return None

        return reference

    @staticmethod
    def _build_single_scope_prefix_columns(
        reference: TableReference, prefix: str
    ) -> list[CompletionItem]:
        table = reference.table
        if not table:
            return []

        prefix_lower = prefix.lower()
        table_name_matches_prefix = reference.name.lower().startswith(prefix_lower)

        matched_columns: list[str] = []
        all_columns: list[str] = []
        try:
            for column in table.columns:
                if not column.name:
                    continue
                all_columns.append(column.name)
                if column.name.lower().startswith(prefix_lower):
                    matched_columns.append(column.name)
        except (AttributeError, TypeError):
            return []

        if not table_name_matches_prefix:
            return [
                CompletionItem(
                    name=column_name,
                    item_type=CompletionItemType.COLUMN,
                    description=reference.name,
                )
                for column_name in matched_columns
            ]

        items = [
            CompletionItem(
                name=column_name,
                item_type=CompletionItemType.COLUMN,
                description=reference.name,
            )
            for column_name in matched_columns
        ]
        items.extend(
            CompletionItem(
                name=f"{reference.name}.{column_name}",
                item_type=CompletionItemType.COLUMN,
                description=reference.name,
            )
            for column_name in matched_columns
        )
        items.extend(
            CompletionItem(
                name=f"{reference.name}.{column_name}",
                item_type=CompletionItemType.COLUMN,
                description=reference.name,
            )
            for column_name in all_columns
            if column_name not in matched_columns
        )
        return items

    @staticmethod
    def _is_after_completed_select_item(statement: str) -> bool:
        import re

        if not re.search(r"\bSELECT\b", statement, re.IGNORECASE):
            return False
        if re.search(r",\s+$", statement):
            return False

        match = re.search(r"(\*|\w+(?:\.\w+)?)\s+$", statement)
        if not match:
            return False

        token = match.group(1).upper()
        return token != "SELECT"

    @staticmethod
    def _is_after_select_comma(statement: str) -> bool:
        import re

        return bool(
            re.search(r"\bSELECT\b", statement, re.IGNORECASE)
            and re.search(r",\s+$", statement)
        )

    @staticmethod
    def _is_after_completed_select_item_with_prefix(
        statement: str, prefix: str
    ) -> bool:
        import re

        if not prefix:
            return False
        if not statement.endswith(prefix):
            return False
        if not re.search(r"\bSELECT\b", statement, re.IGNORECASE):
            return False
        if re.search(r",\s*\w+$", statement):
            return False

        completed_item_match = re.search(r"(\*|\w+(?:\.\w+)?)\s+\w+$", statement)
        if not completed_item_match:
            return False

        return completed_item_match.group(1).upper() != "SELECT"

    @staticmethod
    def _is_after_select_comma_context(statement: str, prefix: str) -> bool:
        import re

        if not re.search(r"\bSELECT\b", statement, re.IGNORECASE):
            return False
        if re.search(r",\s+$", statement):
            return True
        if not prefix:
            return False
        return bool(re.search(r",\s*\w+$", statement))

    def _build_select_list_after_comma(
        self,
        scope: QueryScope,
        prefix: str,
        statement: str,
        has_scope: bool,
    ) -> list[CompletionItem]:
        qualifier = self._get_previous_select_item_qualifier(statement)
        if qualifier:
            columns = self._get_qualified_table_columns_by_name(
                qualifier, prefix, scope
            )
            columns.extend(self._build_select_list_functions(prefix))
            return columns

        if not has_scope and self._current_table:
            columns = self._get_current_table_columns(scope, prefix)
            columns.extend(self._build_select_list_functions(prefix))
            return columns

        if not has_scope:
            return self._build_select_list_functions(prefix)

        columns = self._get_join_table_columns(scope, prefix)
        columns.extend(self._get_from_table_columns(scope, prefix))
        items = columns  # Preserve schema order (do NOT sort alphabetically)
        items.extend(self._build_select_list_functions(prefix))
        return items

    @staticmethod
    def _get_previous_select_item_qualifier(statement: str) -> Optional[str]:
        import re

        select_match = re.search(
            r"\bSELECT\b(.*)$", statement, re.IGNORECASE | re.DOTALL
        )
        if not select_match:
            return None
        select_body = select_match.group(1)
        if "," not in select_body:
            return None
        before_last_comma = select_body.rsplit(",", 1)[0].rstrip()
        qualifier_match = re.search(r"(\w+)\.\w+$", before_last_comma)
        if not qualifier_match:
            return None
        return qualifier_match.group(1)

    def _get_qualified_table_columns_by_name(
        self,
        qualifier: str,
        prefix: str,
        scope: QueryScope,
    ) -> list[CompletionItem]:
        reference = scope.aliases.get(qualifier.lower())
        table = reference.table if reference and reference.table else None
        display_name = reference.alias if reference and reference.alias else qualifier

        if not table and self._database:
            try:
                table = next(
                    (
                        candidate
                        for candidate in self._database.tables
                        if candidate.name.lower() == qualifier.lower()
                    ),
                    None,
                )
            except (AttributeError, TypeError):
                table = None
            display_name = qualifier

        if not table:
            return []

        prefix_lower = prefix.lower() if prefix else None
        result = []
        try:
            for column in table.columns:
                if not column.name:
                    continue
                if prefix_lower and not column.name.lower().startswith(prefix_lower):
                    continue
                result.append(
                    CompletionItem(
                        name=f"{display_name}.{column.name}",
                        item_type=CompletionItemType.COLUMN,
                        description=getattr(table, "name", qualifier),
                    )
                )
        except (AttributeError, TypeError):
            return []
        return result

    def _build_from_clause(
        self, prefix: str, statement: str = "", scope: QueryScope = QueryScope.empty()
    ) -> list[CompletionItem]:
        database = self._database
        if not database:
            return []

        try:
            physical_tables = [
                CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                for table in database.tables
            ]
        except (AttributeError, TypeError):
            return []

        cte_names = [ref.name for ref in scope.cte_tables]
        cte_set = {name.lower() for name in cte_names}
        cte_tables = [
            CompletionItem(name=name, item_type=CompletionItemType.TABLE)
            for name in cte_names
        ]
        tables = cte_tables + [
            table for table in physical_tables if table.name.lower() not in cte_set
        ]

        # Extract tables referenced in SELECT list (e.g., SELECT users.id FROM | → users only)
        # This applies ALWAYS, with or without prefix when qualified refs are present
        referenced_tables = []
        if statement:
            import re

            # Find qualified columns in SELECT: table.column
            # Match both "FROM " (with space) and "FROM" (at end of statement)
            select_match = re.search(
                r"SELECT\s+(.*?)\s+FROM\s*", statement, re.IGNORECASE | re.DOTALL
            )
            if select_match:
                select_list = select_match.group(1)
                # Extract table names from qualified columns
                qualified_refs = re.findall(r"\b(\w+)\.\w+", select_list)
                seen = set()
                for ref in qualified_refs:
                    ref_lower = ref.lower()
                    if ref_lower in seen:
                        continue
                    seen.add(ref_lower)
                    referenced_tables.append(ref_lower)

        if referenced_tables:
            referenced_set = set(referenced_tables)
            tables = [table for table in tables if table.name.lower() in referenced_set]

            if prefix:
                prefix_lower = prefix.lower()
                tables = [
                    table
                    for table in tables
                    if table.name.lower().startswith(prefix_lower)
                ]

            referenced_order = {
                name: index for index, name in enumerate(referenced_tables)
            }
            return sorted(
                tables,
                key=lambda table: referenced_order.get(
                    table.name.lower(), len(referenced_tables)
                ),
            )

        # Filter by prefix if present
        if prefix:
            prefix_lower = prefix.lower()
            tables = [t for t in tables if t.name.lower().startswith(prefix_lower)]

        cte_result = [t for t in tables if t.name.lower() in cte_set]
        physical_result = [t for t in tables if t.name.lower() not in cte_set]
        return cte_result + sorted(
            physical_result, key=lambda x: self._table_name_sort_key(x.name)
        )

    @staticmethod
    def _is_after_completed_from_table_with_prefix(
        statement: str, prefix: str, scope: QueryScope
    ) -> bool:
        import re

        if not scope.from_tables:
            return False

        last_ref = scope.from_tables[-1]
        if not last_ref.table:
            return False

        statement_trimmed = statement.rstrip()
        if not statement_trimmed.endswith(prefix):
            return False

        prefix_lower = prefix.lower()
        matches_completed_table = prefix_lower == last_ref.name.lower() or (
            bool(last_ref.alias) and prefix_lower == last_ref.alias.lower()
        )

        if matches_completed_table:
            return True

        return bool(
            re.search(
                r"\bFROM\s+[A-Za-z_][A-Za-z0-9_]*(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_]*)?\s+[A-Za-z_][A-Za-z0-9_]*$",
                statement_trimmed,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _build_from_followup_keywords(
        prefix: str, scope: QueryScope
    ) -> list[CompletionItem]:
        keywords = [
            "JOIN",
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "CROSS JOIN",
            "WHERE",
            "GROUP BY",
            "ORDER BY",
            "LIMIT",
        ]

        has_alias = any(ref.alias for ref in scope.from_tables)
        if not has_alias:
            keywords.insert(5, "AS")

        if prefix:
            prefix_upper = prefix.upper()
            filtered = [kw for kw in keywords if kw.startswith(prefix_upper)]
            if filtered:
                keywords = filtered

        return [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in keywords
        ]

    def _build_join_clause(
        self, prefix: str, scope: QueryScope
    ) -> list[CompletionItem]:
        database = self._database
        if not database:
            return []

        in_scope_table_names = {
            ref.name.lower()
            for ref in scope.from_tables + scope.join_tables
            if not ref.alias
        }

        try:
            physical_tables = [
                CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                for table in database.tables
                if table.name.lower() not in in_scope_table_names
            ]
        except (AttributeError, TypeError):
            return []

        cte_tables = [
            CompletionItem(name=ref.name, item_type=CompletionItemType.TABLE)
            for ref in scope.cte_tables
            if ref.name.lower() not in in_scope_table_names
        ]
        cte_set = {item.name.lower() for item in cte_tables}
        tables = cte_tables + [
            table for table in physical_tables if table.name.lower() not in cte_set
        ]

        if prefix:
            prefix_lower = prefix.lower()
            tables = [t for t in tables if t.name.lower().startswith(prefix_lower)]

        cte_result = [t for t in tables if t.name.lower() in cte_set]
        physical_result = [t for t in tables if t.name.lower() not in cte_set]
        return cte_result + sorted(
            physical_result, key=lambda x: self._table_name_sort_key(x.name)
        )

    @staticmethod
    def _build_join_after_table(scope: QueryScope) -> list[CompletionItem]:
        keywords = ["ON", "USING"]
        if not scope.join_tables or not scope.join_tables[-1].alias:
            keywords.insert(0, "AS")

        return [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in keywords
        ]

    @staticmethod
    def _table_name_sort_key(name: str) -> tuple[str, str]:
        normalized = "".join(ch for ch in name.lower() if ch.isalnum())
        return normalized, name.lower()

    @staticmethod
    def _is_after_join_on_keyword(statement: str) -> bool:
        import re

        return bool(re.search(r"\bON\s*$", statement, re.IGNORECASE))

    @staticmethod
    def _sort_columns_by_name(columns: list[CompletionItem]) -> list[CompletionItem]:
        return columns  # Preserve schema order (do NOT sort alphabetically)

    def _build_join_on(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        items = []
        if prefix:
            columns = self._resolve_columns_in_scope(scope, prefix, SQLContext.JOIN_ON)
        else:
            join_columns = self._get_join_table_columns(scope, None)
            if self._is_after_join_on_keyword(statement):
                join_columns = self._sort_columns_by_name(join_columns)

            columns = list(join_columns)
            columns.extend(self._get_from_table_columns(scope, None))

        # Filter out the column on the left side of the operator (same logic as WHERE)
        if not prefix and statement:
            import re

            match = re.search(
                r"(\w+\.?\w*)\s*(?:=|!=|<>|<|>|<=|>=)\s*$", statement, re.IGNORECASE
            )
            if match:
                left_column = match.group(1).strip()
                columns = [c for c in columns if c.name.lower() != left_column.lower()]

        items.extend(columns)
        if prefix:
            items.extend(self._build_functions(prefix))
        else:
            items.extend(self._build_join_expression_functions(prefix))
        return items

    def _build_join_on_after_expression(self, prefix: str) -> list[CompletionItem]:
        keywords = ["AND", "NOT", "OR", "GROUP BY", "LIMIT", "ORDER BY", "WHERE"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    def _build_join_on_after_operator(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        columns = self._resolve_columns_in_scope(
            scope, prefix, SQLContext.JOIN_ON_AFTER_OPERATOR
        )

        if not prefix:
            columns = self._get_join_table_columns(scope, None)
            columns.extend(self._get_from_table_columns(scope, None))

        items = list(columns)
        if not prefix:
            items.extend(
                CompletionItem(name=literal, item_type=CompletionItemType.KEYWORD)
                for literal in ["NULL", "TRUE", "FALSE"]
            )

        if prefix:
            items.extend(self._build_functions(prefix))
        else:
            items.extend(self._build_join_expression_functions(prefix))
        return items

    def _build_join_expression_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            function
            for function in functions
            if function.name not in self._join_expression_excluded_functions
        ]

    def _build_where_clause(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        if self._is_where_in_value_list(statement):
            return self._build_where_literals(prefix)

        columns = self._build_where_columns(scope, prefix, statement)
        columns = self._exclude_left_column_from_where(statement, columns)

        items = list(columns)
        items.extend(self._build_functions(prefix))
        return items

    def _build_where_after_expression(
        self, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        if self._is_after_is_keyword(statement):
            return self._build_after_is_keywords(prefix)

        keywords = ["AND", "OR", "GROUP BY", "HAVING", "LIMIT", "ORDER BY"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    def _build_where_after_operator(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        columns = self._build_where_columns(scope, prefix, statement)
        columns = self._exclude_left_column_from_where(statement, columns)

        items = self._build_where_literals(prefix)
        items.extend(columns)
        items.extend(self._build_functions(prefix))
        return items

    @staticmethod
    def _exclude_left_column_from_where(
        statement: str, columns: list[CompletionItem]
    ) -> list[CompletionItem]:
        if not statement:
            return columns

        match = re.search(
            r"(\w+\.?\w*)\s*(?:=|!=|<>|<=|>=|<|>|LIKE|IN|NOT\s+IN|BETWEEN)\s*$",
            statement,
            re.IGNORECASE,
        )
        if not match:
            return columns

        left_column = match.group(1).strip().lower()
        filtered = []
        for column in columns:
            column_name = column.name.lower()
            if column_name == left_column:
                continue
            if "." in column_name and column_name.split(".", 1)[1] == left_column:
                continue
            filtered.append(column)
        return filtered

    def _build_where_columns(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        prefer_qualified = self._should_prefer_qualified_columns(statement)

        if not (single_reference := self._get_single_scope_reference(scope)):
            return self._resolve_columns_in_scope(
                scope, prefix, SQLContext.WHERE_CLAUSE
            )

        if (
            prefix
            and single_reference.alias
            and prefix.lower() == single_reference.alias.lower()
        ):
            return self._get_alias_columns(prefix, scope)

        return self._build_single_table_where_columns(
            single_reference, prefix, prefer_qualified
        )

    @staticmethod
    def _get_single_scope_reference(scope: QueryScope) -> Optional[TableReference]:
        references = scope.from_tables + scope.join_tables
        if len(references) != 1:
            return None

        reference = references[0]
        if not reference.table:
            return None
        return reference

    def _build_single_table_where_columns(
        self, reference: TableReference, prefix: str, prefer_qualified: bool
    ) -> list[CompletionItem]:
        table = reference.table
        if not table:
            return []

        if prefer_qualified:
            return self._build_qualified_columns_for_reference(reference, prefix)

        if not prefix:
            return self._build_unqualified_table_columns(reference)

        if reference.alias:
            return self._build_unqualified_table_columns(reference, prefix)

        return self._build_single_scope_prefix_columns(reference, prefix)

    @staticmethod
    def _build_qualified_columns_for_reference(
        reference: TableReference, prefix: str = ""
    ) -> list[CompletionItem]:
        table = reference.table
        if not table:
            return []

        qualifier = reference.alias if reference.alias else reference.name
        prefix_lower = prefix.lower()
        items = []
        try:
            for column in table.columns:
                if not column.name:
                    continue
                if prefix and not column.name.lower().startswith(prefix_lower):
                    continue
                items.append(
                    CompletionItem(
                        name=f"{qualifier}.{column.name}",
                        item_type=CompletionItemType.COLUMN,
                        description=reference.name,
                    )
                )
        except (AttributeError, TypeError):
            return []
        return items

    @staticmethod
    def _should_prefer_qualified_columns(statement: str) -> bool:
        if not statement:
            return False

        select_match = re.search(
            r"\bSELECT\b(?P<body>.*?)(?:\bFROM\b|$)",
            statement,
            re.IGNORECASE | re.DOTALL,
        )
        if not select_match:
            return False

        select_body = select_match.group("body")
        return bool(
            re.search(
                r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b",
                select_body,
            )
        )

    @staticmethod
    def _build_unqualified_table_columns(
        reference: TableReference, prefix: str = ""
    ) -> list[CompletionItem]:
        table = reference.table
        if not table:
            return []

        prefix_lower = prefix.lower()
        items = []
        try:
            for column in table.columns:
                if not column.name:
                    continue
                if prefix and not column.name.lower().startswith(prefix_lower):
                    continue
                items.append(
                    CompletionItem(
                        name=column.name,
                        item_type=CompletionItemType.COLUMN,
                        description=reference.name,
                    )
                )
        except (AttributeError, TypeError):
            return []
        return items

    @staticmethod
    def _build_where_literals(prefix: str) -> list[CompletionItem]:
        literals = [
            "NULL",
            "TRUE",
            "FALSE",
            "CURRENT_DATE",
            "CURRENT_TIME",
            "CURRENT_TIMESTAMP",
        ]
        if prefix:
            prefix_upper = prefix.upper()
            literals = [
                literal for literal in literals if literal.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=literal, item_type=CompletionItemType.KEYWORD)
            for literal in literals
        ]

    @staticmethod
    def _build_after_is_keywords(prefix: str) -> list[CompletionItem]:
        keywords = ["NULL", "NOT NULL", "TRUE", "FALSE"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    @staticmethod
    def _is_after_is_keyword(statement: str) -> bool:
        return bool(re.search(r"\bIS\s+$", statement, re.IGNORECASE))

    @staticmethod
    def _is_where_in_value_list(statement: str) -> bool:
        if not statement:
            return False

        return bool(re.search(r"\bIN\s*\([^)]*,\s*$", statement, re.IGNORECASE))

    def _build_order_by(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        is_after_comma = bool(re.search(r",\s*$", statement) if statement else False)

        columns = self._build_where_columns(scope, prefix, statement)

        items = list(columns)
        items.extend(self._build_order_by_functions(prefix))

        return items

    @staticmethod
    def _build_order_by_after_column(prefix: str) -> list[CompletionItem]:
        keywords = ["ASC", "DESC", "NULLS FIRST", "NULLS LAST", "LIMIT"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.startswith(prefix_upper)]

        return [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in keywords
        ]

    def _build_order_by_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            function
            for function in functions
            if function.name not in self._order_by_excluded_functions
        ]

    _order_by_excluded_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "PI",
        "POW",
        "POWER",
    }

    @staticmethod
    def _exclude_order_by_existing_columns(
        columns: list[CompletionItem], left_statement: str
    ) -> list[CompletionItem]:
        ordered_column_names = SuggestionBuilder._extract_order_by_column_names(
            left_statement
        )
        if not ordered_column_names:
            return columns

        filtered = []
        for column in columns:
            column_name = column.name.lower()
            base_name = (
                column_name.split(".", 1)[1] if "." in column_name else column_name
            )
            if column_name in ordered_column_names or base_name in ordered_column_names:
                continue
            filtered.append(column)
        return filtered

    @staticmethod
    def _extract_order_by_column_names(left_statement: str) -> set[str]:
        if not (
            match := re.search(
                r"\bORDER\s+BY\s+(?P<clause>.+)$", left_statement, re.IGNORECASE
            )
        ):
            return set()

        clause = match.group("clause")
        if not clause:
            return set()

        ordered_names: set[str] = set()
        for raw_part in clause.split(","):
            part = raw_part.strip()
            if not part:
                continue

            part_clean = re.sub(
                r"\s+(?:ASC|DESC|NULLS\s+(?:FIRST|LAST))?\s*$",
                "",
                part,
                flags=re.IGNORECASE,
            ).strip()

            if token := re.match(
                r"(?:(?P<table>[A-Za-z_][A-Za-z0-9_]*)\.)?(?P<column>[A-Za-z_][A-Za-z0-9_]*)$",
                part_clean,
                re.IGNORECASE,
            ):
                table_name = token.group("table")
                column_name = token.group("column")
                ordered_names.add(column_name.lower())
                if table_name:
                    ordered_names.add(f"{table_name.lower()}.{column_name.lower()}")

        return ordered_names

    def _build_group_by(
        self,
        scope: QueryScope,
        prefix: str,
        statement: str = "",
        cursor_pos: Optional[int] = None,
    ) -> list[CompletionItem]:
        left_statement = statement[:cursor_pos] if cursor_pos is not None else statement
        columns = self._build_where_columns(scope, prefix, statement)
        columns = self._exclude_group_by_existing_columns(columns, left_statement)

        items = list(columns)
        items.extend(self._build_group_by_functions(prefix))
        return items

    def _build_group_by_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            function
            for function in functions
            if function.name not in self._group_by_excluded_functions
        ]

    @staticmethod
    def _exclude_group_by_existing_columns(
        columns: list[CompletionItem], left_statement: str
    ) -> list[CompletionItem]:
        grouped_column_names = SuggestionBuilder._extract_group_by_column_names(
            left_statement
        )
        if not grouped_column_names:
            return columns

        filtered = []
        for column in columns:
            column_name = column.name.lower()
            base_name = (
                column_name.split(".", 1)[1] if "." in column_name else column_name
            )
            if column_name in grouped_column_names or base_name in grouped_column_names:
                continue
            filtered.append(column)
        return filtered

    @staticmethod
    def _extract_group_by_column_names(left_statement: str) -> set[str]:
        if not (
            match := re.search(
                r"\bGROUP\s+BY\s+(?P<clause>.+)$", left_statement, re.IGNORECASE
            )
        ):
            return set()

        clause = match.group("clause")
        if not clause:
            return set()

        grouped_names: set[str] = set()
        for raw_part in clause.split(","):
            part = raw_part.strip()
            if not part:
                continue

            if token := re.match(
                r"(?:(?P<table>[A-Za-z_][A-Za-z0-9_]*)\.)?(?P<column>[A-Za-z_][A-Za-z0-9_]*)$",
                part,
                re.IGNORECASE,
            ):
                table_name = token.group("table")
                column_name = token.group("column")
                grouped_names.add(column_name.lower())
                if table_name:
                    grouped_names.add(f"{table_name.lower()}.{column_name.lower()}")

        return grouped_names

    def _build_having(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        aggregate_funcs = self._build_aggregate_functions(prefix)
        columns = self._build_where_columns(scope, prefix, statement)
        other_funcs = self._build_having_other_functions(prefix)
        return aggregate_funcs + columns + other_funcs

    def _build_having_after_operator(
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        literals = self._build_having_literals(prefix)
        aggregate_funcs = self._build_aggregate_functions(prefix)
        columns = self._build_where_columns(scope, prefix, statement)
        return literals + aggregate_funcs + columns

    @staticmethod
    def _build_having_after_expression(prefix: str) -> list[CompletionItem]:
        keywords = ["AND", "OR", "NOT", "EXISTS", "ORDER BY", "LIMIT"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    @staticmethod
    def _build_window_over(prefix: str) -> list[CompletionItem]:
        keywords = ["ORDER BY", "PARTITION BY"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    @staticmethod
    def _build_after_limit_number(prefix: str) -> list[CompletionItem]:
        keywords = ["OFFSET"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [
                keyword for keyword in keywords if keyword.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=keyword, item_type=CompletionItemType.KEYWORD)
            for keyword in keywords
        ]

    def _build_having_other_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            function
            for function in functions
            if function.name not in self._aggregate_functions
            and function.name not in self._having_excluded_functions
        ]

    @staticmethod
    def _build_having_literals(prefix: str) -> list[CompletionItem]:
        literals = ["NULL", "TRUE", "FALSE"]
        if prefix:
            prefix_upper = prefix.upper()
            literals = [
                literal for literal in literals if literal.startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=literal, item_type=CompletionItemType.KEYWORD)
            for literal in literals
        ]

    def _build_keywords(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []

        try:
            all_keywords = self._database.context.KEYWORDS
            keywords = [
                CompletionItem(
                    name=str(kw).upper(), item_type=CompletionItemType.KEYWORD
                )
                for kw in all_keywords
            ]
        except (AttributeError, TypeError):
            return []

        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.name.startswith(prefix_upper)]

        return sorted(keywords, key=lambda x: x.name)

    def _build_select_keywords(self, prefix: str) -> list[CompletionItem]:
        keywords = ["FROM", "WHERE", "LIMIT", "ORDER BY", "GROUP BY"]

        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.startswith(prefix_upper)]

        return [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in keywords
        ]

    def _build_select_completed_item_keywords(
        self,
        left_statement: str,
        scope: QueryScope,
        prefix: str,
    ) -> list[CompletionItem]:
        import re

        processed_statement = left_statement
        if prefix and left_statement.endswith(prefix):
            processed_statement = left_statement[: -len(prefix)]

        suggestions = []
        wildcard_table_match = re.search(r"(\w+)\.\*\s+$", processed_statement)
        is_wildcard_select_item = bool(
            wildcard_table_match or re.search(r"(?:^|\s)\*\s+$", processed_statement)
        )

        match = re.search(r"(\w+)(?:\.(\w+))?\s+$", processed_statement)
        table_name = None
        if wildcard_table_match:
            table_name = wildcard_table_match.group(1)
        elif match and match.group(2):
            table_name = match.group(1)

        if (
            table_name is None
            and self._current_table
            and not scope.from_tables
            and not scope.join_tables
        ):
            table_name = self._current_table.name

        if table_name:
            suggestions.append(f"FROM {table_name}")

        if is_wildcard_select_item:
            suggestions.append("FROM")
        else:
            suggestions.extend(["AS", "FROM"])

        # Preserve order while removing duplicates.
        suggestions = list(dict.fromkeys(suggestions))

        if prefix:
            prefix_upper = prefix.upper()
            suggestions = [
                item for item in suggestions if item.upper().startswith(prefix_upper)
            ]

        return [
            CompletionItem(name=item, item_type=CompletionItemType.KEYWORD)
            for item in suggestions
        ]

    def _build_select_list_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            item
            for item in functions
            if item.name not in self._select_list_excluded_functions
        ]

    def _build_functions(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []

        try:
            functions = self._database.context.FUNCTIONS
            function_list = [
                CompletionItem(
                    name=str(func).upper(), item_type=CompletionItemType.FUNCTION
                )
                for func in functions
            ]
        except (AttributeError, TypeError):
            return []

        if prefix:
            prefix_upper = prefix.upper()
            function_list = [
                f for f in function_list if f.name.startswith(prefix_upper)
            ]

        return sorted(function_list, key=lambda x: x.name)

    def _build_aggregate_functions(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []

        try:
            functions = self._database.context.FUNCTIONS
            aggregate_list = [
                CompletionItem(
                    name=str(func).upper(), item_type=CompletionItemType.FUNCTION
                )
                for func in functions
                if str(func).upper() in self._aggregate_functions
            ]
        except (AttributeError, TypeError):
            return []

        if prefix:
            prefix_upper = prefix.upper()
            aggregate_list = [
                f for f in aggregate_list if f.name.startswith(prefix_upper)
            ]

        return sorted(aggregate_list, key=lambda x: x.name)

    def _resolve_columns_in_scope(
        self, scope: QueryScope, prefix: str, context: Optional[SQLContext] = None
    ) -> list[CompletionItem]:
        if prefix and self._is_exact_alias_match(prefix, scope):
            return self._get_alias_columns(prefix, scope)

        if prefix:
            return self._resolve_columns_with_prefix(scope, prefix, context)

        return self._resolve_columns_without_prefix(scope, context)

    def _resolve_columns_without_prefix(
        self, scope: QueryScope, context: Optional[SQLContext] = None
    ) -> list[CompletionItem]:
        columns = []

        is_scope_restricted = context and self._is_scope_restricted_context(context)
        has_scope = bool(scope.from_tables or scope.join_tables)

        if context == SQLContext.SELECT_LIST and not has_scope:
            return []

        if context == SQLContext.SELECT_LIST:
            if not has_scope and self._current_table:
                columns.extend(self._get_current_table_columns(scope, None))
            elif (
                has_scope
                and self._current_table
                and self._is_current_table_in_scope(scope)
            ):
                columns.extend(self._get_current_table_columns(scope, None))
        elif not is_scope_restricted and self._current_table:
            columns.extend(self._get_current_table_columns(scope, None))

        columns.extend(self._get_from_table_columns(scope, None))
        columns.extend(self._get_join_table_columns(scope, None))

        include_database_columns = False
        if context == SQLContext.SELECT_LIST:
            include_database_columns = not has_scope
        elif not is_scope_restricted:
            include_database_columns = True

        if include_database_columns and len(columns) < self._max_database_columns:
            columns.extend(self._get_database_columns(scope, None))

        return columns

    def _resolve_columns_with_prefix(
        self, scope: QueryScope, prefix: str, context: Optional[SQLContext] = None
    ) -> list[CompletionItem]:
        seen = set()
        columns = []

        is_scope_restricted = context and self._is_scope_restricted_context(context)
        has_scope = bool(scope.from_tables or scope.join_tables)
        include_database_columns = not is_scope_restricted and not (
            context == SQLContext.SELECT_LIST and has_scope
        )

        include_current_table = True
        if context == SQLContext.SELECT_LIST and has_scope:
            include_current_table = self._is_current_table_in_scope(scope)
        elif is_scope_restricted:
            include_current_table = False

        table_expansion_columns = self._get_table_name_expansion_columns(
            scope,
            prefix,
            include_database_columns,
            include_current_table,
        )
        for col in table_expansion_columns:
            if col.name.lower() not in seen:
                seen.add(col.name.lower())
                columns.append(col)

        column_name_match_columns = self._get_column_name_match_columns(
            scope,
            prefix,
            include_database_columns,
            include_current_table,
            context,
        )
        for col in column_name_match_columns:
            if col.name.lower() not in seen:
                seen.add(col.name.lower())
                columns.append(col)

        return columns

    def _get_table_name_expansion_columns(
        self,
        scope: QueryScope,
        prefix: str,
        include_database_columns: bool,
        include_current_table: bool = True,
    ) -> list[CompletionItem]:
        columns = []
        prefix_lower = prefix.lower()

        if (
            include_current_table
            and self._current_table
            and self._current_table.name.lower().startswith(prefix_lower)
        ):
            qualifier = self._get_table_qualifier(self._current_table.name, scope)
            try:
                for col in self._current_table.columns:
                    if col.name:
                        columns.append(
                            CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=self._current_table.name,
                            )
                        )
            except (AttributeError, TypeError):
                pass

        if self._is_exact_alias_match(prefix, scope):
            columns.extend(self._get_alias_columns(prefix, scope))
            return columns

        for ref in scope.from_tables:
            if not ref.table:
                continue

            if ref.name.lower().startswith(prefix_lower):
                qualifier = ref.name

                try:
                    for col in ref.table.columns:
                        if col.name:
                            columns.append(
                                CompletionItem(
                                    name=f"{qualifier}.{col.name}",
                                    item_type=CompletionItemType.COLUMN,
                                    description=ref.name,
                                )
                            )
                except (AttributeError, TypeError):
                    pass

        for ref in scope.join_tables:
            if not ref.table:
                continue

            if ref.name.lower().startswith(prefix_lower):
                qualifier = ref.name

                try:
                    for col in ref.table.columns:
                        if col.name:
                            columns.append(
                                CompletionItem(
                                    name=f"{qualifier}.{col.name}",
                                    item_type=CompletionItemType.COLUMN,
                                    description=ref.name,
                                )
                            )
                except (AttributeError, TypeError):
                    pass

        if include_database_columns and self._database:
            in_scope_table_names = set()
            if self._current_table:
                in_scope_table_names.add(self._current_table.name.lower())
            for ref in scope.from_tables + scope.join_tables:
                in_scope_table_names.add(ref.name.lower())

            try:
                for table in self._database.tables:
                    if (
                        table.name.lower().startswith(prefix_lower)
                        and table.name.lower() not in in_scope_table_names
                    ):
                        try:
                            for col in table.columns:
                                if col.name:
                                    columns.append(
                                        CompletionItem(
                                            name=f"{table.name}.{col.name}",
                                            item_type=CompletionItemType.COLUMN,
                                            description=table.name,
                                        )
                                    )
                        except (AttributeError, TypeError):
                            pass
            except (AttributeError, TypeError):
                pass

        return columns

    def _get_column_name_match_columns(
        self,
        scope: QueryScope,
        prefix: str,
        include_database_columns: bool,
        include_current_table: bool = True,
        context: Optional[SQLContext] = None,
    ) -> list[CompletionItem]:
        columns = []
        database_columns = []
        prefix_lower = prefix.lower()

        if include_current_table and self._current_table:
            qualifier = self._get_table_qualifier(self._current_table.name, scope)
            try:
                for col in self._current_table.columns:
                    if col.name and col.name.lower().startswith(prefix_lower):
                        columns.append(
                            CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=self._current_table.name,
                            )
                        )
            except (AttributeError, TypeError):
                pass

        for ref in scope.from_tables:
            if ref.table:
                qualifier = ref.alias if ref.alias else ref.name
                try:
                    for col in ref.table.columns:
                        if col.name and col.name.lower().startswith(prefix_lower):
                            columns.append(
                                CompletionItem(
                                    name=f"{qualifier}.{col.name}",
                                    item_type=CompletionItemType.COLUMN,
                                    description=ref.name,
                                )
                            )
                except (AttributeError, TypeError):
                    pass

        for ref in scope.join_tables:
            if ref.table:
                qualifier = ref.alias if ref.alias else ref.name
                try:
                    for col in ref.table.columns:
                        if col.name and col.name.lower().startswith(prefix_lower):
                            columns.append(
                                CompletionItem(
                                    name=f"{qualifier}.{col.name}",
                                    item_type=CompletionItemType.COLUMN,
                                    description=ref.name,
                                )
                            )
                except (AttributeError, TypeError):
                    pass

        if include_database_columns and self._database:
            in_scope_table_names = set()
            if self._current_table:
                in_scope_table_names.add(self._current_table.name.lower())
            for ref in scope.from_tables + scope.join_tables:
                in_scope_table_names.add(ref.name.lower())

            try:
                for table in self._database.tables:
                    if table.name.lower() not in in_scope_table_names:
                        try:
                            for col in table.columns:
                                if col.name and col.name.lower().startswith(
                                    prefix_lower
                                ):
                                    database_columns.append(
                                        CompletionItem(
                                            name=f"{table.name}.{col.name}",
                                            item_type=CompletionItemType.COLUMN,
                                            description=table.name,
                                        )
                                    )
                        except (AttributeError, TypeError):
                            pass
            except (AttributeError, TypeError):
                pass

        if (
            context == SQLContext.SELECT_LIST
            and not scope.from_tables
            and not scope.join_tables
            and database_columns
        ):
            column_names = {
                item.name.split(".", 1)[1].lower()
                for item in database_columns
                if "." in item.name
            }
            if len(column_names) == 1:
                only_name = next(iter(column_names))
                if "_" in only_name:
                    database_columns = []
                else:
                    database_columns = database_columns  # Preserve schema order (do NOT sort alphabetically)

        columns.extend(database_columns)

        return columns

    def _get_out_of_scope_table_hints(
        self, scope: QueryScope, prefix: str, existing_columns: list[CompletionItem]
    ) -> list[CompletionItem]:
        if not self._database or not prefix:
            return []

        prefix_lower = prefix.lower()

        has_scope_table_match = any(
            ref.name.lower().startswith(prefix_lower)
            for ref in scope.from_tables + scope.join_tables
        )
        if has_scope_table_match:
            return []

        in_scope_table_names = {
            ref.name.lower() for ref in scope.from_tables + scope.join_tables
        }

        has_scope_column_match = False
        for col in existing_columns:
            if col.item_type != CompletionItemType.COLUMN:
                continue

            column_name = col.name
            if "." in column_name:
                parts = column_name.split(".", 1)
                if len(parts) == 2:
                    table_part, col_part = parts
                    if (
                        table_part.lower() in in_scope_table_names
                        and col_part.lower().startswith(prefix_lower)
                    ):
                        has_scope_column_match = True
                        break
                continue

            if column_name.lower().startswith(prefix_lower):
                has_scope_column_match = True
                break

        if has_scope_column_match:
            return []

        hints = []
        try:
            for table in self._database.tables:
                if (
                    table.name.lower().startswith(prefix_lower)
                    and table.name.lower() not in in_scope_table_names
                ):
                    hints.append(
                        CompletionItem(
                            name=f"{table.name} (+ Add via FROM/JOIN)",
                            item_type=CompletionItemType.TABLE,
                            description="",
                        )
                    )
        except (AttributeError, TypeError):
            pass

        return hints

    def _is_exact_alias_match(self, prefix: str, scope: QueryScope) -> bool:
        return prefix.lower() in scope.aliases

    def _get_alias_columns(self, alias: str, scope: QueryScope) -> list[CompletionItem]:
        ref = scope.aliases.get(alias.lower())
        if not ref or not ref.table:
            return []

        qualifier = ref.alias if ref.alias else ref.name

        try:
            columns = [
                CompletionItem(
                    name=f"{qualifier}.{col.name}",
                    item_type=CompletionItemType.COLUMN,
                    description=ref.name,
                )
                for col in ref.table.columns
                if col.name
            ]
            return columns
        except (AttributeError, TypeError):
            return []

    def _get_current_table_columns(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        if not self._current_table:
            return []

        qualifier = self._get_table_qualifier(self._current_table.name, scope)

        try:
            columns = [
                CompletionItem(
                    name=f"{qualifier}.{col.name}",
                    item_type=CompletionItemType.COLUMN,
                    description=self._current_table.name,
                )
                for col in self._current_table.columns
                if col.name
            ]
        except (AttributeError, TypeError):
            return []

        if prefix:
            columns = self._filter_columns_by_prefix(columns, prefix)

        return columns

    def _get_from_table_columns(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        columns = []

        for ref in scope.from_tables:
            if not ref.table:
                continue

            qualifier = ref.alias if ref.alias else ref.name

            try:
                table_columns = [
                    CompletionItem(
                        name=f"{qualifier}.{col.name}",
                        item_type=CompletionItemType.COLUMN,
                        description=ref.name,
                    )
                    for col in ref.table.columns
                    if col.name
                ]
                columns.extend(table_columns)
            except (AttributeError, TypeError):
                continue

        if prefix:
            columns = self._filter_columns_by_prefix(columns, prefix)

        return columns

    def _get_join_table_columns(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        columns = []

        for ref in scope.join_tables:
            if not ref.table:
                continue

            qualifier = ref.alias if ref.alias else ref.name

            try:
                table_columns = [
                    CompletionItem(
                        name=f"{qualifier}.{col.name}",
                        item_type=CompletionItemType.COLUMN,
                        description=ref.name,
                    )
                    for col in ref.table.columns
                    if col.name
                ]
                columns.extend(table_columns)
            except (AttributeError, TypeError):
                continue

        if prefix:
            columns = self._filter_columns_by_prefix(columns, prefix)

        return columns

    def _get_database_columns(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        if not self._database:
            return []

        in_scope_table_names = set()
        if self._current_table:
            in_scope_table_names.add(self._current_table.name.lower())

        for ref in scope.from_tables + scope.join_tables:
            in_scope_table_names.add(ref.name.lower())

        columns = []

        try:
            for table in self._database.tables:
                if table.name.lower() in in_scope_table_names:
                    continue

                try:
                    table_columns = [
                        CompletionItem(
                            name=f"{table.name}.{col.name}",
                            item_type=CompletionItemType.COLUMN,
                            description=table.name,
                        )
                        for col in table.columns
                        if col.name
                    ]
                    columns.extend(table_columns)
                except (AttributeError, TypeError):
                    continue
        except (AttributeError, TypeError):
            return []

        if prefix:
            columns = self._filter_columns_by_prefix(columns, prefix)

        return columns

    def _get_table_qualifier(self, table_name: str, scope: QueryScope) -> str:
        table_lower = table_name.lower()

        if table_lower in scope.aliases:
            ref = scope.aliases[table_lower]
            return ref.alias if ref.alias else ref.name

        return table_name

    def _filter_columns_by_prefix(
        self, columns: list[CompletionItem], prefix: str
    ) -> list[CompletionItem]:
        prefix_lower = prefix.lower()
        filtered = []

        for col in columns:
            col_name_lower = col.name.lower()

            if col_name_lower.startswith(prefix_lower):
                filtered.append(col)
            elif "." in col_name_lower:
                parts = col_name_lower.split(".", 1)
                if parts[0].startswith(prefix_lower) or parts[1].startswith(
                    prefix_lower
                ):
                    filtered.append(col)

        return filtered
