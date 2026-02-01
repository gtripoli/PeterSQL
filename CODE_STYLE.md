# Code Style Guidelines (v1.1-rev2)

These rules define the expected coding style and behavior for AI-generated Python code.
They are mandatory unless explicitly stated otherwise.

---

## Design Principles

These principles explain why the rules exist. They protect consistency over time.

- Determinism over preference  
  A rule must always produce the same result. Subjective rules lead to debates and inconsistency.

- Visual structure matters  
  Code is scanned more often than it is read. Structure reduces cognitive load.

- AI-first, human-friendly  
  Rules must be trivial for an AI to apply and easy for a human to verify.

- Clarity beats cleverness  
  Prefer explicit naming, typing, and control flow over smart shortcuts.

- Local consistency over global perfection  
  A consistent rule is more valuable than a perfect one applied inconsistently.

---

## 1. Comments

- Comments MUST be written in English.
- Comments MUST be concise and non-verbose.
- Do NOT describe obvious code behavior.
- Prefer explaining WHY something is done, not WHAT the code does.
- Prefer type hints over comments whenever possible.

### Good examples
```python
# Avoid caching: data changes on every request.
```

### Bad examples
```python
# This function takes a list of strings and returns an integer.
```

---

## 2. Naming Conventions

- Variable, attribute, class, function, and parameter names MUST be descriptive.
- Names MUST NOT be aggressively shortened.
- Meaning and intent must remain explicit at all times.

### Forbidden patterns
- editor -> ed
- params -> par
- configuration -> cfg
- response -> resp

### Good examples
```python
editor = get_editor()
request_params = parse_params(request)
self.editor = editor
self.request_params = request_params
```

### Bad examples
```python
ed = get_editor()
par = parse_params(request)
self.ed = ed
self.par = par
```

---

## 3. Python Typing

- Container type hints MUST use List, Dict, Set, Tuple from typing.
- Built-in generics (list, dict, set) MUST NOT be used in type annotations.
- Prefer explicit and accurate type hints.
- With mypy, avoid using # type: ignore whenever possible.
- Prefer type hints instead of comments.

### Good examples
```python
from typing import Dict, List
```

def build_index(items: List[str]) -> Dict[str, int]:
    ...

### Bad examples
```python
def build_index(items: list[str]) -> dict[str, int]:
    ...

value = external_call()  # type: ignore
```

---

## 4. Import Order

Imports MUST follow this exact order:

1. import of builtin modules (alphabetically ordered)
2. from ... import ... of builtin modules (ordered by increasing character length of the module path between `from` and `import`)

(blank line)

3. import of third-party packages
4. from ... import ... of third-party packages

(blank line)

5. Absolute project imports only, with the following constraints:
- Imports MUST be grouped by package path.
- Groups MUST be ordered from the most distant to the closest package in the folder hierarchy.
- Each group MUST be separated by a single blank line.
- Inside each group, imports MUST be ordered by increasing number of characters (shorter paths first).
- Alphabetical order is secondary and applies only when path lengths are equal.

### Good example
```python
import os
import sys

from pathlib import Path
from datetime import datetime

import requests
import sqlalchemy

from pydantic import BaseModel
from sqlalchemy.orm import Session

from helpers.core.config import AppConfig
from helpers.core.logging import get_logger

from helpers.services.users import UserService
from helpers.services.payments import PaymentService
```

### Bad examples

#### Mixed builtin and third-party imports
```python
import os
import requests
from datetime import datetime
```

#### Wrong order: from-import before import
```python
from pathlib import Path
import pathlib
```

#### Missing blank lines between groups
```python
import os
from datetime import datetime
import requests
from pydantic import BaseModel
```

#### Project imports not grouped or ordered by distance / length
```python
from helpers.services.payments import PaymentService
from helpers.core.config import AppConfig
from helpers.services.users import UserService
```

## Import Aliases (`import ... as ...`)

- In general, `import ... as ...` MUST NOT be used.
- Import aliases are allowed only for widely established, conventional cases, such as:
  - `import gettext as _`
  - `import numpy as np`
  - `import pandas as pd`
- Aliases that hide meaning are forbidden.

### Good examples
```python
import numpy as np
import pandas as pd
import gettext as _
```

### Bad examples
```python
import wx.stc as stc
```



## from ... import ... Ordering

### Ordering of multiple `from ... import ...` statements

When multiple `from ... import ...` statements exist within the same import group,
they MUST be ordered by **increasing character length of the module path**:
the exact string between `from` and `import` (e.g. `helpers.logger`).

- Sorting key: `len(<module_path_between_from_and_import>)`, ascending (shorter first)
- Tie-breaker (only when lengths are equal): alphabetical order of the module path
- Imported names on the right side of `import` MUST NOT influence the order of statements

### Good example (module path length scale):
```python
from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel
from helpers.observables import ObservableList
```

### Bad example:
```python
from helpers.dataview import BaseDataViewListModel
from helpers.logger import logger
from helpers.observables import ObservableList
```
### Ordering inside a single `from ... import ...` statement

Imported names MUST be ordered as follows:
1. CONSTANTS (uppercase names)
2. Classes
3. Functions / methods

Each group MUST be ordered alphabetically.

## Builtin Imports with Aliases

When importing builtin modules:

- Builtin imports **without aliases** MUST be grouped together.
- Builtin imports **with aliases (`as`)** MUST be grouped separately.
- Builtin imports with aliases MUST be ordered by **increasing character length of the string between `import` and `as`**.
- These two groups MUST be separated by a single blank line.

This rule applies only to builtin modules.

### Good example
```python
import os
import sys

import numpy as np
import pandas as pd
import gettext as _
```

### Bad example
```python
import os
import gettext as _
import sys
```

## Parenthesized Multiline `from ... import (...)`

Parenthesized multiline imports MUST NOT be used for functions or methods.

If a `from ... import ...` statement would exceed the maximum line width:
- split it into multiple `from ... import ...` statements
- each resulting line MUST stay within the maximum line width
- keep the same import group ordering rules

### Good examples
```python
from .detectors import is_regex, is_sql, is_xml
from .detectors import is_base64, is_csv, is_html
```

### Bad examples
```python
from .detectors import (
    is_regex,
    is_sql,
    is_xml,
)
```


## 5. Variable Definition Order

When defining multiple variables in sequence, variables MUST be ordered by increasing number of characters in the variable name (shorter names first).

This rule applies when:
- Variables are defined consecutively
- There is no logical dependency requiring a specific order

### Good example
```python
pos = self._editor.GetCurrentPos()
text = self._editor.GetText()
```

### Bad example
```python
text = self._editor.GetText()
pos = self._editor.GetCurrentPos()
```
---

## 6. Python Classes

### Naming

- Class names MUST be clear and descriptive.
- Method names MUST be clear and descriptive.
- Function names MUST be clear and descriptive.

### wxPython event handler pattern

- In wx-based UI code, on_* methods MUST handle only UI concerns:
  - event routing
  - validation
  - user confirmation dialogs
  - gathering UI input
- The actual action MUST be implemented in a do_* method.
- do_* methods SHOULD be UI-agnostic and testable (avoid dialogs and direct widget access when possible).

### Class member order

Class members MUST be ordered as follows:

1. \_\_init\_\_
2. Magic methods (`__str__`, \_\_repr\_\_, \_\_eq\_\_, etc.)
3. Other double-underscore methods (e.g. \_\_post\_init\_\_)
4. @property
5. Private @staticmethod
6. Public @staticmethod
7. Private methods (names starting with _)
8. Public methods

---

## 7. Function and Method Size

- A function/method MUST be at most 50 lines.
- If it exceeds 50 lines, it MUST be split into smaller functions/methods with clear names.

---

## 8. Walrus Operator ( := )

- Always try to use the walrus operator when it improves clarity and avoids redundant calls.
- Do NOT use it if it reduces readability.

### Good examples
```python
if (user := get_user()) is not None:
    process_user(user)

while (line := file.readline()):
    handle_line(line)
```

### Bad examples
```python
user = get_user()
if user is not None:
    process_user(user)
```

---

## 9. Mypy & Static Analysis

- Code MUST be mypy-friendly.
- Do NOT silence errors with # type: ignore unless there is no reasonable alternative.

---

## 10. Method & API Usage

- DO NOT invent methods, attributes, or APIs that do not exist.
- Use only APIs that are part of the standard library, frameworks, or explicitly defined in the codebase.
- If unsure, do not guess.

### Bad examples
```python
user.invalidate_cache()
request.get_json_body()
```

---

## 11. General Principles

- Clarity is preferred over brevity.
- Explicit is better than implicit.
- Code is read many more times than it is written.
- Optimize for maintainability, not cleverness.
