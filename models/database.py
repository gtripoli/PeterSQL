import datetime
import dataclasses

from typing import Optional, Callable, List, Type

import wx
import sqlalchemy

from helpers.lazylist import LazyList
from models.structures import SQLDataType


@dataclasses.dataclass
class Column:
    id: Optional[int]
    name: str
    datatype: Type[SQLDataType]
    is_nullable: bool
    extra: Optional[str] = None
    key: Optional[str] = None
    charset: Optional[str] = None
    collation: Optional[str] = None
    comment: Optional[str] = None

    is_unsigned: Optional[bool] = False
    is_zerofill: Optional[bool] = False
    is_generated: Optional[bool] = False
    generation_expression: Optional[str] = None
    default: Optional[str] = ""

    set: Optional[List[str]] = None
    length: Optional[int] = None
    scale: Optional[int] = None

    def is_valid(self):
        return all([self.name, self.datatype])

    def to_sa_column(self):
        sa_col_args = []
        sa_col_kwargs = {}
        if self.datatype.has_set:
            sa_col_args.append(self.set)
        elif self.datatype.has_length:
            sa_col_args.append(self.length)
            if self.datatype.has_scale:
                sa_col_args.append(self.scale)

        if self.is_unsigned:
            sa_col_kwargs['unsigned'] = True

        if self.is_zerofill:
            sa_col_kwargs['zerofill'] = True

        return sqlalchemy.Column(
            self.name,
            self.datatype.sa_column(*sa_col_args, **sa_col_kwargs),
            # primary_key=self.primary_key,
            # autoincrement=self.auto_increment,
            nullable=self.is_nullable,
            default=self.default
        )


@dataclasses.dataclass
class Table:
    name: str

    engine: Optional[str]
    collation: Optional[str]

    comment: Optional[str] = None
    count_rows: Optional[int] = None
    columns: List[Column] = dataclasses.field(default_factory=list)

    auto_increment: Optional[int] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    control: Optional[wx.Control] = None

    def is_valid(self) -> bool:
        return all([self.name != "", len(self.columns) > 0, all([c.is_valid for c in self.columns])])

    def to_sa_table(self):
        columns = [c.to_sa_column() for c in self.columns]

        sa_table = sqlalchemy.Table(
            self.name,
            sqlalchemy.MetaData(),
            *columns
        )

        return sa_table


@dataclasses.dataclass
class Database:
    id: Optional[int]
    name: str

    get_tables: Callable[..., List[Table]]

    control: Optional[wx.Control] = None

    def __post_init__(self):
        self.tables = LazyList(lambda: self.get_tables(self.name))
