# Code Style Guidelines (v1.2)

These rules define the expected coding style for this project.
They apply to all contributors, including humans, AI-assisted tools, and automated systems.
They are mandatory unless explicitly stated otherwise.

---

## Design Principles

#### These principles explain why the rules exist. They protect consistency over time.

- Determinism over preference  
  A rule must always produce the same result. Subjective rules lead to debates and inconsistency.

- Visual structure matters  
  Code is scanned more often than it is read. Structure reduces cognitive load.

- Automation-friendly, human-verifiable  
  Rules must be trivial to apply mechanically and easy for a human to verify.

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

#### Good examples

```python
# Avoid caching: data changes on every request.
```

#### Bad examples

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

#### Good examples

```python
editor = get_editor()
request_params = parse_params(request)
self.editor = editor
self.request_params = request_params
```

#### Bad examples

```python
ed = get_editor()
par = parse_params(request)
self.ed = ed
self.par = par
```

---

## 3. Python Typing

This project targets Python 3.14 and uses PEP 585 generics for standard collections.

- Use built-in generic containers: `list[T]`, `dict[K, V]`, `set[T]`, `tuple[...]`.
- Do NOT use deprecated `typing` aliases for standard collections (e.g. `typing.List`, `typing.Dict`, `typing.Set`,
  `typing.Tuple`).
- Keep `typing.Optional[T]` for optional types (do NOT use `T | None`).
- Prefer explicit and accurate type hints.
- With mypy, avoid using # type: ignore whenever possible.
- Prefer type hints instead of comments.

#### Good examples

```python
from typing import Optional


def build_index(items: list[str]) -> dict[str, int]:
    ...


def find_user(users: list["User"]) -> Optional["User"]:
    ...
```

#### Bad examples

```python
from typing import Dict, List, Optional


def build_index(items: List[str]) -> Dict[str, int]:
    ...
```

```python
def find_user(users: list["User"]) -> "User | None":
    ...
```

```python
value = external_call()  # type: ignore

```

### Forward References

- Prefer string-based forward references for types when needed (e.g. `"MyType"`).
- `from __future__ import annotations` MUST NOT be used.
- `typing.TYPE_CHECKING` MUST NOT be used in normal code.
- `TYPE_CHECKING` is allowed only as a last resort to break unavoidable circular imports, and MUST include a clear
  inline reason comment.

#### Good examples

```python
def set_user(user: "User") -> None:
    ...
```

```python
from typing import Optional


class Node:
    def __init__(self, parent: Optional["Node"] = None) -> None:
        self.parent = parent
```

#### Bad examples

```python
from __future__ import annotations
```

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pkg.heavy import HeavyType
```

#### Allowed (last resort)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pkg.heavy import HeavyType  # TYPE_CHECKING: unavoidable circular import
```

## 4. Import Rules

### Submodules vs symbols (`from ... import ...`)

- `from ... import ...` MUST be used only to import **symbols** (constants, classes, functions, variables).
- `from ... import ...` MUST NOT be used to import **submodules/packages**.
- Submodules/packages MUST be imported using `import package.submodule`.
- If the imported name is intended to be used as a module namespace (e.g. `stc.SomeClass`), it MUST be imported with
  `import ...`, not `from ... import ...`.

#### Good examples

```python
import wx.stc

from datetime import datetime, timezone

from wx.stc import StyledTextCtrl

from project.package import MyClass, my_function
```

#### Bad examples

```python
from wx import stc
```

### Import Orders

Imports MUST follow this exact order:

1. import of builtin modules (alphabetically ordered)
2. from ... import ... of builtin modules (ordered by increasing character length of the module path between `from` and
   `import`)

(blank line)

3. import of third-party packages
4. from ... import ... of third-party packages **(symbols only; never submodules)**

(blank line)

5. Absolute project imports only, with the following constraints:

- Imports MUST be grouped by package path.
- Groups MUST be ordered from the most distant to the closest package in the folder hierarchy.
- Each group MUST be separated by a single blank line.
- Inside each group, imports MUST be ordered by increasing number of characters (shorter paths first).
- Alphabetical order is secondary and applies only when path lengths are equal.

#### Good example

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

#### Bad examples

###### Mixed builtin and third-party imports

```python
import os
import requests
from datetime import datetime
```

###### Wrong order: from-import before import

```python
from pathlib import Path
import pathlib
```

###### Missing blank lines between groups

```python
import os
from datetime import datetime
import requests
from pydantic import BaseModel
```

###### Project imports not grouped or ordered by distance / length

```python
from helpers.services.payments import PaymentService
from helpers.core.config import AppConfig
from helpers.services.users import UserService
```

### Ordering of multiple `from ... import ...` statements

When multiple `from ... import ...` statements exist within the same import group,
they MUST be ordered by **increasing character length of the module path**:
the exact string between `from` and `import` (e.g. `helpers.logger`).

- Sorting key: `len(<module_path_between_from_and_import>)`, ascending (shorter first)
- Tie-breaker (only when lengths are equal): alphabetical order of the module path
- Imported names on the right side of `import` MUST NOT influence the order of statements

#### Good example (module path length scale):

```python
from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel
from helpers.observables import ObservableList
```

#### Bad example:

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

### Import Aliases (`import ... as ...`)

- In general, `import ... as ...` MUST NOT be used.
- Import aliases are allowed only for widely established, conventional cases, such as:
    - `import gettext as _`
    - `import numpy as np`
    - `import pandas as pd`
- Aliases that hide meaning are forbidden.

#### Good examples

```python
import numpy as np
import pandas as pd
import gettext as _
```

#### Bad examples

```python
import wx.stc as stc
```

### Builtin Imports with Aliases

When importing builtin modules:

- Builtin imports **without aliases** MUST be grouped together.
- Builtin imports **with aliases (`as`)** MUST be grouped separately.
- Builtin imports with aliases MUST be ordered by **increasing character length of the string between `import` and `as`
  **.
- These two groups MUST be separated by a single blank line.

This rule applies only to builtin modules.

#### Good example

```python
import os
import sys

import numpy as np
import pandas as pd
import gettext as _
```

#### Bad example

```python
import os
import gettext as _
import sys
```

### Import Line Splitting (No Parentheses, No Repetition)

When importing multiple symbols from the same module:

- Parenthesized multiline `from ... import (...)` MUST NOT be used for functions or methods.
- Imports MUST NOT be split into one line per symbol.
- Prefer a single `from ... import ...` line whenever possible.
- If a `from ... import ...` statement would exceed the maximum line width:
    - split it into multiple `from ... import ...` statements
    - each resulting line MUST stay within the maximum line width
    - each line MUST import as many symbols as possible
    - keep the same import group ordering rules

### Good examples

```python
from windows.components.stc.detectors import detect_syntax_id, is_base64, is_csv
from windows.components.stc.detectors import is_html, is_json, is_markdown
from windows.components.stc.detectors import is_regex, is_sql, is_xml, is_yaml
```

```python
from .detectors import is_regex, is_sql, is_xml
from .detectors import is_base64, is_csv, is_html
```

### Bad examples

```python
from windows.components.stc.detectors import is_html
from windows.components.stc.detectors import is_json
from windows.components.stc.detectors import is_markdown
from windows.components.stc.detectors import is_regex
from windows.components.stc.detectors import is_sql
from windows.components.stc.detectors import is_xml
from windows.components.stc.detectors import is_yaml
```

```python
from .detectors import (
    is_regex,
    is_sql,
    is_xml,
)
```

---

## 5. Variable Definition Order

When defining multiple variables in sequence, variables MUST be ordered by increasing number of characters in the
variable name (shorter names first).

This rule applies when:

- Variables are defined consecutively
- There is no logical dependency requiring a specific order

#### Good example

```python
pos = self._editor.GetCurrentPos()
text = self._editor.GetText()
```

#### Bad example

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

1. `__init__`
2. Magic methods (`__str__`, `__repr__`, `__eq__`, etc.)
3. Custom and other double-underscore methods (e.g. `__post_init__`)
4. Private `@property`
5. Public `@property`
6. Private `@staticmethod`
7. Public `@staticmethod`
8. Private methods (names starting with `_`)
9. Public methods

### Method Ordering by Usage and Name

Within each visibility group (private or public), methods MUST be ordered as follows:

1. **By usage**: a method MUST be defined before any other method that uses it.
2. **Alphabetically**: if multiple methods are independent, they MUST be ordered alphabetically.

This rule applies independently to:

- private methods (names starting with `_`)
- public methods

#### Good example

```python
class Example:
    def _normalize(self, value: str) -> str:
        return value.strip().lower()

    def _validate(self, value: str) -> bool:
        normalized = self._normalize(value)
        return bool(normalized)

    def process(self, value: str) -> bool:
        return self._validate(value)
```

#### Bad example

```python
class Example:
    def _validate(self, value: str) -> bool:
        normalized = self._normalize(value)
        return bool(normalized)

    def _normalize(self, value: str) -> str:
        return value.strip().lower()
```

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
- Do NOT silence errors with `# type: ignore` unless there is no reasonable alternative.
- When `# type: ignore` is used, the reason MUST be explained clearly in an inline comment.

#### Good Example

```python
value = external_call()  # type: ignore[attr-defined]  # third-party lib exposes this dynamically
```

#### Bad Example

```python
value = external_call()  # type: ignore
```

---
