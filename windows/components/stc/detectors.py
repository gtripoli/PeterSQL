import ast
import base64
import json
import re

_BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/=\s]+$")

_SQL_KEYWORDS = ("select", "insert", "update", "delete", "with", "create", "alter", "drop")
_HTML_TAGS = ("<html", "<div", "<span", "<p", "<body", "<head")
_MARKDOWN_MARKERS = ("```", "# ", "## ", "- ", "* ", "> ")
_REGEX_TOKENS = (".*", "^", "$", "\\d", "\\w", "[", "]", "(", ")", "|", "{", "}")


def is_base64(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 16:
        return False
    if not _BASE64_PATTERN.match(stripped):
        return False
    try:
        base64.b64decode(re.sub(r"\s+", "", stripped), validate=True)
        return True
    except Exception:
        return False


def is_csv(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    counts = [line.count(",") for line in lines[:10]]
    return max(counts) >= 1 and len(set(counts)) <= 2


def is_html(text: str) -> bool:
    stripped = text.strip().lower()
    return any(tag in stripped for tag in _HTML_TAGS)


def is_json(text: str) -> bool:
    stripped = text.strip()
    if not stripped or stripped[0] not in "{[":
        return False
    try:
        json.loads(stripped)
        return True
    except Exception:
        pass
    try:
        ast.literal_eval(text)
        return True
    except Exception:
        return False


def is_markdown(text: str) -> bool:
    return any(marker in text for marker in _MARKDOWN_MARKERS)


def is_regex(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return any(token in stripped for token in _REGEX_TOKENS)


def is_sql(text: str) -> bool:
    stripped = text.strip().lower()
    if not stripped:
        return False
    return any(stripped.startswith(keyword) for keyword in _SQL_KEYWORDS)


def is_xml(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("<") and (stripped.endswith(">") or "</" in stripped)


def is_yaml(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return ("\n" in stripped and ":" in stripped and not stripped.lstrip().startswith("{")) or stripped.startswith("---")


def detect_syntax_id(text: str) -> str:
    if is_json(text):
        return "json"
    if is_xml(text) and is_html(text):
        return "html"
    if is_html(text):
        return "html"
    if is_xml(text):
        return "xml"
    if is_yaml(text):
        return "yaml"
    if is_sql(text):
        return "sql"
    if is_markdown(text):
        return "markdown"
    if is_csv(text):
        return "csv"
    if is_base64(text):
        return "base64"
    if is_regex(text):
        return "regex"
    return "text"