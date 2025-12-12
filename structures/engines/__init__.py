from typing import List, Union, TypeAlias

from structures.engines.database import SQLColumn, SQLIndex, SQLForeignKey

MergeTypes: TypeAlias = List[Union['SQLColumn', 'SQLIndex', 'SQLForeignKey']]


def merge_original_current(original: MergeTypes, current_columns: MergeTypes):
    orig = {o.id: o for o in original}
    return [(orig.pop(c.id, None), c) for c in current_columns] + [(o, None) for o in orig.values()]
