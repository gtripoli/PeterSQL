import math
import datetime
import psutil
import os

from typing import Optional, List, Union

import wx.stc
import wx.html2

from gettext import gettext as _

from helpers.observables import ObservableList
from engines.session import Session
from engines.structures.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase
from engines.structures.context import LOG_QUERY

from windows import MainFrameView
from windows.main import SESSIONS, CURRENT_SESSION, CURRENT_DATABASE, CURRENT_TABLE, CURRENT_COLUMN, CURRENT_INDEX, CURRENT_FOREIGN_KEY, CURRENT_RECORDS, AUTO_APPLY, CURRENT_VIEW, CURRENT_TRIGGER
from windows.main.sessions import TreeSessionsController
from windows.main.table import EditTableModel, NEW_TABLE
from windows.main.index import TableIndexController
from windows.main.column import TableColumnsController
from windows.main.records import TableRecordsController
from windows.main.foreign_key import TableForeignKeyController


class MainFrameController(MainFrameView):
    app = wx.GetApp()

    def __init__(self):
        super().__init__(None)

        self.edit_table_model = EditTableModel()
        self.edit_table_model.bind_controls(
            name=self.table_name,
            comments=self.table_comment,
            auto_increment=self.table_auto_increment,
            collation=self.table_collation,
            engine=self.table_engine,
        )

        self.controller_tree_sessions = TreeSessionsController(self.tree_ctrl_sessions)
        self.controller_tree_sessions.on_cancel_table = self.on_cancel_table

        self.controller_list_table_columns = TableColumnsController(self.list_ctrl_table_columns)
        self.controller_list_table_records = TableRecordsController(self.list_ctrl_table_records)

        self.controller_list_table_index = TableIndexController(self.dv_table_indexes)
        self.controller_list_table_foreign_key = TableForeignKeyController(self.dv_table_foreign_keys)

        self._setup_query_logs()

        self._setup_subscribers()

        # Memory update timer
        self.memory_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._update_memory, self.memory_timer)
        self.memory_timer.Start(5000)  # Update every 5 seconds

    def _setup_query_logs(self):
        for name_styled_text_ctrl in ["sql_logs_query", "sql_view"]:
            styled_text_ctrl = getattr(self, name_styled_text_ctrl)

            font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            styled_text_ctrl.SetLexer(wx.stc.STC_LEX_SQL)
            styled_text_ctrl.SetKeyWords(0, (
                "select from where insert into update delete create alter drop table view "
                "index primary key unique not null default auto_increment autoincrement values set pragma"
                "and or as distinct order by group having join left right inner outer on "
                "if exists like in is between limit offset case when then else end show describe"
                "modify add drop column"
                "sqlite_master begin rollback"
            ))

            styled_text_ctrl.StyleClearAll()
            styled_text_ctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
            styled_text_ctrl.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, wx.Colour("#000000"))
            styled_text_ctrl.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, wx.Colour("#ffffff"))
            # styled_text_ctrl.StyleClearAll()

            # Numbers
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_NUMBER, "fore:#ff6600")

            # Comments
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENT, "fore:#007f00,italic")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENTLINE, "fore:#007f00,italic")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_COMMENTDOC, "fore:#007f00,italic")

            # Keys
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_WORD, "fore:#0000ff,bold")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_WORD2, "fore:#0000ff,bold")

            # String
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_CHARACTER, "fore:#990099")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_STRING, "fore:#990099")

            # Operator
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_OPERATOR, "fore:#000000,bold")

            # Table name, Columns, etc.
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_IDENTIFIER, "fore:#333333")
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_SQL_QUOTEDIDENTIFIER, "fore:#333333")

            # Line numbers
            styled_text_ctrl.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
            styled_text_ctrl.SetMarginWidth(0, 40)
            styled_text_ctrl.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "back:#e0e0e0,fore:#555555")

            # Caret e selection
            styled_text_ctrl.SetCaretForeground(wx.Colour("#000000"))
            styled_text_ctrl.SetSelBackground(True, wx.Colour("#cce8ff"))
            styled_text_ctrl.SetSelForeground(True, wx.Colour("#000000"))

    def _setup_subscribers(self):
        self.toggle_panel()

        LOG_QUERY.subscribe(self._write_query_log, ObservableList.CallbackEvent.ON_APPEND)

        SESSIONS.subscribe(self._load_session, ObservableList.CallbackEvent.ON_APPEND)

        CURRENT_SESSION.subscribe(self._on_current_session)

        CURRENT_DATABASE.subscribe(self._on_current_database)

        CURRENT_VIEW.subscribe(self._on_current_view)

        CURRENT_TRIGGER.subscribe(self._on_current_trigger)

        CURRENT_TABLE.subscribe(self._on_current_table)

        CURRENT_COLUMN.subscribe(self._on_current_column)

        CURRENT_INDEX.subscribe(self._on_current_index)

        CURRENT_FOREIGN_KEY.subscribe(self._on_current_foreign_key)

        CURRENT_RECORDS.subscribe(self._on_current_records)

        NEW_TABLE.subscribe(self._on_new_table)

        AUTO_APPLY.subscribe(self._on_auto_apply)

        # NEW_COLUMN.subscribe(self._on_new_column)

    def _write_query_log(self, text: str):
        self.sql_logs_query.AppendText(f"{text}\n")
        self.sql_logs_query.GotoLine(self.sql_logs_query.GetLineCount() - 1)

    def _toggle_panel(self, index: int, visible: bool):
        panel = self.MainFrameNotebook.GetPage(index)
        panel.Show(visible)
        panel.Enable(visible)

    def _toggle_edit_table(self, visible: bool):
        self._toggle_panel(2, visible)
        self._toggle_panel(3, visible)

    # def _refresh_database(self):
    #     session = CURRENT_SESSION.get_value()
    #     db = CURRENT_DATABASE.get_value()
    #     db.tables = session.statement.get_tables(database=db)
    #     CURRENT_DATABASE.set_value(db)

    def _select_tree_item(self, **filters):
        if table_item := self.controller_tree_sessions.find_by_data(**filters):
            print("select", table_item)
            tree = self.controller_tree_sessions.tree_ctrl_sessions
            tree.UnselectAll()

            tree.SelectItem(table_item, True)
            tree.EnsureVisible(table_item)

    def _format_server_uptime(self, uptime: Optional[float] = None) -> str:
        if not uptime:
            uptime = (datetime.datetime.now()).timestamp()

        return (f"{math.floor(uptime / 86400)} {_('days')}, "
                f"{math.floor((uptime % 86400) / 3600)} {_('hours')}, "
                f"{math.floor((uptime % 3600) / 60)} {_('minutes')}, "
                f"{math.floor(uptime % 60)} {_('seconds')}")

    def _update_memory(self, event):
        memory_info = psutil.Process(os.getpid()).memory_info()
        used = memory_info.rss / 1024 / 1024  # MB
        total = psutil.virtual_memory().total / 1024 / 1024  # MB
        percentage = used / total

        self.status_bar.SetStatusText(_('Memory used: {used:.2f} ({percentage:.2%})').format(used=used, percentage=percentage), 3)

    def _load_session(self, session: Session):
        self.controller_tree_sessions.append_session(session)

    def do_close(self, event):
        super().Destroy()
        wx.GetApp().ExitMainLoop()

    def do_open_session_manager(self, event):
        from windows.sessions.controller import SessionManagerController

        sm = SessionManagerController(self)
        sm.Show()

    def toggle_panel(self, current: Optional[Union[Session, SQLDatabase, SQLTable, SQLView, SQLTrigger]] = None):

        current_session = CURRENT_SESSION.get_value()
        current_database = CURRENT_DATABASE.get_value()
        current_table = CURRENT_TABLE.get_value()
        current_view = CURRENT_VIEW.get_value()
        current_trigger = CURRENT_TRIGGER.get_value()

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

        if isinstance(current, Session):
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

    def _on_current_session(self, session: Session):
        self.toggle_panel(session)

        self.status_bar.SetStatusText(f"{_('Session')}: {session.name}", 0)

        self.status_bar.SetStatusText(f"{_('Version')}: {session.context.get_server_version()}", 1)

        self.status_bar.SetStatusText(f"{_('Uptime')}: {self._format_server_uptime(session.context.get_server_uptime())}", 2)

    def _on_current_database(self, database: SQLDatabase):
        self.toggle_panel(database)

    # VIEW
    def _on_current_view(self, current: SQLView):
        # if NEW_TABLE.get_value() and not self.on_cancel_table(None):
        #     return

        self.toggle_panel(current)

        # if self.MainFrameNotebook.GetSelection() < 2:
        #     self.MainFrameNotebook.SetSelection(2)
        #     self.table_name.SetFocus()

        # CURRENT_COLUMN.set_value(None)
        # CURRENT_RECORDS.set_value([])
        # CURRENT_INDEX.set_value(None)
        # CURRENT_FOREIGN_KEY.set_value(None)

        self.btn_delete_view.Enable(current is not None)

    # TRIGGER
    def _on_current_trigger(self, current: SQLTrigger):
        # if NEW_TABLE.get_value() and not self.on_cancel_table(None):
        #     return

        self.toggle_panel(current)

        # if self.MainFrameNotebook.GetSelection() < 2:
        #     self.MainFrameNotebook.SetSelection(2)
        #     self.table_name.SetFocus()

        # CURRENT_COLUMN.set_value(None)
        # CURRENT_RECORDS.set_value([])
        # CURRENT_INDEX.set_value(None)
        # CURRENT_FOREIGN_KEY.set_value(None)

        # self.btn_delete_view.Enable(view is not None)

    # TABLE
    def _on_current_table(self, current: SQLTable):
        if NEW_TABLE.get_value() and not self.on_cancel_table(None):
            return

        self.toggle_panel(current)

        # print("MainFrameNotebook", self.MainFrameNotebook.GetSelection())
        # self._toggle_edit_table(True)
        # if self.MainFrameNotebook.GetSelection() < 2:
        #     self.MainFrameNotebook.SetSelection(2)
        #     self.table_name.SetFocus()

        CURRENT_COLUMN.set_value(None)
        CURRENT_RECORDS.set_value([])
        CURRENT_INDEX.set_value(None)
        CURRENT_FOREIGN_KEY.set_value(None)

        self.btn_delete_table.Enable(current is not None)

    def _on_new_table(self, current: SQLTable):
        self.btn_apply_table.Enable(bool(current is not None and current.is_valid()))
        self.btn_cancel_table.Enable(bool(current is not None))

    def on_insert_table(self, event):
        NEW_TABLE.set_value(None)
        CURRENT_TABLE.set_value(None)

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

        if not table.is_valid():
            return

        try:
            table.save()

        except Exception as ex:
            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

        else:
            NEW_TABLE.set_value(None)

            if updated_table := next((t for t in list(database.tables) if t.id == table.id), None):
                if item := self.controller_tree_sessions.find_by_data(name=table.name):
                    self.tree_ctrl_sessions.SetItemData(item, updated_table)

            wx.CallAfter(self._select_tree_item, **{"name": database.name})

            wx.CallAfter(self._select_tree_item, **{"name": table.name})

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

        if table := next((t for t in database.tables if t.name == table.name), None):
            CURRENT_TABLE.set_value(None).set_value(table.copy())

        return True

    def on_delete_table(self, event):
        table = CURRENT_TABLE.get_value()

        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the table {table.name}?'),
                                  style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            self.do_delete_table()

    def do_delete_table(self):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        table = CURRENT_TABLE.get_value()
        if session.context.drop_table(database, table):
            CURRENT_TABLE.set_value(None)
            # self._refresh_database()

            self._select_tree_item(name=database.name)

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

        print("row, total_rows", row, total_rows)

        self.btn_delete_column.Enable(column is not None)
        self.btn_move_up_column.Enable(column is not None and row > 0)
        self.btn_move_down_column.Enable(column is not None and row < total_rows)

    def on_insert_column(self, event):
        self.controller_list_table_columns.on_column_insert()

    def on_delete_column(self, event):
        self.controller_list_table_columns.on_column_delete()

    def on_move_up_column(self, event):
        self.controller_list_table_columns.on_column_move_up()

    def on_move_down_column(self, event):
        self.controller_list_table_columns.on_column_move_down()

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

    def on_insert_foreign_key(self, event):
        self.controller_list_table_foreign_key.on_foreign_key_insert()

    def on_delete_foreign_key(self, event):
        self.controller_list_table_foreign_key.on_foreign_key_delete()

    def on_clear_foreign_key(self, event):
        self.controller_list_table_foreign_key.on_foreign_key_clear()

    # RECORDS
    def _on_auto_apply(self, value: bool):
        self.btn_cancel_record.Enable(not self.chb_auto_apply.GetValue())
        self.btn_apply_record.Enable(not self.chb_auto_apply.GetValue())

    def on_auto_apply(self, event):
        AUTO_APPLY.set_value(self.chb_auto_apply.GetValue())

    def _on_current_records(self, records: List[SQLRecord]):
        print("_on_current_records", records)
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

    # def on_clear_record(self, event):
    #     self.controller_list_table_records.on_row_clear()
