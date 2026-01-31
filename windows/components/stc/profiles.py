import ast
import base64
import json
import re

import wx.stc as stc

from .syntax import SyntaxProfile, SyntaxRegistry

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
    try :
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
    # Normalize to wrapped lines (optional). Here: just strip spaces.
    return re.sub(r"\s+", "", text)


# ---------- detectors (best-effort heuristics) ----------
_RE_BASE64 = re.compile(r"^[A-Za-z0-9+/=\s]+$")

def is_json(text: str) -> bool:
    t = text.strip()
    if not t or t[0] not in "{[":
        return False

    try:
        json.loads(t)
        return True
    except Exception:
        pass

    try:
        ast.literal_eval(text)
        return True
    except Exception:
        return False

def is_xml(text: str) -> bool:
    t = text.strip()
    return t.startswith("<") and (t.endswith(">") or "</" in t)

def is_sql(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return False
    return any(t.startswith(k) for k in ("select", "insert", "update", "delete", "with", "create", "alter", "drop"))

def is_yaml(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    # very lightweight
    return "\n" in t and ":" in t and not (t.lstrip().startswith("{") or t.startswith("---"))

def is_markdown(text: str) -> bool:
    t = text
    return any(p in t for p in ("```", "# ", "## ", "- ", "* ", "> "))

def is_html(text: str) -> bool:
    t = text.strip().lower()
    return any(tag in t for tag in ("<html", "<div", "<span", "<p", "<body", "<head"))

def is_regex(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    # heuristic: common regex tokens
    return any(ch in t for ch in (".*", "^", "$", "\\d", "\\w", "[", "]", "(", ")", "|", "{", "}"))

def is_csv(text: str) -> bool:
    # heuristic: multiple lines with consistent commas
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    counts = [ln.count(",") for ln in lines[:10]]
    return max(counts) >= 1 and len(set(counts)) <= 2

def is_base64(text: str) -> bool:
    t = text.strip()
    if len(t) < 16:
        return False
    if not _RE_BASE64.match(t):
        return False
    # try decode
    try:
        base64.b64decode(re.sub(r"\s+", "", t), validate=True)
        return True
    except Exception:
        return False


def detect_syntax_id(text: str) -> str:
    # order matters: start with most distinctive
    if is_json(text): return "json"
    if is_xml(text) and is_html(text): return "html"  # html is a kind of xml-ish
    if is_html(text): return "html"
    if is_xml(text): return "xml"
    if is_yaml(text): return "yaml"
    if is_sql(text): return "sql"
    if is_markdown(text): return "markdown"
    if is_csv(text): return "csv"
    if is_base64(text): return "base64"
    if is_regex(text): return "regex"
    return "text"


# ---------- profiles ----------
# AUTO = SyntaxProfile(id="auto", label="Auto", stc_lexer=stc.STC_LEX_NULL)

JSON = SyntaxProfile(id="json", label="JSON", stc_lexer=stc.STC_LEX_JSON, formatter=fmt_json)
SQL = SyntaxProfile(
    id="sql",
    label="SQL",
    stc_lexer=getattr(stc, "STC_LEX_SQL", stc.STC_LEX_NULL),
    keywords=("select","from","where","join","left","right","inner","outer","group","by","order","limit","and","or","as","on"),
    formatter=fmt_sql,
)
XML = SyntaxProfile(id="xml", label="XML", stc_lexer=stc.STC_LEX_XML, formatter=fmt_xml)
YAML = SyntaxProfile(id="yaml", label="YAML", stc_lexer=getattr(stc, "STC_LEX_YAML", stc.STC_LEX_NULL), formatter=fmt_yaml)
MARKDOWN = SyntaxProfile(id="markdown", label="Markdown", stc_lexer=getattr(stc, "STC_LEX_MARKDOWN", stc.STC_LEX_NULL))
HTML = SyntaxProfile(id="html", label="HTML", stc_lexer=stc.STC_LEX_HTML)
REGEX = SyntaxProfile(id="regex", label="Regex", stc_lexer=stc.STC_LEX_NULL)  # you can custom-style later
CSV = SyntaxProfile(id="csv", label="CSV/TSV", stc_lexer=stc.STC_LEX_NULL, formatter=fmt_csv)
BASE64 = SyntaxProfile(id="base64", label="Base64", stc_lexer=stc.STC_LEX_NULL, formatter=fmt_base64)
TEXT = SyntaxProfile(id="text", label="Plain text", stc_lexer=stc.STC_LEX_NULL)