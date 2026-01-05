from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce, ObservableList

from windows.main import CURRENT_TABLE, CURRENT_DATABASE

from structures.engines.database import SQLTable

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
        if table is None:
            return

        self.name.set_initial(table.name)
        self.comment.set_initial(table.comment)
        self.auto_increment.set_initial(table.auto_increment)
        self.collation.set_initial(table.collation_name)
        self.engine.set_initial(table.engine)

    def update_table(self, *args):
        if not any(args):
            return

        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        table.name = self.name.get_value()
        table.comment = self.comment.get_value()
        table.auto_increment = int(self.auto_increment.get_value() or 0)
        table.collation_name = self.collation.get_value()
        table.engine = self.engine.get_value()

        if not table.is_new:
            original_table = next((t for t in CURRENT_DATABASE.get_value().tables if t.id == table.id), None)

            if not original_table.compare_fields(table):
                NEW_TABLE.set_value(table)
        else:
            NEW_TABLE.set_value(table)
