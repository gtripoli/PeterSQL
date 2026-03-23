import re

from typing import Optional

from windows.components.stc.autocomplete.completion_types import (
    CompletionItem,
    CompletionItemType,
)
from windows.components.stc.autocomplete.dot_completion_handler import (
    DotCompletionHandler,
)
from windows.components.stc.autocomplete.query_scope import QueryScope, TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase, SQLTable


class SuggestionBuilder:
    _identifier_segment_pattern = r"(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`|\"[^\"]+\"|\[[^\]]+\])"
    _table_name_pattern = (
        _identifier_segment_pattern + r"(?:\." + _identifier_segment_pattern + r")?"
    )
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

    _literal_functions = {
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
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
        if context in (SQLContext.EMPTY, SQLContext.SINGLE_TOKEN):
            return self._build_empty(prefix) if context == SQLContext.EMPTY else self._build_single_token(prefix)

        if context == SQLContext.DOT_COMPLETION:
            return self._build_dot_completion(scope, prefix, statement)

        if context in {
            SQLContext.SELECT_LIST,
            SQLContext.FROM_CLAUSE,
            SQLContext.JOIN_CLAUSE,
            SQLContext.JOIN_AFTER_TABLE,
            SQLContext.JOIN_ON,
            SQLContext.JOIN_ON_AFTER_OPERATOR,
            SQLContext.JOIN_ON_AFTER_EXPRESSION,
            SQLContext.WHERE_CLAUSE,
            SQLContext.WHERE_AFTER_EXPRESSION,
            SQLContext.WHERE_AFTER_OPERATOR,
            SQLContext.ORDER_BY_CLAUSE,
            SQLContext.ORDER_BY_AFTER_COLUMN,
            SQLContext.GROUP_BY_CLAUSE,
            SQLContext.HAVING_CLAUSE,
            SQLContext.HAVING_AFTER_OPERATOR,
            SQLContext.HAVING_AFTER_EXPRESSION,
            SQLContext.WINDOW_OVER,
            SQLContext.LIMIT_OFFSET_CLAUSE,
            SQLContext.AFTER_LIMIT_NUMBER,
            SQLContext.WHERE_STRING_LITERAL,
        }:
            return self._build_select_family_context(
                context=context,
                scope=scope,
                prefix=prefix,
                statement=statement,
                cursor_pos=cursor_pos,
            )

        if context in {
            SQLContext.INSERT_INTO,
            SQLContext.INSERT_COLUMNS,
            SQLContext.INSERT_VALUES,
            SQLContext.INSERT_VALUE_EXPRESSIONS,
            SQLContext.INSERT_COMPLETE,
            SQLContext.INSERT_POST_VALUES,
            SQLContext.INSERT_STRING_LITERAL,
        }:
            return self._build_insert_context(context, scope, prefix, statement)

        if context in {
            SQLContext.UPDATE_TABLE,
            SQLContext.UPDATE_SET_CLAUSE,
            SQLContext.UPDATE_SET_COLUMNS,
            SQLContext.UPDATE_SET_EXPRESSIONS,
            SQLContext.UPDATE_WHERE_CLAUSE,
            SQLContext.UPDATE_WHERE_CONDITIONS,
            SQLContext.UPDATE_WHERE_OPERATORS,
            SQLContext.UPDATE_JOIN_ON,
            SQLContext.UPDATE_STRING_LITERAL,
            SQLContext.UPDATE_WHERE_STRING_LITERAL,
        }:
            return self._build_update_context(context, scope, prefix, statement)

        if context in {
            SQLContext.DELETE_FROM,
            SQLContext.DELETE_WHERE_CLAUSE,
            SQLContext.DELETE_WHERE_CONDITIONS,
            SQLContext.DELETE_WHERE_OPERATORS,
            SQLContext.DELETE_WHERE_EXPRESSIONS,
            SQLContext.DELETE_JOIN_ON,
            SQLContext.DELETE_USING,
            SQLContext.DELETE_SUBQUERY,
            SQLContext.DELETE_WHERE_STRING_LITERAL,
        }:
            return self._build_delete_context(context, scope, prefix, statement)

        return self._build_keywords(prefix)

    def _build_select_family_context(
        self,
        context: SQLContext,
        scope: QueryScope,
        prefix: str,
        statement: str,
        cursor_pos: Optional[int],
    ) -> list[CompletionItem]:
        if context == SQLContext.SELECT_LIST:
            return self._build_select_list(scope, prefix, statement, cursor_pos)
        if context == SQLContext.FROM_CLAUSE:
            return self._build_from_context(scope, prefix, statement)
        if context == SQLContext.JOIN_CLAUSE:
            return self._build_join_clause(prefix, scope, statement)
        if context == SQLContext.JOIN_AFTER_TABLE:
            return self._build_join_after_table(scope)
        if context == SQLContext.JOIN_ON:
            return self._build_join_on(scope, prefix, statement)
        if context == SQLContext.JOIN_ON_AFTER_OPERATOR:
            return self._build_join_on_after_operator(scope, prefix, statement)
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
        if context == SQLContext.AFTER_LIMIT_NUMBER:
            return self._build_after_limit_number(prefix)
        return []

    def _build_insert_context(
        self,
        context: SQLContext,
        scope: QueryScope,
        prefix: str,
        statement: str,
    ) -> list[CompletionItem]:
        if context == SQLContext.INSERT_INTO:
            return self._build_insert_into(prefix)
        if context == SQLContext.INSERT_COLUMNS:
            return self._build_insert_columns(scope, prefix, statement)
        if context == SQLContext.INSERT_VALUES:
            return self._build_insert_values(prefix)
        if context == SQLContext.INSERT_VALUE_EXPRESSIONS:
            return self._build_insert_value_expressions(prefix)
        if context == SQLContext.INSERT_POST_VALUES:
            return self._build_insert_post_values(prefix)
        return []

    def _build_update_context(
        self,
        context: SQLContext,
        scope: QueryScope,
        prefix: str,
        statement: str,
    ) -> list[CompletionItem]:
        if context == SQLContext.UPDATE_TABLE:
            return self._build_update_table(prefix)
        if context == SQLContext.UPDATE_SET_CLAUSE:
            return self._build_update_set_clause(prefix, scope)
        if context == SQLContext.UPDATE_SET_COLUMNS:
            return self._build_update_set_columns(scope, prefix, statement)
        if context == SQLContext.UPDATE_SET_EXPRESSIONS:
            return self._build_insert_value_expressions(prefix)
        if context == SQLContext.UPDATE_WHERE_CLAUSE:
            return self._build_update_where_clause(prefix, scope)
        if context == SQLContext.UPDATE_WHERE_CONDITIONS:
            return self._build_update_where_conditions(scope, prefix, statement)
        if context == SQLContext.UPDATE_WHERE_OPERATORS:
            return self._build_update_where_operators(prefix)
        if context == SQLContext.UPDATE_JOIN_ON:
            return self._build_update_join_on(scope, prefix)
        return []

    def _build_delete_context(
        self,
        context: SQLContext,
        scope: QueryScope,
        prefix: str,
        statement: str,
    ) -> list[CompletionItem]:
        if context == SQLContext.DELETE_FROM:
            return self._build_delete_from(prefix)
        if context == SQLContext.DELETE_WHERE_CLAUSE:
            return self._build_delete_where_clause(prefix, scope, statement)
        if context == SQLContext.DELETE_WHERE_CONDITIONS:
            return self._build_delete_where_conditions(scope, prefix, statement)
        if context == SQLContext.DELETE_WHERE_OPERATORS:
            return self._build_update_where_operators(prefix)
        if context == SQLContext.DELETE_WHERE_EXPRESSIONS:
            return self._build_insert_value_expressions(prefix)
        if context == SQLContext.DELETE_JOIN_ON:
            return self._build_update_join_on(scope, prefix)
        if context == SQLContext.DELETE_USING:
            return self._build_delete_using(scope, prefix, statement)
        if context == SQLContext.DELETE_SUBQUERY:
            return self._build_delete_subquery(prefix)
        return []

    def _build_from_context(
        self,
        scope: QueryScope,
        prefix: str,
        statement: str,
    ) -> list[CompletionItem]:
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
                in_scope_table_names = {ref.name.lower() for ref in scope.from_tables}
                try:
                    tables = [
                        CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                        for table in self._database.tables
                        if table.name.lower() not in in_scope_table_names
                    ]
                    return sorted(tables, key=lambda x: self._table_name_sort_key(x.name))
                except (AttributeError, TypeError):
                    return []
            return self._build_from_followup_keywords(prefix, scope)

        return self._build_from_clause(prefix, statement, scope)

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        normalized = identifier.strip()
        if not normalized:
            return normalized
        if normalized[0] in {'`', '"', '['} and normalized[-1] in {'`', '"', ']'}:
            normalized = normalized[1:-1]
        return normalized

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
        # Moved to DotCompletionHandler - this method now delegates to the centralized handler
        handler = DotCompletionHandler(self._database, scope)
        cursor_pos = len(statement)
        if prefix and statement.endswith(prefix):
            cursor_pos -= len(prefix)
        items, _resolved_prefix = handler.get_completions(statement, cursor_pos)
        if items is None:
            return []
        if prefix:
            prefix_lower = prefix.lower()
            items = [item for item in items if item.name.lower().startswith(prefix_lower)]
        return items

    def _get_table_by_name(self, table_name: str):
        raw_name = table_name.split(".")[-1]
        normalized_name = self._normalize_identifier(raw_name).lower()
        try:
            for table in self._database.tables:
                if table.name.lower() == normalized_name:
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
        wildcard_items = self._build_select_wildcards(scope, prefix, has_scope)

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
                items = list(wildcard_items)
                items.extend(columns)
                items.extend(self._build_select_list_functions(prefix))
                hints = self._get_out_of_scope_table_hints(scope, prefix, columns)
                items.extend(hints)
                return items

            columns = self._resolve_columns_in_scope(
                scope, prefix, SQLContext.SELECT_LIST
            )
            items = list(wildcard_items)
            items.extend(columns)
            items.extend(self._build_select_list_functions(prefix))
            if has_scope:
                hints = self._get_out_of_scope_table_hints(scope, prefix, columns)
                items.extend(hints)
            return items

        if not has_scope:
            items = list(wildcard_items)
            items.extend(self._build_select_list_functions(prefix))
            return items

        items = list(wildcard_items)
        items.extend(
            self._resolve_columns_in_scope(scope, prefix, SQLContext.SELECT_LIST)
        )
        items.extend(self._build_select_list_functions(prefix))
        return items

    @staticmethod
    def _build_select_wildcards(
        scope: QueryScope, prefix: str, has_scope: bool
    ) -> list[CompletionItem]:
        wildcard_items: list[CompletionItem] = []

        if not prefix or "*".startswith(prefix):
            wildcard_items.append(
                CompletionItem(name="*", item_type=CompletionItemType.COLUMN)
            )

        if not has_scope:
            return wildcard_items

        for ref in scope.from_tables + scope.join_tables:
            qualifier = ref.alias if ref.alias else ref.name
            item_name = f"{qualifier}.*"
            if prefix and not item_name.lower().startswith(prefix.lower()):
                continue
            wildcard_items.append(
                CompletionItem(name=item_name, item_type=CompletionItemType.COLUMN)
            )

        # preserve first occurrence order
        deduped: list[CompletionItem] = []
        seen: set[str] = set()
        for item in wildcard_items:
            if item.name in seen:
                continue
            seen.add(item.name)
            deduped.append(item)
        return deduped

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
            wildcards = self._build_select_wildcards(scope, prefix, has_scope)
            columns = self._get_qualified_table_columns_by_name(
                qualifier, prefix, scope
            )
            columns = list(wildcards) + columns
            columns.extend(self._build_select_list_functions(prefix))
            return columns

        if not has_scope and self._current_table:
            wildcards = self._build_select_wildcards(scope, prefix, has_scope)
            columns = list(wildcards)
            columns.extend(self._get_current_table_columns(scope, prefix))
            columns.extend(self._build_select_list_functions(prefix))
            return columns

        if not has_scope:
            items = self._build_select_wildcards(scope, prefix, has_scope)
            items.extend(self._build_select_list_functions(prefix))
            return items

        columns = self._build_select_wildcards(scope, prefix, has_scope)
        columns.extend(self._get_join_table_columns(scope, prefix))
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
        if not scope.from_tables:
            return False

        last_ref = scope.from_tables[-1]
        if not last_ref.table:
            return False

        statement_trimmed = statement.rstrip()
        if not statement_trimmed.endswith(prefix):
            return False

        prefix_lower = prefix.lower()
        last_ref_name = SuggestionBuilder._normalize_identifier(last_ref.name).lower()
        last_ref_base_name = last_ref_name.split(".")[-1]
        matches_completed_table = (
            prefix_lower == last_ref_name
            or prefix_lower == last_ref_base_name
            or (bool(last_ref.alias) and prefix_lower == last_ref.alias.lower())
        )

        if matches_completed_table:
            return True

        return bool(
            re.search(
                r"\bFROM\s+"
                + SuggestionBuilder._table_name_pattern
                + r"(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_]*)?\s+[A-Za-z_][A-Za-z0-9_]*$",
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
        self, prefix: str, scope: QueryScope, statement: str = ""
    ) -> list[CompletionItem]:
        if (
            prefix
            and scope.join_tables
            and self._is_after_completed_join_table_with_prefix(
                statement, prefix, scope
            )
        ):
            return self._build_join_after_table_with_prefix(scope, prefix)

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
    def _build_join_after_table_with_prefix(
        scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        keywords = ["ON", "USING"]
        if not scope.join_tables or not scope.join_tables[-1].alias:
            keywords.insert(0, "AS")

        if prefix:
            prefix_upper = prefix.upper()
            keywords = [kw for kw in keywords if kw.startswith(prefix_upper)]

        return [
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in keywords
        ]

    @staticmethod
    def _is_after_completed_join_table_with_prefix(
        statement: str, prefix: str, scope: QueryScope
    ) -> bool:
        if not statement or not prefix or not scope.join_tables:
            return False

        statement_trimmed = statement.rstrip()
        if not statement_trimmed.endswith(prefix):
            return False

        last_ref = scope.join_tables[-1]
        if not last_ref.table:
            return False

        prefix_lower = prefix.lower()

        last_ref_name = SuggestionBuilder._normalize_identifier(last_ref.name).lower()
        last_ref_base_name = last_ref_name.split(".")[-1]

        if (
            prefix_lower == last_ref_name
            or prefix_lower == last_ref_base_name
            or (bool(last_ref.alias) and prefix_lower == last_ref.alias.lower())
        ):
            return True

        return bool(
            re.search(
                r"\bJOIN\s+"
                + SuggestionBuilder._table_name_pattern
                + r"(?:\s+(?:AS\s+)?[A-Za-z_][A-Za-z0-9_]*)?\s+[A-Za-z_][A-Za-z0-9_]*$",
                statement_trimmed,
                re.IGNORECASE,
            )
        )

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
        fk_hints = self._build_join_fk_hints(scope, prefix)
        items = []
        if prefix:
            columns = self._resolve_columns_in_scope(scope, prefix, SQLContext.JOIN_ON)
        else:
            join_columns = self._get_join_table_columns(scope, None)
            if self._is_after_join_on_keyword(statement):
                join_columns = self._sort_columns_by_name(join_columns)
            from_columns = self._get_from_table_columns(scope, None)
            left_qualifier = self._extract_left_qualifier(statement)
            if left_qualifier and self._qualifier_is_join_side(scope, left_qualifier):
                columns = list(from_columns)
                columns.extend(join_columns)
            else:
                columns = list(join_columns)
                columns.extend(from_columns)

        # Filter out the column on the left side of the operator (same logic as WHERE)
        if not prefix and statement:
            import re

            match = re.search(
                r"(\w+\.?\w*)\s*(?:=|!=|<>|<|>|<=|>=)\s*$", statement, re.IGNORECASE
            )
            if match:
                left_column = match.group(1).strip()
                columns = [c for c in columns if c.name.lower() != left_column.lower()]

        items.extend(fk_hints)
        items.extend(columns)
        if prefix:
            items.extend(self._build_functions(prefix))
        else:
            items.extend(self._build_join_expression_functions(prefix))
        return items

    def _build_join_fk_hints(
        self, scope: QueryScope, prefix: str
    ) -> list[CompletionItem]:
        if not scope.join_tables:
            return []

        current_join = scope.join_tables[-1]
        if not current_join.table:
            return []

        left_refs = scope.from_tables + scope.join_tables[:-1]
        if not left_refs:
            return []

        hints: list[CompletionItem] = []
        seen: set[str] = set()

        for left_ref in left_refs:
            if not left_ref.table:
                continue

            for condition in self._fk_conditions_between(left_ref, current_join):
                if condition in seen:
                    continue
                if prefix and not condition.lower().startswith(prefix.lower()):
                    continue
                hints.append(
                    CompletionItem(
                        name=condition,
                        item_type=CompletionItemType.KEYWORD,
                    )
                )
                seen.add(condition)

        return hints

    def _fk_conditions_between(
        self, left_ref: TableReference, right_ref: TableReference
    ) -> list[str]:
        conditions: list[str] = []

        right_to_left = self._build_fk_conditions_from_ref(
            source_ref=right_ref,
            target_ref=left_ref,
            flip=False,
        )
        conditions.extend(right_to_left)

        left_to_right = self._build_fk_conditions_from_ref(
            source_ref=left_ref,
            target_ref=right_ref,
            flip=True,
        )
        conditions.extend(left_to_right)

        return conditions

    def _build_fk_conditions_from_ref(
        self, source_ref: TableReference, target_ref: TableReference, flip: bool
    ) -> list[str]:
        source_table = source_ref.table
        if not source_table:
            return []

        try:
            foreign_keys = list(source_table.foreign_keys)
        except (AttributeError, TypeError):
            return []

        conditions: list[str] = []
        for foreign_key in foreign_keys:
            if not self._fk_targets_reference(foreign_key, target_ref.name):
                continue

            local_columns = list(getattr(foreign_key, "columns", []) or [])
            reference_columns = list(
                getattr(foreign_key, "reference_columns", []) or []
            )
            if not local_columns or not reference_columns:
                continue

            left_qualifier = target_ref.alias if target_ref.alias else target_ref.name
            right_qualifier = source_ref.alias if source_ref.alias else source_ref.name
            pairs: list[str] = []

            for reference_column, local_column in zip(reference_columns, local_columns):
                if flip:
                    pairs.append(
                        f"{right_qualifier}.{local_column} = {left_qualifier}.{reference_column}"
                    )
                else:
                    pairs.append(
                        f"{left_qualifier}.{reference_column} = {right_qualifier}.{local_column}"
                    )

            if pairs:
                conditions.append(" AND ".join(pairs))

        return conditions

    @staticmethod
    def _fk_targets_reference(foreign_key: object, target_table_name: str) -> bool:
        reference_table = str(getattr(foreign_key, "reference_table", "") or "")
        if not reference_table:
            return False

        target_lower = target_table_name.lower()
        reference_lower = reference_table.lower()
        if reference_lower == target_lower:
            return True

        if "." in reference_lower:
            return reference_lower.split(".")[-1] == target_lower

        return False

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
        self, scope: QueryScope, prefix: str, statement: str = ""
    ) -> list[CompletionItem]:
        columns = self._resolve_columns_in_scope(
            scope, prefix, SQLContext.JOIN_ON_AFTER_OPERATOR
        )

        if not prefix:
            join_columns = self._get_join_table_columns(scope, None)
            from_columns = self._get_from_table_columns(scope, None)

            left_qualifier = self._extract_left_qualifier(statement)
            if left_qualifier and self._qualifier_is_join_side(scope, left_qualifier):
                columns = list(from_columns)
                columns.extend(join_columns)
            else:
                columns = list(join_columns)
                columns.extend(from_columns)

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

    @staticmethod
    def _extract_left_qualifier(statement: str) -> Optional[str]:
        if not statement:
            return None

        match = re.search(
            r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|!=|<>|<=|>=|<|>|LIKE|IN|NOT\s+IN|BETWEEN)\s*$",
            statement,
            re.IGNORECASE,
        )
        if not match:
            return None
        return match.group(1)

    @staticmethod
    def _qualifier_is_join_side(scope: QueryScope, qualifier: str) -> bool:
        q = qualifier.lower()
        for ref in scope.join_tables:
            if ref.alias and ref.alias.lower() == q:
                return True
            if ref.name.lower() == q:
                return True
        return False

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

        if reference.alias or prefer_qualified or "." in reference.name:
            return self._build_qualified_columns_for_reference(reference, prefix)

        if not prefix:
            return self._build_unqualified_table_columns(reference)

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
    def _build_join_literals(prefix: str) -> list[CompletionItem]:
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
            suggestions.extend(
                self._build_from_suggestions_for_qualifier(table_name, scope)
            )

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

    def _build_from_suggestions_for_qualifier(
        self, qualifier: str, scope: QueryScope
    ) -> list[str]:
        qualifier_lower = qualifier.lower()

        if qualifier_lower in scope.aliases:
            ref = scope.aliases[qualifier_lower]
            if ref.alias and ref.alias.lower() != ref.name.lower():
                return [f"FROM {ref.name} {ref.alias}"]
            return [f"FROM {ref.name}"]

        if not self._database:
            return []

        try:
            tables = list(self._database.tables)
        except (AttributeError, TypeError):
            return []

        exact_match = next(
            (table for table in tables if table.name.lower() == qualifier_lower), None
        )
        if exact_match is not None:
            return [f"FROM {exact_match.name}"]

        prefix_matches = [
            table for table in tables if table.name.lower().startswith(qualifier_lower)
        ]
        if not prefix_matches:
            return []

        prefix_matches.sort(key=lambda t: self._table_name_sort_key(t.name))
        return [f"FROM {table.name} {qualifier}" for table in prefix_matches]

    def _build_select_list_functions(self, prefix: str) -> list[CompletionItem]:
        functions = self._build_functions(prefix)
        return [
            item
            for item in functions
            if item.name not in self._select_list_excluded_functions
        ]

    def _build_functions(
        self, prefix: str, exclude: Optional[set[str]] = None
    ) -> list[CompletionItem]:
        if not self._database:
            return []

        try:
            functions = self._database.context.FUNCTIONS
            function_list = [
                CompletionItem(
                    name=str(func).upper(), item_type=CompletionItemType.FUNCTION
                )
                for func in functions
                if not exclude or str(func).upper() not in exclude
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

    # ── INSERT builders ──────────────────────────────────────────────

    def _build_insert_into(self, prefix: str) -> list[CompletionItem]:
        return self._build_all_tables(prefix)

    def _build_insert_columns(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        table = self._find_insert_target_table(statement)
        if not table:
            return []

        already_listed = self._extract_already_listed_columns(statement)
        columns = []
        try:
            for col in table.columns:
                if col.name.lower() not in already_listed:
                    if not prefix or col.name.lower().startswith(prefix.lower()):
                        columns.append(
                            CompletionItem(name=col.name, item_type=CompletionItemType.COLUMN)
                        )
        except (AttributeError, TypeError):
            pass
        return columns

    def _build_insert_values(self, prefix: str) -> list[CompletionItem]:
        keywords = ["VALUES", "SELECT", "DEFAULT"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [k for k in keywords if k.startswith(prefix_upper)]
        return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

    def _build_insert_value_expressions(self, prefix: str) -> list[CompletionItem]:
        items = self._build_where_literals(prefix)
        items.extend(self._build_functions(prefix, exclude=self._literal_functions))
        return items

    def _build_insert_post_values(self, prefix: str) -> list[CompletionItem]:
        keywords = ["ON DUPLICATE KEY UPDATE", "ON CONFLICT", "RETURNING", ";"]
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
        return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

    # ── UPDATE builders ──────────────────────────────────────────────

    def _build_update_table(self, prefix: str) -> list[CompletionItem]:
        return self._build_all_tables(prefix)

    def _build_update_set_clause(self, prefix: str, scope: QueryScope) -> list[CompletionItem]:
        keywords = ["SET"]
        if not scope.join_tables:
            keywords.extend(["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"])
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
        return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

    def _build_update_set_columns(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        table = self._find_update_target_table(statement)
        if not table:
            return []

        already_set = self._extract_already_set_columns(statement)
        columns = []
        try:
            for col in table.columns:
                if col.name.lower() not in already_set:
                    if not prefix or col.name.lower().startswith(prefix.lower()):
                        columns.append(
                            CompletionItem(name=col.name, item_type=CompletionItemType.COLUMN)
                        )
        except (AttributeError, TypeError):
            pass
        return columns

    def _build_update_where_clause(self, prefix: str, scope: QueryScope) -> list[CompletionItem]:
        keywords = ["WHERE"]
        if not scope.join_tables:
            keywords.extend(["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"])
        keywords.extend(["RETURNING", ";"])
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
        return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

    def _build_update_where_conditions(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        table = self._find_update_target_table(statement)

        # After a complete condition: suggest AND/OR/LIMIT/etc
        if self._is_after_where_condition_value(statement):
            keywords = ["AND", "OR", "LIMIT", "ORDER BY", "RETURNING", ";"]
            if prefix:
                prefix_upper = prefix.upper()
                keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
            return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

        # Suggest columns + functions
        columns = self._get_table_columns_as_items(table, prefix)
        items = list(columns)
        items.extend(self._build_where_literals(prefix))
        items.extend(self._build_functions(prefix, exclude=self._literal_functions))
        return items

    def _build_update_where_operators(self, prefix: str) -> list[CompletionItem]:
        operators = [
            "=", "!=", "<>", ">", "<", ">=", "<=",
            "IS", "IS NOT", "IN", "NOT IN", "LIKE", "NOT LIKE",
            "BETWEEN", "NOT BETWEEN", "AND", "OR",
        ]
        if prefix:
            prefix_upper = prefix.upper()
            operators = [op for op in operators if op.upper().startswith(prefix_upper)]
        return [CompletionItem(name=op, item_type=CompletionItemType.KEYWORD) for op in operators]

    def _build_update_join_on(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
        items = self._resolve_columns_in_scope(scope, prefix, SQLContext.JOIN_ON)
        items.extend(self._build_join_literals(prefix))
        items.extend(self._build_functions(prefix, exclude=self._literal_functions))
        return items

    # ── DELETE builders ──────────────────────────────────────────────

    def _build_delete_from(self, prefix: str) -> list[CompletionItem]:
        return self._build_all_tables(prefix)

    def _build_delete_where_clause(
        self, prefix: str, scope: QueryScope, statement: str
    ) -> list[CompletionItem]:
        keywords = ["WHERE"]
        if not scope.join_tables:
            keywords.extend(["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"])
            keywords.append("USING")
        keywords.extend(["RETURNING", ";"])
        if prefix:
            prefix_upper = prefix.upper()
            keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
        return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

    def _build_delete_where_conditions(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        table = self._find_delete_target_table(statement)

        if self._is_after_where_condition_value(statement):
            keywords = ["AND", "OR", "LIMIT", "ORDER BY", "RETURNING", ";"]
            if prefix:
                prefix_upper = prefix.upper()
                keywords = [k for k in keywords if k.upper().startswith(prefix_upper)]
            return [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]

        columns = self._get_table_columns_as_items(table, prefix)
        items = list(columns)
        items.extend(self._build_where_literals(prefix))
        items.extend(self._build_functions(prefix, exclude=self._literal_functions))
        return items

    def _build_delete_using(
        self, scope: QueryScope, prefix: str, statement: str
    ) -> list[CompletionItem]:
        delete_table = self._find_delete_target_table(statement)
        exclude = {delete_table.name.lower()} if delete_table else set()
        return self._build_all_tables(prefix, exclude=exclude)

    def _build_delete_subquery(self, prefix: str) -> list[CompletionItem]:
        keywords = ["SELECT", "WITH"]
        items = [CompletionItem(name=k, item_type=CompletionItemType.KEYWORD) for k in keywords]
        items.extend(self._build_where_literals(prefix))
        items.extend(self._build_functions(prefix, exclude=self._literal_functions))
        if prefix:
            prefix_upper = prefix.upper()
            items = [item for item in items if item.name.upper().startswith(prefix_upper)]
        return items

    # ── Shared helpers ───────────────────────────────────────────────

    def _build_all_tables(
        self, prefix: str, exclude: Optional[set[str]] = None
    ) -> list[CompletionItem]:
        if not self._database:
            return []
        try:
            tables = []
            for table in self._database.tables:
                if exclude and table.name.lower() in exclude:
                    continue
                if not prefix or table.name.lower().startswith(prefix.lower()):
                    tables.append(
                        CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                    )
            return sorted(tables, key=lambda x: self._table_name_sort_key(x.name))
        except (AttributeError, TypeError):
            return []

    def _find_insert_target_table(self, statement: str) -> Optional[SQLTable]:
        match = re.search(
            r"\bINSERT\s+INTO\s+(" + self._table_name_pattern + r")",
            statement,
            re.IGNORECASE,
        )
        if match:
            return self._get_table_by_name(match.group(1))
        return None

    def _find_update_target_table(self, statement: str) -> Optional[SQLTable]:
        match = re.search(
            r"\bUPDATE\s+(" + self._table_name_pattern + r")",
            statement,
            re.IGNORECASE,
        )
        if match:
            return self._get_table_by_name(match.group(1))
        return None

    def _find_delete_target_table(self, statement: str) -> Optional[SQLTable]:
        match = re.search(
            r"\bFROM\s+(" + self._table_name_pattern + r")",
            statement,
            re.IGNORECASE,
        )
        if match:
            return self._get_table_by_name(match.group(1))
        return None

    def _get_table_columns_as_items(
        self, table: Optional[SQLTable], prefix: str
    ) -> list[CompletionItem]:
        if not table:
            return []
        try:
            columns = []
            for col in table.columns:
                if not prefix or col.name.lower().startswith(prefix.lower()):
                    columns.append(
                        CompletionItem(name=col.name, item_type=CompletionItemType.COLUMN)
                    )
            return columns
        except (AttributeError, TypeError):
            return []

    @staticmethod
    def _extract_already_listed_columns(statement: str) -> set[str]:
        match = re.search(r"\(\s*(.+?)(?:\)|$)", statement, re.IGNORECASE)
        if not match:
            return set()
        column_list = match.group(1)
        return {col.strip().lower() for col in column_list.split(",") if col.strip()}

    @staticmethod
    def _extract_already_set_columns(statement: str) -> set[str]:
        set_match = re.search(r"\bSET\s+(.*)", statement, re.IGNORECASE | re.DOTALL)
        if not set_match:
            return set()
        set_clause = set_match.group(1)
        columns = set()
        for assignment in set_clause.split(","):
            eq_match = re.match(r"\s*(\w+)\s*=", assignment)
            if eq_match:
                columns.add(eq_match.group(1).lower())
        return columns

    def _is_after_where_condition_value(self, statement: str) -> bool:
        where_match = re.search(r"\bWHERE\s+(.*)", statement, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return False
        clause = where_match.group(1).strip()
        if not clause:
            return False
        return bool(re.search(
            r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*\s*"
            r"(?:=|!=|<>|<=|>=|<|>|LIKE|IN|BETWEEN)\s*"
            r"(?:[A-Za-z_][A-Za-z0-9_]*|\d+|'[^']*'|\"[^\"]*\"|NULL|TRUE|FALSE|\w+\([^)]*\))\s*$",
            clause,
            re.IGNORECASE,
        ))
