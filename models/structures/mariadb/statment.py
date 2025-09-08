import re
import math
from typing import Iterator, List, Optional, Union

from gettext import gettext as _
import sqlalchemy as sa

from models.database import Database, Table, Column, Index
from models.structures.mariadb.datatype import MariaDBDataType
from models.structures.statement import AbstractStatement


class MariaDBStatement(AbstractStatement):

    def __init__(self, session):
        connection_url = f"mysql+pymysql://{session.configuration.username}:{session.configuration.password}@{session.configuration.hostname}"
        super().__init__(connection_url)

    def get_server_version(self) -> str:
        version = list(self.connection.execute(sa.text("SELECT VERSION()")).fetchone())

        return version[0]

    def get_server_uptime(self) -> str:
        uptime = list(self.connection.execute(sa.text(f"SHOW STATUS LIKE 'Uptime';")).fetchone())

        uptime_value = int(uptime[1])

        formatted = (f"{math.floor(uptime_value / 86400)} {_('days')}, "
                     f"{math.floor((uptime_value % 86400) / 3600)} {_('hours')}, "
                     f"{math.floor((uptime_value % 3600) / 60)} {_('minutes')}, "
                     f"{math.floor(uptime_value % 60)} {_('seconds')}")

        return formatted

    def get_databases(self) -> Iterator[Database]:
        for index, database in enumerate(self.inspector.get_schema_names()):
            yield Database(id=index, name=database, get_tables=lambda database: self.get_tables(database))

    def get_tables(self, database: str) -> Iterator[Table]:
        tables_result = self.execute(f"""
            SELECT * 
            FROM `information_schema`.`tables` 
            WHERE table_schema = '{database}'
                AND table_type = 'BASE TABLE'
            """).mappings().fetchall()

        for row in tables_result:
            yield Table(
                id=row['TABLE_ROWS'],
                name=row['TABLE_NAME'],
                schema=row['TABLE_SCHEMA'],
                engine=row['ENGINE'],
                get_columns=lambda database, table: self.get_columns(database, table)
            )

    @staticmethod
    @staticmethod
    def _parse_type(column_type: str) -> Optional[Union[int, List[str]]]:
        # Cerca un numero tra parentesi per i tipi interi
        int_match = re.search(r'\((\d+)\)', column_type)
        if int_match:
            return int(int_match.group(1))

        enum_match = re.search(r'^enum\((.*)\)$', column_type)
        if enum_match:
            inner = enum_match.group(1)
            return [value.strip("'") for value in inner.split(",")]

        return None

    def get_columns(self, database: str, table: str) -> Iterator[Column]:
        columns_result = self.execute(f"""
            SELECT *
            FROM `information_schema`.`columns`
            WHERE table_schema = '{database}'
                AND table_name = '{table}'
            ORDER BY ORDINAL_POSITION
        """).mappings().fetchall()

        indexes_result = self.execute(f"""
            SELECT *
            FROM `information_schema`.`statistics`
            WHERE table_schema = '{database}'
                AND table_name = '{table}'
        """).mappings().fetchall()

        indexes_map = {}
        for idx in indexes_result:
            col_name = idx['COLUMN_NAME']
            if col_name not in indexes_map:
                indexes_map[col_name] = []
            indexes_map[col_name].append(idx)

        for col in columns_result:
            column_indexes = []
            for idx in indexes_map.get(col['COLUMN_NAME'], []):
                index_type = idx['INDEX_TYPE']
                if idx['INDEX_NAME'] == 'PRIMARY':
                    index_type = 'PRIMARY'

                index_obj = Index(
                    name=idx['INDEX_NAME'],
                    type=index_type,
                    columns=[idx['COLUMN_NAME']],
                    is_primary=(idx['INDEX_NAME'] == 'PRIMARY'),
                    is_unique=(idx['NON_UNIQUE'] == 0),
                    is_fulltext=(index_type == 'FULLTEXT'),
                    is_spatial=(index_type == 'SPATIAL')
                )
                column_indexes.append(index_obj)

            yield Column(
                id=col['ORDINAL_POSITION'],
                name=col['COLUMN_NAME'],
                datatype=MariaDBDataType.get_by_name(col['DATA_TYPE']),
                is_nullable=col['IS_NULLABLE'] == 'YES',
                extra=col['EXTRA'] if col['EXTRA'] not in ['', 'auto_increment', 'VIRTUAL GENERATED', 'STORED GENERATED'] else None,
                key=col['COLUMN_KEY'],
                character_set=col['CHARACTER_SET_NAME'],
                collation_name=col['COLLATION_NAME'],
                comment=col['COLUMN_COMMENT'],
                is_unsigned='unsigned' in col['COLUMN_TYPE'],
                is_zerofill='zerofill' in col['COLUMN_TYPE'],

                virtuality="VIRTUAL" if 'VIRTUAL' in col['EXTRA'] else "STORED" if 'STORED' in col['EXTRA'] else None,
                expression=col['GENERATION_EXPRESSION'],

                server_default=col['COLUMN_DEFAULT'],
                set=self._parse_type(col['COLUMN_TYPE']) if col['DATA_TYPE'] == 'enum' else None,
                length=col.get('CHARACTER_MAXIMUM_LENGTH', None),
                indexes=column_indexes,
                is_auto_increment='auto_increment' in col['EXTRA'],


                numeric_precision=self._parse_type(col['COLUMN_TYPE']) if col['DATA_TYPE'] in ["int", "tinyint", "smallint", "mediumint", "bigint"] else col.get('NUMERIC_PRECISION', None),
                numeric_scale=col.get('NUMERIC_SCALE', None),
                datetime_precision=col.get('DATETIME_PRECISION', None)
            )
