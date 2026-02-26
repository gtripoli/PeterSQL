from dataclasses import dataclass

from typing import Optional

from structures.engines.database import SQLTable


@dataclass
class TableReference:
    name: str
    alias: Optional[str] = None
    table: Optional[SQLTable] = None


@dataclass
class QueryScope:
    from_tables: list[TableReference]
    join_tables: list[TableReference]
    current_table: Optional[SQLTable]
    aliases: dict[str, TableReference]
    
    @staticmethod
    def empty(current_table: Optional[SQLTable] = None) -> "QueryScope":
        return QueryScope(
            from_tables=[],
            join_tables=[],
            current_table=current_table,
            aliases={}
        )
