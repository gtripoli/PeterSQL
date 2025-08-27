import math
from typing import Iterator, List

from gettext import gettext as _
import sqlalchemy as sa

from models.database import Database, Table, Column
from models.structures.mysql.datatype import MySQLDataType
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
                     f"{math.floor(uptime_value  % 60)} {_('seconds')}")

        return formatted

    def get_databases(self) -> Iterator[Database]:
        for index, database in enumerate(self.inspector.get_schema_names()):
            yield Database(id=index, name=database, get_tables=self.get_tables)
