import wx.stc
import wx.html2

from gettext import gettext as _

from helpers.observables import ObservableArray
from models.database import Column, Table
from models.session import Session
from models.structures.statement import LOG_QUERY

from windows import MainFrameView
from windows.main import SESSIONS, CURRENT_COLUMN, CURRENT_TABLE, CURRENT_DATABASE, CURRENT_SESSION
from windows.main.data import TableDataController
from windows.main.sessions import TreeSessionsController
from windows.main.table import EditTableModel, ListTableColumnsController, NEW_TABLE


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
        self.controller_list_table_columns = ListTableColumnsController(self.list_ctrl_table_columns)
        self.controller_table_data = TableDataController(self.list_ctrl_table_data)

        self._setup_query_logs()

        self._setup_subscribers()

    def _setup_query_logs(self):
        self.query_logs.SetLexer(wx.stc.STC_LEX_SQL)
        self.query_logs.SetKeyWords(0, (
            "select from where insert into update delete create alter drop table view "
            "index primary key unique not null default auto_increment values set pragma"
            "and or as distinct order by group having join left right inner outer on "
            "if exists like in is between limit offset case when then else end show describe"
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

        # Line numbers
        self.query_logs.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        self.query_logs.SetMarginWidth(0, 40)
        self.query_logs.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "back:#e0e0e0,fore:#555555")

        # Caret e selection
        self.query_logs.SetCaretForeground(wx.Colour("#000000"))
        self.query_logs.SetSelBackground(True, wx.Colour("#cce8ff"))
        self.query_logs.SetSelForeground(True, wx.Colour("#000000"))

    def _setup_subscribers(self):
        LOG_QUERY.subscribe(self._write_query_log)

        SESSIONS.subscribe(self._load_session, ObservableArray.CallbackEvent.ON_APPEND)

        CURRENT_SESSION.subscribe(self.show_panel_session)

        CURRENT_DATABASE.subscribe(self.show_panel_database)

        CURRENT_TABLE.subscribe(self.show_panel_table)

        NEW_TABLE.subscribe(self.on_new_table)

        # NEW_COLUMN.subscribe(self._on_new_column)

    def _write_query_log(self, text: str):
        self.query_logs.AppendText(f"{text}\n")
        # self.query_logs.EnsureCaretVisible()
        self.query_logs.GotoLine(self.query_logs.GetLineCount() - 1)

    def _toggle_panel(self, index: int, visible: bool):
        panel = self.MainFrameNotebook.GetPage(index)
        panel.Show(visible)
        panel.Enable(visible)

    def _toggle_edit_table(self, visible: bool):
        self._toggle_panel(2, visible)
        self._toggle_panel(3, visible)

    def _refresh_database(self):
        session = CURRENT_SESSION.get_value()
        db = CURRENT_DATABASE.get_value()
        db.tables = session.statement.get_tables(schema=db.name)
        CURRENT_DATABASE.set_value(None)
        CURRENT_DATABASE.set_value(db)

    def _select_tree_item(self, **filters):
        if table_item := self.controller_tree_sessions.find_by_data(**filters):
            tree = self.controller_tree_sessions.tree_ctrl_sessions
            tree.SelectItem(table_item, True)
            tree.EnsureVisible(table_item)

    def _load_session(self, session: Session):
        self.controller_tree_sessions.append_session(session)

    def do_close(self, event):
        super().Destroy()
        wx.GetApp().ExitMainLoop()

    def do_open_session_manager(self, event):
        from windows.session_manager import SessionManagerController

        sm = SessionManagerController(self, sessions=self.app.settings.get_value("sessions"))
        sm.Show()

    def on_insert_column(self, event):
        self.controller_list_table_columns.on_insert_column()

    def on_insert_table(self, event):
        NEW_TABLE.set_value(None)
        CURRENT_TABLE.set_value(None)

        self._toggle_panel(2, True)
        self.MainFrameNotebook.SetSelection(2)
        self.table_name.SetFocus()
        self.edit_table_model.build_table()

    def show_panel_session(self, session: Session):
        self._toggle_panel(0, True)
        self.MainFrameNotebook.SetSelection(0)

        self.status_bar.SetStatusText(f"{_('Version')}: {session.statement.get_server_version()}", 1)
        self.status_bar.SetStatusText(f"{_('Uptime')}: {session.statement.get_server_uptime()}", 2)

    def show_panel_database(self, *args):
        self._toggle_panel(1, True)
        self.MainFrameNotebook.SetSelection(1)

    def show_panel_table(self, table: Table):
        self._toggle_edit_table(True)
        if self.MainFrameNotebook.GetSelection() != 2:
            self.MainFrameNotebook.SetSelection(2)
            self.table_name.SetFocus()

        self.btn_table_delete.Enable(table is not None)

    def _on_new_column(self, column: Column):
        self.btn_table_save.Enable(column.is_valid())

    def on_page_changed(self, event: wx.BookCtrlEvent):
        if event.GetEventObject() != self.MainFrameNotebook:
            event.Skip()
            return
        if event.GetSelection() == 1 and not CURRENT_TABLE.get_value():
            self._toggle_edit_table(False)

    def on_new_table(self, new_table: Table):
        self.btn_table_save.Enable(bool(new_table is not None))

    def do_save_table(self, event: wx.Event):
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        table = NEW_TABLE.get_value()
        session.statement.update_table(database, table)

        NEW_TABLE.set_value(None)
        self._refresh_database()
        # CURRENT_TABLE.set_value(table)
        self._select_tree_item(name=table.name)

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
        table = CURRENT_TABLE.get_value()
        session.statement.drop_table(table)

        CURRENT_TABLE.set_value(None)
        self._refresh_database()
