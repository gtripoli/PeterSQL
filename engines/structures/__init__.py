from typing import List, Union

from engines.structures.database import SQLColumn


def merge_original_current(original: List[Union['SQLColumn', 'SQLIndex']], current_columns:  List[Union['SQLColumn', 'SQLIndex']]):
    orig = {o.id: o for o in original}
    return [(orig.pop(c.id, None), c) for c in current_columns] + [(o, None) for o in orig.values()]
