import copy
import enum
import inspect
import weakref

from typing import Callable, TypeVar, Generic, Any, SupportsIndex, Union, Optional, cast, Self, Hashable

import wx

from helpers.logger import logger

T = TypeVar("T")


class CallbackEvent(enum.Enum):
    BEFORE_CHANGE = "before"
    AFTER_CHANGE = "after"
    ON_APPEND = "append"
    ON_REPLACE = "replace"
    ON_INSERT = "insert"
    ON_POP = "pop"
    ON_EXTEND = "extend"
    ON_REMOVE = "remove"
    ON_MOVE = "on_move"
    ON_FILTER = "on_filter"


class ValueState(enum.Enum):
    UNDEFINED = 0
    EMPTY = 1
    DEFINED = 2


class Observable(Generic[T]):
    _unset = object()

    def __init__(self, initial: Any = ...):
        self._initial = None if initial is ... else initial

        if initial is not ...:
            self._value = initial

        self.callbacks: dict[CallbackEvent, dict[Hashable, object]] = {event: {} for event in CallbackEvent}

    @property
    def state(self) -> ValueState:
        if not hasattr(self, "_value"):
            return ValueState.UNDEFINED
        return ValueState.EMPTY if self.is_empty else ValueState.DEFINED

    @property
    def is_empty(self) -> bool:
        return self._get_value() in (None, "", [])

    def _get_value(self) -> Optional[T]:
        return getattr(self, "_value", None)

    def _set_value(self, value: Any) -> Self:
        value = value if value is not None else self._initial

        if getattr(self, "_value", self._unset) != value:
            self.execute_callback(CallbackEvent.BEFORE_CHANGE)
            self._value = value
            self.execute_callback(CallbackEvent.AFTER_CHANGE)

        return self

    def get_value(self) -> Optional[T]:
        return self._get_value()

    def set_value(self, value: Optional[T]) -> Self:
        return self._set_value(value)

    def set_initial(self, value: Optional[T]) -> Self:
        self._initial = value

        self._set_value(value)

        return self

    def subscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE) -> Self:
        if not callable(callback):
            return self

        if inspect.ismethod(callback):
            key = (id(callback.__self__), id(callback.__func__))
            stored = weakref.WeakMethod(callback)
        else:
            key = id(callback)
            stored = callback

        self.callbacks[callback_event][key] = stored

        if callback_event in (CallbackEvent.BEFORE_CHANGE, CallbackEvent.AFTER_CHANGE) and hasattr(self, "_value"):
            cb = stored() if isinstance(stored, weakref.ReferenceType) else stored
            if cb is None:
                return self

            try:
                cb(self._get_value())
            except Exception as ex:
                logger.error(ex, exc_info=True)
                raise

        return self

    def unsubscribe(self, callback: Callable, event: CallbackEvent = CallbackEvent.AFTER_CHANGE) -> Self:
        if not callable(callback):
            return self

        if inspect.ismethod(callback):
            key = (id(callback.__self__), id(callback.__func__))
        else:
            key = id(callback)

        self.callbacks[event].pop(key, None)
        return self

    def execute_callback(self, event: CallbackEvent) -> Self:
        dead = []
        for key, stored in list(self.callbacks[event].items()):
            cb = stored() if isinstance(stored, weakref.ReferenceType) else stored
            if cb is None:
                dead.append(key)
                continue

            try:
                cb(self._get_value())
            except Exception as ex:
                logger.error(ex, exc_info=True)
                raise

        for key in dead:
            self.callbacks[event].pop(key, None)

        return self

    def __call__(self, value: Optional[T] = ...) -> Union[Self, Optional[T]]:
        if value is not ...:
            self._set_value(value)
            return self

        return self._get_value()


class ObservableList(Observable[list[T]]):
    def __init__(self, initial: Optional[list[Any]] = None):
        super().__init__(initial if initial is not None else [])

    def __eq__(self, other: Self):
        if len(self) != len(other):
            return False

        return self.get_value() == other.get_value()

    def __len__(self) -> int:
        return len(self.get_value())

    def __iter__(self):
        return iter(self.get_value())

    def __contains__(self, item):
        return item in self.get_value()

    def __getitem__(self, key):
        return self.get_value()[key]

    def __setitem__(self, key, value):
        self.get_value()[key] = value

    def __delitem__(self, key):
        del self.get_value()[key]

    def _ensure(self):
        value = super()._get_value()
        if value is None:
            value = []
            self._value = value
        if not isinstance(value, list):
            raise TypeError(f"Expected list, got {type(value)}")

        return value

    def get_value(self) -> List:
        return self._ensure()

    def append(self, value: Any, replace_existing: bool = False) -> Self:
        values = self.get_value()

        if replace_existing:
            try:
                idx = values.index(value)
                values[idx] = value
                callback = dict(event=CallbackEvent.ON_REPLACE, value=value, index=idx)
            except ValueError:
                values.append(value)
                callback = dict(event=CallbackEvent.ON_APPEND, value=value)
        else:
            values.append(value)
            callback = dict(event=CallbackEvent.ON_APPEND, value=value)

        self._value = values
        self.execute_callback_on_value(**callback)

        return self

    def insert(self, index: int, value: Any) -> Self:
        values = self.get_value()
        values.insert(index, value)

        self._value = values
        self.execute_callback_on_value(CallbackEvent.ON_INSERT, value=value, index=index)

        return self

    def extend(self, other: list[Any]) -> Self:
        values = self.get_value()
        values.extend(other)

        self._value = values
        self.execute_callback_on_value(CallbackEvent.ON_EXTEND, value=other)

        return self

    def pop(self, index: int = -1) -> Self:
        values = self.get_value()
        value = values.pop(index)

        self._value = values
        self.execute_callback_on_value(CallbackEvent.ON_POP, value=value)

        return self

    def remove(self, value: Any) -> Self:
        values = self.get_value()
        values.remove(value)

        self._value = values
        self.execute_callback_on_value(CallbackEvent.ON_REMOVE, value=value)

        return self

    def reverse(self) -> Self:
        values = self.get_value()
        values.reverse()

        return self._set_value(values)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> Self:
        values = self.get_value()
        values.sort(key=key, reverse=reverse)

        return self._set_value(values)

    def move_up(self, value) -> Self:
        values = self.get_value()
        idx = values.index(value)
        if idx > 0:
            values[idx], values[idx - 1] = values[idx - 1], values[idx]

        self._value = values

        self.execute_callback_on_value(CallbackEvent.ON_MOVE, value=value, current=idx, future=idx - 1)

        return self

    def move_down(self, value):
        values = self.get_value()
        idx = values.index(value)
        if idx < len(values) - 1:
            values[idx], values[idx + 1] = values[idx + 1], values[idx]

        self._value = values

        self.execute_callback_on_value(CallbackEvent.ON_MOVE, value=value, current=idx, future=idx + 1)

        return self

    def clear(self) -> Self:
        self.set_value([])
        return self

    def filter(self, function: Callable[[Any], bool]) -> list[T]:
        filtered = [v for v in self.get_value() if function(v)]

        self.execute_callback_on_value(CallbackEvent.ON_FILTER, value=filtered)

        return filtered

    def index(self, item: Any) -> Optional[int]:
        try:
            return self.get_value().index(item)
        except ValueError:
            return None

    def find(self, function: Callable[[Any], bool]) -> Optional[T]:
        return next((v for v in self.get_value() if function(v)), None)

    def find_index(self, function: Callable[[Any], bool]) -> Optional[int]:
        return next((i for i, v in enumerate(self.get_value()) if function(v)), None)

    def execute_callback_on_value(self, event: CallbackEvent, value: Any, **kwargs) -> Self:
        dead = []
        for key, stored in list(self.callbacks[event].items()):
            cb = stored() if isinstance(stored, weakref.ReferenceType) else stored
            if cb is None:
                dead.append(key)
                continue

            try:
                cb(value, **kwargs)
            except Exception as ex:
                logger.error(ex, exc_info=True)
                raise

        for key in dead:
            self.callbacks[event].pop(key, None)

        return self


class ObservableLazyList(ObservableList[T]):
    def __init__(self, loader: Callable[[], list[T]]) -> None:
        super().__init__()
        self._loaded = False
        self._loader = loader

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _ensure(self):
        value = super()._ensure()
        if not self._loaded:
            loaded = list(self._loader())
            self._loaded = True
            super()._set_value(loaded)
            return loaded
        return value

    def get_value(self) -> list[T]:
        return self._ensure()

    def subscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE) -> Self:
        super().subscribe(callback, callback_event)

        if callback_event in (CallbackEvent.BEFORE_CHANGE, CallbackEvent.AFTER_CHANGE) and not self._loaded:
            self.get_value()

        return self

    def clear(self) -> Self:
        return super().clear()

    def refresh(self) -> Self:
        self._value = None
        self._loaded = False
        self.get_value()
        return self


class ObservableObject(Observable):
    def _get_in_ref(self, ref: Union[Dict, List, Any], key: Union[str, SupportsIndex]):
        if isinstance(ref, dict):
            return ref.get(key)
        elif isinstance(ref, list):
            return ref[cast(SupportsIndex, key)]
        else:
            return getattr(ref, str(key), None)

    def _set_in_ref(self, ref: Union[Dict, List, Any], key: Union[str, SupportsIndex], value: Any):
        if isinstance(ref, dict):
            ref[key] = value
        elif isinstance(ref, list):
            ref[cast(SupportsIndex, key)] = value
        else:
            setattr(ref, str(key), value)

        return ref

    def set_value(self, *attributes: str, value: Any) -> Self:  # type: ignore[override]  # intentional signature change for nested attribute access
        ref = copy.deepcopy(super()._get_value())
        target = ref

        for i, attr in enumerate(attributes):
            if i == len(attributes) - 1:
                self._set_in_ref(target, attr, value)
            else:
                target = self._get_in_ref(target, attr)
                if target is None:
                    raise KeyError(f"Attribute '{attr}' not found in {ref}")

        return super()._set_value(ref)

    def get_value(self, *attributes: str) -> Any:
        ref = super()._get_value()
        for attr in attributes:
            ref = self._get_in_ref(ref, attr)
            if ref is None:
                return None
        return ref


def debounce(*observables: Observable, callback: Callable, wait_time: float = 0.4):
    waiting = False

    def _debounced(*args, **kwargs):
        nonlocal waiting
        if not waiting:
            waiting = True

            def call_and_reset():
                nonlocal waiting
                callback(*args, **kwargs)
                waiting = False

            wx.CallAfter(call_and_reset)

    for obs in observables:
        setattr(obs, '_debounce_callback', _debounced)
        obs.subscribe(_debounced)
