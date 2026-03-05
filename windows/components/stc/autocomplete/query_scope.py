from dataclasses import dataclass, field

from typing import Optional

from structures.engines.database import SQLTable


@dataclass
class VirtualColumn:
    name: str


@dataclass
class VirtualTable:
    name: str
    columns: list[VirtualColumn]


@dataclass
class TableReference:
    name: str
    alias: Optional[str] = None
    table: Optional[SQLTable | VirtualTable] = None


@dataclass
class QueryScope:
    from_tables: list[TableReference]
    join_tables: list[TableReference]
    current_table: Optional[SQLTable]
    aliases: dict[str, TableReference]
    cte_tables: list[TableReference] = field(default_factory=list)

    @staticmethod
    def empty(current_table: Optional[SQLTable] = None) -> "QueryScope":
        return QueryScope(
            from_tables=[],
            join_tables=[],
            current_table=current_table,
            aliases={},
            cte_tables=[],
        )
