import json
from dataclasses import dataclass
from typing import Any
from typing import Optional
from unittest.mock import Mock

import yaml

from constants import WORKDIR
from structures.engines.database import SQLColumn
from structures.engines.database import SQLDatabase
from structures.engines.database import SQLDataType
from structures.engines.database import SQLTable
from windows.components.stc.autocomplete.auto_complete import SQLCompletionProvider
from windows.components.stc.autocomplete.context_detector import ContextDetector
from windows.components.stc.autocomplete.dot_completion_handler import (
    DotCompletionHandler,
)
from windows.components.stc.autocomplete.sql_context import SQLContext
from windows.components.stc.autocomplete.statement_extractor import StatementExtractor

SUPPORTED_ENGINE_VERSIONS: dict[str, list[str]] = {
    "mysql": ["8", "9"],
    "mariadb": ["5", "10", "11", "12"],
    "postgresql": ["15", "16", "17", "18"],
    "sqlite": ["3"],
}

AVAILABLE_ENGINES: list[str] = list(SUPPORTED_ENGINE_VERSIONS.keys())


@dataclass(frozen=True)
class AutocompleteRequest:
    sql: str
    dialect: str
    current_table: Optional[str]
    schema: dict[str, Any]
    engine: str = "mysql"
    engine_version: Optional[str] = None


@dataclass(frozen=True)
class AutocompleteResponse:
    mode: str
    context: str
    prefix: Optional[str]
    suggestions: list[str]
    extras: dict[str, Any]


def _load_legacy_vocab() -> dict[str, list[str]]:
    config_path = WORKDIR / "tests" / "autocomplete" / "test_config.json"
    if not config_path.exists():
        return {"functions": [], "keywords": []}

    with open(config_path, encoding="utf-8") as file_handle:
        config = json.load(file_handle)

    vocab = config.get("vocab", {})
    return {
        "functions": vocab.get("functions_all", []),
        "keywords": vocab.get("keywords_all", []),
    }


def _resolve_engine_version(engine: str, requested_version: Optional[str]) -> str:
    versions = SUPPORTED_ENGINE_VERSIONS.get(engine, [])
    if not versions:
        return ""

    if requested_version and requested_version in versions:
        return requested_version

    return versions[0]


def _load_yaml(path: Any) -> dict[str, Any]:
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle)

    if not isinstance(data, dict):
        return {}

    return data


def _merge_spec_lists(
    base_items: list[str], add_items: list[str], remove_items: list[str]
) -> list[str]:
    removed_values = {item.upper() for item in remove_items}
    merged = [item for item in base_items if item.upper() not in removed_values]

    existing_values = {item.upper() for item in merged}
    for item in add_items:
        if item.upper() not in existing_values:
            merged.append(item)
            existing_values.add(item.upper())

    return merged


def _extract_names(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []

    names: list[str] = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
            continue
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str):
                names.append(name)
    return names


def _load_engine_vocab(
    engine: str, engine_version: Optional[str]
) -> dict[str, list[str]]:
    global_spec_path = WORKDIR / "structures" / "engines" / "specification.yaml"
    engine_spec_path = (
        WORKDIR / "structures" / "engines" / engine / "specification.yaml"
    )

    global_spec = _load_yaml(global_spec_path)
    engine_spec = _load_yaml(engine_spec_path)

    global_common = (
        global_spec.get("common", {})
        if isinstance(global_spec.get("common", {}), dict)
        else {}
    )
    engine_common = (
        engine_spec.get("common", {})
        if isinstance(engine_spec.get("common", {}), dict)
        else {}
    )

    keywords = _extract_names(global_common.get("keywords", []))
    functions = _extract_names(global_common.get("functions", []))

    keywords = _merge_spec_lists(
        keywords,
        _extract_names(engine_common.get("keywords", [])),
        [],
    )
    functions = _merge_spec_lists(
        functions,
        _extract_names(engine_common.get("functions", [])),
        [],
    )

    selected_version = _resolve_engine_version(engine, engine_version)
    versions_map = (
        engine_spec.get("versions", {})
        if isinstance(engine_spec.get("versions", {}), dict)
        else {}
    )
    version_spec = (
        versions_map.get(selected_version, {})
        if isinstance(versions_map.get(selected_version, {}), dict)
        else {}
    )

    keywords = _merge_spec_lists(
        keywords,
        [],
        _extract_names(version_spec.get("keywords_remove", [])),
    )
    functions = _merge_spec_lists(
        functions,
        [],
        _extract_names(version_spec.get("functions_remove", [])),
    )

    return {"functions": functions, "keywords": keywords}


def _select_vocab(request: AutocompleteRequest) -> dict[str, list[str]]:
    if request.dialect == "generic":
        return _load_legacy_vocab()

    if request.engine not in AVAILABLE_ENGINES:
        return _load_legacy_vocab()

    return _load_engine_vocab(request.engine, request.engine_version)


def _create_mock_database(
    schema: dict[str, Any], vocab: dict[str, list[str]]
) -> SQLDatabase:
    mock_database = Mock(spec=SQLDatabase)
    mock_database.name = "test_db"

    mock_context = Mock()
    mock_context.KEYWORDS = vocab.get("keywords", [])
    mock_context.FUNCTIONS = vocab.get("functions", [])
    mock_database.context = mock_context

    tables: list[SQLTable] = []
    for table_data in schema.get("tables", []):
        mock_table = Mock(spec=SQLTable)
        mock_table.name = table_data["name"]
        mock_table.database = mock_database

        columns: list[SQLColumn] = []
        for column_data in table_data.get("columns", []):
            mock_column = Mock(spec=SQLColumn)
            mock_column.name = column_data["name"]
            mock_column.datatype = Mock(spec=SQLDataType)
            mock_column.table = mock_table
            columns.append(mock_column)

        mock_table.columns = columns
        tables.append(mock_table)

    mock_database.tables = tables
    return mock_database


def _resolve_current_table(
    database: SQLDatabase, current_table_name: Optional[str]
) -> Optional[SQLTable]:
    if not current_table_name:
        return None

    for table in database.tables:
        if table.name == current_table_name:
            return table

    return None


def get_suggestions(request: AutocompleteRequest) -> AutocompleteResponse:
    vocab = _select_vocab(request)
    database = _create_mock_database(request.schema, vocab)
    current_table = _resolve_current_table(database, request.current_table)

    provider = SQLCompletionProvider(
        get_database=lambda: database,
        get_current_table=lambda: current_table,
    )

    cursor_position = request.sql.find("|")
    if cursor_position == -1:
        cursor_position = len(request.sql)

    text = request.sql.replace("|", "")

    extractor = StatementExtractor()
    statement, relative_position = extractor.extract_current_statement(
        text, cursor_position
    )

    detector = ContextDetector()
    sql_context, scope, _prefix = detector.detect(
        statement, relative_position, database
    )

    dot_handler = DotCompletionHandler(database, scope)
    if dot_handler.is_dot_completion(statement, relative_position):
        sql_context = SQLContext.DOT_COMPLETION

    completion_result = provider.get(text=text, pos=cursor_position)
    if completion_result is None:
        suggestions: list[str] = []
        completion_prefix: str = ""
    else:
        suggestions = [item.name for item in completion_result.items]
        completion_prefix = completion_result.prefix

    if sql_context.name == "DOT_COMPLETION":
        mode = "DOT"
    elif sql_context.name == "EMPTY":
        mode = "EMPTY"
    elif sql_context.name == "JOIN_AFTER_TABLE":
        mode = "AFTER_JOIN_TABLE"
    elif sql_context.name in {
        "JOIN_ON_AFTER_OPERATOR",
        "WHERE_AFTER_OPERATOR",
        "HAVING_AFTER_OPERATOR",
    }:
        mode = "AFTER_OPERATOR"
    elif sql_context.name in {
        "JOIN_ON_AFTER_EXPRESSION",
        "WHERE_AFTER_EXPRESSION",
        "HAVING_AFTER_EXPRESSION",
    }:
        mode = "AFTER_EXPRESSION"
    elif completion_prefix:
        mode = "PREFIX"
    else:
        mode = "CONTEXT"

    return AutocompleteResponse(
        mode=mode,
        context=sql_context.name,
        prefix=completion_prefix or None,
        suggestions=suggestions,
        extras={},
    )
