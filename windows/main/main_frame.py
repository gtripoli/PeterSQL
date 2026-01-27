import time

import math
from collections import defaultdict

import psutil
import os
import sqlglot
import textwrap

from typing import Optional, List, Union

import wx.adv
import wx.stc
import wx.lib.wordwrap

from gettext import gettext as _

from helpers import bytes_to_human
from helpers.logger import logger
from helpers.observables import CallbackEvent
from structures.connection import Connection
from structures.engines import ConnectionEngine

from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase
from structures.engines.context import QUERY_LOGS

from windows import MainFrameView
from windows.main import CURRENT_CONNECTION, CURRENT_DATABASE, CURRENT_TABLE, CURRENT_COLUMN, CURRENT_INDEX, CURRENT_FOREIGN_KEY, CURRENT_RECORDS, AUTO_APPLY, CURRENT_VIEW, CURRENT_TRIGGER, ENGINE_COMMON_KEYWORDS
from windows.connections import wx_colour_to_hex

from windows.main.database import ListDatabaseTable
from windows.main.explorer import TreeExplorerController
from windows.main.table import EditTableModel, NEW_TABLE
from windows.main.index import TableIndexController
from windows.main.check import TableCheckController
from windows.main.column import TableColumnsController
from windows.main.records import TableRecordsController
from windows.main.foreign_key import TableForeignKeyController


class MainFrameController(MainFrameView):
    app = wx.GetApp()

    def __init__(self):
        super().__init__(None)

        self.styled_text_ctrls_name = ["sql_query_logs", "sql_view", "sql_query_filters", "sql_create_table"]

        self.edit_table_model = EditTableModel()
        self.edit_table_model.bind_controls(
            name=self.table_name,
            comments=self.table_comment,
            auto_increment=self.table_auto_increment,
            collation=self.table_collation,
            engine=self.table_engine,
        )

        self.list_database_tables = ListDatabaseTable(self.list_ctrl_database_tables)

        self.controller_tree_connections = TreeExplorerController(self.tree_ctrl_explorer)
        self.controller_tree_connections.on_cancel_table = self.on_cancel_table

        self.controller_list_table_columns = TableColumnsController(self.list_ctrl_table_columns)
        self.controller_list_table_records = TableRecordsController(self.list_ctrl_table_records)

        self.controller_list_table_index = TableIndexController(self.dv_table_indexes)
        self.controller_list_table_check = TableCheckController(self.dv_table_checks)
        self.controller_list_table_foreign_key = TableForeignKeyController(self.dv_table_foreign_keys)

        self._setup_query_editors()

        self._setup_subscribers()

        # Memory update timer
        self.memory_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._update_memory, self.memory_timer)
        self.memory_timer.Start(5000)  # Update every 5 seconds

        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.on_sys_colour_changed)

    def on_sys_colour_changed(self, event):
        self._setup_query_editors()

    def _setup_query_editors(self):
        bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)

        ln_bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
        ln_fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

        is_dark = wx.SystemSettings.GetAppearance().IsDark()

        if is_dark:
            keyword = "#569cd6"
            string = "#ce9178"
            comment = "#6a9955"
            number = "#b5cea8"
            operator = wx_colour_to_hex(fg)
        else:
            keyword = "#0000ff"
            string = "#990099"
            comment = "#007f00"
            number = "#ff6600"
            operator = "#000000"

        for styled_text_ctrl_name in self.styled_text_ctrls_name:
            styled_text_ctrl = getattr(self, styled_text_ctrl_name)

            font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            styled_text_ctrl.SetLexer(wx.stc.STC_LEX_SQL)

            styled_text_ctrl.StyleClearAll()
            styled_text_ctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)

            styled_text_ctrl.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, bg)
            # styled_text_ctrl.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, fg)

            # Numbers
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_NUMBER, f"fore:{number}")

            # Comments
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENT, f"fore:{comment},italic")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENTLINE, f"fore:{comment},italic")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENTDOC, f"fore:{comment},italic")

            # Keys
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_WORD, f"fore:{keyword},bold")
            # styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_WORD2, f"fore:{keyword},bold")

            # String
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_CHARACTER, f"fore:{string}")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_STRING, f"fore:{string}")

            # Operator
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_OPERATOR, f"fore:{operator},bold")

            # Table name, Columns, etc.
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_IDENTIFIER, "fore:#333333")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_QUOTEDIDENTIFIER, "fore:#333333")

            # Line numbers
            styled_text_ctrl.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
            styled_text_ctrl.SetMarginWidth(0, 40)
            # print(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION))
            styled_text_ctrl.StyleSetSpec(
                wx.stc.STC_STYLE_LINENUMBER,
                f"back:{wx_colour_to_hex(ln_bg)},"
                f"fore:{wx_colour_to_hex(ln_fg)}"
            )
            styled_text_ctrl.SetMarginBackground(0, ln_bg)

            # Caret e selection
            styled_text_ctrl.SetCaretForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            styled_text_ctrl.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
            styled_text_ctrl.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

            # styled_text_ctrl.SetCaretForeground(wx.Colour("#000000"))
            # styled_text_ctrl.SetSelBackground(True, wx.Colour("#cce8ff"))
            # styled_text_ctrl.SetSelForeground(True, wx.Colour("#ff0000P"))

    def _setup_subscribers(self):
        self.toggle_panel()

        QUERY_LOGS.subscribe(self._write_query_log, CallbackEvent.ON_APPEND)

        # SESSIONS.subscribe(self._load_connection, CallbackEvent.ON_APPEND)

        CURRENT_CONNECTION.subscribe(self._on_current_connection)

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
        from windows.connections.manager import ConnectionsManager

        sm = ConnectionsManager(self)
        sm.Show()

    def toggle_panel(self, current: Optional[Union[Connection, SQLDatabase, SQLTable, SQLView, SQLTrigger]] = None):
        current_connection = CURRENT_CONNECTION()
        current_database = CURRENT_DATABASE()
        current_table = CURRENT_TABLE()
        current_view = CURRENT_VIEW()
        current_trigger = CURRENT_TRIGGER()

        self.MainFrameNotebook.SetSelection(0)

        if not current_database:
            self.MainFrameNotebook.GetPage(1).Hide()

        if not current_table:
            self.MainFrameNotebook.GetPage(2).Hide()

        if not current_view:
            self.MainFrameNotebook.GetPage(3).Hide()

        if not current_trigger:
            self.MainFrameNotebook.GetPage(4).Hide()

        if not current_table and not current_view:
            self.MainFrameNotebook.GetPage(5).Hide()

        if isinstance(current, Connection):
            self.MainFrameNotebook.SetSelection(0)

        elif isinstance(current, SQLDatabase):
            self.MainFrameNotebook.GetPage(1).Show()
            self.MainFrameNotebook.SetSelection(1)

        elif isinstance(current, SQLTable) or isinstance(current, SQLView):
            if isinstance(current, SQLTable):
                self.MainFrameNotebook.GetPage(2).Show()
                self.MainFrameNotebook.SetSelection(2)

            if isinstance(current, SQLView):
                self.MainFrameNotebook.GetPage(3).Show()
                self.MainFrameNotebook.SetSelection(3)

            self.MainFrameNotebook.GetPage(5).Show()

        elif isinstance(current, SQLTrigger):
            self.MainFrameNotebook.GetPage(4).Show()
            self.MainFrameNotebook.SetSelection(3)

    def on_page_chaged(self, event):
        if int(event.Selection) == 5:
            if table := CURRENT_TABLE():
                table.load_records()

                self.controller_list_table_records.load_model()

    def _on_current_connection(self, connection: Connection):
        self.toggle_panel(connection)

        if connection:
            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Connection')}: {connection.name}", 0)

            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Version')}: {connection.context.get_server_version()}", 1)

            wx.CallAfter(self.status_bar.SetStatusText, f"{_('Uptime')}: {self._format_server_uptime(connection.context.get_server_uptime())}", 2)

            common_keywords = f"{ENGINE_COMMON_KEYWORDS} {connection.context.KEYWORDS}".strip()

            colors_datatypes = defaultdict(list)

            for datatype in connection.context.DATATYPE.get_all():
                colors_datatypes[datatype.category.value.color].append(datatype.name.lower())
                colors_datatypes[datatype.category.value.color].extend([d.lower() for d in datatype.alias])

            for stc_name in self.styled_text_ctrls_name:
                stc_ctrl = getattr(self, stc_name)

                stc_ctrl.SetKeyWords(0, common_keywords)

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

        if CURRENT_CONNECTION.get_value().engine in [ConnectionEngine.SQLITE]:
            self.table_collation.Enable(False)

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
            # `%(database_name)s`.`%(table_name)s`
            self.name_database_table.SetLabel(
                self.name_database_table.GetLabel() % {
                    "database_name": table.database.name,
                    "table_name": table.name,
                    "total_rows": table.total_rows
                }
            )

            self.toggle_panel(table)

            CURRENT_COLUMN.set_value(None)
            CURRENT_RECORDS.set_value([])
            CURRENT_INDEX.set_value(None)
            CURRENT_FOREIGN_KEY.set_value(None)

            try :
                self.sql_create_table.SetText(
                    sqlglot.parse_one(table.raw_create(), read=CURRENT_CONNECTION.get_value().engine.value.dialect).sql(pretty=True)
                )
            except Exception as ex:
                self.sql_create_table.SetText(
                    table.raw_create()
                )


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
        connection = CURRENT_CONNECTION.get_value()
        database = CURRENT_DATABASE.get_value()

        CURRENT_TABLE.set_value(None)
        # SELECTED_TABLE.set_value(None)

        NEW_TABLE.set_value(
            connection.context.build_empty_table(database)
        )

        self._toggle_panel(2, True)
        self.MainFrameNotebook.SetSelection(2)
        self.table_name.SetFocus()

        self.controller_list_table_columns.model.clear()

    def do_apply_table(self, event: wx.Event):
        connection = CURRENT_CONNECTION.get_value()
        database = CURRENT_DATABASE.get_value()
        table = NEW_TABLE.get_value()

        if connection is None or database is None or table is None:
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
                                message=_(f'Do you want discard the change to {new_table.name}?'),
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
                                  message=_(f'Do you want delete the table {table.name}?'),
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
            new_table.name = _(f"{new_table.name} (COPY)")

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

    def _on_current_records(self, records: List[SQLRecord]):
        self.btn_duplicate_record.Enable(len(records) == 1)
        self.btn_delete_record.Enable(len(records) > 0)

    def on_insert_record(self, event):
        self.controller_list_table_records.do_insert_record()

    def on_duplicate_record(self, event):
        self.controller_list_table_records.do_duplicate_record()

    def on_delete_record(self, event):
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the records?'),
                                  style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            self.controller_list_table_records.do_delete_record()

    def on_apply_filters(self, event):
        # self.controller_list_table_records.do_apply_filters()
        table = CURRENT_TABLE.get_value()
        if table:
            filters = (self.sql_query_filters.GetSelectedText() or self.sql_query_filters.GetText()).strip()
            table.load_records(filters)

            self.controller_list_table_records.load_model()

    # def on_clear_record(self, event):
    #     self.controller_list_table_records.on_row_clear()
