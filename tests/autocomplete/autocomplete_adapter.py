from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from windows.components.stc.autocomplete.auto_complete import SQLCompletionProvider
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLDataType


@dataclass(frozen=True)
class AutocompleteRequest:
    sql: str
    dialect: str
    current_table: Optional[str]
    schema: Dict[str, Any]


@dataclass(frozen=True)
class AutocompleteResponse:
    mode: str
    context: str
    prefix: Optional[str]
    suggestions: List[str]
    extras: Dict[str, Any]


def _create_mock_database(schema: Dict[str, Any], vocab: Dict[str, Any] = None) -> SQLDatabase:
    mock_db = Mock(spec=SQLDatabase)
    mock_db.name = "test_db"
    
    mock_context = Mock()
    if vocab:
        mock_context.KEYWORDS = vocab.get("keywords_all", [])
        mock_context.FUNCTIONS = vocab.get("functions_all", [])
    else:
        mock_context.KEYWORDS = []
        mock_context.FUNCTIONS = []
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
    from windows.components.stc.autocomplete.statement_extractor import StatementExtractor
    import json
    from pathlib import Path
    
    config_path = Path(__file__).parent / "test_config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    database = _create_mock_database(request.schema, config.get("vocab", {}))
    
    current_table = None
    if request.current_table:
        for table in database.tables:
            if table.name == request.current_table:
                current_table = table
                break
    
    provider = SQLCompletionProvider(
        get_database=lambda: database,
        get_current_table=lambda: current_table
    )
    
    cursor_pos = request.sql.find("|")
    if cursor_pos == -1:
        cursor_pos = len(request.sql)
    
    text = request.sql.replace("|", "")
    
    from windows.components.stc.autocomplete.dot_completion_handler import DotCompletionHandler
    from windows.components.stc.autocomplete.sql_context import SQLContext
    
    extractor = StatementExtractor()
    statement, relative_pos = extractor.extract_current_statement(text, cursor_pos)
    
    dot_handler = DotCompletionHandler(database)
    is_dot = dot_handler.is_dot_completion(statement, relative_pos)
    
    if is_dot:
        sql_context = SQLContext.DOT_COMPLETION
    else:
        detector = ContextDetector()
        sql_context, scope, prefix = detector.detect(statement, relative_pos, database)
    
    result = provider.get(text=text, pos=cursor_pos)
    
    suggestions = [item.name for item in result.items]
    
    if sql_context.name == "DOT_COMPLETION":
        mode = "DOT"
    elif result.prefix:
        mode = "PREFIX"
    else:
        mode = "CONTEXT"
    
    return AutocompleteResponse(
        mode=mode,
        context=sql_context.name,
        prefix=result.prefix if result.prefix else None,
        suggestions=suggestions,
        extras={}
    )
