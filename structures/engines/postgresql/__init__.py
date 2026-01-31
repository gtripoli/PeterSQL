from helpers.dataview import ColumnField

MAP_COLUMN_FIELDS = {
    0: ColumnField("#", lambda s, v: str(s.id + 1) if s.id >= 0 else ""),
    1: ColumnField("name"),
    2: ColumnField("datatype", str),
    3: ColumnField("length_scale_set"),
    4: ColumnField("is_nullable"),
    5: ColumnField("default"),
    6: ColumnField("virtuality"),
    7: ColumnField("expression"),
    8: ColumnField("collation_name"),
    9: ColumnField("comment"),
}