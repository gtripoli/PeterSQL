import io
import re
import abc

from typing import List, Dict, Iterator, Optional

import sqlalchemy as sa

import alembic
import alembic.migration
import alembic.operations
import alembic.autogenerate

from helpers.logger import logger
from models.database import Database, Table, Column

from helpers.observables import Observable

LOG_QUERY: Observable[str] = Observable()


class AbstractStatement(abc.ABC):
    _engine = None
    _connection = None
    _inspector = None
    _metadata: Dict[str, sa.MetaData] = {}

    def __init__(self, connection_url):
        self.connection_url = connection_url

    def create_engine(self, **engine_kwargs) -> sa.Engine:
        return sa.create_engine(
            self.connection_url,
            echo=True,
            echo_pool=True,
            **engine_kwargs
        )

    def connect(self, **engine_kwargs) -> None:
        if self._engine is None:
            self._engine = self.create_engine(**engine_kwargs)

            sa.event.listen(self._engine, "connect", self._on_connect)
            sa.event.listen(self._engine, "close", self._on_disconnect)

        if self._connection is None:
            self._connection = self._engine.connect()
            self._inspector = sa.inspect(self._engine)

    def disconnect(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

        self._inspector = None

    @property
    def engine(self) -> sa.Engine:
        if self._engine is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._engine

    @property
    def connection(self) -> sa.Connection:
        if self._connection is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._connection

    @property
    def inspector(self) -> sa.Inspector:
        if self._connection is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._inspector

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _on_connect(self, *args, **kwargs):
        print("CONNECTED", args, kwargs)

    def _on_disconnect(self, *args, **kwargs):
        print("DISCONNECTED", args, kwargs)

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_databases(self) -> Iterator[Database]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tables(self, database: str) -> Iterator[Table]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_columns(self, database: str, table: str) -> Iterator[Column]:
        raise NotImplementedError

    def execute(self, query: str, **kwargs) -> sa.CursorResult:
        query = re.sub(r'\s+', ' ', str(query)).strip()

        LOG_QUERY.set_value(query)

        try:
            q = self.connection.execute(sa.text(query), **kwargs)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            LOG_QUERY.set_value(str(ex))

        else:
            return q

    # def get_tables(self, schema: str) -> List[sa.Table]:
    #     tables = []
    #
    #     if (metadata := self._metadata.get(schema)) is None:
    #         metadata = sa.MetaData(schema=schema)
    #         metadata.reflect(bind=self.engine, schema=schema)
    #
    #         self._metadata[schema] = metadata
    #
    #     table_names = self.inspector.get_table_names(schema=schema)
    #
    #     for table_name in table_names:
    #         table = sa.Table(table_name, metadata, autoload_with=self.engine.execution_options(
    #             schema_translate_map={None: schema}
    #         ), schema=schema)
    #         tables.append(table)
    #
    #     return tables

    # def _filter_operations(self, operations, table_name: str):
    #     _operations = []
    #     stack = operations
    #     while stack:
    #         elem = stack.pop(0)
    #
    #         if isinstance(elem, alembic.operations.ops.ModifyTableOps) and elem.table_name == table_name:
    #             _operations.extend(elem.ops)
    #         elif hasattr(elem, "ops"):
    #             stack.extend(elem.ops)
    #
    #     return _operations

    # def render_sql_from_diff(self, metadata, schema: str, table_name: str | None = None, ) -> str:
    #     buf = io.StringIO()
    #
    #     with self.connection.execution_options(schema_translate_map={None: schema}) as connection:
    #         connection.dialect.default_schema_name = schema
    #         connection.execute(sa.text(f"USE {schema}"))
    #
    #         mc_read = alembic.migration.MigrationContext.configure(
    #             connection=connection,
    #             opts={
    #                 "as_sql": False,
    #                 "target_metadata": metadata,
    #             },
    #         )
    #         migrations = alembic.autogenerate.produce_migrations(mc_read, metadata)
    #
    #         mc_write = alembic.migration.MigrationContext.configure(
    #             connection=connection,
    #             opts={
    #                 "as_sql": True,
    #                 "target_metadata": metadata,
    #                 "output_buffer": buf
    #             },
    #         )
    #
    #         ops = alembic.operations.Operations(mc_write)
    #
    #         for op in self._filter_operations(migrations.upgrade_ops.ops, table_name):
    #             ops.invoke(op)
    #
    #     return buf.getvalue()

    # def _clone_table(self, table: sa.Table, metadata: sa.MetaData, extend_existing: bool = True) -> sa.Table:
    #     new_cols = []
    #     for col in list(table.columns):
    #         copied = sa.Column(
    #             col.name,
    #             col.type,
    #             *col.foreign_keys,  # mantiene le FK
    #             primary_key=col.primary_key,
    #             nullable=col.nullable,
    #             unique=col.unique,
    #             index=col.index,
    #             autoincrement=col.autoincrement,
    #         )
    #
    #         if col.server_default is not None:
    #             if hasattr(col.server_default, "arg"):
    #                 try:
    #                     copied.server_default = col.server_default.arg.text
    #                 except Exception as ex:
    #                     logger.warning(ex)
    #             else:
    #                 copied.server_default = col.server_default
    #
    #         new_cols.append(copied)
    #
    #     new_table = sa.Table(
    #         table.name,
    #         metadata,
    #         *new_cols,
    #         extend_existing=extend_existing
    #     )
    #
    #     # Copiamo i vincoli (eccetto PK che è gestita nelle colonne)
    #     for constraint in table.constraints:
    #         if constraint.__class__.__name__ == "PrimaryKeyConstraint":
    #             continue
    #         new_table.append_constraint(constraint.copy(new_table))
    #
    #     for idx in list(table.indexes):
    #         sa.Index(idx.name, *[new_table.c[col.name] for col in idx.columns], unique=idx.unique)
    #
    #     return new_table
    #
    # def update_table(self, database: Database, table: sa.Table) -> bool:
    #     metadata = self._metadata[database.name]
    #
    #     new_table = self._clone_table(table, metadata)
    #
    #     d = self.render_sql_from_diff(metadata, schema=database.name, table_name=table.name)
    #     print(d)
