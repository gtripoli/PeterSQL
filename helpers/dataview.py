import abc
from typing import Optional, Any, Union, NamedTuple, Callable

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


class BaseDataModel():
    def __init__(self, column_count: Optional[int] = None):
        self._data: list[Any] = []
        self._column_count = column_count

    def load(self, data: list[Any]):
        self._data = data

    def filter(self, data: list[Any]):
        if data:
            self._data = data.copy()

    def append(self, data: Any) -> int:
        self._data.append(data)

        return len(self._data) - 1

    def insert(self, data: Any, index: int) -> int:
        self._data.insert(index, data)

        return index

    def replace(self, data: Any, index: int) -> int:
        index = self._data.index(data)

        self._data.remove(data)
        self._data.insert(index, data)

        return index

    def move(self, data: Any, current: int, future: int) -> tuple[int, int]:
        self._data[current], self._data[future] = self._data[future], self._data[current]

        return current, future

    def remove(self, data: Any) -> int:
        index = self._data.index(data)

        self._data.remove(data)

        return index

    def pop(self, data: Any) -> int:
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

    data = property(lambda self: self._data, lambda self, *args: None, lambda self: None)


class _DataViewListValueMixin:
    def _get_column_fields(self):
        return getattr(self, "MAP_COLUMN_FIELDS", None)

    def get_data_by_item(self, item: wx.dataview.DataViewItem):
        return self.get_data_by_row(self.GetRow(item))

    def clear(self):
        super().clear()
        self.Reset(0)
        self.Cleared()

    def GetColumnCount(self) -> int:
        fields = self._get_column_fields()
        if fields:
            return len(fields)

        return self._column_count

    def GetValueByRow(self, row, col):
        if not self.data or row >= len(self.data):
            return ""

        if fields := self._get_column_fields():
            return fields[col].get_value(self.get_data_by_row(row))

        return self.get_data_by_row(row)[col]

    def HasValue(self, item, col):
        if not self.data:
            return False

        if fields := self._get_column_fields():
            return fields[col].has_value(self.get_data_by_item(item))

        return getattr(self.get_data_by_item(item), col, None) is not None


class BaseDataViewListModel(_DataViewListValueMixin, BaseDataModel, wx.dataview.DataViewIndexListModel):
    def __init__(self, column_count: Optional[int] = None):
        BaseDataModel.__init__(self, column_count)
        wx.dataview.DataViewIndexListModel.__init__(self)

    def load(self, data: list[Any]):
        self.clear()

        BaseDataModel.load(self, data)

        self.Reset(len(self._data))

    def append(self, data: Any) -> wx.dataview.DataViewItem:
        index = BaseDataModel.append(self, data)

        self.RowAppended()

        return self.GetItem(index)

    def insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        index = BaseDataModel.insert(self, data, index)

        self.RowInserted(index)

        return self.GetItem(index)

    def remove(self, data: Any) -> bool:
        index = BaseDataModel.remove(self, data)

        self.RowDeleted(index)

        self.Reset(len(self._data))

        return True

    def replace(self, data: Any, index: int) -> bool:
        index = BaseDataModel.replace(self, data, index)

        self.RowChanged(index)

        return True

    def move(self, data: Any, current: int, future: int) -> bool:
        BaseDataModel.move(self, data, current, future)

        self.RowChanged(current)
        self.RowChanged(future)

        return True


class BaseObservableDataModel(BaseDataModel):
    def __init__(self, column_count: Optional[int] = None):
        super().__init__(column_count)
        self._observable: Union[ObservableList, ObservableLazyList]

    def load(self, data: list[Any]):
        super().load(data.copy())

    @abc.abstractmethod
    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        raise NotImplementedError

    def _set_observable_handlers(
            self,
            observable: Union[ObservableList, ObservableLazyList],
            on_load: Callable,
            handlers: dict[CallbackEvent, Callable],
    ):
        self._observable = observable
        self._observable.subscribe(on_load)

        for event, handler in handlers.items():
            self._observable.subscribe(handler, callback_event=event)


class BaseObservableDataViewTreeModel(BaseObservableDataModel, wx.dataview.PyDataViewModel):
    def __init__(self, column_count: Optional[int] = None):
        BaseObservableDataModel.__init__(self, column_count)
        wx.dataview.PyDataViewModel.__init__(self)

    def _load(self, data: list[Any]):
        self.clear()
        BaseObservableDataModel.load(self, data)
        self.Cleared()

    def _apply_tree_update(self, data: Any, deleted: bool = False) -> wx.dataview.DataViewItem:
        item = self.ObjectToItem(data)
        if item.IsOk():
            if deleted:
                self.ItemDeleted(wx.dataview.NullDataViewItem, item)
            else:
                self.ItemAdded(wx.dataview.NullDataViewItem, item)

        self.Cleared()

        return item

    def _append(self, data: Any) -> wx.dataview.DataViewItem:
        BaseObservableDataModel.append(self, data)
        return self._apply_tree_update(data)

    def _replace(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        BaseObservableDataModel.replace(self, data, index)
        return self._apply_tree_update(data)

    def _insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        BaseObservableDataModel.insert(self, data, index)
        return self._apply_tree_update(data)

    def _remove(self, data: Any) -> wx.dataview.DataViewItem:
        BaseObservableDataModel.remove(self, data)
        return self._apply_tree_update(data, deleted=True)

    def _pop(self, data: Any):
        BaseObservableDataModel.pop(self, data)
        return self._apply_tree_update(data, deleted=True)

    def _filter(self, data: Any):
        self.clear()
        BaseObservableDataModel.filter(self, data)
        self.Cleared()

    def find(self, resolution: Callable[[Any], bool]) -> Optional[Any]:
        return next((v for v in self._data if resolution(v)), None)

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._set_observable_handlers(
            observable,
            self._load,
            {
                CallbackEvent.ON_APPEND: self._append,
                CallbackEvent.ON_REPLACE: self._replace,
                CallbackEvent.ON_INSERT: self._insert,
                CallbackEvent.ON_REMOVE: self._remove,
                CallbackEvent.ON_POP: self._pop,
                CallbackEvent.ON_FILTER: self._filter,
            },
        )

    def clear(self):
        super().clear()
        self.Cleared()

    def GetCount(self):
        return len(self._data)

    def GetColumnCount(self):
        return self.column_count

    def GetColumnType(self, col):
        return "string"


class BaseObservableDataViewListModel(_DataViewListValueMixin, BaseObservableDataModel, wx.dataview.DataViewIndexListModel):
    def __init__(self, column_count: Optional[int] = None):
        BaseObservableDataModel.__init__(self, column_count)
        wx.dataview.DataViewIndexListModel.__init__(self)

    def _load(self, data: list[Any]):
        self.clear()
        BaseObservableDataModel.load(self, data)

        self.Reset(len(self._data))

    def _append(self, data: Any) -> wx.dataview.DataViewItem:
        index = BaseObservableDataModel.append(self, data)

        self.RowAppended()

        return self.GetItem(index)

    def _insert(self, data: Any, index: int) -> wx.dataview.DataViewItem:
        index = BaseObservableDataModel.insert(self, data, index)

        self.RowInserted(index)

        return self.GetItem(index)

    def _remove(self, data: Any) -> bool:
        index = BaseObservableDataModel.remove(self, data)

        self.RowDeleted(index)

        self.Reset(len(self._data))

        return True

    def _replace(self, data: Any, index: int) -> bool:
        index = BaseObservableDataModel.replace(self, data, index)

        self.RowChanged(index)

        return True

    def _move(self, data: Any, current: int, future: int) -> bool:
        BaseObservableDataModel.move(self, data, current, future)

        self.RowChanged(current)
        self.RowChanged(future)

        return True

    def set_observable(self, observable: Union[ObservableList, ObservableLazyList]):
        self._set_observable_handlers(
            observable,
            self._load,
            {
                CallbackEvent.ON_APPEND: self._append,
                CallbackEvent.ON_INSERT: self._insert,
                CallbackEvent.ON_REMOVE: self._remove,
                CallbackEvent.ON_MOVE: self._move,
            },
        )
