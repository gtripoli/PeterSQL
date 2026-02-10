import psycopg2
import psycopg2.extras

from typing import Any, Optional
from gettext import gettext as _

from helpers.logger import logger
from structures.connection import Connection

from structures.engines.context import QUERY_LOGS, AbstractContext
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLTrigger
from structures.engines.datatype import SQLDataType, DataTypeCategory, DataTypeFormat

from structures.engines.postgresql import MAP_COLUMN_FIELDS
from structures.engines.postgresql.database import PostgreSQLTable, PostgreSQLColumn, PostgreSQLIndex, PostgreSQLForeignKey, PostgreSQLRecord, PostgreSQLView, PostgreSQLTrigger, PostgreSQLDatabase
from structures.engines.postgresql.datatype import PostgreSQLDataType
from structures.engines.postgresql.indextype import PostgreSQLIndexType


class PostgreSQLContext(AbstractContext):
    MAP_COLUMN_FIELDS = MAP_COLUMN_FIELDS

    DATATYPE = PostgreSQLDataType
    INDEXTYPE = PostgreSQLIndexType

    IDENTIFIER_QUOTE = '"'

    def __init__(self, connection: Connection):
        super().__init__(connection)

        self.host = connection.configuration.hostname
        self.user = connection.configuration.username
        self.password = connection.configuration.password
        self.port = getattr(connection.configuration, 'port', 5432)
        self._current_database: Optional[str] = None

    def _on_connect(self, *args, **kwargs):
        super()._on_connect(*args, **kwargs)

        self.execute("SELECT collname FROM pg_collation;")
        self.COLLATIONS = {row['collname']: row['collname'] for row in self.fetchall()}

        self.execute("""
            SELECT word FROM pg_get_keywords()
            WHERE catcode = 'R'
            ORDER BY word;
        """)
        self.KEYWORDS = tuple(row["word"] for row in self.fetchall())

        self.execute("""
            SELECT routine_name FROM information_schema.routines
            WHERE routine_type = 'FUNCTION'
            ORDER BY routine_name;
        """)
        self.FUNCTIONS = tuple(row["routine_name"] for row in self.fetchall())

        self._load_custom_types()

    def _load_custom_types(self) -> None:
        """Load user-defined enum types from the database."""
        self.execute("""
            SELECT t.typname, t.typtype
            FROM pg_type t
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            AND t.typtype = 'e'
            ORDER BY t.typname
        """)

        for row in self.fetchall():
            self.execute(f"""
                SELECT enumlabel
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = '{row['typname']}'
                ORDER BY e.enumsortorder
            """)
            labels = [r['enumlabel'] for r in self.fetchall()]
            datatype = SQLDataType(
                name=row['typname'],
                category=DataTypeCategory.CUSTOM,
                has_set=True,
                set=labels,
                format=DataTypeFormat.STRING
            )
            setattr(PostgreSQLDataType, row['typname'].upper(), datatype)

    def connect(self, **connect_kwargs) -> None:
        if self._connection is None:
            try:
                database = connect_kwargs.pop('database', 'postgres')
                self._connection = psycopg2.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=database,
                    port=self.port,
                    **connect_kwargs
                )
                self._cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                self._current_database = database
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
                raise
            else:
                self._on_connect()

    def _set_database(self, db_name: str) -> None:
        """Switch to a different database by reconnecting."""
        if self._current_database != db_name:
            self.disconnect()
            self.connect(database=db_name)

    def get_server_version(self) -> str:
        self.execute("SELECT version() as version")
        version = self.fetchone()
        return version["version"]

    def get_server_uptime(self) -> Optional[int]:
        self.execute("SELECT extract(epoch from now() - pg_postmaster_start_time()) as uptime;")
        result = self.fetchone()
        return int(result['uptime']) if result else None

    def get_databases(self) -> list[SQLDatabase]:
        self.execute("""
            SELECT datname as database_name, pg_database_size(datname) as total_bytes
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        results = []
        for i, row in enumerate(self.fetchall()):
            results.append(PostgreSQLDatabase(
                id=i,
                name=row["database_name"],
                context=self,
                total_bytes=float(row["total_bytes"]),
                get_tables_handler=self.get_tables,
                get_views_handler=self.get_views,
                get_triggers_handler=self.get_triggers,
            ))
        return results

    def get_views(self, database: SQLDatabase) -> list[PostgreSQLView]:
        self._set_database(database.name)
        results = []
        self.execute(f"SELECT schemaname, viewname, definition FROM pg_views WHERE schemaname NOT IN ('information_schema', 'pg_catalog') ORDER BY schemaname, viewname")
        for i, result in enumerate(self.fetchall()):
            results.append(PostgreSQLView(
                id=i,
                name=f"{result['schemaname']}.{result['viewname']}",
                database=database,
                sql=result['definition']
            ))

        return results

    def get_triggers(self, database: SQLDatabase) -> list[PostgreSQLTrigger]:
        self._set_database(database.name)
        results = []
        self.execute(f"SELECT n.nspname as schemaname, tgname, pg_get_triggerdef(t.oid) as sql FROM pg_trigger t JOIN pg_class c ON t.tgrelid = c.oid JOIN pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname NOT IN ('information_schema', 'pg_catalog') ORDER BY n.nspname, tgname")
        for i, result in enumerate(self.fetchall()):
            results.append(PostgreSQLTrigger(
                id=i,
                name=f"{result['schemaname']}.{result['tgname']}",
                database=database,
                sql=result['sql']
            ))

        return results

    def get_tables(self, database: SQLDatabase) -> list[SQLTable]:
        self._set_database(database.name)
        QUERY_LOGS.append(f"/* get_tables for database={database.name} */")

        self.execute(f"""
            SELECT t.schemaname, t.tablename, pg_total_relation_size(quote_ident(t.schemaname) || '.' || quote_ident(t.tablename)) as total_bytes, c.reltuples as total_rows
            FROM pg_tables t
            JOIN pg_class c ON c.relname = t.tablename AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = t.schemaname)
            WHERE t.schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY t.schemaname, t.tablename
        """)

        results = []
        for i, row in enumerate(self.fetchall()):
            results.append(
                PostgreSQLTable(
                    id=i,
                    name=row['tablename'],
                    schema=row['schemaname'],
                    database=database,
                    total_bytes=float(row['total_bytes']),
                    total_rows=row['total_rows'],
                    get_columns_handler=self.get_columns,
                    get_indexes_handler=self.get_indexes,
                    get_foreign_keys_handler=self.get_foreign_keys,
                    get_records_handler=self.get_records,
                )
            )

        return results

    def get_columns(self, table: SQLTable) -> list[SQLColumn]:
        results = []
        if table.id == -1:
            return results

        QUERY_LOGS.append(f"/* get_columns for table={table.name} */")

        self.execute(f"""
            SELECT column_name, data_type, character_maximum_length, numeric_precision, numeric_scale,
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = '{table.schema}' AND table_name = '{table.name}'
            ORDER BY ordinal_position
        """)

        for i, row in enumerate(self.cursor.fetchall()):
            is_nullable = row['is_nullable'] == 'YES'
            datatype = PostgreSQLDataType.get_by_name(row['data_type'])

            results.append(
                PostgreSQLColumn(
                    id=i,
                    name=row['column_name'],
                    datatype=datatype,
                    is_nullable=is_nullable,
                    table=table,
                    server_default=row['column_default'],
                    length=row['character_maximum_length'],
                    numeric_precision=row['numeric_precision'],
                    numeric_scale=row['numeric_scale'],
                )
            )

        return results

    def get_indexes(self, table: SQLTable) -> list[SQLIndex]:
        if table is None or table.is_new:
            return []

        QUERY_LOGS.append(f"/* get_indexes for table={table.name} */")

        results: list[SQLIndex] = []
        index_data: dict[str, dict[str, Any]] = {}

        # Get primary key
        self.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{table.schema}' AND TABLE_NAME = '{table.name}' AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """)
        pk_columns = [row['COLUMN_NAME'] for row in self.fetchall()]
        if pk_columns:
            results.append(
                PostgreSQLIndex(
                    id=0,
                    name="PRIMARY KEY",
                    type=PostgreSQLIndexType.PRIMARY,
                    columns=pk_columns,
                    table=table,
                )
            )

        # Get other indexes
        self.execute(f"""
            SELECT idx.relname AS index_name,
                   ind.indisunique AS is_unique,
                   array_agg(att.attname ORDER BY keys.ordinality) AS columns
            FROM pg_index ind
            JOIN pg_class tbl ON tbl.oid = ind.indrelid
            JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
            JOIN pg_class idx ON idx.oid = ind.indexrelid
            JOIN LATERAL unnest(ind.indkey) WITH ORDINALITY AS keys(attnum, ordinality) ON TRUE
            JOIN pg_attribute att ON att.attrelid = tbl.oid AND att.attnum = keys.attnum
            WHERE ns.nspname = '{table.schema}' AND tbl.relname = '{table.name}' AND NOT ind.indisprimary
            GROUP BY idx.relname, ind.indisunique
        """)
        for row in self.fetchall():
            index_data[row['index_name']] = {
                'columns': list(row['columns']) if row['columns'] else [],
                'unique': bool(row['is_unique'])
            }

        for i, (idx_name, data) in enumerate(index_data.items(), start=1):
            idx_type = PostgreSQLIndexType.UNIQUE if data['unique'] else PostgreSQLIndexType.INDEX
            results.append(
                PostgreSQLIndex(
                    id=i,
                    name=idx_name,
                    type=idx_type,
                    columns=data['columns'],
                    table=table,
                )
            )

        return results

    def get_foreign_keys(self, table: SQLTable) -> list[SQLForeignKey]:
        if table is None or table.is_new:
            return []

        self._set_database(table.database.name)

        logger.debug(f"get_foreign_keys for table={table.name}")

        QUERY_LOGS.append(f"/* get_foreign_keys for table={table.name} */")

        self.execute(f"""
            SELECT
                con.conname AS constraint_name,
                array_agg(att.attname ORDER BY ord.ordinality) AS columns,
                n2.nspname AS referenced_schema,
                rel2.relname AS referenced_table,
                array_agg(att2.attname ORDER BY ord.ordinality) AS referenced_columns,
                con.confupdtype AS on_update,
                con.confdeltype AS on_delete
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = rel.relnamespace
            JOIN pg_class rel2 ON rel2.oid = con.confrelid
            JOIN pg_namespace n2 ON n2.oid = rel2.relnamespace
            JOIN unnest(con.conkey) WITH ORDINALITY AS ord(attnum, ordinality) ON TRUE
            JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ord.attnum
            JOIN pg_attribute att2
                ON att2.attrelid = rel2.oid
               AND att2.attnum = con.confkey[ord.ordinality]
            WHERE con.contype = 'f'
              AND n.nspname = '{table.schema}'
              AND rel.relname = '{table.name}'
            GROUP BY
                con.conname,
                n2.nspname,
                rel2.relname,
                con.confupdtype,
                con.confdeltype
            ORDER BY con.conname
        """)
        foreign_keys = []
        _rule_map = {
            'a': 'NO ACTION',
            'r': 'RESTRICT',
            'c': 'CASCADE',
            'n': 'SET NULL',
            'd': 'SET DEFAULT',
        }

        for i, row in enumerate(self.fetchall()):
            foreign_keys.append(PostgreSQLForeignKey(
                id=i,
                name=row['constraint_name'],
                columns=list(row['columns']),
                table=table,
                reference_table=f"{row['referenced_schema']}.{row['referenced_table']}",
                reference_columns=list(row['referenced_columns']),
                on_update=_rule_map.get(row['on_update'], 'NO ACTION'),
                on_delete=_rule_map.get(row['on_delete'], 'NO ACTION'),
            ))

        return foreign_keys

    def get_records(self, table: SQLTable, /, *, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None) -> list[PostgreSQLRecord]:
        logger.debug(f"get records for table={table.name}")
        QUERY_LOGS.append(f"/* get_records for table={table.name} */")
        if table is None or table.is_new:
            return []

        order = ""
        where = ""
        if filters:
            where = f"WHERE {filters}"

        if orders:
            order = f"ORDER BY {orders}"

        query = [f"SELECT *",
                 f'FROM "{table.schema}"."{table.name}"',
                 f"{where}",
                 f"{order}",
                 f"LIMIT {limit} OFFSET {offset}",
                 ]

        self.execute(" ".join(query))

        results = []
        for i, record in enumerate(self.fetchall(), start=offset):
            results.append(
                PostgreSQLRecord(id=i, table=table, values=dict(record))
            )

        return results

    def build_empty_table(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> PostgreSQLTable:
        id = PostgreSQLContext.get_temporary_id(database.tables)

        if name is None:
            name = _(f"Table{str(id * -1):03}")

        return PostgreSQLTable(
            id=id,
            name=name,
            database=database,
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_foreign_keys_handler=self.get_foreign_keys,
            get_records_handler=self.get_records,
        ).copy()

    def build_empty_column(self, table: SQLTable, datatype: SQLDataType, /, name: Optional[str] = None, **default_values) -> PostgreSQLColumn:
        id = PostgreSQLContext.get_temporary_id(table.columns)

        if name is None:
            name = _(f"Column{str(id * -1):03}")

        return PostgreSQLColumn(
            id=id,
            name=name,
            table=table,
            datatype=datatype,
            **default_values
        )

    def build_empty_index(self, table: PostgreSQLTable, indextype: PostgreSQLIndexType, columns: list[str], /, name: Optional[str] = None, **default_values) -> PostgreSQLIndex:
        id = PostgreSQLContext.get_temporary_id(table.indexes)

        if name is None:
            name = _(f"Index{str(id * -1):03}")

        return PostgreSQLIndex(
            id=id,
            name=name,
            type=indextype,
            columns=columns,
            table=table,
        )

    def build_empty_foreign_key(self, table: PostgreSQLTable, columns: list[str], /, name: Optional[str] = None, **default_values) -> PostgreSQLForeignKey:
        id = PostgreSQLContext.get_temporary_id(table.foreign_keys)

        if name is None:
            name = _(f"ForeignKey{str(id * -1):03}")

        return PostgreSQLForeignKey(
            id=id,
            name=name,
            table=table,
            columns=columns,
            reference_table="",
            reference_columns=[],
            on_update="NO ACTION",
            on_delete="NO ACTION",
        )

    def build_empty_record(self, table: PostgreSQLTable, /, *, values: dict[str, Any]) -> PostgreSQLRecord:
        return PostgreSQLRecord(
            id=PostgreSQLContext.get_temporary_id(table.records),
            table=table,
            values=values
        )

    def build_empty_view(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> PostgreSQLView:
        id = PostgreSQLContext.get_temporary_id(database.views)

        if name is None:
            name = _(f"View{str(id * -1):03}")

        return PostgreSQLView(
            id=id,
            name=name,
            database=database,
            sql=default_values.get("sql", ""),
        )

    def build_empty_trigger(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> PostgreSQLTrigger:
        id = PostgreSQLContext.get_temporary_id(database.triggers)

        if name is None:
            name = _(f"Trigger{str(id * -1):03}")

        return PostgreSQLTrigger(
            id=id,
            name=name,
            database=database,
            sql=default_values.get("sql", ""),
        )
