import abc
from typing import List, Any, Union, Optional

import wx
import wx.dataview

from helpers.logger import logger
from helpers.observables import Observable, ObservableList, ObservableLazyList
from engines.session import Session
from engines.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLForeignKey, SQLIndex, SQLRecord, SQLTrigger, SQLView

SESSIONS: ObservableList[Session] = ObservableList()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_DATABASE: Observable[SQLDatabase] = Observable()
CURRENT_TABLE: Observable[SQLTable] = Observable()
CURRENT_VIEW: Observable[SQLView] = Observable()
CURRENT_TRIGGER: Observable[SQLTrigger] = Observable()
CURRENT_FUNCTION: Observable[SQLTrigger] = Observable()
CURRENT_PROCEDURE: Observable[SQLTrigger] = Observable()
CURRENT_EVENT: Observable[SQLTrigger] = Observable()
CURRENT_COLUMN: Observable[SQLColumn] = Observable()
CURRENT_INDEX: Observable[SQLIndex] = Observable()
CURRENT_FOREIGN_KEY: Observable[SQLForeignKey] = Observable()
CURRENT_RECORDS: ObservableList[SQLRecord] = ObservableList()

AUTO_APPLY: Observable[bool] = Observable(True)


class AbstractBaseDataModel():
    _data: List[Any] = []
    _observable: Union[ObservableList, ObservableLazyList]

    def __init__(self, column_count: Optional[int] = None):
        self.column_count = column_count

    def load(self, data: List[Any]):
        logger.debug(f"{self.__class__.__name__}._load: {data}")

        if data:
            self._data = data.copy()

    def append(self, data: Any) -> int:
        logger.debug(f"{self.__class__.__name__}._append: {data}")

        self._data.append(data)

        return len(self._data) - 1

    def insert(self, data: Any, index: int) -> int:
        logger.debug(f"{self.__class__.__name__}._insert: {index} {data} ")

        self._data.insert(index, data)

        return index

    def remove(self, data: Any) -> int:
        logger.debug(f"{self.__class__.__name__}._remove: {data}")

        index = self._data.index(data)

        self._data.remove(data)

        return index

    def clear(self):
        self._data = []

    def get_data_by_row(self, row: int):
        return self._data[row]

    @abc.abstractmethod
    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        raise NotImplementedError

    def GetCount(self):
        return len(self._data)

    def GetColumnCount(self):
        return self.column_count

    def GetColumnType(self, col):
        return "string"

    data = property(lambda self: self._data, lambda self, *args: None, lambda self: None)


class BaseDataViewModel(AbstractBaseDataModel, wx.dataview.PyDataViewModel):
    def __init__(self, column_count: Optional[int] = None):
        AbstractBaseDataModel.__init__(self, column_count)
        wx.dataview.PyDataViewModel.__init__(self)

    def _load(self, data: List[Any]):
        self.clear()
        AbstractBaseDataModel.load(self, data)
        self.Cleared()

    def _append(self, data: Any) -> wx.dataview.DataViewItem:
        AbstractBaseDataModel.append(self, data)

        item = self.ObjectToItem(data)

        if item.IsOk():
            self.ItemAdded(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def _insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        AbstractBaseDataModel.insert(self, data, index)

        item = self.ObjectToItem(data)

        if item.IsOk():
            self.ItemAdded(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def _remove(self, data: Any) -> wx.dataview.DataViewItem:
        logger.debug(f"{self.__class__.__name__}._remove: {data}")

        AbstractBaseDataModel.remove(self, data)

        item = self.ObjectToItem(data)

        if item.IsOk():
            self.ItemDeleted(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._observable = observable
        self._observable.subscribe(self._load, execute_immediately=True)
        self._observable.subscribe(self._append, callback_event=ObservableList.CallbackEvent.ON_APPEND)
        self._observable.subscribe(self._insert, callback_event=ObservableList.CallbackEvent.ON_INSERT)
        self._observable.subscribe(self._remove, callback_event=ObservableList.CallbackEvent.ON_REMOVE)

    def clear(self):
        super().clear()
        self.Cleared()


class BaseDataViewIndexListModel(AbstractBaseDataModel, wx.dataview.DataViewIndexListModel):
    def __init__(self, column_count: Optional[int] = None):
        AbstractBaseDataModel.__init__(self, column_count)
        wx.dataview.DataViewIndexListModel.__init__(self)

    def _load(self, data: List[Any]):
        self.clear()
        AbstractBaseDataModel.load(self, data)
        self.Reset(len(self._data))

        # self.Cleared()

    def _append(self, data: Any) -> wx.dataview.DataViewItem:
        index = AbstractBaseDataModel.append(self, data)

        self.RowAppended()

        return self.GetItem(index)

    def _insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        index = AbstractBaseDataModel.insert(self, data, index)

        self.RowInserted(index)

        return self.GetItem(index)

    def _remove(self, data: Any) -> bool:
        index = AbstractBaseDataModel.remove(self, data)

        self.RowDeleted(index)

        self.Reset(len(self._data))

        return True

    def get_data_by_item(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)

        return self.get_data_by_row(row)

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._observable = observable
        self._observable.subscribe(self._load, execute_immediately=True)
        self._observable.subscribe(self._append, callback_event=ObservableList.CallbackEvent.ON_APPEND)
        self._observable.subscribe(self._insert, callback_event=ObservableList.CallbackEvent.ON_INSERT)
        self._observable.subscribe(self._remove, callback_event=ObservableList.CallbackEvent.ON_REMOVE)

    def clear(self):
        AbstractBaseDataModel.clear(self)
        self.Reset(0)
        self.Cleared()
