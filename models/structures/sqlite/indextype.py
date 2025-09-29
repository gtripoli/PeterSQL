from icons import BitmapList
from models.structures.indextype import SQLIndexType, StandardIndexType


class SQLiteIndexType(StandardIndexType):
    PARTIAL = SQLIndexType(name="PARTIAL", prefix="pt", bitmap=BitmapList.KEY_SPATIAL)
    EXPRESSION = SQLIndexType(name="EXPRESSION", prefix="ex", bitmap=BitmapList.KEY_SPATIAL)
    COVERING = SQLIndexType(name="COVERING", prefix="cv", bitmap=BitmapList.KEY_SPATIAL)
