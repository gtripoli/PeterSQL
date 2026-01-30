import ast
import base64
import json
import re

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
    return ("\n" in t and ":" in t and not t.lstrip().startswith("{")) or t.startswith("---")

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