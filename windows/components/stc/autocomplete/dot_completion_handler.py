import re

from typing import Optional

from windows.components.stc.autocomplete.completion_types import CompletionItem, CompletionItemType

from structures.engines.database import SQLDatabase, SQLTable


class DotCompletionHandler:
    _token_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    
    def __init__(self, database: Optional[SQLDatabase], scope: Optional[object] = None):
        self._database = database
        self._scope = scope
        self._table_index: dict[str, SQLTable] = {}
        self._build_table_index()
    
    def is_dot_completion(self, text: str, cursor_pos: int) -> bool:
        if cursor_pos < 1:
            return False
        
        left_text = text[:cursor_pos]
        
        if not left_text or left_text[-1] != '.':
            tokens = self._token_pattern.findall(left_text)
            if not tokens:
                return False
            
            last_part = left_text[left_text.rfind(tokens[-1]):]
            return '.' in last_part
        
        return True
    
    def get_completions(self, text: str, cursor_pos: int) -> tuple[Optional[list[CompletionItem]], str]:
        if not self.is_dot_completion(text, cursor_pos):
            return None, ""
        
        left_text = text[:cursor_pos]
        
        tokens = self._token_pattern.findall(left_text)
        if not tokens:
            return None, ""
        
        if left_text.rstrip().endswith('.'):
            table_or_alias = tokens[-1] if tokens else None
            prefix = ""
        else:
            if len(tokens) < 2:
                return None, ""
            
            last_part = left_text[left_text.rfind(tokens[-2]):]
            if '.' not in last_part:
                return None, ""
            
            table_or_alias = tokens[-2]
            prefix = tokens[-1]
        
        if not table_or_alias:
            return None, ""
        
        table = self._find_table(table_or_alias)
        if not table:
            return None, ""
        
        try:
            columns = [
                CompletionItem(
                    name=col.name,
                    item_type=CompletionItemType.COLUMN,
                    description=table.name
                )
                for col in table.columns
                if col.name
            ]
        except (AttributeError, TypeError):
            return None, prefix
        
        if prefix:
            prefix_lower = prefix.lower()
            columns = [c for c in columns if c.name.lower().startswith(prefix_lower)]
        
        return columns, prefix
    
    def _find_table(self, name: str) -> Optional[SQLTable]:
        return self._table_index.get(name.lower())
    
    def _build_table_index(self) -> None:
        self._table_index.clear()
        
        if self._scope:
            try:
                for ref in self._scope.from_tables + self._scope.join_tables:
                    if ref.table:
                        self._table_index[ref.name.lower()] = ref.table
                        if ref.alias:
                            self._table_index[ref.alias.lower()] = ref.table
            except (AttributeError, TypeError):
                pass
        
        if not self._database:
            return
        
        try:
            for table in self._database.tables:
                if table.name.lower() not in self._table_index:
                    self._table_index[table.name.lower()] = table
        except (AttributeError, TypeError):
            pass
    
    def refresh(self, database: Optional[SQLDatabase], scope: Optional[object] = None) -> None:
        self._database = database
        self._scope = scope
        self._build_table_index()
