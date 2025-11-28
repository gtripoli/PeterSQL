from icons import BitmapList
from engines.structures.indextype import SQLIndexType, StandardIndexType


class MariaDBIndexType(StandardIndexType):
    BTREE = SQLIndexType(name="BTREE", prefix="btree_", bitmap=BitmapList.KEY_SPATIAL, enable_append=True)
    HASH = SQLIndexType(name="HASH", prefix="hash_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
    FULLTEXT = SQLIndexType(name="FULLTEXT", prefix="ft_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
    SPATIAL = SQLIndexType(name="SPATIAL", prefix="spatial_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
