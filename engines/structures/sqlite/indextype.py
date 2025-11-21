from icons import BitmapList
from engines.structures.indextype import SQLIndexType, StandardIndexType


class SQLiteIndexType(StandardIndexType):
    PARTIAL = SQLIndexType(name="PARTIAL", prefix="prt_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
    EXPRESSION = SQLIndexType(name="EXPRESSION", prefix="exp_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
