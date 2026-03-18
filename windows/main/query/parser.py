import dataclasses
import enum

from typing import Optional

import wx.stc

from structures.connection import ConnectionEngine

from windows.components.stc.autocomplete.statement_extractor import StatementExtractor


@dataclasses.dataclass
class ParsedStatement:
    text: str
    start_pos: int
    end_pos: int
    statement_index: int


class ExecutionMode(enum.Enum):
    ALL = "all"
    SELECTION = "selection"
    CURRENT = "current"


class SQLStatementParser:
    def __init__(self, engine: ConnectionEngine):
        self.engine = engine

    def parse(self, sql_text: str) -> list[ParsedStatement]:
        return [
            ParsedStatement(text=text, start_pos=start, end_pos=end, statement_index=i)
            for i, (text, start, end) in enumerate(StatementExtractor.extract_all_statements(sql_text))
        ]


class StatementSelector:
    def __init__(self, stc_editor: wx.stc.StyledTextCtrl):
        self.editor = stc_editor

    def get_execution_scope(
            self,
            statements: list[ParsedStatement]
    ) -> tuple[ExecutionMode, list[ParsedStatement]]:
        selection_start = self.editor.GetSelectionStart()
        selection_end = self.editor.GetSelectionEnd()

        if selection_start != selection_end:
            if selected_text := self.editor.GetSelectedText().strip():
                return (ExecutionMode.SELECTION, [ParsedStatement(
                    text=selected_text,
                    start_pos=selection_start,
                    end_pos=selection_end,
                    statement_index=0
                )])

        caret_pos = self.editor.GetCurrentPos()

        if current_stmt := self._find_statement_at_caret(caret_pos, statements):
            return (ExecutionMode.CURRENT, [current_stmt])

        return (ExecutionMode.ALL, statements)

    def _find_statement_at_caret(
            self,
            caret_pos: int,
            statements: list[ParsedStatement]
    ) -> Optional[ParsedStatement]:
        for stmt in statements:
            if stmt.start_pos <= caret_pos <= stmt.end_pos:
                return stmt

        # Caret is in whitespace: execute next statement
        for stmt in statements:
            if caret_pos < stmt.start_pos:
                return stmt

        # Caret after all statements: execute last
        if statements:
            return statements[-1]

        return None
