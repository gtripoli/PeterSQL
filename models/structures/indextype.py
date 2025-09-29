import dataclasses
import functools
from typing import List

import wx

from icons import BitmapList


@dataclasses.dataclass
class SQLIndexType:
    name: str
    bitmap: wx.Bitmap
    prefix: str

    def __str__(self):
        return self.name


class StandardIndexType():
    PRIMARY = SQLIndexType(name="PRIMARY", prefix="pk", bitmap=BitmapList.KEY_PRIMARY)
    UNIQUE = SQLIndexType(name="UNIQUE", prefix="uq", bitmap=BitmapList.KEY_UNIQUE)
    INDEX = SQLIndexType(name="INDEX", prefix="ix", bitmap=BitmapList.KEY_NORMAL)

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_all(cls) -> List[SQLIndexType]:
        types = [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), SQLIndexType)
        ]

        # category_order = {cat: i for i, cat in enumerate(DataTypeCategory)}

        # return sorted(types, key=lambda t: category_order[t.category])
        return types
