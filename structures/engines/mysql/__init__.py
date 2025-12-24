import re
from typing import NamedTuple


class ColumnField(NamedTuple):
    attr: str
    transform: callable


MAP_COLUMN_FIELDS = {
    0: ColumnField("#", lambda v: str(v + 1) if v >= 0 else ""),
    1: ColumnField("name", lambda v: str(v)),
    2: ColumnField("datatype", str),
    3: ColumnField("length_scale_set", str),
    4: ColumnField("is_unsigned", bool),
    5: ColumnField("is_nullable", bool),
    6: ColumnField("is_zerofill", bool),
    7: ColumnField("default", str),
    8: ColumnField("virtuality", str),
    9: ColumnField("expression", str),
    10: ColumnField("collation_name", str),
    11: ColumnField("comment", str),
}
