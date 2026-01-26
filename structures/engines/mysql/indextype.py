from icons import IconList
from structures.engines.indextype import SQLIndexType, StandardIndexType


class MySQLIndexType(StandardIndexType):
    BTREE = SQLIndexType(name="BTREE", prefix="btree_", bitmap=IconList.KEY_SPATIAL, enable_append=True)
    HASH = SQLIndexType(name="HASH", prefix="hash_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    FULLTEXT = SQLIndexType(name="FULLTEXT", prefix="ft_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    SPATIAL = SQLIndexType(name="SPATIAL", prefix="spatial_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
