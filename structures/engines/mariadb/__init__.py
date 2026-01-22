from helpers.dataview import ColumnField

MAP_COLUMN_FIELDS = {
    0: ColumnField("#", lambda s, v: str(s.id + 1) if s.id >= 0 else ""),
    1: ColumnField("name"),
    2: ColumnField("datatype", str),
    3: ColumnField("length_scale_set"),
    4: ColumnField("is_unsigned"),
    5: ColumnField("is_nullable"),
    6: ColumnField("is_zerofill"),
    7: ColumnField("default"),
    8: ColumnField("virtuality"),
    9: ColumnField("expression"),
    10: ColumnField("collation_name"),
    11: ColumnField("comment"),
}

ENGINE_KEYWORDS = (
    "show "
    "describe "
    "explain "
    "replace "
    "ignore "
    "limit "
    "offset "
    "auto_increment "
    "engine "
    "charset "
    "collate "
    "unsigned "
    "zerofill "
    "if "
    "exists "
    "on "
    "duplicate "
    "key "
    "update "
    "lock "
    "unlock "
    "delimiter "
    "returning "
)
