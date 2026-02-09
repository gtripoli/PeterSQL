from icons import IconList
from structures.engines.indextype import SQLIndexType, StandardIndexType


class PostgreSQLIndexType(StandardIndexType):
    PRIMARY = SQLIndexType(name="PRIMARY", prefix="pk_", bitmap=IconList.KEY_PRIMARY, is_primary=True, is_unique=True)
    UNIQUE = SQLIndexType(name="UNIQUE INDEX", prefix="uq_", bitmap=IconList.KEY_UNIQUE, is_unique=True)
    INDEX = SQLIndexType(name="INDEX", prefix="idx_", bitmap=IconList.KEY_NORMAL)
    BTREE = SQLIndexType(name="BTREE", prefix="btree_", bitmap=IconList.KEY_NORMAL)
    HASH = SQLIndexType(name="HASH", prefix="hash_", bitmap=IconList.KEY_NORMAL, enable_append=False)
    GIST = SQLIndexType(name="GIST", prefix="gist_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    GIN = SQLIndexType(name="GIN", prefix="gin_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    SPGIST = SQLIndexType(name="SP-GIST", prefix="spgist_", bitmap=IconList.KEY_SPATIAL, enable_append=False)
    BRIN = SQLIndexType(name="BRIN", prefix="brin_", bitmap=IconList.KEY_NORMAL, enable_append=True)
