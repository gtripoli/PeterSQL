from typing import List, Any, Union, Optional

import wx
import wx.dataview

from helpers.logger import logger
from helpers.observables import Observable, ObservableList
from engines.session import Session
from engines.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLForeignKey, SQLIndex, SQLRecord, SQLTrigger, SQLView

SESSIONS: ObservableList[Session] = ObservableList()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_DATABASE: Observable[SQLDatabase] = Observable()
CURRENT_TABLE: Observable[SQLTable] = Observable()
CURRENT_VIEW: Observable[SQLView] = Observable()
CURRENT_TRIGGER: Observable[SQLTrigger] = Observable()
CURRENT_COLUMN: Observable[SQLColumn] = Observable()
CURRENT_INDEX: Observable[SQLIndex] = Observable()
CURRENT_FOREIGN_KEY: Observable[SQLForeignKey] = Observable()
CURRENT_RECORDS: ObservableList[SQLRecord] = ObservableList()

AUTO_APPLY: Observable[bool] = Observable(True)


class BaseDataViewIndexListModel(wx.dataview.DataViewIndexListModel):
    def __init__(self, column_count: Optional[int] = None):
        super().__init__()
        self._data: List[Any] = []
        self._observable: ObservableList

        self.column_count = column_count

    def _load(self, data: List[Any]):
        logger.debug(f"{self.__class__.__name__}._load: {data}")

        self.clear()
        self._data = data.copy()
        self.Reset(len(self._data))

    def _append(self, data: Any) -> wx.dataview.DataViewItem:
        logger.debug(f"{self.__class__.__name__}._append: {data}")

        self._data.append(data)

        self.RowAppended()

        new_row_index = len(self._data) - 1
        return self.GetItem(new_row_index)

    def _insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        logger.debug(f"{self.__class__.__name__}._insert: {index} {data} ")

        self._data.insert(index, data)

        self.RowInserted(index)

        return self.GetItem(index)

    def _remove(self, data: Any) -> bool:
        logger.debug(f"{self.__class__.__name__}._remove: {data}")

        self._data.remove(data)

        self.Reset(len(self._data))
        return True

    def get_data_by_row(self, row: int):
        return self._data[row]

    def get_data_by_item(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)

        return self.get_data_by_row(row)

    def set_observable(self, observable: ObservableList):
        self._observable = observable
        self._observable.subscribe(self._load, execute_immediately=True)
        self._observable.subscribe(self._append, callback_event=ObservableList.CallbackEvent.ON_APPEND)
        self._observable.subscribe(self._insert, callback_event=ObservableList.CallbackEvent.ON_INSERT)
        self._observable.subscribe(self._remove, callback_event=ObservableList.CallbackEvent.ON_REMOVE)

    def clear(self):
        self._data = []
        self.Reset(0)
        self.Cleared()

    def GetCount(self):
        return len(self._data)

    def GetColumnCount(self):
        return self._column_count

    def GetColumnType(self, col):
        return "string"

    data = property(lambda self: self._data, lambda self, *args: None, lambda self: None)