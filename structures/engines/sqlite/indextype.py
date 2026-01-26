from icons import IconList
from structures.engines.indextype import SQLIndexType, StandardIndexType


class SQLiteIndexType(StandardIndexType):
    PARTIAL = SQLIndexType(name="PARTIAL", prefix="prt_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    EXPRESSION = SQLIndexType(name="EXPRESSION", prefix="exp_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
