import ast
import json
import re

try:
    import sqlparse
except ImportError:
    sqlparse = None

try:
    import yaml
except ImportError:
    yaml = None

try:
    from xml.dom import minidom
except ImportError:
    minidom = None


def format_json(text: str) -> str:
    try:
        obj = json.loads(text)
    except Exception:
        obj = ast.literal_eval(text)
    return json.dumps(obj, indent=2, ensure_ascii=False)


def format_sql(text: str) -> str:
    if sqlparse is None:
        return text
    return sqlparse.format(text, reindent=True, keyword_case="upper")


def format_xml(text: str) -> str:
    if minidom is None:
        return text
    dom = minidom.parseString(text)
    return dom.toprettyxml(indent="  ")


def format_yaml(text: str) -> str:
    if yaml is None:
        return text
    data = yaml.safe_load(text)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def format_csv(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip("\n")


def format_base64(text: str) -> str:
    return re.sub(r"\s+", "", text)