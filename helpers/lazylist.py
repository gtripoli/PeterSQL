from typing import List, Callable, Iterator, TypeVar, Generic, Type, Any, overload, Union, Tuple
from collections.abc import Sequence

T = TypeVar('T')

class LazyList(List[T]):
    def __init__(self, loader: Callable[[], Iterator[T]]) -> None:
        super().__init__()
        self._loader = loader
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            items = self._loader()
            self.clear()
            self.extend(items)
            self._loaded = True

    def __iter__(self) -> Iterator[T]:
        self._ensure_loaded()
        return super().__iter__()

    @overload
    def __getitem__(self, i: int) -> T: ...
    
    @overload
    def __getitem__(self, s: slice) -> List[T]: ...
    
    def __getitem__(self, i: Union[int, slice]) -> Union[T, List[T]]:
        self._ensure_loaded()
        return super().__getitem__(i)

    def __len__(self) -> int:
        self._ensure_loaded()
        return super().__len__()

    def append(self, item: T, replace_existing: bool = False) -> None:
        self._ensure_loaded()
        if replace_existing and item in self:
            idx = self.index(item)
            self[idx] = item
        else:
            super().append(item)
    
    def __contains__(self, item: object) -> bool:
        self._ensure_loaded()
        return super().__contains__(item)
    
    def index(self, item: T, *args: Any) -> int:
        self._ensure_loaded()
        return super().index(item, *args)
    
    def count(self, item: T) -> int:
        self._ensure_loaded()
        return super().count(item)
