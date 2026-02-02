import re

from dataclasses import dataclass
from typing import Callable, List, Optional, Set, Tuple

import wx
import wx.stc

from structures.engines.database import SQLDatabase, SQLTable


@dataclass(frozen=True, slots=True)
class CompletionResult:
    prefix: str
    prefix_length: int
    items: Tuple[str, ...]


class SQLCompletionProvider:
    _word_at_caret_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
    _token_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[.,()*=]")

    _from_like_keywords: Set[str] = {"FROM", "JOIN", "UPDATE", "INTO"}

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

    def get(self, text: str, pos: int) -> Optional[CompletionResult]:
        if (database := self._get_database()) is None:
            return None

        safe_pos = self._clamp_position(pos=pos, text=text)
        prefix = self._extract_prefix(pos=safe_pos, text=text)
        previous_token = self._previous_token(pos=safe_pos, text=text)
        previous_keyword = previous_token.upper() if previous_token and previous_token[0].isalpha() else None

        if self._is_dot_trigger(pos=safe_pos, text=text):
            owner = self._word_before_dot(dot_pos=safe_pos - 1, text=text)
            items = self._columns_for_owner(database=database, owner=owner)
            return CompletionResult(items=tuple(items), prefix="", prefix_length=0)

        if previous_keyword in self._from_like_keywords:
            items = self._tables(database=database)
            return CompletionResult(items=tuple(items), prefix=prefix, prefix_length=len(prefix))

        if self._is_filter_editor:
            items = self._filter_items(database=database)
            return CompletionResult(items=tuple(items), prefix=prefix, prefix_length=len(prefix))

        if self._should_suggest_select_items(previous_token=previous_token, pos=safe_pos, text=text):
            items = self._columns_prioritized(database=database) + self._functions(database=database)
            return CompletionResult(items=tuple(items), prefix=prefix, prefix_length=len(prefix))

        items = self._keywords(database=database)
        return CompletionResult(items=tuple(items), prefix=prefix, prefix_length=len(prefix))

    @staticmethod
    def _clamp_position(*, pos: int, text: str) -> int:
        if pos < 0:
            return 0
        if pos > len(text):
            return len(text)
        return pos

    def _extract_prefix(self, *, pos: int, text: str) -> str:
        left_text = text[:pos]
        if (match := self._word_at_caret_pattern.search(left_text)) is None:
            return ""
        return match.group(0)

    def _previous_token(self, *, pos: int, text: str) -> Optional[str]:
        tokens = self._token_pattern.findall(text[:pos])
        if not tokens:
            return None
        return tokens[-1]

    @staticmethod
    def _is_dot_trigger(*, pos: int, text: str) -> bool:
        return pos > 0 and text[pos - 1] == "."

    def _word_before_dot(self, *, dot_pos: int, text: str) -> str:
        if dot_pos <= 0:
            return ""
        left_text = text[:dot_pos]
        if (match := self._word_at_caret_pattern.search(left_text)) is None:
            return ""
        return match.group(0)

    def _should_suggest_select_items(self, *, previous_token: Optional[str], pos: int, text: str) -> bool:
        if not self._is_in_select_list(pos=pos, text=text):
            return False
        if not previous_token:
            return False
        if previous_token == ",":
            return True
        return previous_token.upper() == "SELECT"

    @staticmethod
    def _is_in_select_list(*, pos: int, text: str) -> bool:
        left_upper = text[:pos].upper()
        select_index = left_upper.rfind("SELECT")
        if select_index == -1:
            return False
        from_index = left_upper.rfind("FROM")
        return from_index == -1 or from_index < select_index

    def _keywords(self, *, database: SQLDatabase) -> List[str]:
        keywords = database.context.KEYWORDS
        return [str(keyword).upper() for keyword in keywords]

    def _functions(self, *, database: SQLDatabase) -> List[str]:
        functions = database.context.FUNCTIONS
        return [str(function_name).upper() for function_name in functions]

    def _tables(self, *, database: SQLDatabase) -> List[str]:
        return [table.name for table in database.tables]

    def _filter_items(self, *, database: SQLDatabase) -> List[str]:
        # In filters, suggest columns/functions directly.
        return self._columns_prioritized(database=database) + self._functions(database=database)

    def _columns_prioritized(self, *, database: SQLDatabase) -> List[str]:
        items: List[str] = []
        current_table = self._get_current_table()

        if current_table is not None:
            items.extend([column.name for column in current_table.columns if column.name])

        for table in database.tables:
            if table is current_table:
                continue
            for column in table.columns:
                if column.name:
                    items.append(f"{table.name}.{column.name}")

        return items

    def _columns_for_owner(self, *, database: SQLDatabase, owner: str) -> List[str]:
        if not owner:
            return []
        for table in database.tables:
            if table.name.lower() == owner.lower():
                return [column.name for column in table.columns if column.name]
        return []


class SQLAutoCompleteController:
    def __init__(
        self,
        editor: wx.stc.StyledTextCtrl,
        provider: SQLCompletionProvider,
        *,
        debounce_ms: int = 80,
        is_enabled: bool = True,
        min_prefix_length: int = 1,
    ) -> None:
        self._editor = editor
        self._provider = provider
        self._debounce_ms = debounce_ms
        self._is_enabled = is_enabled
        self._min_prefix_length = min_prefix_length

        self._is_showing = False
        self._pending_call: Optional[wx.CallLater] = None

        self._configure_autocomp()

        self._editor.Bind(wx.stc.EVT_STC_CHARADDED, self._on_char_added)
        self._editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def set_enabled(self, is_enabled: bool) -> None:
        self._is_enabled = is_enabled
        if not is_enabled:
            self._cancel_pending()
            self._cancel_if_active()

    def show(self, *, force: bool) -> None:
        if not self._is_enabled:
            return
        if self._is_showing:
            return

        self._is_showing = True
        try:
            pos = self._editor.GetCurrentPos()
            text = self._editor.GetText()

            result = self._provider.get(pos=pos, text=text)
            if result is None:
                self._cancel_if_active()
                return

            if not force and result.prefix_length < self._min_prefix_length:
                self._cancel_if_active()
                return

            if not result.items:
                self._cancel_if_active()
                return

            items = self._unique_sorted_items(items=result.items)

            self._editor.AutoCompShow(result.prefix_length, "\n".join(items))
            if result.prefix:
                self._editor.AutoCompSelect(result.prefix)
        finally:
            self._is_showing = False

    def _configure_autocomp(self) -> None:
        # Use newline separator to support a wide range of identifiers.
        self._editor.AutoCompSetSeparator(ord("\n"))
        self._editor.AutoCompSetIgnoreCase(True)
        self._editor.AutoCompSetAutoHide(True)
        self._editor.AutoCompSetDropRestOfWord(True)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        if not self._is_enabled:
            event.Skip()
            return

        key_code = event.GetKeyCode()

        if event.ControlDown() and key_code == wx.WXK_SPACE:
            self._cancel_pending()
            self.show(force=True)
            return

        if key_code == wx.WXK_TAB and self._editor.AutoCompActive():
            self._cancel_pending()
            self._editor.AutoCompComplete()
            return

        if key_code == wx.WXK_ESCAPE and self._editor.AutoCompActive():
            self._cancel_pending()
            self._editor.AutoCompCancel()
            return

        event.Skip()

    def _on_char_added(self, event: wx.stc.StyledTextEvent) -> None:
        if not self._is_enabled:
            return

        key_code = event.GetKey()
        character = chr(key_code)

        if character.isalnum() or character in {"_", ".", ","}:
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

    def _cancel_if_active(self) -> None:
        if self._editor.AutoCompActive():
            self._editor.AutoCompCancel()

    @staticmethod
    def _unique_sorted_items(*, items: Tuple[str, ...]) -> List[str]:
        unique_items: Set[str] = set(items)
        return sorted(unique_items, key=str.upper)
