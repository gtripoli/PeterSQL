from typing import Optional

from windows.components.stc.autocomplete.completion_types import CompletionItem, CompletionItemType
from windows.components.stc.autocomplete.query_scope import QueryScope, TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase, SQLTable


class SuggestionBuilder:
    _primary_keywords = {
        "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", 
        "TRUNCATE", "SHOW", "DESCRIBE", "EXPLAIN", "WITH", "REPLACE", "MERGE"
    }
    
    _aggregate_functions = {
        "COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP_CONCAT"
    }

    _select_list_excluded_functions = {
        "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP"
    }
    
    _max_database_columns = 400
    
    _scope_restricted_contexts = {
        SQLContext.WHERE_CLAUSE,
        SQLContext.JOIN_ON,
        SQLContext.ORDER_BY_CLAUSE,
        SQLContext.GROUP_BY_CLAUSE,
        SQLContext.HAVING_CLAUSE
    }
    
    def __init__(self, database: Optional[SQLDatabase], current_table: Optional[SQLTable]):
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
        
        if context == SQLContext.SELECT_LIST:
            return self._build_select_list(scope, prefix, statement, cursor_pos)
        
        if context == SQLContext.FROM_CLAUSE:
            import re
            statement_upper = statement.upper()
            
            if re.search(r'\bAS\s+$', statement_upper):
                return []
            
            if prefix and re.search(r'\bAS\s+\w+$', statement_upper):
                return []
            
            if not prefix and scope.from_tables:
                if ',' in statement:
                    in_scope_table_names = {ref.name.lower() for ref in scope.from_tables}
                    try:
                        tables = [
                            CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                            for table in self._database.tables
                            if table.name.lower() not in in_scope_table_names
                        ]
                        return sorted(tables, key=lambda x: x.name.lower())
                    except (AttributeError, TypeError):
                        return []
                else:
                    keywords = ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN", "WHERE", "GROUP BY", "ORDER BY", "LIMIT"]
                    
                    has_alias = any(ref.alias for ref in scope.from_tables)
                    if not has_alias:
                        keywords.insert(5, "AS")
                    
                    return [CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD) for kw in keywords]
            
            return self._build_from_clause(prefix, statement)
        
        if context == SQLContext.JOIN_CLAUSE:
            if not prefix and scope.join_tables:
                if statement.rstrip().endswith(scope.join_tables[-1].name):
                    keywords = ["AS", "ON", "USING"]
                    return [CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD) for kw in keywords]
            return self._build_join_clause(prefix, scope)
        
        if context == SQLContext.JOIN_ON:
            return self._build_join_on(scope, prefix, statement)
        
        if context == SQLContext.WHERE_CLAUSE:
            return self._build_where_clause(scope, prefix, statement)
        
        if context == SQLContext.ORDER_BY_CLAUSE:
            return self._build_order_by(scope, prefix)
        
        if context == SQLContext.GROUP_BY_CLAUSE:
            return self._build_group_by(scope, prefix)
        
        if context == SQLContext.HAVING_CLAUSE:
            return self._build_having(scope, prefix)
        
        if context == SQLContext.LIMIT_OFFSET_CLAUSE:
            return []
        
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
    
    def _build_single_token(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []
        
        try:
            all_keywords = self._database.context.KEYWORDS
            keywords = [
                CompletionItem(name=str(kw).upper(), item_type=CompletionItemType.KEYWORD)
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

        if self._is_after_completed_select_item(left_statement) or self._is_after_completed_select_item_with_prefix(
                left_statement,
                prefix,
        ):
            return self._build_select_completed_item_keywords(left_statement, scope, prefix)

        if self._is_after_select_comma_context(left_statement, prefix):
            return self._build_select_list_after_comma(scope, prefix, left_statement, has_scope)

        if prefix:
            columns = self._resolve_columns_in_scope(scope, prefix, SQLContext.SELECT_LIST)
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
    def _is_after_completed_select_item(statement: str) -> bool:
        import re

        if not re.search(r"\bSELECT\b", statement, re.IGNORECASE):
            return False
        if re.search(r",\s+$", statement):
            return False

        match = re.search(r"(\w+(?:\.\w+)?)\s+$", statement)
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
    def _is_after_completed_select_item_with_prefix(statement: str, prefix: str) -> bool:
        import re

        if not prefix:
            return False
        if not statement.endswith(prefix):
            return False
        if not re.search(r"\bSELECT\b", statement, re.IGNORECASE):
            return False
        if re.search(r",\s*\w+$", statement):
            return False

        completed_item_match = re.search(r"(\w+(?:\.\w+)?)\s+\w+$", statement)
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
            columns = self._get_qualified_table_columns_by_name(qualifier, prefix, scope)
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
        items = sorted(columns, key=lambda item: item.name.lower())
        items.extend(self._build_select_list_functions(prefix))
        return items

    @staticmethod
    def _get_previous_select_item_qualifier(statement: str) -> Optional[str]:
        import re

        select_match = re.search(r"\bSELECT\b(.*)$", statement, re.IGNORECASE | re.DOTALL)
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
                    (candidate for candidate in self._database.tables if candidate.name.lower() == qualifier.lower()),
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
    
    def _build_from_clause(self, prefix: str, statement: str = "") -> list[CompletionItem]:
        if not self._database:
            return []
        
        try:
            tables = [
                CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                for table in self._database.tables
            ]
        except (AttributeError, TypeError):
            return []
        
        # Extract tables referenced in SELECT list (e.g., SELECT users.id FROM | → prioritize users)
        # This applies ALWAYS, with or without prefix
        referenced_tables = set()
        if statement:
            import re
            # Find qualified columns in SELECT: table.column
            # Match both "FROM " (with space) and "FROM" (at end of statement)
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM\s*', statement, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_list = select_match.group(1)
                # Extract table names from qualified columns
                qualified_refs = re.findall(r'\b(\w+)\.\w+', select_list)
                referenced_tables = {ref.lower() for ref in qualified_refs}
        
        # Filter by prefix if present
        if prefix:
            prefix_lower = prefix.lower()
            tables = [t for t in tables if t.name.lower().startswith(prefix_lower)]
        
        # Sort: referenced tables first, then alphabetically
        # This ensures SELECT users.id FROM | shows users first
        def sort_key(table):
            is_referenced = table.name.lower() in referenced_tables
            return (not is_referenced, table.name.lower())
        
        return sorted(tables, key=sort_key)
    
    def _build_join_clause(self, prefix: str, scope: QueryScope) -> list[CompletionItem]:
        if not self._database:
            return []
        
        in_scope_table_names = {ref.name.lower() for ref in scope.from_tables + scope.join_tables}
        
        try:
            tables = [
                CompletionItem(name=table.name, item_type=CompletionItemType.TABLE)
                for table in self._database.tables
                if table.name.lower() not in in_scope_table_names
            ]
        except (AttributeError, TypeError):
            return []
        
        if prefix:
            prefix_lower = prefix.lower()
            tables = [t for t in tables if t.name.lower().startswith(prefix_lower)]
        
        return sorted(tables, key=lambda x: x.name.lower())
    
    def _build_join_on(self, scope: QueryScope, prefix: str, statement: str = "") -> list[CompletionItem]:
        items = []
        columns = self._resolve_columns_in_scope(scope, prefix, SQLContext.JOIN_ON)
        
        # Filter out the column on the left side of the operator (same logic as WHERE)
        if not prefix and statement:
            import re
            match = re.search(r'(\w+\.?\w*)\s*(?:=|!=|<>|<|>|<=|>=)\s*$', statement, re.IGNORECASE)
            if match:
                left_column = match.group(1).strip()
                columns = [c for c in columns if c.name.lower() != left_column.lower()]
        
        items.extend(columns)
        items.extend(self._build_functions(prefix))
        return items
    
    def _build_where_clause(self, scope: QueryScope, prefix: str, statement: str = "") -> list[CompletionItem]:
        items = []
        
        columns = self._resolve_columns_in_scope(scope, prefix, SQLContext.WHERE_CLAUSE)
        
        # Filter out the column on the left side of the operator
        # e.g., "WHERE users.id = |" should NOT suggest users.id
        if not prefix and statement:
            import re
            # Match: column_name (qualified or not) followed by operator and whitespace
            # Operators: =, !=, <>, <, >, <=, >=, LIKE, IN, etc.
            match = re.search(r'(\w+\.?\w*)\s*(?:=|!=|<>|<|>|<=|>=|LIKE|IN|NOT\s+IN)\s*$', statement, re.IGNORECASE)
            if match:
                left_column = match.group(1).strip()
                # Remove the left column from suggestions
                columns = [c for c in columns if c.name.lower() != left_column.lower()]
        
        functions = self._build_functions(prefix)
        
        items.extend(columns)
        items.extend(functions)
        
        return items
    
    def _build_order_by(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
        items = []
        items.extend(self._resolve_columns_in_scope(scope, prefix, SQLContext.ORDER_BY_CLAUSE))
        items.extend(self._build_functions(prefix))
        
        order_keywords = ["ASC", "DESC", "NULLS FIRST", "NULLS LAST"]
        if prefix:
            prefix_upper = prefix.upper()
            order_keywords = [kw for kw in order_keywords if kw.startswith(prefix_upper)]
        
        items.extend([
            CompletionItem(name=kw, item_type=CompletionItemType.KEYWORD)
            for kw in order_keywords
        ])
        
        return items
    
    def _build_group_by(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
        items = []
        items.extend(self._resolve_columns_in_scope(scope, prefix, SQLContext.GROUP_BY_CLAUSE))
        items.extend(self._build_functions(prefix))
        return items
    
    def _build_having(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
        items = []
        
        aggregate_funcs = self._build_aggregate_functions(prefix)
        items.extend(aggregate_funcs)
        
        items.extend(self._resolve_columns_in_scope(scope, prefix, SQLContext.HAVING_CLAUSE))
        
        other_funcs = [f for f in self._build_functions(prefix) if f.name not in self._aggregate_functions]
        items.extend(other_funcs)
        
        return items
    
    def _build_keywords(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []
        
        try:
            all_keywords = self._database.context.KEYWORDS
            keywords = [
                CompletionItem(name=str(kw).upper(), item_type=CompletionItemType.KEYWORD)
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
            processed_statement = left_statement[:-len(prefix)]

        suggestions = []
        match = re.search(r"(\w+)(?:\.(\w+))?\s+$", processed_statement)
        table_name = match.group(1) if match and match.group(2) else None

        if table_name is None and self._current_table and not scope.from_tables and not scope.join_tables:
            table_name = self._current_table.name

        if table_name:
            suggestions.append(f"FROM {table_name}")

        suggestions.extend(["AS", "FROM"])

        if prefix:
            prefix_upper = prefix.upper()
            suggestions = [item for item in suggestions if item.upper().startswith(prefix_upper)]

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
                CompletionItem(name=str(func).upper(), item_type=CompletionItemType.FUNCTION)
                for func in functions
            ]
        except (AttributeError, TypeError):
            return []
        
        if prefix:
            prefix_upper = prefix.upper()
            function_list = [f for f in function_list if f.name.startswith(prefix_upper)]
        
        return sorted(function_list, key=lambda x: x.name)
    
    def _build_aggregate_functions(self, prefix: str) -> list[CompletionItem]:
        if not self._database:
            return []
        
        try:
            functions = self._database.context.FUNCTIONS
            aggregate_list = [
                CompletionItem(name=str(func).upper(), item_type=CompletionItemType.FUNCTION)
                for func in functions
                if str(func).upper() in self._aggregate_functions
            ]
        except (AttributeError, TypeError):
            return []
        
        if prefix:
            prefix_upper = prefix.upper()
            aggregate_list = [f for f in aggregate_list if f.name.startswith(prefix_upper)]
        
        return sorted(aggregate_list, key=lambda x: x.name)
    
    def _resolve_columns_in_scope(self, scope: QueryScope, prefix: str, context: Optional[SQLContext] = None) -> list[CompletionItem]:
        if prefix and self._is_exact_alias_match(prefix, scope):
            return self._get_alias_columns(prefix, scope)
        
        if prefix:
            return self._resolve_columns_with_prefix(scope, prefix, context)
        
        return self._resolve_columns_without_prefix(scope, context)
    
    def _resolve_columns_without_prefix(self, scope: QueryScope, context: Optional[SQLContext] = None) -> list[CompletionItem]:
        columns = []
        
        is_scope_restricted = context and self._is_scope_restricted_context(context)
        has_scope = bool(scope.from_tables or scope.join_tables)

        if context == SQLContext.SELECT_LIST and not has_scope:
            return []
        
        if context == SQLContext.SELECT_LIST:
            if not has_scope and self._current_table:
                columns.extend(self._get_current_table_columns(scope, None))
            elif has_scope and self._current_table and self._is_current_table_in_scope(scope):
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
    
    def _resolve_columns_with_prefix(self, scope: QueryScope, prefix: str, context: Optional[SQLContext] = None) -> list[CompletionItem]:
        seen = set()
        columns = []
        
        is_scope_restricted = context and self._is_scope_restricted_context(context)
        has_scope = bool(scope.from_tables or scope.join_tables)
        include_database_columns = not is_scope_restricted and not (context == SQLContext.SELECT_LIST and has_scope)
        
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
        
        if include_current_table and self._current_table and self._current_table.name.lower().startswith(prefix_lower):
            qualifier = self._get_table_qualifier(self._current_table.name, scope)
            try:
                for col in self._current_table.columns:
                    if col.name:
                        columns.append(CompletionItem(
                            name=f"{qualifier}.{col.name}",
                            item_type=CompletionItemType.COLUMN,
                            description=self._current_table.name
                        ))
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
                            columns.append(CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=ref.name
                            ))
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
                            columns.append(CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=ref.name
                            ))
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
                    if table.name.lower().startswith(prefix_lower) and table.name.lower() not in in_scope_table_names:
                        try:
                            for col in table.columns:
                                if col.name:
                                    columns.append(CompletionItem(
                                        name=f"{table.name}.{col.name}",
                                        item_type=CompletionItemType.COLUMN,
                                        description=table.name
                                    ))
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
                        columns.append(CompletionItem(
                            name=f"{qualifier}.{col.name}",
                            item_type=CompletionItemType.COLUMN,
                            description=self._current_table.name
                        ))
            except (AttributeError, TypeError):
                pass
        
        for ref in scope.from_tables:
            if ref.table:
                qualifier = ref.alias if ref.alias else ref.name
                try:
                    for col in ref.table.columns:
                        if col.name and col.name.lower().startswith(prefix_lower):
                            columns.append(CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=ref.name
                            ))
                except (AttributeError, TypeError):
                    pass
        
        for ref in scope.join_tables:
            if ref.table:
                qualifier = ref.alias if ref.alias else ref.name
                try:
                    for col in ref.table.columns:
                        if col.name and col.name.lower().startswith(prefix_lower):
                            columns.append(CompletionItem(
                                name=f"{qualifier}.{col.name}",
                                item_type=CompletionItemType.COLUMN,
                                description=ref.name
                            ))
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
                                if col.name and col.name.lower().startswith(prefix_lower):
                                    database_columns.append(CompletionItem(
                                        name=f"{table.name}.{col.name}",
                                        item_type=CompletionItemType.COLUMN,
                                        description=table.name
                                    ))
                        except (AttributeError, TypeError):
                            pass
            except (AttributeError, TypeError):
                pass

        if context == SQLContext.SELECT_LIST and not scope.from_tables and not scope.join_tables and database_columns:
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
                    database_columns = sorted(database_columns, key=lambda item: item.name.lower())

        columns.extend(database_columns)
        
        return columns
    
    def _get_out_of_scope_table_hints(self, scope: QueryScope, prefix: str, existing_columns: list[CompletionItem]) -> list[CompletionItem]:
        if not self._database or not prefix:
            return []
        
        prefix_lower = prefix.lower()
        
        has_scope_table_match = any(
            ref.name.lower().startswith(prefix_lower) 
            for ref in scope.from_tables + scope.join_tables
        )
        if has_scope_table_match:
            return []
        
        in_scope_table_names = {ref.name.lower() for ref in scope.from_tables + scope.join_tables}
        
        has_scope_column_match = False
        for col in existing_columns:
            if col.item_type == CompletionItemType.COLUMN and '.' in col.name:
                parts = col.name.split('.')
                if len(parts) == 2:
                    table_part, col_part = parts
                    if table_part.lower() in in_scope_table_names and col_part.lower().startswith(prefix_lower):
                        has_scope_column_match = True
                        break
        
        if has_scope_column_match:
            return []
        
        hints = []
        try:
            for table in self._database.tables:
                if (table.name.lower().startswith(prefix_lower) and 
                    table.name.lower() not in in_scope_table_names):
                    hints.append(CompletionItem(
                        name=f"{table.name} (+ Add via FROM/JOIN)",
                        item_type=CompletionItemType.TABLE,
                        description=""
                    ))
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
                    description=ref.name
                )
                for col in ref.table.columns
                if col.name
            ]
            return columns
        except (AttributeError, TypeError):
            return []
    
    def _get_current_table_columns(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
        if not self._current_table:
            return []
        
        qualifier = self._get_table_qualifier(self._current_table.name, scope)
        
        try:
            columns = [
                CompletionItem(
                    name=f"{qualifier}.{col.name}",
                    item_type=CompletionItemType.COLUMN,
                    description=self._current_table.name
                )
                for col in self._current_table.columns
                if col.name
            ]
        except (AttributeError, TypeError):
            return []
        
        if prefix:
            columns = self._filter_columns_by_prefix(columns, prefix)
        
        return columns
    
    def _get_from_table_columns(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
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
                        description=ref.name
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
    
    def _get_join_table_columns(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
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
                        description=ref.name
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
    
    def _get_database_columns(self, scope: QueryScope, prefix: str) -> list[CompletionItem]:
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
                            description=table.name
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
    
    def _filter_columns_by_prefix(self, columns: list[CompletionItem], prefix: str) -> list[CompletionItem]:
        prefix_lower = prefix.lower()
        filtered = []
        
        for col in columns:
            col_name_lower = col.name.lower()
            
            if col_name_lower.startswith(prefix_lower):
                filtered.append(col)
            elif "." in col_name_lower:
                parts = col_name_lower.split(".", 1)
                if parts[0].startswith(prefix_lower) or parts[1].startswith(prefix_lower):
                    filtered.append(col)
        
        return filtered
