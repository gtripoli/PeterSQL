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

ENGINE_KEYWORDS = (
    "select "
    "insert "
    "update "
    "delete "
    "create "
    "alter "
    "drop "
    "table "
    "index "
    "view "
    "trigger "
    "function "
    "procedure "
    "database "
    "schema "
    "serial "
    "bigserial "
    "primary "
    "key "
    "foreign "
    "references "
    "check "
    "unique "
    "default "
    "not "
    "null "
    "using "
    "where "
    "order "
    "by "
    "group "
    "having "
    "limit "
    "offset "
    "join "
    "inner "
    "left "
    "right "
    "full "
    "outer "
    "on "
    "union "
    "all "
    "distinct "
    "as "
    "from "
    "into "
    "values "
    "set "
    "begin "
    "commit "
    "rollback "
    "savepoint "
    "returning "
)
