import ast
import json
import re

import wx.stc

from windows.components.stc.syntax import SyntaxProfile

try:
    import sqlparse
except Exception:
    sqlparse = None

try:
    import yaml
except Exception:
    yaml = None

try:
    from xml.dom import minidom
except Exception:
    minidom = None


# ---------- formatters ----------
def fmt_json(text: str) -> str:
    try:
        obj = json.loads(text)
    except Exception:
        obj = ast.literal_eval(text)

    return json.dumps(obj, indent=2, ensure_ascii=False)


def fmt_sql(text: str) -> str:
    if sqlparse is None:
        # best-effort: no external formatter
        return text
    return sqlparse.format(text, reindent=True, keyword_case="upper")


def fmt_xml(text: str) -> str:
    if minidom is None:
        return text
    dom = minidom.parseString(text)
    return dom.toprettyxml(indent="  ")


def fmt_yaml(text: str) -> str:
    if yaml is None:
        return text
    data = yaml.safe_load(text)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def fmt_csv(text: str) -> str:
    # Minimal: trim trailing spaces, normalize newlines.
    # (A full pretty printer would need delimiter detection.)
    lines = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join(lines).strip("\n")


def fmt_base64(text: str) -> str:
    # Strip whitespace to keep raw payload.
    return re.sub(r"\s+", "", text)


# ---------- profiles ----------
# AUTO = SyntaxProfile(id="auto", label="Auto", stc_lexer=wx.stc.STC_LEX_NULL)

JSON = SyntaxProfile(id="json", label="JSON", stc_lexer=wx.stc.STC_LEX_JSON, formatter=fmt_json)
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
    formatter=fmt_sql,
)
XML = SyntaxProfile(id="xml", label="XML", stc_lexer=wx.stc.STC_LEX_XML, formatter=fmt_xml)
YAML = SyntaxProfile(id="yaml", label="YAML", stc_lexer=getattr(wx.stc, "STC_LEX_YAML", wx.stc.STC_LEX_NULL), formatter=fmt_yaml)
MARKDOWN = SyntaxProfile(id="markdown", label="Markdown", stc_lexer=getattr(wx.stc, "STC_LEX_MARKDOWN", wx.stc.STC_LEX_NULL))
HTML = SyntaxProfile(id="html", label="HTML", stc_lexer=wx.stc.STC_LEX_HTML)
REGEX = SyntaxProfile(id="regex", label="Regex", stc_lexer=wx.stc.STC_LEX_NULL)  # you can custom-style later
CSV = SyntaxProfile(id="csv", label="CSV/TSV", stc_lexer=wx.stc.STC_LEX_NULL, formatter=fmt_csv)
BASE64 = SyntaxProfile(id="base64", label="Base64", stc_lexer=wx.stc.STC_LEX_NULL, formatter=fmt_base64)
TEXT = SyntaxProfile(id="text", label="Plain text", stc_lexer=wx.stc.STC_LEX_NULL)