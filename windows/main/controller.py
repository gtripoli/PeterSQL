import math
import os
import threading
import time
import contextlib

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
from windows.main.tabs.query import QueryResultsController
from windows.main.tabs.table import EditTableModel, NEW_TABLE
from windows.main.tabs.index import TableIndexController
from windows.main.tabs.check import TableCheckController
from windows.main.tabs.column import TableColumnsController
from windows.main.tabs.records import TableRecordsController
from windows.main.tabs.database import ListDatabaseTable
from windows.main.tabs.database_options import DatabaseOptionsController
from windows.main.tabs.explorer import TreeExplorerController
from windows.main.tabs.foreign_key import TableForeignKeyController
from windows.main.tabs.view import ViewEditorController


class MainFrameController(MainFrameView):
    app = wx.GetApp()

    def __init__(self):
        super().__init__(None)

        self.styled_text_ctrls_name = ["sql_query_logs", "stc_view_select", "sql_query_filters", "sql_create_table", "sql_query_editor"]

        self.edit_table_model = EditTableModel()
        self.edit_table_model.bind_controls(
            name=self.table_name,
            comments=self.table_comment,
            auto_increment=self.table_auto_increment,
            collation=self.table_collation,
            engine=self.table_engine,
        )

        self.list_database_tables = ListDatabaseTable(self.list_ctrl_database_tables)
        self.controller_database_options = DatabaseOptionsController(self)

        self.controller_tree_connections = TreeExplorerController(self.tree_ctrl_explorer)
        self.controller_tree_connections.on_cancel_table = self.on_cancel_table

        self.controller_list_table_columns = TableColumnsController(self.list_ctrl_table_columns)
        self.controller_list_table_records = TableRecordsController(self.list_ctrl_table_records)

        self.controller_list_table_index = TableIndexController(self.dv_table_indexes)
        self.controller_list_table_check = TableCheckController(self.dv_table_checks)
        self.controller_list_table_foreign_key = TableForeignKeyController(self.dv_table_foreign_keys)

        self.controller_query_records = QueryResultsController(
            self.sql_query_editor,
            self.notebook_sql_results,
            cancel_button=self.cancel_query_execution,
        )

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

        self._setup_subscribers()

        # Memory update timer
        self.memory_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._update_memory, self.memory_timer)
        self.memory_timer.Start(5000)  # Update every 5 seconds

        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.on_sys_colour_changed)

    def on_sys_colour_changed(self, event):
        self._setup_query_editors()

        wx.CallAfter(self.app.theme_manager.refresh)
        event.Skip()

    def _setup_query_editors(self):
        for styled_text_ctrl_name in self.styled_text_ctrls_name:
            styled_text_ctrl = getattr(self, styled_text_ctrl_name)

            styled_text_ctrl.EmptyUndoBuffer()

            wx.GetApp().theme_manager.register(styled_text_ctrl, lambda: wx.GetApp().syntax_registry.get("sql"))

            apply_stc_theme(styled_text_ctrl, SQL)

            sql_completion_provider = SQLCompletionProvider(
                get_database=lambda: CURRENT_DATABASE.get_value(),
                get_current_table=lambda: CURRENT_TABLE.get_value(),
            )

            sql_autocomplete_controller = SQLAutoCompleteController(
                editor=styled_text_ctrl,
                provider=sql_completion_provider,
                settings=wx.GetApp().settings,
                theme_loader=wx.GetApp().theme_loader,
            )
            
            sql_template_menu = SQLTemplateMenuController(
                editor=styled_text_ctrl,
                get_database=lambda: CURRENT_DATABASE.get_value(),
                get_current_table=lambda: CURRENT_TABLE.get_value(),
            )

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
        total_rows = row.get("total_rows")
        if total_rows is None and row:
            total_rows = next(iter(row.values()), 0)

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
            context.connect()
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
        locale = wx.GetApp().settings.get_value("locale") or wx.GetApp().settings.get_value("language") or "en_US"
        try:
            return babel.numbers.format_decimal(value, locale=locale)
        except Exception:
            return str(value)

    def _load_records_limit_from_settings(self) -> int:
        settings = wx.GetApp().settings
        if settings.get_value("records") is None:
            settings.set_value("records", value={})

        max_limit = 1000
        if hasattr(self, "limit_records"):
            with contextlib.suppress(Exception):
                max_limit = max(1, int(self.limit_records.GetMax()))

        saved_limit = settings.get_value("records", "limit")
        if saved_limit is None:
            return min(100, max_limit)

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
            self._load_records_page()
            return

        self._update_records_label(table)
        self._set_records_paging_buttons(table)

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

        with Loader.cursor_wait():
            table.load_records(filters=filters, limit=limit, offset=self._records_offset)
            self.controller_list_table_records.load_model()

        self._update_records_label(table)
        self._set_records_paging_buttons(table)

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
        from structures.session import Session

        self.toggle_panel(session.connection if session else None)

        if session:
            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Connection')}: {session.name}", 0)

            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Version')}: {session.context.get_server_version()}", 1)

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
        self.toggle_panel(database)

        if database:
            self.table_engine.Enable(len(database.context.ENGINES) > 1)
            self.table_engine.SetItems(database.context.ENGINES)

            self.table_collation.Enable(len(database.context.COLLATIONS.keys()) > 1)
            self.table_collation.SetItems(list(database.context.COLLATIONS.keys()))

        if (session := CURRENT_SESSION.get_value()) and session.engine in [ConnectionEngine.SQLITE]:
            self.table_collation.Enable(False)

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
        self.toggle_panel(current)

        self.btn_delete_view.Enable(current is not None)

    # TRIGGER
    def _on_current_trigger(self, current: SQLTrigger):
        self.toggle_panel(current)

    # TABLE
    def _on_current_table(self, table: SQLTable):
        if NEW_TABLE.get_value() and not self.on_cancel_table(None):
            return

        if table:
            self._records_offset = 0
            self._records_limit = max(1, self.limit_records.GetValue())
            self._records_total_rows = 0
            self._records_total_key = None
            self._records_total_is_loading = False
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

        self.btn_clone_table.Enable(table is not None)
        self.btn_delete_table.Enable(table is not None)

    def _on_new_table(self, table: SQLTable):
        self.btn_apply_table.Enable(bool(table is not None and table.is_valid))
        self.btn_cancel_table.Enable(bool(table is not None))

        if isinstance(table, SQLTable):
            self.sql_create_table.SetText(
                sqlglot.parse_one(table.raw_create(), read=table.database.context.connection.engine.value.dialect).sql(pretty=True)
            )

    # def _on_selected_table(self, table : SQLTable):
    #     self.btn_delete_table.Enable(table is not None)

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
            self.btn_delete_column.Enable(False)
            self.btn_move_up_column.Enable(False)
            self.btn_move_down_column.Enable(False)
            return

        row = self.controller_list_table_columns.model.GetRow(selected)
        total_rows = len(self.controller_list_table_columns.model.data) - 1

        self.btn_delete_column.Enable(column is not None)
        self.btn_move_up_column.Enable(column is not None and row > 0)
        self.btn_move_down_column.Enable(column is not None and row < total_rows)

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
        self.btn_cancel_record.Enable(not self.chb_auto_apply.GetValue())
        self.btn_apply_record.Enable(not self.chb_auto_apply.GetValue())

    def on_auto_apply(self, event):
        AUTO_APPLY.set_value(self.chb_auto_apply.GetValue())

    def on_collapsible_pane_changed(self, event):
        self.panel_records.Layout()
        event.Skip()

    def _on_current_records(self, records: list[SQLRecord]):
        self.btn_duplicate_record.Enable(len(records) == 1)
        self.btn_delete_record.Enable(len(records) > 0)

    def on_insert_record(self, event):
        self.controller_list_table_records.do_insert_record()

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

    def on_cancel_query_execution(self, event):
        self.controller_query_records.cancel_execution(event)

    # def on_clear_record(self, event):
    #     self.controller_list_table_records.on_row_clear()
