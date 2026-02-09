from typing import TypeAlias, Union

from structures.engines.database import SQLColumn, SQLIndex, SQLForeignKey

SQLTypeAlias: TypeAlias = Union['SQLView', 'SQLTrigger', 'SQLTable', 'SQLColumn', 'SQLIndex', 'SQLForeignKey', 'SQLRecord', 'SQLCheck']

MergeTypes: TypeAlias = list[Union['SQLColumn', 'SQLIndex', 'SQLForeignKey']]


def merge_original_current(original: MergeTypes, current_columns: MergeTypes):
    orig = {o.id: o for o in original}
    return [(orig.pop(c.id, None), c) for c in current_columns] + [(o, None) for o in orig.values()]
