from icons import IconList
from structures.engines.indextype import SQLIndexType, StandardIndexType


class PostgreSQLIndexType(StandardIndexType):
    BTREE = SQLIndexType(name="BTREE", prefix="btree_", bitmap=IconList.KEY_NORMAL)
    HASH = SQLIndexType(name="HASH", prefix="hash_", bitmap=IconList.KEY_NORMAL, enable_append=False)
    GIST = SQLIndexType(name="GIST", prefix="gist_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    GIN = SQLIndexType(name="GIN", prefix="gin_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    SPGIST = SQLIndexType(name="SP-GIST", prefix="spgist_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    BRIN = SQLIndexType(name="BRIN", prefix="brin_", bitmap=IconList.KEY_NORMAL, enable_append=True)
