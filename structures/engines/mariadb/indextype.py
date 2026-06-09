from icons import IconList
from structures.engines.indextype import SQLIndexType, StandardIndexType


class MariaDBIndexType(StandardIndexType):
    FULLTEXT = SQLIndexType(name="FULLTEXT", prefix="ft_", bitmap=IconList.KEY_FULLTEXT, enable_append=False)
    SPATIAL = SQLIndexType(name="SPATIAL", prefix="spatial_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
