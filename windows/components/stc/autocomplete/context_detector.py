import re

from typing import Optional

import sqlglot

from helpers.logger import logger

from windows.components.stc.autocomplete.query_scope import QueryScope, TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext

from structures.engines.database import SQLDatabase


class ContextDetector:
    _prefix_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
    
    def __init__(self, dialect: Optional[str] = None):
        self._dialect = dialect
    
    def detect(self, text: str, cursor_pos: int, database: Optional[SQLDatabase]) -> tuple[SQLContext, QueryScope, str]:
        left_text = text[:cursor_pos]
        left_text_stripped = left_text.strip()
        
        if not left_text_stripped:
            return SQLContext.EMPTY, QueryScope.empty(), ""
        
        if " " not in left_text and "\n" not in left_text:
            return SQLContext.SINGLE_TOKEN, QueryScope.empty(), left_text_stripped
        
        prefix = self._extract_prefix(text, cursor_pos)
        
        try:
            context = self._detect_context_with_regex(left_text_stripped)
            scope = self._extract_scope_from_text(text, database)
            return context, scope, prefix
        except Exception as ex:
            logger.debug(f"context detection error: {ex}")
            return SQLContext.UNKNOWN, QueryScope.empty(), prefix
    
    def _extract_prefix(self, text: str, cursor_pos: int) -> str:
        if cursor_pos == 0:
            return ""
        
        left_text = text[:cursor_pos]
        
        if left_text and left_text[-1] in (' ', '\t', '\n'):
            return ""
        
        match = self._prefix_pattern.search(left_text)
        if match is None:
            return ""
        return match.group(0)
    
    def _detect_context_with_regex(self, left_text: str) -> SQLContext:
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
            return SQLContext.LIMIT_OFFSET_CLAUSE
        
        if having_pos > select_pos and having_pos != -1:
            if having_pos > max(group_by_pos, order_by_pos, -1):
                return SQLContext.HAVING_CLAUSE
        
        if group_by_pos > select_pos and group_by_pos != -1:
            if group_by_pos > max(where_pos, order_by_pos, having_pos, -1):
                return SQLContext.GROUP_BY_CLAUSE
        
        if order_by_pos > select_pos and order_by_pos != -1:
            if order_by_pos > max(where_pos, group_by_pos, having_pos, -1):
                return SQLContext.ORDER_BY_CLAUSE
        
        if on_pos > select_pos and on_pos != -1:
            if on_pos > max(join_pos, from_pos, where_pos, -1):
                return SQLContext.JOIN_ON
        
        if join_pos > select_pos and join_pos != -1:
            if join_pos > max(from_pos, where_pos, -1):
                return SQLContext.JOIN_CLAUSE
        
        if where_pos > select_pos and where_pos != -1:
            if where_pos > max(from_pos, order_by_pos, group_by_pos, -1):
                return SQLContext.WHERE_CLAUSE
        
        if from_pos > select_pos and from_pos != -1:
            if from_pos > max(where_pos, join_pos, order_by_pos, group_by_pos, -1):
                return SQLContext.FROM_CLAUSE
        
        return SQLContext.SELECT_LIST
    
    def _extract_scope_from_select(self, parsed: sqlglot.exp.Select, database: Optional[SQLDatabase]) -> QueryScope:
        from_tables = []
        join_tables = []
        aliases = {}
        
        if from_clause := parsed.args.get("from"):
            if isinstance(from_clause, sqlglot.exp.From):
                for table_exp in from_clause.find_all(sqlglot.exp.Table):
                    table_name = table_exp.name
                    alias = table_exp.alias if hasattr(table_exp, 'alias') and table_exp.alias else None
                    
                    table_obj = self._find_table_in_database(table_name, database) if database else None
                    ref = TableReference(name=table_name, alias=alias, table=table_obj)
                    from_tables.append(ref)
                    
                    if alias:
                        aliases[alias.lower()] = ref
                    aliases[table_name.lower()] = ref
        
        for join_exp in parsed.find_all(sqlglot.exp.Join):
            if table_exp := join_exp.this:
                if isinstance(table_exp, sqlglot.exp.Table):
                    table_name = table_exp.name
                    alias = table_exp.alias if hasattr(table_exp, 'alias') and table_exp.alias else None
                    
                    table_obj = self._find_table_in_database(table_name, database) if database else None
                    ref = TableReference(name=table_name, alias=alias, table=table_obj)
                    join_tables.append(ref)
                    
                    if alias:
                        aliases[alias.lower()] = ref
                    aliases[table_name.lower()] = ref
        
        return QueryScope(
            from_tables=from_tables,
            join_tables=join_tables,
            current_table=None,
            aliases=aliases
        )
    
    def _extract_scope_from_text(self, text: str, database: Optional[SQLDatabase]) -> QueryScope:
        sql_keywords = {
            'WHERE', 'ORDER', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 
            'INTERSECT', 'EXCEPT', 'ON', 'USING', 'AND', 'OR', 'NOT', 'IN', 
            'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'ASC', 'DESC',
            'AS', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'OUTER'
        }
        
        from_pattern = re.compile(r'\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s*(?:,|\bJOIN\b|\bWHERE\b|\bORDER\b|\bGROUP\b|\bLIMIT\b|$)', re.IGNORECASE)
        join_pattern = re.compile(r'\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*))?\s*(?:\bON\b|\bUSING\b|$)', re.IGNORECASE)
        
        from_tables = []
        join_tables = []
        aliases = {}
        
        for match in from_pattern.finditer(text):
            table_name = match.group(1)
            alias = match.group(2) if match.group(2) else None
            
            if table_name.upper() in sql_keywords:
                continue
            if alias and alias.upper() in sql_keywords:
                alias = None
            
            table_obj = self._find_table_in_database(table_name, database) if database else None
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
            
            table_obj = self._find_table_in_database(table_name, database) if database else None
            ref = TableReference(name=table_name, alias=alias, table=table_obj)
            join_tables.append(ref)
            
            if alias:
                aliases[alias.lower()] = ref
            aliases[table_name.lower()] = ref
        
        return QueryScope(
            from_tables=from_tables,
            join_tables=join_tables,
            current_table=None,
            aliases=aliases
        )
    
    def _find_table_in_database(self, table_name: str, database: SQLDatabase) -> Optional:
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
        return "ORDER BY" not in after_where and "GROUP BY" not in after_where and "LIMIT" not in after_where
    
    def _is_after_from(self, text: str) -> bool:
        upper = text.upper()
        from_pos = upper.rfind("FROM")
        if from_pos == -1:
            return False
        
        after_from = upper[from_pos + 4:].strip()
        return len(after_from) == 0 or (len(after_from) > 0 and after_from[-1] in [' ', '\n', '\t'])
    
    def _is_after_on(self, text: str) -> bool:
        upper = text.upper()
        on_pos = upper.rfind(" ON ")
        if on_pos == -1:
            return False
        
        after_on = upper[on_pos + 4:].strip()
        return len(after_on) == 0 or (len(after_on) > 0 and not after_on.endswith(('WHERE', 'ORDER', 'GROUP', 'LIMIT')))
    
    def _is_after_order_by(self, text: str) -> bool:
        upper = text.upper()
        order_by_pos = upper.rfind("ORDER BY")
        if order_by_pos == -1:
            return False
        
        after_order_by = upper[order_by_pos + 8:].strip()
        return "LIMIT" not in after_order_by
    
    def _is_after_group_by(self, text: str) -> bool:
        upper = text.upper()
        group_by_pos = upper.rfind("GROUP BY")
        if group_by_pos == -1:
            return False
        
        after_group_by = upper[group_by_pos + 8:].strip()
        return "HAVING" not in after_group_by and "ORDER BY" not in after_group_by and "LIMIT" not in after_group_by
    
    def _is_in_having(self, text: str) -> bool:
        upper = text.upper()
        having_pos = upper.rfind("HAVING")
        if having_pos == -1:
            return False
        
        after_having = upper[having_pos:]
        return "ORDER BY" not in after_having and "LIMIT" not in after_having
