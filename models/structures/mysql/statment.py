from typing import Iterator, List

import sqlalchemy as sa
from gettext import gettext as _

from models.database import Database, Table, Column
from models.structures.mysql.datatype import MySQLDataType
from models.structures.statement import AbstractStatement


class MySQLStatement(AbstractStatement):

    def __init__(self, session):
        connection_url = f"mysql+pymysql://{session.configuration.username}:{session.configuration.password}@{session.configuration.hostname}"
        super().__init__(connection_url)

    def get_server_version(self) -> str:
        version = self.connection.execute(sa.text("SELECT VERSION()")).fetchone()

        return version

    def get_server_uptime(self) -> str:
        uptime = self.connection.execute(sa.text(f"""
            SELECT 
              DATE_FORMAT(
                NOW() - INTERVAL VARIABLE_VALUE SECOND, 
                '%Y-%m-%dT%H:%i:%s.000Z'
              ) AS up_since_iso,
              CONCAT(
                FLOOR(VARIABLE_VALUE / 86400), ' {_("days")}, ',
                FLOOR((VARIABLE_VALUE % 86400) / 3600), ' {_("hours")}, ',
                FLOOR((VARIABLE_VALUE % 3600) / 60), ' {_("minutes")}, ',
                VARIABLE_VALUE % 60, ' {_("seconds")}'
              ) AS uptime_formatted
            FROM performance_schema.session_status 
            WHERE VARIABLE_NAME = 'Uptime';
        """)).fetchone()

        return uptime['uptime_formatted']

    def get_databases(self) -> Iterator[Database]:
        for index, database in enumerate(self.inspector.get_schema_names()):
            yield Database(id=index, name=database, get_tables=lambda *args, **kwargs: self.get_tables(*args, **kwargs))

    def get_tables(self, database: str) -> Iterator[Table]:
        # Ottieni tutte le informazioni sulle tabelle
        tables_result = self.execute(f"""
            SELECT *
            FROM information_schema.tables
            WHERE table_schema = '{database}'
                AND table_type = 'BASE TABLE'
        """).fetchall()

        tables = []
        for row in tables_result:
            yield Table(
                id=row['TABLE_ROWS'],  # Usiamo il numero di righe come ID temporaneo
                name=row['TABLE_NAME'],
                schema=row['TABLE_SCHEMA'],
                engine=row['ENGINE'],
                row_format=row['ROW_FORMAT'],
                table_rows=row['TABLE_ROWS'],
                avg_row_length=row['AVG_ROW_LENGTH'],
                data_length=row['DATA_LENGTH'],
                max_data_length=row['MAX_DATA_LENGTH'],
                index_length=row['INDEX_LENGTH'],
                data_free=row['DATA_FREE'],
                auto_increment=row['AUTO_INCREMENT'],
                create_time=row['CREATE_TIME'],
                update_time=row['UPDATE_TIME'],
                check_time=row['CHECK_TIME'],
                table_collation=row['TABLE_COLLATION'],
                checksum=row['CHECKSUM'],
                create_options=row['CREATE_OPTIONS'],
                comment=row['TABLE_COMMENT'],
                temporary=row['TEMPORARY'] == 'YES',
                get_columns=lambda t=row['TABLE_NAME']: self.get_columns(database, t)
            )

    def get_columns(self, database: str, table: str) -> Iterator[Column]:
        # Ottieni tutte le informazioni sulle colonne
        columns_result = self.execute(f"""
            SELECT *
            FROM information_schema.columns
            WHERE table_schema = '{database}'
                AND table_name = '{table}'
        """).fetchall()

        columns = []
        for col in columns_result:
            yield Column(
                id=col['ORDINAL_POSITION'],
                name=col['COLUMN_NAME'],
                datatype=MySQLDataType.get_by_type(col['COLUMN_TYPE']),
                is_nullable=col['IS_NULLABLE'] == 'YES',
                is_primary=col['COLUMN_KEY'] == 'PRI',
                is_unique=col['COLUMN_KEY'] == 'UNI',
                is_indexed=col['COLUMN_KEY'] == 'MUL',
                default=col['COLUMN_DEFAULT'],
                extra=col['EXTRA'],
                character_set=col['CHARACTER_SET_NAME'],
                collation=col['COLLATION_NAME'],
                numeric_precision=col['NUMERIC_PRECISION'],
                numeric_scale=col['NUMERIC_SCALE'],
                datetime_precision=col['DATETIME_PRECISION'],
                is_auto_increment='auto_increment' in col['EXTRA'].lower(),
                comment=col['COLUMN_COMMENT']
            )
