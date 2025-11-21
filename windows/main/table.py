import copy

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
            callback=self.build_table
        )

        CURRENT_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.name.set_value(table.name if table is not None else "")
        self.comment.set_value(table.comment if table is not None else "")
        # self.auto_increment.set_value(table.auto_increment if table is not None else 0)
        # self.collation.set_value(table.collation if table is not None else "")
        # self.engine.set_value(table.engine if table is not None else "")

    def build_table(self, *args):
        if not any(args):
            return
        if (current_table := CURRENT_TABLE.get_value()) is None:
            session = CURRENT_SESSION.get_value()
            database = CURRENT_DATABASE.get_value()
            new_table = session.context.build_empty_table(database)
        else:
            new_table = copy.copy(current_table)

        new_table.name = self.name.get_value()
        new_table.comment = self.comment.get_value()
        new_table.collation = self.collation.get_value()
        new_table.auto_increment = self.auto_increment.get_value()

        if new_table == current_table:
            return

        NEW_TABLE.set_value(new_table)
