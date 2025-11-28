import copy

from engines.structures.mariadb.database import MariaDBTable
from helpers.bindings import AbstractModel
from helpers.logger import logger
from helpers.observables import Observable, debounce, ObservableList, Loader

from windows.main import CURRENT_SESSION, CURRENT_TABLE, CURRENT_DATABASE, CURRENT_COLUMN

from engines.structures.database import SQLTable

NEW_TABLE: Observable[SQLTable] = Observable()


class EditTableModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.comment = Observable()
        self.columns = ObservableList()

        self.auto_increment = Observable()
        self.collation = Observable()
        self.engine = Observable()

        debounce(
            self.name, self.comment, self.auto_increment, self.collation, self.engine,
            callback=self.update_table
        )

        CURRENT_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.name.set_value(table.name if table is not None else "")
        self.comment.set_value(table.comment if table is not None else "")
        self.auto_increment.set_value(table.auto_increment if table is not None else 0)
        self.collation.set_value(table.collation_name if table is not None else "")
        self.engine.set_value(table.engine if table is not None else "")

    def update_table(self, *args):
        if not any(args):
            return

        if (current_table := CURRENT_TABLE.get_value()) is None :
            table = NEW_TABLE.get_value()
        else :
            table = CURRENT_TABLE.get_value().copy()


        table.name = self.name.get_value()
        table.comment = self.comment.get_value()
        table.auto_increment = self.auto_increment.get_value()
        table.collation = self.collation.get_value()
        table.engine = self.engine.get_value()


        if not table.is_new() :
            original_table = next((t for t in CURRENT_DATABASE.get_value().tables if t.id == table.id), None)

            if original_table is not None and original_table != table :
                # CURRENT_TABLE.set_value(None)
                NEW_TABLE.set_value(table)
        else :
            NEW_TABLE.set_value(table)

