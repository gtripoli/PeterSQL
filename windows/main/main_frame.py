import math
import datetime
import psutil
import os

from typing import Optional, List

import wx.stc
import wx.html2

from gettext import gettext as _

from helpers.observables import ObservableArray
from models.session import Session
from models.structures.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord
from models.structures.statement import LOG_QUERY

from windows import MainFrameView
from windows.main import SESSIONS, CURRENT_SESSION, CURRENT_DATABASE, CURRENT_TABLE, CURRENT_COLUMN, CURRENT_INDEX, CURRENT_FOREIGN_KEY, CURRENT_RECORDS, AUTO_APPLY
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
        self.query_logs.SetLexer(wx.stc.STC_LEX_SQL)
        self.query_logs.SetKeyWords(0, (
            "select from where insert into update delete create alter drop table view "
            "index primary key unique not null default auto_increment autoincrement values set pragma"
            "and or as distinct order by group having join left right inner outer on "
            "if exists like in is between limit offset case when then else end show describe"
            "modify add drop column"
            "sqlite_master begin rollback"
        ))

        self.query_logs.StyleClearAll()
        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.query_logs.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.query_logs.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, wx.Colour("#000000"))
        self.query_logs.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, wx.Colour("#ffffff"))
        self.query_logs.StyleClearAll()

        # Numbers
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_NUMBER, "fore:#ff6600")

        # Comments
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_COMMENT, "fore:#007f00,italic")
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_COMMENTLINE, "fore:#007f00,italic")
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_COMMENTDOC, "fore:#007f00,italic")

        # Keys
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_WORD, "fore:#0000ff,bold")
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_WORD2, "fore:#0000ff,bold")

        # String
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_CHARACTER, "fore:#990099")
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_STRING, "fore:#990099")

        # Operator
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_OPERATOR, "fore:#000000,bold")

        # Table name, Columns, etc.
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_IDENTIFIER, "fore:#333333")
        self.query_logs.StyleSetSpec(wx.stc.STC_SQL_QUOTEDIDENTIFIER, "fore:#333333")

        # Line numbers
        self.query_logs.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        self.query_logs.SetMarginWidth(0, 40)
        self.query_logs.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "back:#e0e0e0,fore:#555555")

        # Caret e selection
        self.query_logs.SetCaretForeground(wx.Colour("#000000"))
        self.query_logs.SetSelBackground(True, wx.Colour("#cce8ff"))
        self.query_logs.SetSelForeground(True, wx.Colour("#000000"))

    def _setup_subscribers(self):
        LOG_QUERY.subscribe(self._write_query_log, ObservableArray.CallbackEvent.ON_APPEND)

        SESSIONS.subscribe(self._load_session, ObservableArray.CallbackEvent.ON_APPEND)

        CURRENT_SESSION.subscribe(self.show_panel_session)

        CURRENT_DATABASE.subscribe(self.show_panel_database)

        CURRENT_TABLE.subscribe(self._on_current_table)

        CURRENT_COLUMN.subscribe(self._on_current_column)

        CURRENT_INDEX.subscribe(self._on_current_index)

        CURRENT_FOREIGN_KEY.subscribe(self._on_current_foreign_key)

        CURRENT_RECORDS.subscribe(self._on_current_records)

        NEW_TABLE.subscribe(self._on_new_table)

        AUTO_APPLY.subscribe(self._on_auto_apply)

        # NEW_COLUMN.subscribe(self._on_new_column)

    def _write_query_log(self, text: str):
        self.query_logs.AppendText(f"{text}\n")
        self.query_logs.GotoLine(self.query_logs.GetLineCount() - 1)

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

    def show_panel_session(self, session: Session):
        self._toggle_panel(0, True)
        self.MainFrameNotebook.SetSelection(0)

        self.status_bar.SetStatusText(f"{_('Version')}: {session.statement.get_server_version()}", 1)

        self.status_bar.SetStatusText(f"{_('Uptime')}: {self._format_server_uptime(session.statement.get_server_uptime())}", 2)

    def show_panel_database(self, *args):
        self._toggle_panel(1, True)
        self.MainFrameNotebook.SetSelection(1)

    def on_page_changed(self, event: wx.BookCtrlEvent):
        if event.GetEventObject() != self.MainFrameNotebook:
            event.Skip()
            return
        if event.GetSelection() == 1 and not CURRENT_TABLE.get_value() and not NEW_TABLE.get_value():
            self._toggle_edit_table(False)

    # TABLE
    def _on_current_table(self, table: SQLTable):
        self._toggle_edit_table(True)
        if self.MainFrameNotebook.GetSelection() == 1:
            self.MainFrameNotebook.SetSelection(2)
            self.table_name.SetFocus()

        self.btn_delete_table.Enable(table is not None)

    def _on_new_table(self, new_table: SQLTable):
        self.btn_apply_table.Enable(bool(new_table is not None and new_table.is_valid()))
        self.btn_cancel_table.Enable(bool(new_table is not None))

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

        try :
            session.statement.save_table(database, table)


        except Exception as ex :
            wx.MessageDialog(None, str(ex), "Error", wx.OK | wx.ICON_ERROR).ShowModal()

        else :
            NEW_TABLE.set_value(None)

            if updated_table := next((t for t in database.tables if t.name == table.name), None):
                CURRENT_TABLE.set_value(updated_table)

            wx.CallAfter(self._select_tree_item, **{"name": database.name})

            wx.CallAfter(self._select_tree_item, **{"name": table.name})

    def do_cancel_table(self, event: wx.Event):
        database = CURRENT_DATABASE.get_value()
        table = CURRENT_TABLE.get_value()

        NEW_TABLE.set_value(None)

        if table := next((t for t in database.tables if t.name == table.name), None):
            print("set table", None)
            CURRENT_TABLE.set_value(None)
            print("set table", table)
            CURRENT_TABLE.set_value(table)

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
        if session.statement.drop_table(database, table):
            CURRENT_TABLE.set_value(None)
            # self._refresh_database()

            self._select_tree_item(name=database.name)

    # COLUMNS
    def _on_current_column(self, column: SQLColumn):
        self.btn_delete_column.Enable(column is not None)
        self.btn_move_up_column.Enable(column is not None)
        self.btn_move_down_column.Enable(column is not None)

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
        self.controller_list_table_records.on_insert_record()

    def on_delete_record(self, event):
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the records?'),
                                  style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            self.do_delete_records()

    def do_delete_records(self):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        table = CURRENT_TABLE.get_value()
        records = CURRENT_RECORDS.get_value()

        if session.statement.delete_records(database, table, records):
            for record in records:
                index = self.controller_list_table_records.model.data.index(record)
                item = self.controller_list_table_records.model.GetItem(index)
                self.controller_list_table_records.model.del_row(item)

        self.controller_list_table_records.list_ctrl_records.refresh()

    # def on_clear_record(self, event):
    #     self.controller_list_table_records.on_row_clear()
