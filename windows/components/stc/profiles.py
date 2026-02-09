from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import wx.stc

from windows.components.stc.formatters import format_base64, format_csv
from windows.components.stc.formatters import format_json, format_sql, format_xml, format_yaml

Formatter = Callable[[str], str]
Detector = Callable[[str], bool]


@dataclass(frozen=True)
class SyntaxProfile:
    id: str
    label: str
    stc_lexer: int
    keywords: Sequence[str] = ()
    formatter: Optional[Formatter] = None
    detector: Optional[Detector] = None


JSON = SyntaxProfile(
    id="json",
    label="JSON",
    stc_lexer=wx.stc.STC_LEX_JSON,
    formatter=format_json,
)
SQL = SyntaxProfile(
    id="sql",
    label="SQL",
    stc_lexer=getattr(wx.stc, "STC_LEX_SQL", wx.stc.STC_LEX_NULL),
    keywords=(
        "select",
        "from",
        "where",
        "join",
        "left",
        "right",
        "inner",
        "outer",
        "group",
        "by",
        "order",
        "limit",
        "and",
        "or",
        "as",
        "on",
    ),
    formatter=format_sql,
)
XML = SyntaxProfile(
    id="xml",
    label="XML",
    stc_lexer=wx.stc.STC_LEX_XML,
    formatter=format_xml,
)
YAML = SyntaxProfile(
    id="yaml",
    label="YAML",
    stc_lexer=getattr(wx.stc, "STC_LEX_YAML", wx.stc.STC_LEX_NULL),
    formatter=format_yaml,
)
MARKDOWN = SyntaxProfile(
    id="markdown",
    label="Markdown",
    stc_lexer=getattr(wx.stc, "STC_LEX_MARKDOWN", wx.stc.STC_LEX_NULL),
)
HTML = SyntaxProfile(
    id="html",
    label="HTML",
    stc_lexer=wx.stc.STC_LEX_HTML,
)
REGEX = SyntaxProfile(
    id="regex",
    label="Regex",
    stc_lexer=wx.stc.STC_LEX_NULL,
)
CSV = SyntaxProfile(
    id="csv",
    label="CSV/TSV",
    stc_lexer=wx.stc.STC_LEX_NULL,
    formatter=format_csv,
)
BASE64 = SyntaxProfile(
    id="base64",
    label="Base64",
    stc_lexer=wx.stc.STC_LEX_NULL,
    formatter=format_base64,
)
TEXT = SyntaxProfile(
    id="text",
    label="Plain text",
    stc_lexer=wx.stc.STC_LEX_NULL,
)