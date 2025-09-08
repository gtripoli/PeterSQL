from typing import Iterator

from models.database import Database, Table, Column
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.statement import AbstractStatement


class SQLiteStatement(AbstractStatement):
    def __init__(self, session: 'Session'):
        connection_url = f"sqlite:///{session.configuration.filename}"
        super().__init__(connection_url)

    def get_server_version(self) -> str:
        version = self.execute("SELECT sqlite_version()").fetchone()
        return version[0]

    def get_server_uptime(self) -> str:
        # SQLite non ha un uptime del server, restituiamo una stringa vuota
        return ""

    def get_databases(self) -> Iterator[Database]:
        # SQLite supporta solo un database per connessione
        yield Database(id=0, name='main', get_tables=lambda: self.get_tables('main'))

    def get_tables(self, database: str) -> Iterator[Table]:
        # Ottieni tutte le tabelle
        tables_result = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        for row in tables_result:
            table_name = row[0]
            yield Table(
                id=0,  # Non abbiamo un ID univoco
                name=table_name,
                schema=database,
                engine='sqlite',
                get_columns=lambda t=table_name: self.get_columns(database, t)
            )

    def get_columns(self, database: str, table: str) -> Iterator[Column]:
        # Ottieni le colonne usando PRAGMA
        columns_result = self.execute(f"PRAGMA table_info({table})").fetchall()

        for col in columns_result:
            yield Column(
                id=col['cid'],
                name=col['name'],
                datatype=SQLiteDataType.get_by_type(col['type']),
                is_nullable=not col['notnull'],
                is_primary=col['pk'] == 1,
                default=col['dflt_value'],
                # Altri campi non disponibili in SQLite
            )
