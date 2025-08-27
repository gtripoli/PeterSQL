from typing import Iterator, List


import sqlalchemy as sa
from gettext import gettext as _


from models.database import Database
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
            yield Database(id=index, name=database, get_tables=self.get_tables)
