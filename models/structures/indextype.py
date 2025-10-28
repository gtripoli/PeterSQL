import dataclasses
import functools
from typing import List, Self

import wx

from icons import BitmapList


@dataclasses.dataclass
class SQLIndexType:
    name: str
    bitmap: wx.Bitmap
    prefix: str

    is_unique: bool = False
    is_primary: bool = False
    enable_append: bool = True
    enable_condition: bool = True

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: Self):
        if not isinstance(other, SQLIndexType):
            return False

        return self.name == other.name


class StandardIndexType():
    PRIMARY = SQLIndexType(name="PRIMARY", prefix="pk_", bitmap=BitmapList.KEY_PRIMARY, is_primary=True)
    UNIQUE = SQLIndexType(name="UNIQUE", prefix="uq_", bitmap=BitmapList.KEY_UNIQUE, is_unique=True)
    NORMAL = SQLIndexType(name="NORMAL", prefix="ix_", bitmap=BitmapList.KEY_NORMAL)

    @classmethod
    @functools.lru_cache()
    def get_all(cls) -> list[SQLIndexType]:
        types = []
        for base in reversed(cls.__mro__):
            for key, value in base.__dict__.items():
                if isinstance(value, SQLIndexType) and value not in types:
                    types.append(value)
        return types
