import copy
import enum
import inspect
import weakref
from threading import Timer
from typing import Any, Dict, List, Callable, Union, Optional, Self, TypeVar, Generic

T = TypeVar("T")


class Observable(Generic[T]):
    class CallbackEvent(enum.Enum):
        BEFORE_CHANGE = "before"
        AFTER_CHANGE = "after"

    def __init__(self, default: Any = None):
        self._value = default
        self._initial = default
        self._default = default

        self._callbacks: Dict[str, List[Callable]] = {
            "before": [],
            "after": [],
        }

    def execute_callback(self, event: CallbackEvent, **kwargs) -> None:
        dead = []
        value = kwargs.pop("value", self._value)
        for callback in self._callbacks[event.value]:
            ref = callback()
            if ref is None:
                dead.append(callback)
                continue

            ref(value, **kwargs)

        for callback in dead:
            self._callbacks[event.value].remove(callback)

        return None

    def _set_value(self, value: Any, **kwargs) -> None:
        if self._value != value:
            self.execute_callback(Observable.CallbackEvent.BEFORE_CHANGE, **kwargs)
            self._value = value
            self.execute_callback(Observable.CallbackEvent.AFTER_CHANGE, **kwargs)

        return None

    def set_value(self, value: Optional[T], **kwargs) -> Self:
        if self._initial is None and self._value is None:
            self._initial = value

        resolved_value = (
            value if value is not None else self._default if self._default is not None else None
        )

        self._set_value(resolved_value, **kwargs)

        return self

    def get_value(self) -> Optional[T]:
        return self._value

    def subscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE, execute_immediately: bool = False) -> Self:
        if callable(callback):
            if inspect.ismethod(callback):
                ref = weakref.WeakMethod(callback)
            else:
                ref = weakref.ref(callback)

            self._callbacks[callback_event.value].append(ref)

            if self.is_dirty or execute_immediately:
                callback(self._value)

        return self

    def unsubscribe(self, callback: Callable, callback_event: CallbackEvent = CallbackEvent.AFTER_CHANGE):
        to_remove = []
        for ref in self._callbacks[callback_event.value]:
            if ref() is callback:
                to_remove.append(ref)

        for r in to_remove:
            self._callbacks[callback_event.value].remove(r)

    @property
    def is_empty(self) -> bool:
        return self._value in (None, "")

    @property
    def is_pristine(self) -> bool:
        return self._value == self._initial

    @property
    def is_dirty(self) -> bool:
        return self._value != self._initial


class ObservableArray(Observable[List[T]]):
    class CallbackEvent(enum.Enum):
        BEFORE_CHANGE = "before"
        AFTER_CHANGE = "after"
        ON_APPEND = "append"
        ON_INSERT = "insert"

    def __init__(self, default: Any = None):
        super().__init__(default)

        self._callbacks[ObservableArray.CallbackEvent.ON_APPEND.value] = []
        self._callbacks[ObservableArray.CallbackEvent.ON_INSERT.value] = []

    def _ensure_list(self) -> List:
        value = super().get_value() or []
        if not isinstance(value, list):
            raise TypeError(f"Expected list, got {type(value)}")
        return value

    def __len__(self) -> int:
        return len(self._ensure_list())

    def __iter__(self):
        return iter(self._ensure_list())

    def get_value(self) -> List:
        return self._ensure_list()

    def append(self, value: Any) -> Self:
        values = self._ensure_list()
        values.append(value)

        self.execute_callback(ObservableArray.CallbackEvent.ON_APPEND, value=value)

        return self.set_value(values)

    def insert(self, index: int, value: Any) -> Self:
        values = self._ensure_list()
        values.insert(index, value)

        self.execute_callback(ObservableArray.CallbackEvent.ON_INSERT, value=value)

        return self.set_value(values)

    def extend(self, other: List[Any]) -> Self:
        values = self._ensure_list()
        values.extend(other)
        return self.set_value(values)

    def pop(self, index: int = -1) -> Any:
        values = self._ensure_list()
        value = values.pop(index)
        self.set_value(values)
        return value

    def reverse(self) -> Self:
        values = self._ensure_list()
        values.reverse()
        return self.set_value(values)

    def remove(self, value: Any) -> Self:
        values = self._ensure_list()
        values.remove(value)
        return self.set_value(values)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> Self:
        values = self._ensure_list()
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

    def find(self, function: Callable[[Any], bool]) -> Optional[Any]:
        return next((v for v in self._ensure_list() if function(v)), None)

    def find_index(self, function: Callable[[Any], bool]) -> Optional[int]:
        for i, v in enumerate(self._ensure_list()):
            if function(v):
                return i
        return None


class ObservableObject(Observable):
    def _get_in_ref(self, ref: Any, key: Union[str, int]):
        if isinstance(ref, dict):
            return ref.get(key)
        elif isinstance(ref, list):
            return ref[key]
        else:
            return getattr(ref, key, None)

    def _set_in_ref(self, ref: Any, key: Union[str, int], value: Any):
        if isinstance(ref, dict) or isinstance(ref, list):
            ref[key] = value
        else:
            setattr(ref, key, value)
        return ref

    def set_value(self, *attributes: str, value: Any) -> Self:
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


def debounce(*observables: Observable, callback: Callable, wait_time: float = 0.4):
    timer: Optional[Timer] = None

    def _debounced(*args, **kwargs):
        nonlocal timer
        if timer:
            timer.cancel()
        timer = Timer(wait_time, callback, args, kwargs)
        timer.start()

    for obs in observables:
        obs.subscribe(_debounced)
