import re
from typing import NamedTuple

COLLATIONS = {
    "BINARY": "utf8",
    "NOCASE": "utf8",
    "RTRIM": "utf8"
}


class ColumnField(NamedTuple):
    attr: str
    transform: callable


MAP_COLUMN_FIELDS = {
    0: ColumnField("#", lambda v: str(v + 1) if v >= 0 else ''),
    1: ColumnField("name", lambda v: str(v) if v.strip() else "New Column"),
    2: ColumnField("datatype", str),
    3: ColumnField("length_scale_set", str),
    4: ColumnField("is_nullable", bool),
    5: ColumnField("check", str),
    6: ColumnField("default", str),
    7: ColumnField("virtuality", str),
    8: ColumnField("expression", str),
    9: ColumnField("collation_name", str),
}

#   https://sqlite.org/syntax/column-constraint.html
#   column_name data_type
#       [PRIMARY KEY [ASC|DESC] [AUTOINCREMENT]]
#       [NOT NULL]
#       [UNIQUE]
#       [CHECK (expression)]
#       [DEFAULT default_value]
#       [COLLATE collation_name]
#       [REFERENCES foreign_table(column_name)
#           [ON DELETE {SET NULL | SET DEFAULT | CASCADE | RESTRICT | NO ACTION}]
#           [ON UPDATE {SET NULL | SET DEFAULT | CASCADE | RESTRICT | NO ACTION}]
#       ]
#       [GENERATED ALWAYS AS (expression) [VIRTUAL | STORED]]

COLUMNS_PATTERN = re.compile(r"""
^\s*
(?:`|\"|\[)?(?P<name>\w+)(?:`|\"|\])?                                                       # column name
\s+
(?P<datatype>\w+)                                                                           # data type (ex. VARCHAR, INT)
(?:\s*\((?:(?P<length>\d+)|(?P<precision>\d+)\s*,\s*(?P<scale>\d+)|(?P<set>[^)]+))\))?      # length or precision and scale or set
(?P<attributes>.*)$
""", re.IGNORECASE | re.VERBOSE)

ATTRIBUTES_PATTERN = [
    re.compile(r"""(?P<is_primary_key>PRIMARY\s+KEY)(?:\s+(?P<primary_key_order>ASC|DESC)?)?(?:\s+ON\s+CONFLICT\s+(?P<primary_key_conflict>ROLLBACK|ABORT|FAIL|IGNORE|REPLACE))?"""),
    re.compile(r"""(?P<is_auto_increment>AUTOINCREMENT)"""),
    re.compile(r"""(?P<is_nullable>NOT\s+NULL|NULL)(?:\s+ON\s+CONFLICT\s+(?P<nullability_conflict>ROLLBACK|ABORT|FAIL|IGNORE|REPLACE))?"""),
    re.compile(r"""(?P<is_unique>UNIQUE)(?:\s+ON\s+CONFLICT\s+(?P<conflict>ROLLBACK|ABORT|FAIL|IGNORE|REPLACE))?"""),
    re.compile(r"""CHECK\s*\((?P<check>[^)].*)\)"""),
    re.compile(r"""DEFAULT\s+(?P<default>\(.*?\))(?=\s|$)"""),
    re.compile(r"""DEFAULT\s+(?P<default>-?\d+(\.\d+)?)"""),
    re.compile(r"""DEFAULT\s+(?P<default>\w?(\'.*\'|\".*\"))"""),
    re.compile(r"""DEFAULT\s+(?P<default>[a-zA-Z_-]{2,})"""),
    re.compile(r"""COLLATE\s+(?P<collate>\w+)"""),
    re.compile(r"""GENERATED\s+ALWAYS\s+AS\s*\((?P<expression>.*?)\)\s*(?P<virtuality>VIRTUAL|STORED)"""),
    re.compile(r"""REFERENCES\s+(?P<references>\w+)(?:\s+ON\s+DELETE\s+(?P<on_delete>SET\s+NULL|SET\s+DEFAULT|CASCADE|RESTRICT|NO\s+ACTION))?(?:\s+ON\s+UPDATE\s+(?P<on_update>SET\s+NULL|SET\s+DEFAULT|CASCADE|RESTRICT|NO\s+ACTION))?"""),
]
