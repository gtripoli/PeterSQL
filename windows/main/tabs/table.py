from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce, ObservableList

from structures.engines.database import SQLTable

from windows.state import CURRENT_TABLE, CURRENT_DATABASE, NEW_TABLE


class EditTableModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.comment = Observable()
        self.columns = ObservableList()

        self.auto_increment = Observable()
        self.collation = Observable()
        self.convert_data = Observable()
        self.engine = Observable()
        self.row_format = Observable()

        debounce(
            self.name, self.comment, self.auto_increment, self.collation, self.convert_data,
            self.engine, self.row_format,
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
        self.convert_data.set_initial(False)
        self.engine.set_initial(table.engine)
        self.row_format.set_initial(getattr(table, "row_format", None))

    def update_table(self, *args):
        if not any(args):
            return

        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        table.name = self.name.get_value()
        table.comment = self.comment.get_value()
        table.auto_increment = int(self.auto_increment.get_value() or 0)
        table.collation_name = self.collation.get_value()
        table.engine = self.engine.get_value()
        if hasattr(table, "convert_data"):
            table.convert_data = bool(self.convert_data.get_value())
        if hasattr(table, "row_format"):
            table.row_format = self.row_format.get_value() or None

        if not table.is_new:
            original_table = next((t for t in CURRENT_DATABASE.get_value().tables if t.id == table.id), None)

            if not original_table.compare_fields(table):
                NEW_TABLE.set_value(table)
        else:
            NEW_TABLE.set_value(table)
