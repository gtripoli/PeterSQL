from dataclasses import dataclass
from enum import Enum


class CompletionItemType(Enum):
    KEYWORD = "keyword"
    FUNCTION = "function"
    TABLE = "table"
    COLUMN = "column"


@dataclass(frozen=True, slots=True)
class CompletionItem:
    name: str
    item_type: CompletionItemType
    description: str = ""


@dataclass(frozen=True, slots=True)
class CompletionResult:
    prefix: str
    prefix_length: int
    items: tuple[CompletionItem, ...]
