from icons import BitmapList
from models.structures.indextype import SQLIndexType, StandardIndexType


class MariaDBIndexType(StandardIndexType):
    FULLTEXT = SQLIndexType(name="FULLTEXT", prefix="ft_", bitmap=BitmapList.KEY_FULLTEXT, enable_append=False)
    SPATIAL = SQLIndexType(name="SPATIAL", prefix="sp_", bitmap=BitmapList.KEY_SPATIAL, enable_append=False)
