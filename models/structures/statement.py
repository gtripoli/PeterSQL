import io
import re
import abc

from typing import List, Dict, Iterator

from sqlalchemy import MetaData, Table, create_engine, inspect, text, event

import alembic
import alembic.migration
import alembic.operations
import alembic.autogenerate

from models.database import Database

from helpers.observables import Observable

LOG_QUERY: Observable[str] = Observable()


class AbstractStatement(abc.ABC):
    _engine = None
    _connection = None
    _inspector = None
    _metadata: Dict[str, MetaData] = {}

    def __init__(self, connection_url):
        self.connection_url = connection_url

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.connection_url, echo=True, echo_pool=True)

        event.listen(self._engine, "connect", self._on_disconnect)
        event.listen(self._engine, "close", self._on_disconnect)

        return self._engine

    @property
    def connection(self):
        if self._connection is None:
            self._connection = self.engine.connect()

        return self._connection

    @property
    def inspector(self):
        if self._inspector is None:
            self._inspector = inspect(self.engine)

        return self._inspector

    def _on_connected(self, *args, **kwargs):
        print("CONNECTED", args, kwargs)

    def _on_disconnect(self, *args, **kwargs):
        print("DISCONNECTED", args, kwargs)
        self._connection = None

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_databases(self) -> Iterator[Database]:
        raise NotImplementedError

    def connect(self):
        engine = create_engine(self.connection_url)
        engine.connect()

    def execute(self, query: str, **kwargs):
        query = re.sub(r'\s+', ' ', str(query)).strip()

        LOG_QUERY.set_value(query)

        try:
            q = self.connection.execute(query, **kwargs)
        except Exception as ex:
            LOG_QUERY.set_value(str(ex))

        else:
            return q

    def get_tables(self, schema: str) -> List[Table]:
        tables = []

        if (metadata := self._metadata.get(schema)) is None:
            metadata = MetaData(schema=schema)
            metadata.reflect(bind=self.engine, schema=schema)

            self._metadata[schema] = metadata

        table_names = self.inspector.get_table_names(schema=schema)

        for table_name in table_names:
            table = Table(table_name, metadata, autoload_with=self.engine.execution_options(
                schema_translate_map={None: schema}
            ), schema=schema)
            tables.append(table)

        return tables

    def _filter_operations(self, operations, table_name: str):
        _operations = []
        stack = operations
        while stack:
            elem = stack.pop(0)

            if isinstance(elem, alembic.operations.ops.ModifyTableOps) and elem.table_name == table_name:
                _operations.extend(elem.ops)
            elif hasattr(elem, "ops"):
                stack.extend(elem.ops)

        return _operations

    def render_sql_from_diff(self, metadata, schema: str, table_name: str | None = None, ) -> str:
        buf = io.StringIO()

        with self.connection.execution_options(schema_translate_map={None: schema}) as connection:
            connection.dialect.default_schema_name = schema
            connection.execute(text(f"USE {schema}"))

            mc_read = alembic.migration.MigrationContext.configure(
                connection=connection,
                opts={
                    "as_sql": False,
                    "target_metadata": metadata,
                },
            )
            migrations = alembic.autogenerate.produce_migrations(mc_read, metadata)

            mc_write = alembic.migration.MigrationContext.configure(
                connection=connection,
                opts={
                    "as_sql": True,
                    "target_metadata": metadata,
                    "output_buffer": buf
                },
            )

            ops = alembic.operations.Operations(mc_write)

            for op in self._filter_operations(migrations.upgrade_ops.ops, table_name):
                ops.invoke(op)

        return buf.getvalue()

    def update_table(self, database: Database, table: Table) -> bool:
        metadata = self._metadata[database.name]

        Table(
            table.name,
            metadata,
            *[c.copy() for c in list(table.columns)],
            extend_existing=True
        )

        d = self.render_sql_from_diff(metadata, schema=database.name, table_name=table.name)
        print(d)

        # connection = self.connection.execution_options(schema_translate_map={None: database.name})
        # connection.dialect.default_schema_name = database.name
        # connection.execute(text(f"USE {database.name}"))
        #
        # buf = io.StringIO()
        # context = alembic.migration.MigrationContext.configure(connection=connection, opts={
        #     "target_metadata": metadata,
        #     "script": None,
        #     "as_sql": True,
        #     "output_buffer": buf,  # dove scrivere l'SQL
        # })
        #
        # # difference = alembic.autogenerate.compare_metadata(context, metadata)
        #
        # migrations = alembic.autogenerate.produce_migrations(context, metadata)
        #
        # operations = alembic.operations.Operations(context)
        #
        # # impl = context.impl

    # for op in self._filter_operations(migrations.upgrade_ops, table.name):
    #         operations.invoke(op)
    #         # for sql in op.to_diff_tuple() :
    #         #     print(sql)

    # stack = [migrations.upgrade_ops]
    # while stack:
    #     elem = stack.pop(0)
    #
    #     if isinstance(elem, alembic.operations.ops.ModifyTableOps):
    #         with operations.batch_alter_table(
    #                 elem.table_name, schema=elem.schema
    #         ) as batch_ops:
    #             for table_elem in elem.ops:
    #                 batch_ops.invoke(table_elem)
    #
    #     elif hasattr(elem, "ops"):
    #         stack.extend(elem.ops)
    #     else:
    #         operations.invoke(elem)

    # buf = []
    # alembic.autogenerate.render_python_code(op, )
    # render._produce_migration_diffs(context, difference, buf.append)
    # print("\n".join(buf))

    # for action, operation in difference:
    #     # action, change = change[0], change[1]
    #
    #     if operation.name != table.name:
    #         continue
    #
    #     function = getattr(op, action)
    #
    #     try :
    #         function(operation)
    #     except Exception as ex:
    #         logger.error(ex, exc_info=True)
    #         raise
    #     else :
    #         logger.info(f"{action} : {change.name} ")

    #
    # if action == "add_column":
    #     _schema, table_name, column = change[1], change[2], change[3]
    #     print(f"[+] Adding column {column.name} to {table_name}")
    #     op.add_column(table_name, column)
    #
    # elif action == "remove_column":
    #     _schema, table_name, column = change[1], change[2], change[3]
    #     print(f"[-] Dropping column {column.name} from {table_name}")
    #     op.drop_column(table_name, column.name)
    #
    # elif action == "add_table":
    #     table = change[1]
    #     print(f"[+] Creating table {table.name}")
    #     op.create_table(table)
    #
    # elif action == "remove_table":
    #     table = change[1]
    #     print(f"[-] Dropping table {table.name}")
    #     op.drop_table(table.name)
    #
    # elif action == "add_index":
    #     index = change[1]
    #     print(f"[+] Creating index {index.name} on {index.table.name}")
    #     op.create_index(index.name, index.table.name, [c.name for c in index.columns])
    #
    # elif action == "remove_index":
    #     index = change[1]
    #     print(f"[-] Dropping index {index.name}")
    #     op.drop_index(index.name, table_name=index.table.name)
    #
    # elif action == "add_constraint":
    #     constraint = change[1]
    #     print(f"[+] Adding constraint {constraint.name} on {constraint.table.name}")
    #     op.create_unique_constraint(constraint.name, constraint.table.name, [c.name for c in constraint.columns])
    #
    # elif action == "remove_constraint":
    #     constraint = change[1]
    #     print(f"[-] Dropping constraint {constraint.name}")
    #     op.drop_constraint(constraint.name, constraint.table.name, type_=constraint.__visit_name__)
    #
    # else:
    #     print(f"[?] Unsupported action: {change}")

    # def create_column(self, table: Table, column: Column) -> bool:
    #     columns = [c.to_sa_column() for c in table.columns]
    #
    #     sa_table = sqlalchemy.Table(
    #         table.name,
    #         sqlalchemy.MetaData(),
    #         *columns
    #     )
    #
    #     self.execute(str(sqlalchemy.schema.AddColumn(sa_table).compile(dialect=self.dialect.dialect())))
    #
    # def drop_table(self, table: Table) -> bool:
    #     columns = [c.to_sa_column() for c in table.columns]
    #
    #     sa_table = sqlalchemy.Table(
    #         table.name,
    #         sqlalchemy.MetaData(),
    #         *columns
    #     )
    #
    #     self.execute(str(sqlalchemy.schema.DropTable(sa_table).compile(dialect=self.dialect.dialect())))
    #
    # def select_table(self, table: Table, limit: int = 1000, offset: Optional[int] = None) -> List:
    #     statement = sqlalchemy.select(table.to_sa_table())
    #
    #     if limit is not None:
    #         statement = statement.limit(limit)
    #
    #     if offset is not None:
    #         statement = statement.offset(offset)
    #
    #     self.execute(str(statement.compile(dialect=self.dialect.dialect(), compile_kwargs={"literal_binds": True})))

    # return self.cursor.fetchall()

    # @abc.abstractmethod
    # def get_databases(self) -> List[Database]:
    #     raise NotImplementedError
    #
    # @abc.abstractmethod
    # def get_tables(self, database: str) -> List[Table]:
    #     raise NotImplementedError
    #
    # @abc.abstractmethod
    # def get_columns(self, database: str, table: str) -> List[Column]:
    #     raise NotImplementedError
    #
    # @abc.abstractmethod
    # def generate_column_definition(self, column: Column) -> str:
    #     raise NotImplementedError

# class SQLiteStatement(AbstractStatement):
#
#     def get_databases(self) -> List[Database]:
#         databases = []
#         self.cursor.execute("SHOW DATABASES;")
#
#         for index, database in enumerate(self.cursor.fetchall()):
#             databases.append(Database(id=index, name=database['Database']))
#
#         return databases
#
#     def get_tables(self) -> List[Database]:
#         databases = []
#         self.cursor.execute(".tables;")
#
#         for index, table in enumerate(self.cursor.fetchall()):
#             databases.append(Database(id=index, name=table['Database']))
#
#         return databases
