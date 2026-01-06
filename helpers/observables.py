import copy
import enum
import inspect
import weakref
from typing import List, Callable, TypeVar, Generic, Any, overload, Union, Tuple, Optional, Dict, cast, Self, NewType
from typing import SupportsIndex
from contextlib import contextmanager

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
    ON_REVERSE = "reverse"
    ON_MOVE = "on_move"


class Observable(Generic[T]):

    def __init__(self, initial: Any = None):
        self._initial = initial

        if initial is not None:
            self._value = initial
            self._last_value = initial

        self._callbacks: Dict[CallbackEvent, Dict[int, Callable]] = {event: {} for event in CallbackEvent}

    @property
    def callbacks(self) -> Dict[CallbackEvent, Dict[Any, Callable]]:
        return self._callbacks

    @property
    def is_empty(self) -> bool:
        return getattr(self, "_value", None) in (None, "", [])

    @property
    def is_pristine(self) -> bool:
        return not hasattr(self, "_value")

    @property
    def is_dirty(self) -> bool:
        return not self.is_empty and (hasattr(self, "_value") or getattr(self, '_value', None) != getattr(self, '_last_value', None))

    def _set_value(self, value: Any, **kwargs) -> None:
        if getattr(self, "_value", None) != value:
            self.execute_callback(CallbackEvent.BEFORE_CHANGE, **kwargs)
            self._value = value
            self.execute_callback(CallbackEvent.AFTER_CHANGE, **kwargs)
            self._last_value = value

        return None

    def execute_callback(self, event: CallbackEvent) -> None:
        dead = []
        for callback, ref_callback in self._callbacks[event].items():
            ref = ref_callback()
            if ref is None:
                dead.append(callback)
                continue

            if not self.is_empty:
                try:
                    ref(getattr(self, "_value"))
                except Exception as ex:
                    logger.error(ex, exc_info=True)

        for callback in dead:
            self._callbacks[event].pop(callback)

        return None

    def set_value(self, value: Optional[T], **kwargs) -> Self:
        # if self._last is None and self._value is None:
        #     self._last = value

        resolved_value = (
            value if value is not None else self._initial if self._initial is not None else None
        )

        self._set_value(resolved_value, **kwargs)

        return self

    def set_initial(self, value: Optional[T]) -> Self:
        self._initial = value

        self.set_value(value)

        return self

    def get_value(self) -> Optional[T]:
        return getattr(self, "_value", None)

    def subscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE) -> Self:
        if callable(callback):
            if inspect.ismethod(callback):
                ref = weakref.WeakMethod(callback)
            else:
                ref = weakref.ref(callback)

            self._callbacks[callback_event][id(callback)] = ref

            if callback_event in [CallbackEvent.BEFORE_CHANGE, CallbackEvent.AFTER_CHANGE] and self.is_dirty:
                self.execute_callback(event=callback_event)

        return self

    def unsubscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE):
        to_remove = []
        for ref in self._callbacks[callback_event]:
            if ref() is callback:
                to_remove.append(ref)

        for r in to_remove:
            self._callbacks[callback_event].pop(r)


class ObservableList(Observable[List[T]]):
    def __init__(self, default: Any = None):
        super().__init__(default)

    def _ensure_list(self) -> List:
        value = super().get_value() or []
        if not isinstance(value, list):
            raise TypeError(f"Expected list, got {type(value)}")
        return value

    def __len__(self) -> int:
        return len(self._ensure_list())

    def __iter__(self):
        return iter(self._ensure_list())

    def __contains__(self, item):
        return item in self._ensure_list()

    def __getitem__(self, key):
        return self._ensure_list()[key]

    def __setitem__(self, key, value):
        self._ensure_list()[key] = value

    def __delitem__(self, key):
        del self._ensure_list()[key]

    def get_value(self) -> List:
        return self._ensure_list()

    def append(self, value: Any, replace_existing: bool = False) -> Self:
        values = self.get_value()

        if replace_existing and value in values:
            idx = self.index(value)
            values[idx] = value

            callback = dict(event=CallbackEvent.ON_REPLACE, value=value, index=idx)
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

    def extend(self, other: List[Any]) -> Self:
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

        self.execute_callback_on_value(CallbackEvent.ON_REMOVE, value=value)
        self._value = values

        return self

    def reverse(self) -> Self:
        values = self.get_value()
        values.reverse()

        return self.set_value(values)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> Self:
        values = self.get_value()
        values.sort(key=key, reverse=reverse)

        return self.set_value(values)

    def filter(self, function: Callable[[Any], bool]) -> Self:
        filtered = [v for v in self._ensure_list() if function(v)]

        return self.set_value(filtered)

    def index(self, item: Any) -> Optional[int]:
        try:
            return self._ensure_list().index(item)
        except ValueError:
            return None

    def find(self, function: Callable[[Any], bool]) -> Optional[T]:
        return next((v for v in self._ensure_list() if function(v)), None)

    def find_index(self, function: Callable[[Any], bool]) -> Optional[int]:
        for i, v in enumerate(self._ensure_list()):
            if function(v):
                return i
        return None

    def move_up(self, value) -> Self:
        values = self._ensure_list()
        idx = values.index(value)
        if idx > 0:
            values[idx], values[idx - 1] = values[idx - 1], values[idx]

        self._values = values

        self.execute_callback_on_value(CallbackEvent.ON_MOVE, value=value, current=idx, future=idx - 1)

        return self

    def move_down(self, value):
        values = self._ensure_list()
        idx = values.index(value)
        if idx < len(values) - 1:
            values[idx], values[idx + 1] = values[idx + 1], values[idx]

        self._values = values

        self.execute_callback_on_value(CallbackEvent.ON_MOVE, value=value, current=idx, future=idx + 1)

        return self

    def clear(self) -> Self:
        self.set_value([])
        return self

    def execute_callback_on_value(self, event: CallbackEvent, value: Any, **kwargs) -> None:
        dead = []
        for callback, ref_callback in self._callbacks[event].items():
            ref = ref_callback()
            if ref is None:
                dead.append(callback)
                continue

            try:
                ref(value, **kwargs)
            except Exception as ex:
                logger.error(ex, exc_info=True)


class ObservableLazyList(ObservableList[T]):
    def __init__(self, loader: Callable[[], List[T]]) -> None:
        super().__init__(default=[])
        self._loaded = False
        self._loader = loader

    def __eq__(self, other: Self):
        if len(self) != len(other):
            return False

        return not all([o1 != o2 for o1, o2 in zip(self.get_value(), other.get_value())])

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _ensure_list(self):
        self._ensure_loaded()
        return super()._ensure_list()

    def _ensure_loaded(self, force: bool = False) -> None:
        if force or not self._loaded:
            super().set_value(list(self._loader()))
            self._loaded = True

    def get_value(self) -> List[T]:
        self._ensure_loaded()
        return super().get_value()

    def set_value(self, value: Optional[List[T]], **kwargs) -> Self:
        self._loaded = True
        return super().set_value(value, **kwargs)

    def clear(self) -> Self:
        # self._loaded = False
        return super().clear()

    def refresh(self) -> Self:
        self._ensure_loaded(force=True)
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

    def set_value(self, *attributes: str, value: Any) -> Self:  # type: ignore[override]
        ref = copy.deepcopy(super().get_value())
        target = ref

        for i, attr in enumerate(attributes):
            if i == len(attributes) - 1:
                self._set_in_ref(target, attr, value)
            else:
                target = self._get_in_ref(target, attr)
                if target is None:
                    raise KeyError(f"Attribute '{attr}' not found in {ref}")

        return super().set_value(ref)

    def get_value(self, *attributes: str) -> Any:
        ref = super().get_value()
        for attr in attributes:
            ref = self._get_in_ref(ref, attr)
            if ref is None:
                return None
        return ref


class Loader:
    _queue: Observable[list] = Observable([])
    loading: Observable[bool] = Observable(False)

    @classmethod
    def _update_loading_state(cls):
        """Update loading state based on queue length"""
        cls.loading.set_value(len(cls._queue.get_value()) > 0)

    @classmethod
    @contextmanager
    def cursor_wait(cls):
        """Context manager to show wait cursor during operations"""
        token = object()  # Unique token for this operation

        # Add token to queue
        current_queue = cls._queue.get_value()
        current_queue.append(token)
        cls._queue.set_value(current_queue)
        cls._update_loading_state()

        try:
            yield
        finally:
            # Remove token from queue
            current_queue = cls._queue.get_value()
            if token in current_queue:
                current_queue.remove(token)
                cls._queue.set_value(current_queue)
                cls._update_loading_state()


def debounce(*observables: Observable, callback: Callable, wait_time: float = 0.4):
    call_later: Optional[wx.CallLater] = None

    def _debounced(*args, **kwargs):
        nonlocal call_later
        if call_later:
            call_later.Stop()
        call_later = wx.CallLater(int(wait_time * 1000), callback, *args, **kwargs)

    for obs in observables:
        setattr(obs, '_debounce_callback', _debounced)
        obs.subscribe(_debounced)
