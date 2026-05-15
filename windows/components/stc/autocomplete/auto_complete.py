from typing import Callable, Optional

import wx
import wx.stc

from helpers.logger import logger

from structures.engines.database import SQLDatabase, SQLTable

from windows.components.stc.autocomplete.autocomplete_popup import AutoCompletePopup
from windows.components.stc.autocomplete.completion_types import (
    CompletionItem,
    CompletionItemType,
    CompletionResult,
)
from windows.components.stc.autocomplete.context_detector import ContextDetector
from windows.components.stc.autocomplete.query_scope import TableReference
from windows.components.stc.autocomplete.sql_context import SQLContext
from windows.components.stc.autocomplete.dot_completion_handler import (
    DotCompletionHandler,
)
from windows.components.stc.autocomplete.statement_extractor import StatementExtractor
from windows.components.stc.autocomplete.suggestion_builder import SuggestionBuilder

from windows.state import CURRENT_SESSION


class SQLCompletionProvider:
    def __init__(
            self,
            get_database: Callable[[], Optional[SQLDatabase]],
            get_current_table: Optional[Callable[[], Optional[SQLTable]]] = None,
            *,
            is_filter_editor: bool = False,
    ) -> None:
        self._get_database = get_database
        self._get_current_table = get_current_table or (lambda: None)
        self._is_filter_editor = is_filter_editor
        self._cached_database_id: Optional[int] = None
        self._cached_dialect: Optional[str] = None

        self._context_detector: Optional[ContextDetector] = None
        self._dot_handler: Optional[DotCompletionHandler] = None
        self._statement_extractor = StatementExtractor()

    def _get_current_dialect(self) -> Optional[str]:
        if session := CURRENT_SESSION.get_value():
            return session.engine.value.dialect

    def get(
            self,
            text: str,
            pos: int,
            separator: Optional[str] = None,
    ) -> Optional[CompletionResult]:
        try:
            database = self._get_database()
            if database is None:
                return None

            self._update_cache(database=database)

            safe_pos = self._clamp_position(pos=pos, text=text)

            statement, relative_pos = (
                self._statement_extractor.extract_current_statement(
                    text,
                    safe_pos,
                    separator=separator,
                )
            )

            if not self._context_detector:
                return None

            context, scope, prefix = self._context_detector.detect(
                statement, relative_pos, database
            )
            scope.current_table = self._get_current_table()

            if self._is_filter_editor:
                context = SQLContext.WHERE_CLAUSE
                if scope.current_table and not scope.from_tables:
                    scope.from_tables = [TableReference(
                        name=scope.current_table.name,
                        alias=None,
                        table=scope.current_table,
                    )]

            if self._dot_handler:
                self._dot_handler.refresh(database, scope)
                if self._dot_handler.is_dot_completion(statement, relative_pos):
                    items, prefix = self._dot_handler.get_completions(
                        statement, relative_pos
                    )
                    if items is not None:
                        return CompletionResult(
                            items=tuple(items),
                            prefix=prefix or "",
                            prefix_length=len(prefix) if prefix else 0,
                        )

            builder = SuggestionBuilder(database, scope.current_table)
            items = builder.build(context, scope, prefix, statement, relative_pos)

            return CompletionResult(
                items=tuple(items), prefix=prefix, prefix_length=len(prefix)
            )
        except Exception as ex:
            logger.error(ex, exc_info=True)
            return None

    @staticmethod
    def _clamp_position(*, pos: int, text: str) -> int:
        if pos < 0:
            return 0
        if pos > len(text):
            return len(text)
        return pos

    def _update_cache(self, *, database: SQLDatabase) -> None:
        database_id = id(database)
        dialect = self._get_current_dialect()

        if (
            self._cached_database_id != database_id
            or self._cached_dialect != dialect
        ):
            self._cached_database_id = database_id
            self._cached_dialect = dialect

            self._context_detector = ContextDetector(dialect)
            self._dot_handler = DotCompletionHandler(database, None)


class SQLAutoCompleteController:
    def __init__(
            self,
            editor: wx.stc.StyledTextCtrl,
            provider: SQLCompletionProvider,
            *,
            settings: object,
            theme_loader: Optional[object] = None,
            debounce_ms: int = 80,
            is_enabled: bool = True,
            min_prefix_length: int = 1,
    ) -> None:
        self._editor = editor
        self._provider = provider
        self._settings = settings
        self._theme_loader = theme_loader

        self._debounce_ms = settings.get_value("editor", "autocomplete", "debounce_ms", default=debounce_ms)
        self._min_prefix_length = settings.get_value("editor", "autocomplete", "min_prefix_length", default=min_prefix_length)
        self._add_space_after_completion = settings.get_value("editor", "autocomplete", "add_space_after_completion", default=True)

        self._is_enabled = is_enabled

        self._is_showing = False
        self._pending_call: Optional[wx.CallLater] = None
        self._popup: Optional[AutoCompletePopup] = None
        self._current_result: Optional[CompletionResult] = None

        self._editor.Bind(wx.stc.EVT_STC_CHARADDED, self._on_char_added)
        self._editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self._editor.Bind(wx.EVT_KILL_FOCUS, self._on_editor_kill_focus)

        top_level = wx.GetTopLevelParent(editor)
        top_level.Bind(wx.EVT_MOVE, self._on_parent_move)

    def set_enabled(self, is_enabled: bool) -> None:
        self._is_enabled = is_enabled
        if not is_enabled:
            self._cancel_pending()
            self._hide_popup()

    def get_effective_separator(self) -> str:
        user_override = ";"
        if settings := getattr(self, "_settings", None):
            user_override = settings.get_value(
                "editor",
                "statement_separator",
                default=";",
            )

        session = CURRENT_SESSION.get_value()
        default_separator = ";"
        if session and hasattr(session, "context"):
            default_separator = session.context.DEFAULT_STATEMENT_SEPARATOR

        return StatementExtractor.normalize_separator(
            user_override,
            default=default_separator,
        )

    def show(self, *, force: bool) -> None:
        if not self._is_enabled:
            return
        if self._is_showing:
            return

        self._is_showing = True
        try:
            pos = self._editor.GetCurrentPos()
            text = self._editor.GetText()

            result = self._provider.get(
                pos=pos,
                text=text,
                separator=self.get_effective_separator(),
            )

            if result is None:
                self._hide_popup()
                return

            if not result.items:
                self._hide_popup()
                return

            if not force and result.prefix_length < self._min_prefix_length:
                self._hide_popup()
                return

            self._current_result = result
            items = self._unique_items(items=result.items)
            self._show_popup(items)
        except Exception as ex:
            logger.error(f"Error in show(): {ex}", exc_info=True)
        finally:
            self._is_showing = False

    def _show_popup(self, items: list[CompletionItem]) -> None:
        if not self._popup:
            self._popup = AutoCompletePopup(
                self._editor, settings=self._settings, theme_loader=self._theme_loader
            )
            self._popup.set_on_item_selected(self._on_item_completed)

        caret_pos = self._editor.GetCurrentPos()
        point = self._editor.PointFromPosition(caret_pos)
        screen_point = self._editor.ClientToScreen(point)

        line_height = self._editor.TextHeight(self._editor.GetCurrentLine())
        popup_position = wx.Point(screen_point.x, screen_point.y + line_height)

        self._popup.show_items(items, popup_position)

    def _hide_popup(self) -> None:
        if self._popup and self._popup.IsShown():
            self._popup.Hide()

    def _on_item_completed(self, item: CompletionItem) -> None:
        if not self._current_result:
            return

        current_pos = self._editor.GetCurrentPos()
        start_pos, end_pos = self._get_identifier_bounds_around_cursor(current_pos)

        if start_pos == end_pos:
            start_pos = max(0, current_pos - self._current_result.prefix_length)
            end_pos = current_pos

        self._editor.SetSelection(start_pos, end_pos)

        should_add_space = (
                self._add_space_after_completion
                and item.item_type == CompletionItemType.KEYWORD
        )
        completion_text = item.name + " " if should_add_space else item.name
        self._editor.ReplaceSelection(completion_text)

        self._current_result = None
        self._hide_popup()

        if should_add_space:
            trigger_keywords = [
                "SELECT",
                "FROM",
                "JOIN",
                "UPDATE",
                "INTO",
                "WHERE",
                "AND",
                "OR",
            ]
            if item.name.upper() in trigger_keywords:
                wx.CallAfter(lambda: self._schedule_show(force=False))

    @staticmethod
    def _is_identifier_char(character: str) -> bool:
        return character.isalnum() or character == "_"

    def _get_identifier_bounds_around_cursor(self, cursor_pos: int) -> tuple[int, int]:
        text = self._editor.GetText()
        text_length = len(text)

        start_pos = min(max(cursor_pos, 0), text_length)
        end_pos = start_pos

        while start_pos > 0 and self._is_identifier_char(text[start_pos - 1]):
            start_pos -= 1

        while end_pos < text_length and self._is_identifier_char(text[end_pos]):
            end_pos += 1

        return start_pos, end_pos

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        if not self._is_enabled:
            event.Skip()
            return

        key_code = event.GetKeyCode()

        if key_code == wx.WXK_SPACE:
            if self._popup and self._popup.IsShown():
                self._cancel_pending()
                self._hide_popup()
            if not event.ControlDown():
                event.Skip()
                return

        if event.ControlDown() and key_code == wx.WXK_SPACE:
            self._cancel_pending()
            self.show(force=True)
            return

        if key_code == wx.WXK_TAB and self._popup and self._popup.IsShown():
            self._cancel_pending()
            selected_item = self._popup.get_selected_item()
            if selected_item:
                self._on_item_completed(selected_item)
            return

        if key_code == wx.WXK_ESCAPE and self._popup and self._popup.IsShown():
            self._cancel_pending()
            self._hide_popup()
            return

        if key_code == wx.WXK_BACK and self._popup and self._popup.IsShown():
            event.Skip()
            wx.CallAfter(self._schedule_show, force=False)
            return

        if key_code == wx.WXK_RETURN and self._popup and self._popup.IsShown():
            self._cancel_pending()
            selected_item = self._popup.get_selected_item()
            if selected_item:
                self._on_item_completed(selected_item)
            return

        if key_code == wx.WXK_UP and self._popup and self._popup.IsShown():
            self._popup.select_prev()
            return

        if key_code == wx.WXK_DOWN and self._popup and self._popup.IsShown():
            self._popup.select_next()
            return

        if key_code == wx.WXK_PAGEUP and self._popup and self._popup.IsShown():
            self._popup.select_prev_page()
            return

        if key_code == wx.WXK_PAGEDOWN and self._popup and self._popup.IsShown():
            self._popup.select_next_page()
            return

        event.Skip()

    def _on_editor_kill_focus(self, event: wx.FocusEvent) -> None:
        wx.CallAfter(self._hide_if_focus_outside_popup)
        event.Skip()

    def _hide_if_focus_outside_popup(self) -> None:
        if not (self._popup and self._popup.IsShown()):
            return
        focused = wx.Window.FindFocus()
        current = focused
        while current is not None:
            if current is self._popup:
                return
            current = current.GetParent()
        self._hide_popup()

    def _on_parent_move(self, event: wx.MoveEvent) -> None:
        self._hide_popup()
        event.Skip()

    def _on_char_added(self, event: wx.stc.StyledTextEvent) -> None:
        if not self._is_enabled:
            return

        key_code = event.GetKey()
        character = chr(key_code)

        if character == " ":
            self._schedule_show(force=False)
            return

        if character.isalnum() or character in {"_", "."}:
            self._schedule_show(force=False)

    def _schedule_show(self, *, force: bool) -> None:
        self._cancel_pending()
        self._pending_call = wx.CallLater(self._debounce_ms, self.show, force=force)

    def _cancel_pending(self) -> None:
        if self._pending_call is None:
            return
        if self._pending_call.IsRunning():
            self._pending_call.Stop()
        self._pending_call = None

    @staticmethod
    def _unique_items(
            *, items: tuple[CompletionItem, ...]
    ) -> list[CompletionItem]:
        seen_keys: set[tuple[str, CompletionItemType]] = set()
        unique_items: list[CompletionItem] = []

        for item in items:
            key = (item.name, item.item_type)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_items.append(item)

        return unique_items

    @staticmethod
    def _unique_sorted_items(
            *, items: tuple[CompletionItem, ...]
    ) -> list[CompletionItem]:
        return SQLAutoCompleteController._unique_items(items=items)
