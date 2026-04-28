import contextlib
import dataclasses
import math
import os
import threading
import time

from collections import defaultdict
from gettext import gettext as _
from typing import Any, Optional, Union

import babel.numbers
import psutil
import sqlglot
import wx.adv
import wx.lib.wordwrap
import wx.stc

from helpers import bytes_to_human
from helpers.loader import Loader
from helpers.logger import logger
from helpers.observables import CallbackEvent

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase

from windows.views import MainFrameView

from windows.components.stc.styles import apply_stc_theme
from windows.components.stc.profiles import SQL
from windows.components.stc.autocomplete.auto_complete import SQLAutoCompleteController, SQLCompletionProvider
from windows.components.stc.template_menu import SQLTemplateMenuController

from windows.main import CURRENT_CONNECTION, CURRENT_SESSION, CURRENT_DATABASE, CURRENT_TABLE, CURRENT_COLUMN, CURRENT_INDEX, CURRENT_FOREIGN_KEY, CURRENT_RECORDS, AUTO_APPLY, CURRENT_VIEW, CURRENT_TRIGGER

from windows.main.explorer import TreeExplorerController

from windows.main.database.list import ListDatabaseTable, ListDatabaseView
from windows.main.database.view import ViewEditorController
from windows.main.database.options import DatabaseOptionsController

from windows.main.table.check import TableCheckController
from windows.main.table.index import TableIndexController
from windows.main.table.column import TableColumnsController
from windows.main.table.records import TableRecordsController
from windows.main.table.options import EditTableModel, NEW_TABLE
from windows.main.table.foreign_key import TableForeignKeyController

from windows.main.query.controller import QueryResultsController


class MainFrameController(MainFrameView):
    app = wx.GetApp()

    def __init__(self):
        super().__init__(None)

        self.styled_text_ctrls_name = ["sql_query_logs", "stc_view_select", "sql_query_filters", "sql_create_table", "sql_query_editor"]
        self._query_pages: list[wx.Panel] = []
        self._query_page_counter = 1
        self._query_page_meta: dict[wx.Panel, dict[str, Any]] = {}
        self._query_shortcuts = self._load_query_shortcuts()

        self.edit_table_model = EditTableModel()
        self.edit_table_model.bind_controls(
            name=self.table_name,
            comments=self.table_comment,
            auto_increment=self.table_auto_increment,
            collation=self.table_collation,
            convert_data=self.convert_data_collation,
            engine=self.table_engine,
            row_format=self.table_row_format,
        )

        self.list_database_tables = ListDatabaseTable(self.list_ctrl_database_tables)
        self.list_database_views = ListDatabaseView(self.list_ctrl_database_views)
        self.controller_database_options = DatabaseOptionsController(self)

        self.controller_tree_connections = TreeExplorerController(self.tree_ctrl_explorer)
        self.controller_tree_connections.on_cancel_table = self.on_cancel_table

        self.controller_list_table_columns = TableColumnsController(self.list_ctrl_table_columns)
        self.controller_list_table_records = TableRecordsController(self.list_ctrl_table_records)

        self.controller_list_table_index = TableIndexController(self.dv_table_indexes)
        self.controller_list_table_check = TableCheckController(self.dv_table_checks)
        self.controller_list_table_foreign_key = TableForeignKeyController(self.dv_table_foreign_keys)

        self._setup_query_pages()

        self.controller_view_editor = ViewEditorController(self)

        records_limit = self._load_records_limit_from_settings()
        self.limit_records.SetValue(records_limit)

        self._records_offset = 0
        self._records_limit = records_limit
        self._records_total_rows = 0
        self._records_total_key = None
        self._records_total_request_id = 0
        self._records_total_is_loading = False
        self._records_label_template = self.name_database_table.GetLabel()

        self.limit_records.Bind(wx.EVT_SPINCTRL, self.on_limit_records_changed)

        self._setup_query_editors()

        self._setup_database_action_buttons_bindings()

        self._setup_subscribers()

        # Memory update timer
        self.memory_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._update_memory, self.memory_timer)
        self.memory_timer.Start(5000)  # Update every 5 seconds

        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.on_sys_colour_changed)

        self.sql_query_filters.Bind(wx.EVT_KEY_DOWN, self._on_filters_key_down)

        self._id_f5_refresh = wx.NewIdRef()
        accel = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_F5, self._id_f5_refresh)])
        self.SetAcceleratorTable(accel)
        self.Bind(wx.EVT_MENU, self._on_f5_refresh, id=self._id_f5_refresh)

    def _setup_database_action_buttons_bindings(self) -> None:
        model = self.controller_database_options.model

        database_observables = [
            model.database_name,
            model.database_collation,
            model.database_encryption,
            model.database_read_only,
            model.database_tablespace,
            model.database_connection_limit,
            model.database_password,
            model.database_profile,
            model.database_default_tablespace,
            model.database_temporary_tablespace,
            model.database_quota,
            model.database_unlimited_quota,
            model.database_account_status,
            model.database_password_expire,
        ]

        for observable in database_observables:
            observable.subscribe(self._on_database_options_changed)

        CURRENT_SESSION.subscribe(self._on_database_options_changed)

    def _on_database_options_changed(self, _=None) -> None:
        logger.debug("ui trace: _on_database_options_changed")
        self._update_database_action_buttons()

    @staticmethod
    def _database_has_changes(database: Optional[SQLDatabase]) -> bool:
        if database is None:
            return False

        if database.is_new:
            return True

        session = CURRENT_SESSION.get_value()
        if session is None:
            return False

        original_database = next(
            (db for db in session.context.databases.get_value() if db.id == database.id),
            None,
        )

        if original_database is None:
            return True

        for field in dataclasses.fields(database):
            if not field.compare:
                continue

            if getattr(database, field.name, None) != getattr(original_database, field.name, None):
                return True

        return False

    def _update_database_action_buttons(self) -> None:
        database = CURRENT_DATABASE.get_value()

        has_database = database is not None
        has_changes = self._database_has_changes(database)
        is_persisted = bool(database is not None and not database.is_new)

        self.btn_apply_database.Enable(has_database and has_changes)
        self.btn_cancel_database.Enable(is_persisted and has_changes)
        self.btn_delete_database.Enable(is_persisted)
        logger.debug(
            "ui trace: _update_database_action_buttons has_database=%s has_changes=%s is_persisted=%s",
            has_database,
            has_changes,
            is_persisted,
        )

    def on_sys_colour_changed(self, event):
        self._setup_query_editors()

        wx.CallAfter(self.app.theme_manager.refresh)
        event.Skip()

    def _setup_query_editors(self):
        editors = set()

        for styled_text_ctrl_name in self.styled_text_ctrls_name:
            styled_text_ctrl = getattr(self, styled_text_ctrl_name)
            self._setup_sql_editor(styled_text_ctrl)
            editors.add(styled_text_ctrl)

        for meta in self._query_page_meta.values():
            styled_text_ctrl = meta["editor"]
            if styled_text_ctrl in editors:
                continue

            self._setup_sql_editor(styled_text_ctrl)

    def _setup_sql_editor(self, styled_text_ctrl: wx.stc.StyledTextCtrl) -> None:
        styled_text_ctrl.EmptyUndoBuffer()

        wx.GetApp().theme_manager.register(styled_text_ctrl, lambda: wx.GetApp().syntax_registry.get("sql"))

        apply_stc_theme(styled_text_ctrl, SQL)

        sql_completion_provider = SQLCompletionProvider(
            get_database=lambda: CURRENT_DATABASE.get_value(),
            get_current_table=lambda: CURRENT_TABLE.get_value(),
        )

        SQLAutoCompleteController(
            editor=styled_text_ctrl,
            provider=sql_completion_provider,
            settings=wx.GetApp().settings,
            theme_loader=wx.GetApp().theme_loader,
        )

        SQLTemplateMenuController(
            editor=styled_text_ctrl,
            get_database=lambda: CURRENT_DATABASE.get_value(),
            get_current_table=lambda: CURRENT_TABLE.get_value(),
        )

    def _build_query_editor(self, parent: wx.Window) -> wx.stc.StyledTextCtrl:
        editor = wx.stc.StyledTextCtrl(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        editor.SetUseTabs(True)
        editor.SetTabWidth(4)
        editor.SetIndent(4)
        editor.SetTabIndents(True)
        editor.SetBackSpaceUnIndents(True)
        editor.SetViewEOL(False)
        editor.SetViewWhiteSpace(False)
        editor.SetMarginWidth(2, 0)
        editor.SetIndentationGuides(True)
        editor.SetReadOnly(False)
        editor.SetMarginType(1, wx.stc.STC_MARGIN_SYMBOL)
        editor.SetMarginMask(1, wx.stc.STC_MASK_FOLDERS)
        editor.SetMarginWidth(1, 16)
        editor.SetMarginSensitive(1, True)
        editor.SetProperty("fold", "1")
        editor.SetFoldFlags(wx.stc.STC_FOLDFLAG_LINEBEFORE_CONTRACTED | wx.stc.STC_FOLDFLAG_LINEAFTER_CONTRACTED)
        editor.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        editor.SetMarginWidth(0, editor.TextWidth(wx.stc.STC_STYLE_LINENUMBER, "_99999"))
        editor.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        editor.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
        return editor

    def _load_query_shortcuts(self) -> dict[str, str]:
        settings = wx.GetApp().settings
        return {
            "execute_current": settings.get_value("ui", "shortcuts", "query", "execute_current", default="Ctrl+Enter"),
            "execute_all": settings.get_value("ui", "shortcuts", "query", "execute_all", default="Ctrl+Shift+Enter"),
            "stop": settings.get_value("ui", "shortcuts", "query", "stop", default="Esc"),
            "new_query": settings.get_value("ui", "shortcuts", "query", "new_query", default="Ctrl+T"),
            "close_query": settings.get_value("ui", "shortcuts", "query", "close_query", default="Ctrl+W"),
            "save": settings.get_value("ui", "shortcuts", "query", "save", default="Ctrl+S"),
            "save_as": settings.get_value("ui", "shortcuts", "query", "save_as", default="Ctrl+Shift+S"),
        }

    def _with_shortcut(self, text: str, shortcut_key: str) -> str:
        shortcut = self._query_shortcuts.get(shortcut_key)
        if not shortcut:
            return text

        return _("{text} ({shortcut})").format(text=text, shortcut=shortcut)

    def _apply_query_toolbar_shortcuts(self, toolbar: wx.ToolBar, tool_ids: dict[str, int]) -> None:
        toolbar.SetToolShortHelp(tool_ids["new"], self._with_shortcut(_("New query"), "new_query"))
        toolbar.SetToolShortHelp(tool_ids["close"], self._with_shortcut(_("Close query"), "close_query"))
        toolbar.SetToolShortHelp(tool_ids["execute"], self._with_shortcut(_("Execute"), "execute_current"))
        toolbar.SetToolShortHelp(tool_ids["execute_all"], self._with_shortcut(_("Execute all"), "execute_all"))
        toolbar.SetToolShortHelp(tool_ids["stop"], self._with_shortcut(_("Stop"), "stop"))
        toolbar.SetToolShortHelp(tool_ids["save"], self._with_shortcut(_("Save"), "save"))

    def _build_query_toolbar(self, parent: wx.Window) -> tuple[wx.ToolBar, dict[str, int]]:
        toolbar = wx.ToolBar(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL)
        new_query = toolbar.AddTool(wx.ID_ANY, _("New query"), wx.Bitmap("icons/16x16/add.png", wx.BITMAP_TYPE_ANY),
                                    wx.NullBitmap, wx.ITEM_NORMAL, _("New query"), wx.EmptyString, None)
        close_query = toolbar.AddTool(wx.ID_ANY, _("Close query"), wx.Bitmap("icons/16x16/delete.png", wx.BITMAP_TYPE_ANY),
                                      wx.NullBitmap, wx.ITEM_NORMAL, _("Close query"), wx.EmptyString, None)
        toolbar.AddSeparator()
        execute_statement = toolbar.AddTool(wx.ID_ANY, _("Execute"), wx.Bitmap("icons/16x16/arrow_right.png", wx.BITMAP_TYPE_ANY),
                                            wx.NullBitmap, wx.ITEM_NORMAL, _("Execute"), wx.EmptyString, None)
        execute_all = toolbar.AddTool(wx.ID_ANY, _("Execute all"), wx.Bitmap("icons/16x16/arrows_lefttoright.png", wx.BITMAP_TYPE_ANY),
                                      wx.NullBitmap, wx.ITEM_NORMAL, _("Execute all statements"), wx.EmptyString, None)
        toolbar.AddSeparator()
        stop_statements = toolbar.AddTool(wx.ID_ANY, _("Stop"), wx.Bitmap("icons/16x16/cancel.png", wx.BITMAP_TYPE_ANY),
                                          wx.NullBitmap, wx.ITEM_NORMAL, _("Stop"), wx.EmptyString, None)
        toolbar.AddSeparator()
        save_query = toolbar.AddTool(wx.ID_ANY, _("Save"), wx.Bitmap("icons/16x16/disk.png", wx.BITMAP_TYPE_ANY),
                                     wx.NullBitmap, wx.ITEM_NORMAL, _("Save"), wx.EmptyString, None)
        toolbar.Realize()

        tool_ids = {
            "new": new_query.GetId(),
            "close": close_query.GetId(),
            "execute": execute_statement.GetId(),
            "execute_all": execute_all.GetId(),
            "stop": stop_statements.GetId(),
            "save": save_query.GetId(),
        }

        self._apply_query_toolbar_shortcuts(toolbar, tool_ids)

        toolbar.Bind(wx.EVT_TOOL, self.on_new_query, id=new_query.GetId())
        toolbar.Bind(wx.EVT_TOOL, self.on_close_query, id=close_query.GetId())
        toolbar.Bind(wx.EVT_TOOL, self.on_execute_statement, id=execute_statement.GetId())
        toolbar.Bind(wx.EVT_TOOL, self.on_execute_statements, id=execute_all.GetId())
        toolbar.Bind(wx.EVT_TOOL, self.on_stop_statements, id=stop_statements.GetId())
        toolbar.Bind(wx.EVT_TOOL, self.on_save, id=save_query.GetId())
        return toolbar, tool_ids

    def _build_query_page(self) -> tuple[wx.Panel, wx.stc.StyledTextCtrl, wx.Window, wx.ToolBar, dict[str, int]]:
        panel_query = wx.Panel(self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        query_sizer = wx.BoxSizer(wx.VERTICAL)
        splitter = wx.SplitterWindow(panel_query, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D)

        panel_top = wx.Panel(splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        toolbar, tool_ids = self._build_query_toolbar(panel_top)
        editor = self._build_query_editor(panel_top)
        top_sizer.Add(toolbar, 0, wx.EXPAND, 5)
        top_sizer.Add(editor, 1, wx.EXPAND | wx.ALL, 5)
        panel_top.SetSizer(top_sizer)

        panel_bottom = wx.Panel(splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        results_notebook_class = self.notebook_sql_results.__class__
        results_notebook = results_notebook_class(panel_bottom, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        bottom_sizer.Add(results_notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel_bottom.SetSizer(bottom_sizer)

        splitter.SplitHorizontally(panel_top, panel_bottom, -300)
        query_sizer.Add(splitter, 1, wx.EXPAND, 5)
        panel_query.SetSizer(query_sizer)
        return panel_query, editor, results_notebook, toolbar, tool_ids

    def _get_active_query_controller(self) -> Optional[QueryResultsController]:
        page = self.notebook_query_editor.GetCurrentPage()
        if page is None:
            return None

        meta = self._query_page_meta.get(page)
        if meta is None:
            return None

        return meta["controller"]

    def _register_query_page(
            self,
            panel: wx.Panel,
            editor: wx.stc.StyledTextCtrl,
            results_notebook: wx.Window,
            toolbar: wx.ToolBar,
            tool_ids: dict[str, int],
            display_name: str,
    ) -> None:
        controller = QueryResultsController(
            editor,
            results_notebook,
            cancel_button=None,
            on_new_query=self.on_new_query,
            on_close_query=self.on_close_query,
            on_save_query=self.on_save,
            on_save_as_query=self.on_save_as_query,
            on_stop_state_changed=lambda enabled: self._set_query_stop_enabled(panel, enabled),
            on_before_execute=lambda: self._autosave_query_page_before_execute(panel),
        )
        self._query_pages.append(panel)
        self._query_page_meta[panel] = {
            "editor": editor,
            "toolbar": toolbar,
            "controller": controller,
            "tool_ids": tool_ids,
            "file_path": None,
            "is_dirty": False,
            "display_name": display_name,
        }
        self._bind_query_editor_events(panel, editor)
        self._set_query_stop_enabled(panel, enabled=False)
        self._set_query_save_enabled(panel, enabled=False)

    def _set_query_save_enabled(self, page: wx.Panel, enabled: bool) -> None:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return

        toolbar = meta["toolbar"]
        tool_ids = meta["tool_ids"]
        toolbar.EnableTool(tool_ids["save"], enabled)

    def _set_query_stop_enabled(self, page: wx.Panel, enabled: bool) -> None:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return

        toolbar = meta["toolbar"]
        tool_ids = meta["tool_ids"]
        toolbar.EnableTool(tool_ids["stop"], enabled)
        toolbar.EnableTool(tool_ids["execute"], not enabled)
        toolbar.EnableTool(tool_ids["execute_all"], not enabled)

    def _bind_query_editor_events(self, page: wx.Panel, editor: wx.stc.StyledTextCtrl) -> None:
        editor.Bind(wx.stc.EVT_STC_CHANGE, lambda event: self._on_query_editor_changed(page, event))

    def _on_query_editor_changed(self, page: wx.Panel, event: wx.Event) -> None:
        self._set_query_dirty(page, is_dirty=True)
        event.Skip()

    def _set_query_dirty(self, page: wx.Panel, is_dirty: bool) -> None:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return

        if meta["is_dirty"] == is_dirty:
            return

        meta["is_dirty"] = is_dirty
        self._update_query_page_title(page)
        self._set_query_save_enabled(page, enabled=is_dirty)

    def _update_query_page_title(self, page: wx.Panel) -> None:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return

        page_index = self.notebook_query_editor.FindPage(page)
        if page_index < 0:
            return

        title = meta["display_name"]
        if meta["is_dirty"]:
            title = f"{title} *"

        self.notebook_query_editor.SetPageText(page_index, title)

    def _build_query_editor_panel(self) -> tuple[wx.Panel, wx.stc.StyledTextCtrl]:
        panel = wx.Panel(self.notebook_query_editor, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        editor = self._build_query_editor(panel)
        sizer.Add(editor, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel, editor

    def _on_notebook_query_tab_changed(self, event: wx.BookCtrlEvent) -> None:
        controller = self._get_active_query_controller()
        if controller is not None:
            self.controller_query_records = controller
        event.Skip()

    def _setup_query_pages(self) -> None:
        shared_tool_ids = {
            "new": self.new_query.GetId(),
            "close": self.close_query.GetId(),
            "execute": self.execute_statement.GetId(),
            "execute_all": self.execute_all_statements.GetId(),
            "stop": self.stop_statements.GetId(),
            "save": self.save.GetId(),
        }

        self.notebook_query_editor.SetPageText(0, _("Query (1)"))

        self._register_query_page(
            panel=self.m_panel63,
            editor=self.sql_query_editor,
            results_notebook=self.notebook_query_results,
            toolbar=self.m_toolBar2,
            tool_ids=shared_tool_ids,
            display_name=_("Query (1)"),
        )

        self._apply_query_toolbar_shortcuts(self.m_toolBar2, shared_tool_ids)

        self.controller_query_records = self._query_page_meta[self.m_panel63]["controller"]
        self.notebook_query_editor.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_notebook_query_tab_changed)
        self._update_query_close_tools_state()

    def _update_query_close_tools_state(self) -> None:
        can_close = self.notebook_query_editor.GetPageCount() > 1
        for meta in self._query_page_meta.values():
            toolbar = meta["toolbar"]
            close_query_tool_id = meta["tool_ids"]["close"]
            toolbar.EnableTool(close_query_tool_id, can_close)

    def _create_new_query_page(self) -> None:
        self._query_page_counter += 1
        label = _("Query ({query_number})").format(query_number=self._query_page_counter)

        panel, editor = self._build_query_editor_panel()
        self.notebook_query_editor.AddPage(panel, label, select=True)

        shared_tool_ids = {
            "new": self.new_query.GetId(),
            "close": self.close_query.GetId(),
            "execute": self.execute_statement.GetId(),
            "execute_all": self.execute_all_statements.GetId(),
            "stop": self.stop_statements.GetId(),
            "save": self.save.GetId(),
        }

        self._register_query_page(
            panel=panel,
            editor=editor,
            results_notebook=self.notebook_query_results,
            toolbar=self.m_toolBar2,
            tool_ids=shared_tool_ids,
            display_name=label,
        )

        self._setup_sql_editor(editor)
        self._update_query_close_tools_state()

    def _confirm_close_query_page(self, page: wx.Panel) -> bool:
        meta = self._query_page_meta.get(page)
        if meta is None or not meta["is_dirty"]:
            return True

        result = wx.MessageDialog(
            None,
            message=_("You have unsaved changes. Save before closing?"),
            caption=_("Unsaved query"),
            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
        ).ShowModal()

        if result == wx.ID_YES:
            return self._save_query_page(page, force_save_as=False)

        if result == wx.ID_NO:
            return True

        return False

    def _close_active_query_page(self) -> None:
        if self.notebook_query_editor.GetPageCount() <= 1:
            return

        page = self.notebook_query_editor.GetCurrentPage()
        if page is None or page not in self._query_page_meta:
            return

        if not self._confirm_close_query_page(page):
            return

        meta = self._query_page_meta.pop(page)
        self._query_pages.remove(page)

        controller = meta["controller"]
        controller.cancel_execution(wx.CommandEvent())

        query_page_index = self.notebook_query_editor.FindPage(page)
        if query_page_index >= 0:
            self.notebook_query_editor.DeletePage(query_page_index)

        self._update_query_close_tools_state()

        active_controller = self._get_active_query_controller()
        if active_controller is not None:
            self.controller_query_records = active_controller

    def _ask_query_save_path(self, file_path: Optional[str] = None) -> Optional[str]:
        default_dir = os.path.dirname(file_path) if file_path else os.getcwd()
        default_name = os.path.basename(file_path) if file_path else "query.sql"

        dialog = wx.FileDialog(
            self,
            message=_("Save query"),
            defaultDir=default_dir,
            defaultFile=default_name,
            wildcard=_("SQL files (*.sql)|*.sql|All files (*.*)|*.*"),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )

        if dialog.ShowModal() != wx.ID_OK:
            return None

        return dialog.GetPath()

    @staticmethod
    def _write_query_file(file_path: str, content: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file_obj:
            file_obj.write(content)

    @staticmethod
    def _get_query_autosave_path() -> str:
        query_dir = os.path.join(os.getcwd(), ".queries")
        os.makedirs(query_dir, exist_ok=True)
        return os.path.join(query_dir, f"query_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()}.sql")

    def _save_query_page(self, page: wx.Panel, force_save_as: bool) -> bool:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return False

        file_path = meta["file_path"]
        if force_save_as or not file_path:
            file_path = self._ask_query_save_path(file_path)
            if not file_path:
                return False

        editor = meta["editor"]

        try:
            self._write_query_file(file_path, editor.GetText())
        except Exception as ex:
            logger.error(str(ex), exc_info=True)
            wx.MessageDialog(None, str(ex), _("Error"), wx.OK | wx.ICON_ERROR).ShowModal()
            return False

        meta["file_path"] = file_path
        meta["display_name"] = os.path.basename(file_path)
        self._set_query_dirty(page, is_dirty=False)
        QUERY_LOGS.append(_("-- Saved query to {file_path}").format(file_path=file_path))
        return True

    def _autosave_query_page_before_execute(self, page: wx.Panel) -> bool:
        meta = self._query_page_meta.get(page)
        if meta is None:
            return False

        if meta["file_path"] is not None:
            return True

        editor = meta["editor"]
        if not editor.GetText().strip():
            return True

        file_path = self._get_query_autosave_path()
        try:
            self._write_query_file(file_path, editor.GetText())
        except Exception as ex:
            logger.error(str(ex), exc_info=True)
            wx.MessageDialog(None, str(ex), _("Error"), wx.OK | wx.ICON_ERROR).ShowModal()
            return False

        meta["file_path"] = file_path
        self._set_query_dirty(page, is_dirty=False)
        QUERY_LOGS.append(_("-- Autosaved query to {file_path}").format(file_path=file_path))
        return True

    def _setup_subscribers(self):
        self.toggle_panel()

        QUERY_LOGS.subscribe(self._write_query_log, CallbackEvent.ON_APPEND)

        # SESSIONS.subscribe(self._load_connection, CallbackEvent.ON_APPEND)

        CURRENT_SESSION.subscribe(self._on_current_session)

        CURRENT_DATABASE.subscribe(self._on_current_database)

        CURRENT_VIEW.subscribe(self._on_current_view)

        CURRENT_TRIGGER.subscribe(self._on_current_trigger)

        CURRENT_TABLE.subscribe(self._on_current_table)

        CURRENT_COLUMN.subscribe(self._on_current_column)

        CURRENT_INDEX.subscribe(self._on_current_index)

        CURRENT_FOREIGN_KEY.subscribe(self._on_current_foreign_key)

        CURRENT_RECORDS.subscribe(self._on_current_records)

        # SELECTED_TABLE.subscribe(self._on_selected_table)

        NEW_TABLE.subscribe(self._on_new_table)

        AUTO_APPLY.subscribe(self._on_auto_apply)

        # Initialize record toolbar states
        self._initialize_record_toolbar_states()
        
        # Initialize column toolbar states
        self._initialize_column_toolbar_states()

    def _write_query_log(self, text: str):
        self.sql_query_logs.AppendText(f"{text}\n")
        self.sql_query_logs.GotoLine(self.sql_query_logs.GetLineCount() - 1)

    def _toggle_panel(self, index: int, visible: bool):
        panel = self.MainFrameNotebook.GetPage(index)
        panel.Show(visible)
        panel.Enable(visible)

    def _toggle_edit_table(self, visible: bool):
        self._toggle_panel(2, visible)
        self._toggle_panel(3, visible)

    def _format_server_uptime(self, uptime: Optional[float] = None) -> str:
        if not uptime:
            uptime = time.time() - psutil.boot_time()

        return (f"{math.floor(uptime / 86400)} {_('days')}, "
                f"{math.floor((uptime % 86400) / 3600)} {_('hours')}, "
                f"{math.floor((uptime % 3600) / 60)} {_('minutes')}, "
                f"{math.floor(uptime % 60)} {_('seconds')}")

    def _update_memory(self, event):
        memory_info = psutil.Process(os.getpid()).memory_info()
        used = memory_info.rss  # B
        total = psutil.virtual_memory().total  # MB
        percentage = used / total

        self.status_bar.SetStatusText(_('Memory used: {used} ({percentage:.2%})').format(used=bytes_to_human(used), percentage=percentage), 3)

    def on_menu_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("PeterSQL")
        info.SetVersion(open("VERSION", "r").read().strip())
        info.SetLicense(wx.lib.wordwrap.wordwrap(open("LICENSE", "r").read().strip(), 500, wx.ClientDC(self)))
        info.SetCopyright("(c) 2025 Giuseppe Tripoli")
        info.SetWebSite("https://github.com/gtripoli/petersql", "PeterSQL HomePage")
        info.SetIcon(wx.Icon("petersql_large.png"))
        info.SetDevelopers(["Giuseppe Tripoli"])
        info.SetArtists(["Giuseppe Tripoli"])
        info.SetDescription(wx.lib.wordwrap.wordwrap("""
            PeterSQL is a graphical client for database management, inspired by the
            excellent [HeidiSQL](https://www.heidisql.com/), but written entirely in
            Python with **wxPython**, and designed to run natively on **All OS**.""",
                                                     500, wx.ClientDC(self)))

        # Then we call wx.AboutBox giving it that info object
        wx.adv.AboutBox(info)

    def do_close(self, event):
        super().Destroy()
        wx.GetApp().ExitMainLoop()

    def do_open_connection_manager(self, event):
        from windows.dialogs.connections.view import ConnectionsManager

        sm = ConnectionsManager(self)
        sm.Show()

    def on_open_settings(self, event):
        from windows.dialogs.settings.controller import SettingsController

        controller = SettingsController(self, wx.GetApp().settings)
        if controller.show_modal() == wx.ID_OK:
            wx.MessageBox(_("Settings saved successfully"), _("Settings"), wx.OK | wx.ICON_INFORMATION)

    def toggle_panel(self, current: Optional[Union[SQLDatabase, SQLTable, SQLView, SQLTrigger]] = None):
        # self.MainFrameNotebook.SetSelection(0)
        logger.debug(
            "ui trace: toggle_panel current=%s",
            type(current).__name__ if current is not None else "None",
        )

        current_session = CURRENT_SESSION.get_value()
        current_database = CURRENT_DATABASE.get_value()
        current_table = CURRENT_TABLE.get_value()
        current_view = CURRENT_VIEW.get_value()
        current_trigger = CURRENT_TRIGGER.get_value()

        total_pages = self.MainFrameNotebook.GetPageCount()

        if not current:
            if not current_session:
                for page in range(total_pages):
                    self.MainFrameNotebook.GetPage(page).Hide()

            if not current_database:
                for page in range(1, total_pages):
                    self.MainFrameNotebook.GetPage(page).Hide()

            if not current_table:
                self.MainFrameNotebook.GetPage(2).Hide()
                self.MainFrameNotebook.GetPage(5).Hide()

            if not current_view:
                self.MainFrameNotebook.GetPage(3).Hide()
                self.MainFrameNotebook.GetPage(5).Hide()

            if not current_trigger:
                self.MainFrameNotebook.GetPage(4).Hide()

            return

        if isinstance(current, Session):
            self.MainFrameNotebook.GetPage(0).Show()
            self.MainFrameNotebook.SetSelection(0)

        elif isinstance(current, SQLDatabase):
            self.MainFrameNotebook.GetPage(1).Show()
            self.MainFrameNotebook.GetPage(6).Show()
            self.MainFrameNotebook.SetSelection(1)

        elif isinstance(current, SQLTable) or isinstance(current, SQLView):
            if isinstance(current, SQLTable):
                self.MainFrameNotebook.GetPage(2).Show()
                if self.MainFrameNotebook.GetSelection() < 2:
                    self.MainFrameNotebook.SetSelection(2)

            if isinstance(current, SQLView):
                self.MainFrameNotebook.GetPage(3).Show()
                if self.MainFrameNotebook.GetSelection() < 3:
                    self.MainFrameNotebook.SetSelection(3)

            self.MainFrameNotebook.GetPage(5).Show()
            self.MainFrameNotebook.GetPage(6).Show()

        elif isinstance(current, SQLTrigger):
            self.MainFrameNotebook.GetPage(4).Show()
            self.MainFrameNotebook.GetPage(6).Show()
            if self.MainFrameNotebook.GetSelection() < 4:
                self.MainFrameNotebook.SetSelection(3)

    def _get_records_filters(self) -> str:
        return (self.sql_query_filters.GetSelectedText() or self.sql_query_filters.GetText()).strip()

    def _build_records_total_key(self, table: SQLTable, filters: str) -> tuple[str, str, str, str]:
        schema = str(getattr(table, "schema", "") or "")
        return table.database.name, schema, table.name, filters

    def _count_table_records(
            self,
            table: SQLTable,
            filters: str,
            context: Optional[Any] = None,
    ) -> int:
        if context is None:
            context = table.database.context

        where = f" WHERE {filters}" if filters else ""
        schema = str(getattr(table, "schema", "") or "")

        if schema:
            from_clause = context.qualify(schema, table.name)
        else:
            from_clause = context.qualify(table.database.name, table.name)

        query = f"SELECT COUNT(*) AS total_rows FROM {from_clause}{where}"
        context.execute(query)

        row = context.fetchone() or {}
        total_rows = None
        try:
            total_rows = dict(row).get("total_rows")
        except Exception as ex:
            logger.error(ex)
        if total_rows is None and row:
            try:
                total_rows = next(iter(row.values()), 0)
            except Exception:
                total_rows = 0

        return int(total_rows or 0)

    def _count_table_records_worker(
            self,
            session: Session,
            table: SQLTable,
            filters: str,
            total_key: tuple[str, str, str, str],
            request_id: int,
    ) -> None:
        total_rows = 0
        error = None
        context = None

        try:
            context = session._get_context_class()(self._build_records_count_connection(session))
            context.connect(skip_before_connect=True, skip_after_connect=True)
            context.set_database(table.database)
            total_rows = self._count_table_records(table, filters, context)
        except Exception as ex:
            error = str(ex)
            logger.warning("Failed async records count: %s", ex, exc_info=True)
        finally:
            if context is not None:
                try:
                    context.disconnect()
                except Exception:
                    pass

        wx.CallAfter(
            self._on_records_count_complete,
            total_key,
            request_id,
            total_rows,
            error,
        )

    def _build_records_count_connection(self, session: Session) -> Connection:
        connection = session.connection.copy()

        if not connection.has_enabled_tunnel():
            return connection

        context = getattr(session, "context", None)
        configuration = getattr(connection, "configuration", None)

        if context is not None and configuration is not None and hasattr(configuration, "_replace"):
            replace_kwargs = {}

            if hasattr(configuration, "hostname") and getattr(context, "host", None):
                replace_kwargs["hostname"] = context.host

            if hasattr(configuration, "port") and getattr(context, "port", None) is not None:
                replace_kwargs["port"] = int(context.port)

            if replace_kwargs:
                connection.configuration = configuration._replace(**replace_kwargs)

        connection.ssh_tunnel = None
        return connection

    def _format_records_number(self, value: int) -> str:
        locale = wx.GetApp().settings.get_value("language", default="en_US")
        try:
            return babel.numbers.format_decimal(value, locale=locale)
        except Exception:
            return str(value)

    def _load_records_limit_from_settings(self) -> int:
        settings = wx.GetApp().settings

        max_limit = 1000
        if hasattr(self, "limit_records"):
            with contextlib.suppress(Exception):
                max_limit = max(1, int(self.limit_records.GetMax()))

        saved_limit = settings.get_value("records", "limit", default=100)

        try:
            return min(max(1, int(saved_limit)), max_limit)
        except Exception:
            return min(100, max_limit)

    def _can_skip_count_query(self, table: SQLTable, filters: str) -> bool:
        if filters:
            return False

        if table.total_rows is None:
            return False

        return int(table.total_rows) <= self._records_limit

    def _get_loaded_records_count(self, table: SQLTable) -> int:
        records = getattr(table, "records", None)
        if records is None:
            return 0

        if getattr(records, "is_loaded", False):
            return len(records)

        return 0

    def _get_loading_total_text(self, table: SQLTable, filters: str) -> str:
        if not filters and table.total_rows is not None:
            estimated = self._format_records_number(int(table.total_rows))
            return _("~{estimated} (Loading...)").format(estimated=estimated)

        return _("~ (Loading...)")

    def _refresh_records_total_rows(self, table: SQLTable, filters: str) -> None:
        total_key = self._build_records_total_key(table, filters)
        if self._records_total_key == total_key:
            return

        self._records_total_key = total_key
        self._records_total_request_id += 1

        if self._can_skip_count_query(table, filters):
            self._records_total_is_loading = False
            self._records_total_rows = max(int(table.total_rows or 0), 0)
            self._update_records_label(table)
            self._set_records_paging_buttons(table)
            return

        self._records_total_is_loading = True

        self._update_records_label(table)
        self._set_records_paging_buttons(table)

        session = CURRENT_SESSION.get_value()
        if session is None:
            self._records_total_is_loading = False
            self._update_records_label(table)
            self._set_records_paging_buttons(table)
            return

        worker = threading.Thread(
            target=self._count_table_records_worker,
            args=(
                session,
                table,
                filters,
                total_key,
                self._records_total_request_id,
            ),
            daemon=True,
        )
        worker.start()

    def _on_records_count_complete(
            self,
            total_key: tuple[str, str, str, str],
            request_id: int,
            total_rows: int,
            error: Optional[str],
    ) -> None:
        if request_id != self._records_total_request_id:
            return

        self._records_total_is_loading = False

        if error:
            table = CURRENT_TABLE.get_value()
            if table is not None:
                self._update_records_label(table)
                self._set_records_paging_buttons(table)
            return

        table = CURRENT_TABLE.get_value()
        if table is None:
            return

        filters = self._get_records_filters()
        if self._build_records_total_key(table, filters) != total_key:
            return

        self._records_total_rows = max(int(total_rows), 0)
        last_offset = self._get_records_last_offset(self._records_limit)

        if self._records_offset > last_offset:
            self._records_offset = last_offset
            try:
                self._load_records_page()
            except Exception as ex:
                logger.error(f"Error reloading records page after count: {ex}", exc_info=True)
            return

        try:
            self._update_records_label(table)
            self._set_records_paging_buttons(table)
        except Exception as ex:
            logger.error(f"Error updating records label: {ex}", exc_info=True)

    def _get_records_last_offset(self, limit: int) -> int:
        total_rows = int(self._records_total_rows or 0)
        if total_rows <= 0:
            return 0

        return ((total_rows - 1) // limit) * limit

    def _load_records_page(self):
        table = CURRENT_TABLE.get_value()
        if table is None:
            return

        limit = max(1, self.limit_records.GetValue())
        self._records_limit = limit

        filters = self._get_records_filters()
        self._refresh_records_total_rows(table, filters)

        last_offset = self._get_records_last_offset(limit)

        self._records_offset = min(max(self._records_offset, 0), last_offset)

        logger.debug(
            "ui trace: records._load_records_page start table=%s limit=%s offset=%s filters=%s",
            table.name,
            limit,
            self._records_offset,
            filters,
        )
        with Loader.cursor_wait():
            logger.debug("ui trace: records._load_records_page before table.load_records table=%s", table.name)
            table.load_records(filters=filters, limit=limit, offset=self._records_offset)
            logger.debug("ui trace: records._load_records_page after table.load_records table=%s", table.name)
            logger.debug("ui trace: records._load_records_page before controller.load_model table=%s", table.name)
            self.controller_list_table_records.load_model()
            logger.debug("ui trace: records._load_records_page after controller.load_model table=%s", table.name)

        self._update_records_label(table)
        self._set_records_paging_buttons(table)
        logger.debug("ui trace: records._load_records_page end table=%s", table.name)

    def _update_records_label(self, table: SQLTable):
        rows_count = self._get_loaded_records_count(table)
        from_row = 0 if rows_count == 0 else self._records_offset + 1
        to_row = 0 if rows_count == 0 else self._records_offset + rows_count

        if self._records_total_is_loading:
            total_rows_text = self._get_loading_total_text(table, self._get_records_filters())
        else:
            total_rows_text = self._format_records_number(int(self._records_total_rows or 0))

        self.name_database_table.SetLabel(
            self._records_label_template.format(
                database_name=table.database.name,
                table_name=table.name,
                total_rows=total_rows_text,
                from_row=self._format_records_number(from_row),
                to_row=self._format_records_number(to_row),
            )
        )

    def _set_records_paging_buttons(self, table: SQLTable):
        if self._records_total_is_loading:
            rows_count = self._get_loaded_records_count(table)
            at_first_page = self._records_offset <= 0
            has_next_page = rows_count >= self._records_limit

            self.btn_first_records.Enable(not at_first_page)
            self.btn_prev_records.Enable(not at_first_page)
            self.btn_next_records.Enable(has_next_page)
            self.btn_last_records.Enable(False)
            return

        total_rows = int(self._records_total_rows or 0)
        at_first_page = self._records_offset <= 0
        at_last_page = self._records_offset >= self._get_records_last_offset(self._records_limit)
        has_rows = total_rows > 0

        self.btn_first_records.Enable(has_rows and not at_first_page)
        self.btn_prev_records.Enable(has_rows and not at_first_page)
        self.btn_next_records.Enable(has_rows and not at_last_page)
        self.btn_last_records.Enable(has_rows and not at_last_page)

    def on_page_chaged(self, event):
        if int(event.Selection) == 5:
            if table := CURRENT_TABLE.get_value():
                self._records_offset = 0
                self._load_records_page()

    def _on_current_session(self, session: Session):
        if not wx.IsMainThread():
            logger.debug("ui trace: _on_current_session rescheduled to main thread")
            wx.CallAfter(self._on_current_session, session)
            return

        from structures.session import Session

        self.toggle_panel(session.connection if session else None)

        if session:
            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Connection')}: {session.name}", 0)

            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Version')}: {session.context.server_version}", 1)

            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Uptime')}: {self._format_server_uptime(session.context.get_server_uptime())}", 2)

            keywords = " ".join(k.lower() for k in session.context.KEYWORDS)

            colors_datatypes = defaultdict(list)

            for datatype in session.context.DATATYPE.get_all():
                colors_datatypes[datatype.category.value.color].append(datatype.name.lower())
                colors_datatypes[datatype.category.value.color].extend([d.lower() for d in datatype.alias])

            for stc_name in self.styled_text_ctrls_name:
                stc_ctrl = getattr(self, stc_name)

                stc_ctrl.SetKeyWords(0, keywords)

                for idx, (color, words) in enumerate(colors_datatypes.items(), start=1):
                    stc_ctrl.SetKeyWords(idx, " ".join(sorted(words)))

                    stc_ctrl.StyleSetForeground(wx.stc.STC_SQL_WORD + idx, wx.Colour(*color))

                stc_ctrl.Colourise(0, -1)

    def _on_current_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            logger.debug("ui trace: _on_current_database rescheduled to main thread")
            wx.CallAfter(self._on_current_database, database)
            return

        logger.debug(
            "ui trace: _on_current_database database=%s",
            getattr(database, "name", None) if database is not None else None,
        )
        self.toggle_panel(database)

        self._update_database_action_buttons()

        if database:
            self.table_engine.Enable(len(database.context.ENGINES) > 1)
            self.table_engine.SetItems(database.context.ENGINES)

            self.table_collation.Enable(len(database.context.COLLATIONS.keys()) > 1)
            self.table_collation.SetItems(list(database.context.COLLATIONS.keys()))

            row_formats = database.context.ROW_FORMATS
            self.table_row_format.Enable(bool(row_formats))
            self.table_row_format.SetItems(row_formats)

            self.convert_data_collation.Enable(bool(database.context.COLLATIONS))

        if (session := CURRENT_SESSION.get_value()) and session.engine in [ConnectionEngine.SQLITE]:
            self.table_collation.Enable(False)
            self.convert_data_collation.Enable(False)
            self.table_row_format.Enable(False)

    def on_apply_database(self, event: wx.Event):
        database = CURRENT_DATABASE.get_value()
        session = CURRENT_SESSION.get_value()

        if database is None or session is None:
            return

        try:
            database.save()
            session.context.databases.refresh()

            database = next(
                (d for d in session.context.databases.get_value() if d.id == database.id),
                None,
            )

            if database is not None:
                CURRENT_DATABASE.set_value(None).set_value(database)
                session.context.set_database(database)

        except Exception as ex:
            logger.error(str(ex), exc_info=True)
            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

    def on_cancel_database(self, event: wx.Event):
        database = CURRENT_DATABASE.get_value()
        session = CURRENT_SESSION.get_value()

        if database is None or session is None:
            return

        if wx.MessageDialog(
                None,
                message=_("Do you want discard the change to {database_name}?").format(
                    database_name=database.name
                ),
                style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
        ).ShowModal() != wx.ID_YES:
            return

        try:
            session.context.databases.refresh()

            database = next(
                (d for d in session.context.databases.get_value() if d.id == database.id),
                None,
            )

            if database is not None:
                CURRENT_DATABASE.set_value(None).set_value(database)
                session.context.set_database(database)

        except Exception as ex:
            logger.error(str(ex), exc_info=True)
            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

    def on_delete_database(self, event: wx.Event):
        database = CURRENT_DATABASE.get_value()
        session = CURRENT_SESSION.get_value()

        if database is None or session is None:
            return

        choice = wx.MessageDialog(
            None,
            message=_(
                "Do you want to create a dump before dropping database '{database_name}'?\n\n"
                "Dump is not implemented yet.\n"
                "- Yes: open dump flow (coming soon, no drop).\n"
                "- No: drop the database now."
            ).format(database_name=database.name),
            caption=_("Delete database"),
            style=wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_WARNING,
        ).ShowModal()

        if choice == wx.ID_YES:
            wx.MessageBox(
                _("Dump is not implemented yet. No action has been performed."),
                _("Dump not available"),
                wx.OK | wx.ICON_INFORMATION,
            )
            return

        if choice != wx.ID_NO:
            return

        try:
            dropped = database.drop()

            if not dropped:
                wx.MessageBox(
                    _("Database deletion is not supported by this engine."),
                    _("Delete database"),
                    wx.OK | wx.ICON_WARNING,
                )
                return

            session.context.databases.refresh()

            CURRENT_DATABASE.set_value(None)
            next_database = next(iter(session.context.databases.get_value()), None)
            if next_database is not None:
                CURRENT_DATABASE.set_value(next_database)
                session.context.set_database(next_database)

            wx.MessageBox(
                _("Database deleted successfully"),
                _("Success"),
                wx.OK | wx.ICON_INFORMATION,
            )

        except Exception as ex:
            logger.error(str(ex), exc_info=True)
            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

    # VIEW
    def _on_current_view(self, current: SQLView):
        logger.debug(
            "ui trace: _on_current_view view=%s is_new=%s",
            getattr(current, "name", None) if current is not None else None,
            getattr(current, "is_new", None) if current is not None else None,
        )
        self.toggle_panel(current)

        self.btn_delete_view.Enable(current is not None and not current.is_new)

    def on_insert_view(self, event):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        if not session or not database:
            return
        CURRENT_VIEW.set_value(None)
        new_view = session.context.build_empty_view(database)
        CURRENT_VIEW.set_value(new_view)
        self._toggle_panel(3, True)
        self.MainFrameNotebook.SetSelection(3)

    # TRIGGER
    def _on_current_trigger(self, current: SQLTrigger):
        logger.debug(
            "ui trace: _on_current_trigger trigger=%s",
            getattr(current, "name", None) if current is not None else None,
        )
        self.toggle_panel(current)

    # TABLE
    def _on_current_table(self, table: SQLTable):
        logger.debug(
            "ui trace: _on_current_table table=%s",
            getattr(table, "name", None) if table is not None else None,
        )
        if NEW_TABLE.get_value() and not self.on_cancel_table(None):
            return

        if table:
            self._records_offset = 0
            self._records_limit = max(1, self.limit_records.GetValue())
            self._records_total_rows = 0
            self._records_total_key = None
            self._records_total_is_loading = False
            self.sql_query_filters.ClearAll()
            self._update_records_label(table)

            self.toggle_panel(table)
            self._set_records_paging_buttons(table)

            CURRENT_COLUMN.set_value(None)
            CURRENT_RECORDS.set_value([])
            CURRENT_INDEX.set_value(None)
            CURRENT_FOREIGN_KEY.set_value(None)

            try:
                self.sql_create_table.SetText(
                    sqlglot.parse_one(table.raw_create(), read=CURRENT_CONNECTION.get_value().engine.value.dialect).sql(pretty=True)
                )
            except Exception as ex:
                self.sql_create_table.SetText(
                    table.raw_create()
                )

            if self.MainFrameNotebook.GetSelection() == 5:
                self._load_records_page()

        self.tool_clone_table.Enable(table is not None)
        self.tool_delete_table.Enable(table is not None)

    def _on_new_table(self, table: SQLTable):
        self.btn_apply_table.Enable(bool(table is not None and table.is_valid))
        self.btn_cancel_table.Enable(bool(table is not None))

        if isinstance(table, SQLTable):
            self.sql_create_table.SetText(
                sqlglot.parse_one(table.raw_create(), read=table.database.context.connection.engine.value.dialect).sql(pretty=True)
            )

    # def _on_selected_table(self, table : SQLTable):
    #     self.tool_delete_table.Enable(table is not None)

    def on_insert_table(self, event):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()

        CURRENT_TABLE.set_value(None)
        # SELECTED_TABLE.set_value(None)

        NEW_TABLE.set_value(
            session.context.build_empty_table(database)
        )

        self._toggle_panel(2, True)
        self.MainFrameNotebook.SetSelection(2)
        self.table_name.SetFocus()

        self.controller_list_table_columns.model.clear()

    def do_apply_table(self, event: wx.Event):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        table = NEW_TABLE.get_value()

        if session is None or database is None or table is None:
            return

        if not table.is_valid:
            return

        try:
            table.save()

        except Exception as ex:
            logger.error(str(ex), exc_info=True)

            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

        else:
            NEW_TABLE.set_value(None)

            database.tables.refresh()

            if table := next((t for t in database.tables if t.id == table.id), None):
                CURRENT_TABLE.set_value(None).set_value(table.copy())
                # item = self.controller_tree_connections.model.ObjectToItem(updated_table)
                #
                # self.tree_ctrl_connections.UnselectAll()
                # self.tree_ctrl_connections.Select(item)

                # self.list_ctrl_table_columns.Select(item)

    def on_cancel_table(self, event: wx.Event):
        if new_table := NEW_TABLE.get_value():
            if wx.MessageDialog(None,
                                message=_("Do you want discard the change to {table_name}?").format(
                                    table_name=new_table.name
                                ),
                                style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                ).ShowModal() == wx.ID_YES:
                return self.do_cancel_table(event)

        return False

    def do_cancel_table(self, event: wx.Event):
        database = CURRENT_DATABASE.get_value()
        table = CURRENT_TABLE.get_value()

        NEW_TABLE.set_value(None)

        CURRENT_TABLE.set_value(None)

        if table and (table := next((t for t in database.tables if t.id == table.id), None)):
            CURRENT_TABLE.set_value(None).set_value(table.copy())

        return True

    def on_delete_table(self, event):
        table = CURRENT_TABLE.get_value()

        dialog = wx.MessageDialog(None,
                                  message=_("Do you want delete the table {table_name}?").format(
                                      table_name=table.name
                                  ),
                                  caption=_("Delete table"),
                                  style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            self.do_delete_table()

    def do_delete_table(self):
        database = CURRENT_DATABASE.get_value()
        if (table := CURRENT_TABLE.get_value()) and table.drop():
            CURRENT_TABLE.set_value(None)
            database.tables.refresh()

    def on_clone_table(self, event):
        table = CURRENT_TABLE.get_value()

        if table:
            new_table = table.copy()
            new_table.id = -1
            new_table.name = _("{table_name} (COPY)").format(table_name=new_table.name)

            for column in new_table.columns:
                column.id = -1
                column.table = new_table

            for index in new_table.indexes:
                index.id = -1
                index.table = new_table

            for foreign_key in new_table.foreign_keys:
                foreign_key.id = -1
                foreign_key.table = new_table

            NEW_TABLE.set_value(new_table)

            # SELECTED_TABLE.set_value(None)
            CURRENT_TABLE.set_value(None)

            self._toggle_panel(2, True)
            self.MainFrameNotebook.SetSelection(2)
            self.table_name.SetFocus()

    # COLUMNS
    def _on_current_column(self, column: SQLColumn):
        selected = self.controller_list_table_columns.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            self.toolbar_columns.EnableTool(self.tool_remove_column.GetId(), False)
            self.toolbar_columns.EnableTool(self.tool_move_up_column.GetId(), False)
            self.toolbar_columns.EnableTool(self.tool_move_down_column.GetId(), False)
            return

        row = self.controller_list_table_columns.model.GetRow(selected)
        total_rows = len(self.controller_list_table_columns.model.data) - 1

        self.toolbar_columns.EnableTool(self.tool_remove_column.GetId(), column is not None)
        self.toolbar_columns.EnableTool(self.tool_move_up_column.GetId(), column is not None and row > 0)
        self.toolbar_columns.EnableTool(self.tool_move_down_column.GetId(), column is not None and row < total_rows)

    def on_insert_column(self, event: wx.Event):
        self.controller_list_table_columns.on_column_insert(event)

    def on_delete_column(self, event: wx.Event):
        self.controller_list_table_columns.on_column_delete(event)

    def on_move_up_column(self, event: wx.Event):
        self.controller_list_table_columns.on_column_move_up(event)

    def on_move_down_column(self, event: wx.Event):
        self.controller_list_table_columns.on_column_move_down(event)

    # INDEXES
    def _on_current_index(self, index: SQLIndex):
        self.btn_delete_index.Enable(index is not None)

    def on_delete_index(self, event):
        self.controller_list_table_index.on_index_delete()

    def on_clear_index(self, event):
        self.controller_list_table_index.on_index_clear()

    # FOREIGN KEYS
    def _on_current_foreign_key(self, foreign_key: SQLForeignKey):
        self.btn_delete_foreign_key.Enable(foreign_key is not None)

    def on_insert_foreign_key(self, event: wx.Event):
        self.controller_list_table_foreign_key.on_foreign_key_insert(event)

    def on_delete_foreign_key(self, event: wx.Event):
        self.controller_list_table_foreign_key.on_foreign_key_delete(event)

    def on_clear_foreign_key(self, event: wx.Event):
        self.controller_list_table_foreign_key.on_foreign_key_clear(event)

    # RECORDS
    def _on_auto_apply(self, value: bool):
        auto_apply_enabled = self.chb_auto_apply.GetValue()
        
        # Enable/disable apply and cancel tools based on auto-apply state
        self.m_toolBar3.EnableTool(self.tool_apply_record.GetId(), not auto_apply_enabled)
        self.m_toolBar3.EnableTool(self.tool_cancel_record.GetId(), not auto_apply_enabled)

    def _initialize_record_toolbar_states(self):
        """Initialize toolbar states to ensure proper default behavior."""
        # Initially disable duplicate and delete tools (no selection)
        self.m_toolBar3.EnableTool(self.tool_duplicate_record.GetId(), False)
        self.m_toolBar3.EnableTool(self.tool_delete_record.GetId(), False)
        
        # Set apply/cancel tools based on auto-apply checkbox state
        auto_apply_enabled = self.chb_auto_apply.GetValue()
        self.m_toolBar3.EnableTool(self.tool_apply_record.GetId(), not auto_apply_enabled)
        self.m_toolBar3.EnableTool(self.tool_cancel_record.GetId(), not auto_apply_enabled)

    def _initialize_column_toolbar_states(self):
        """Initialize column toolbar states to ensure proper default behavior."""
        # Initially disable all column tools (no selection)
        self.toolbar_columns.EnableTool(self.tool_remove_column.GetId(), False)
        self.toolbar_columns.EnableTool(self.tool_move_up_column.GetId(), False)
        self.toolbar_columns.EnableTool(self.tool_move_down_column.GetId(), False)

    def on_auto_apply(self, event):
        AUTO_APPLY.set_value(self.chb_auto_apply.GetValue())

    def on_collapsible_pane_changed(self, event):
        self.panel_records.Layout()
        event.Skip()

    def _on_current_records(self, records: list[SQLRecord]):
        # Enable/disable duplicate and delete tools based on record selection
        self.m_toolBar3.EnableTool(self.tool_duplicate_record.GetId(), len(records) == 1)
        self.m_toolBar3.EnableTool(self.tool_delete_record.GetId(), len(records) > 0)

    def on_apply_record(self, event):
        self.controller_list_table_records.do_apply_records()

    def on_cancel_record(self, event):
        self.controller_list_table_records.do_cancel_records()

    def on_insert_record(self, event):
        self.controller_list_table_records.do_insert_record()

    def on_refresh_records(self, event):
        self.controller_list_table_records.do_refresh_records()

    def _on_filters_key_down(self, event: wx.KeyEvent):
        if event.ControlDown() and event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self._load_records_page()
        else:
            event.Skip()

    def _on_f5_refresh(self, event):
        logger.debug("F5 refresh triggered, page=%s", self.MainFrameNotebook.GetSelection())
        with Loader.cursor_wait():
            self.controller_tree_connections.refresh_current_database()
            page = self.MainFrameNotebook.GetSelection()
            if page == 2:
                self.controller_list_table_columns.do_refresh_columns()
            elif page == 5:
                self.controller_list_table_records.do_refresh_records()

    def on_duplicate_record(self, event):
        self.controller_list_table_records.do_duplicate_record()

    def on_delete_record(self, event):
        dialog = wx.MessageDialog(None,
                                  message=_("Do you want delete the records?"),
                                  style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            self.controller_list_table_records.do_delete_record()

    def on_first_records(self, event):
        self._records_offset = 0
        self._load_records_page()

    def on_prev_records(self, event):
        self._records_offset = max(self._records_offset - self._records_limit, 0)
        self._load_records_page()

    def on_next_records(self, event):
        table = CURRENT_TABLE.get_value()
        if table is None:
            return

        self._records_offset = min(
            self._records_offset + self._records_limit,
            self._get_records_last_offset(self._records_limit),
        )
        self._load_records_page()

    def on_last_records(self, event):
        table = CURRENT_TABLE.get_value()
        if table is None:
            return

        self._records_offset = self._get_records_last_offset(self._records_limit)
        self._load_records_page()

    def on_limit_records_changed(self, event):
        min_limit = max(1, int(self.limit_records.GetMin()))
        max_limit = max(min_limit, int(self.limit_records.GetMax()))
        self._records_limit = min(max(int(self.limit_records.GetValue()), min_limit), max_limit)
        wx.GetApp().settings.set_value("records", "limit", value=self._records_limit)
        self._records_offset = 0
        self._load_records_page()

    def on_apply_filters(self, event):
        self._records_offset = 0
        self._load_records_page()

    def on_new_query(self, event):
        self._create_new_query_page()

    def on_close_query(self, event):
        self._close_active_query_page()

    def on_save(self, event):
        page = self.notebook_query_editor.GetCurrentPage()
        if page is None:
            return

        self._save_query_page(page, force_save_as=False)

    def on_save_as_query(self, event):
        page = self.notebook_query_editor.GetCurrentPage()
        if page is None:
            return

        self._save_query_page(page, force_save_as=True)

    def on_execute_statement(self, event):
        controller = self._get_active_query_controller()
        if controller is not None:
            self.controller_query_records = controller
            controller.execute_current(event)

    def on_execute_statements(self, event):
        controller = self._get_active_query_controller()
        if controller is not None:
            self.controller_query_records = controller
            controller.execute_all(event)

    def on_stop_statements(self, event):
        controller = self._get_active_query_controller()
        if controller is not None:
            self.controller_query_records = controller
            controller.cancel_execution(event)

    def on_cancel_query_execution(self, event):
        controller = self._get_active_query_controller()
        if controller is not None:
            self.controller_query_records = controller
            controller.cancel_execution(event)

    # def on_clear_record(self, event):
    #     self.controller_list_table_records.on_row_clear()
