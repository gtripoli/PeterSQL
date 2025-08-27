from typing import List, Callable, Iterator, Any


class LazyList(list):
    def __init__(self, loader: Callable[[], List[Any]]):
        super().__init__()
        self._loader = loader
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.extend(self._loader())
            self._loaded = True

    def __iter__(self) -> Iterator[Any]:
        self._ensure_loaded()
        return super().__iter__()

    def __getitem__(self, index):
        self._ensure_loaded()
        return super().__getitem__(index)

    def __len__(self):
        self._ensure_loaded()
        return super().__len__()
