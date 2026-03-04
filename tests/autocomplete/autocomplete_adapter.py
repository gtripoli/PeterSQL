from __future__ import annotations

import json
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from constants import WORKDIR
from windows.components.stc.autocomplete.auto_complete import SQLCompletionProvider
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLDataType


def _get_engine_names() -> list[str]:
    """Get list of engine names that have functions.yaml."""
    return ["mysql", "postgresql", "mariadb", "sqlite"]


AVAILABLE_ENGINES = _get_engine_names()


def _load_functions_from_yaml(engine: str) -> list[str]:
    """Load function names from engine's functions.yaml."""
    yaml_path = WORKDIR / "structures" / "engines" / engine / "functions.yaml"
    if not yaml_path.exists():
        return []

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    versions = data.get("versions", [])
    if versions:
        functions = versions[0].get("functions", [])
    else:
        functions = data.get("functions", [])

    return [func["name"] for func in functions]


def _load_keywords_from_config() -> list[str]:
    """Load generic SQL keywords from test_config.json."""
    config_path = WORKDIR / "tests" / "autocomplete" / "test_config.json"
    if not config_path.exists():
        return []

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return config.get("vocab", {}).get("keywords_all", [])


def _load_functions_from_config() -> list[str]:
    """Load generic SQL functions from test_config.json."""
    config_path = WORKDIR / "tests" / "autocomplete" / "test_config.json"
    if not config_path.exists():
        return []

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return config.get("vocab", {}).get("functions_all", [])


ENGINE_FUNCTIONS: Dict[str, list[str]] = {
    engine: _load_functions_from_config() for engine in AVAILABLE_ENGINES
}
ENGINE_KEYWORDS: Dict[str, list[str]] = {
    engine: _load_keywords_from_config() for engine in AVAILABLE_ENGINES
}


@dataclass(frozen=True)
class AutocompleteRequest:
    sql: str
    dialect: str
    current_table: Optional[str]
    schema: Dict[str, Any]
    engine: str = "generic"


@dataclass(frozen=True)
class AutocompleteResponse:
    mode: str
    context: str
    prefix: Optional[str]
    suggestions: List[str]
    extras: Dict[str, Any]


def _create_mock_database(
    schema: Dict[str, Any], engine: str = "generic"
) -> SQLDatabase:
    mock_db = Mock(spec=SQLDatabase)
    mock_db.name = "test_db"

    mock_context = Mock()
    mock_context.KEYWORDS = ENGINE_KEYWORDS.get(engine, [])
    mock_context.FUNCTIONS = ENGINE_FUNCTIONS.get(engine, [])
    mock_db.context = mock_context

    tables = []
    for table_data in schema.get("tables", []):
        mock_table = Mock(spec=SQLTable)
        mock_table.name = table_data["name"]
        mock_table.database = mock_db

        columns = []
        for col_data in table_data.get("columns", []):
            mock_col = Mock(spec=SQLColumn)
            mock_col.name = col_data["name"]
            mock_col.datatype = Mock(spec=SQLDataType)
            mock_col.table = mock_table
            columns.append(mock_col)

        mock_table.columns = columns
        tables.append(mock_table)

    mock_db.tables = tables
    return mock_db


def get_suggestions(request: AutocompleteRequest) -> AutocompleteResponse:
    from windows.components.stc.autocomplete.context_detector import ContextDetector
    from windows.components.stc.autocomplete.statement_extractor import (
        StatementExtractor,
    )

    engine = request.engine if request.engine in AVAILABLE_ENGINES else "mysql"
    database = _create_mock_database(request.schema, engine)

    current_table = None
    if request.current_table:
        for table in database.tables:
            if table.name == request.current_table:
                current_table = table
                break

    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: current_table
    )

    cursor_pos = request.sql.find("|")
    if cursor_pos == -1:
        cursor_pos = len(request.sql)

    text = request.sql.replace("|", "")

    from windows.components.stc.autocomplete.dot_completion_handler import (
        DotCompletionHandler,
    )
    from windows.components.stc.autocomplete.sql_context import SQLContext

    extractor = StatementExtractor()
    statement, relative_pos = extractor.extract_current_statement(text, cursor_pos)

    detector = ContextDetector()
    sql_context, scope, prefix = detector.detect(statement, relative_pos, database)

    dot_handler = DotCompletionHandler(database, scope)
    is_dot = dot_handler.is_dot_completion(statement, relative_pos)

    if is_dot:
        sql_context = SQLContext.DOT_COMPLETION

    result = provider.get(text=text, pos=cursor_pos)

    suggestions = [item.name for item in result.items]

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
    elif result.prefix:
        mode = "PREFIX"
    else:
        mode = "CONTEXT"

    return AutocompleteResponse(
        mode=mode,
        context=sql_context.name,
        prefix=result.prefix if result.prefix else None,
        suggestions=suggestions,
        extras={},
    )
