import abc
from typing import Optional, List, Any, Union, NamedTuple, Callable

import wx
import wx.dataview

from helpers.logger import logger
from helpers.observables import ObservableList, ObservableLazyList, CallbackEvent


class ColumnField(NamedTuple):
    attr: str
    transform: Optional[Callable] = None

    def get_value(self, *args):
        value = getattr(args[0], self.attr, None)
        if callable(self.transform):
            if self.transform.__name__ == "<lambda>":
                return self.transform(args[0], value)

            return self.transform(value)

        return value

    def has_value(self, *args):
        return self.get_value(args[0]) is not None


class AbstractBaseDataModel():
    def __init__(self, column_count: Optional[int] = None):
        self._data: List[Any] = []
        self._observable: Union[ObservableList, ObservableLazyList] = None

        self.column_count = column_count

    def load(self, data: List[Any]):
        logger.debug(f"{self.__class__.__name__}.load: {data[:50]}")

        if data:
            self._data = data.copy()

    def filter(self, data: List[Any]):
        logger.debug(f"{self.__class__.__name__}.filter: {data[:50]}")

        if data:
            self._data = data.copy()

    def append(self, data: Any) -> int:
        logger.debug(f"{self.__class__.__name__}.append: {data}")

        self._data.append(data)

        return len(self._data) - 1

    def insert(self, data: Any, index: int) -> int:
        logger.debug(f"{self.__class__.__name__}._insert: {index} {data} ")

        self._data.insert(index, data)

        return index

    def replace(self, data: Any, index: int) -> int:
        logger.debug(f"{self.__class__.__name__}.replace: index={index} {data}")

        index = self._data.index(data)

        self._data.remove(data)
        self._data.insert(index, data)

        return index

    def move(self, data: Any, current: int, future: int) -> (int, int):
        logger.debug(f"{self.__class__.__name__}.move: {data} current={current} future={future}")

        self._data[current], self._data[future] = self._data[future], self._data[current]

        return current, future

    def remove(self, data: Any) -> int:
        logger.debug(f"{self.__class__.__name__}.remove: {data}")

        index = self._data.index(data)

        self._data.remove(data)

        return index

    def pop(self, data: Any) -> int:
        logger.debug(f"{self.__class__.__name__}.pop: {data}")

        index = self._data.index(data)

        self._data.pop(index)

        return index

    def clear(self):
        self._data = []

    def get_data_by_row(self, row: int):
        return self._data[row]

    def set_data_by_row(self, row: int, data: Any):
        self._data[row] = data

    def get_item_by_name(self, name: str):
        return next((d for d in self._data if d.name == name), None)

    def get_item_by_filters(self, **filters):
        return next((d for d in self._data if all(hasattr(d, k) and getattr(d, k) == v for k, v in filters.items())), None)

    @abc.abstractmethod
    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        raise NotImplementedError

    data = property(lambda self: self._data, lambda self, *args: None, lambda self: None)


class BaseDataViewTreeModel(AbstractBaseDataModel, wx.dataview.PyDataViewModel):
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

    def _replace(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        AbstractBaseDataModel.replace(self, data, index)

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
        AbstractBaseDataModel.remove(self, data)

        item = self.ObjectToItem(data)

        if item.IsOk():
            self.ItemDeleted(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def _pop(self, data: Any):
        AbstractBaseDataModel.pop(self, data)

        item = self.ObjectToItem(data)

        if item.IsOk():
            self.ItemDeleted(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def _filter(self, data: Any):
        self.clear()
        AbstractBaseDataModel.filter(self, data)
        self.Cleared()

    def find(self, resolution: Callable[[Any], bool]) -> Optional[Any]:
        return next((v for v in self._data if resolution(v)), None)

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._observable = observable
        self._observable.subscribe(self._load)
        self._observable.subscribe(self._append, callback_event=CallbackEvent.ON_APPEND)
        self._observable.subscribe(self._replace, callback_event=CallbackEvent.ON_REPLACE)
        self._observable.subscribe(self._insert, callback_event=CallbackEvent.ON_INSERT)
        self._observable.subscribe(self._remove, callback_event=CallbackEvent.ON_REMOVE)
        self._observable.subscribe(self._pop, callback_event=CallbackEvent.ON_POP)
        self._observable.subscribe(self._filter, callback_event=CallbackEvent.ON_FILTER)

    def clear(self):
        super().clear()
        self.Cleared()

    def GetCount(self):
        return len(self._data)

    def GetColumnCount(self):
        return self.column_count

    def GetColumnType(self, col):
        return "string"


class BaseDataViewListModel(AbstractBaseDataModel, wx.dataview.DataViewIndexListModel):
    def __init__(self, column_count: Optional[int] = None):
        AbstractBaseDataModel.__init__(self, column_count)
        wx.dataview.DataViewIndexListModel.__init__(self)

    def _load(self, data: List[Any]):
        self.clear()
        AbstractBaseDataModel.load(self, data)

        self.Reset(len(self._data))

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

    def _replace(self, data: Any, index: int) -> bool:
        index = AbstractBaseDataModel.replace(self, data, index)

        self.RowChanged(index)

        return True

    def _move(self, data: Any, current: int, future: int) -> bool:
        AbstractBaseDataModel.move(self, data, current, future)

        self.RowChanged(current)
        self.RowChanged(future)

        return True

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._observable = observable
        self._observable.subscribe(self._load)
        self._observable.subscribe(self._append, callback_event=CallbackEvent.ON_APPEND)
        self._observable.subscribe(self._insert, callback_event=CallbackEvent.ON_INSERT)
        self._observable.subscribe(self._remove, callback_event=CallbackEvent.ON_REMOVE)
        self._observable.subscribe(self._move, callback_event=CallbackEvent.ON_MOVE)

    def get_data_by_item(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)

        return self.get_data_by_row(row)

    def clear(self):
        AbstractBaseDataModel.clear(self)
        self.Reset(0)
        self.Cleared()

    def GetValueByRow(self, row, col):
        if not self.data:
            return ""

        if row >= len(self.data):
            return ""

        if not hasattr(self, "MAP_COLUMN_FIELDS"):
            return ""

        return self.MAP_COLUMN_FIELDS[col].get_value(self.get_data_by_row(row))

    def HasValue(self, item, col):
        if not self.data:
            return False

        if not hasattr(self, "MAP_COLUMN_FIELDS"):
            return True

        return self.MAP_COLUMN_FIELDS[col].has_value(self.get_data_by_item(item))
