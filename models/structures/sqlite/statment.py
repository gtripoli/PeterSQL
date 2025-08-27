from typing import Iterator

from models.database import Database
from models.structures.statement import AbstractStatement


class SQLiteStatement(AbstractStatement):
    def __init__(self, session: 'Session'):
        connection_url = f"sqlite:///{session.configuration.filename}"
        super().__init__(connection_url)

    def get_server_uptime(self) -> str:
        return "1"

    def get_server_version(self) -> str:
        return "1"

    def get_databases(self) -> Iterator[Database]:
        for index, database in enumerate(self.inspector.get_schema_names()):
            yield Database(id=index, name="main", get_tables=self.get_tables)
