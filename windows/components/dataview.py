from typing import Callable, Optional, List

import wx
import wx.dataview

from gettext import gettext as _

from structures.session import Session, SessionEngine

from structures.engines.database import SQLColumn, SQLTable, SQLIndex
from structures.engines.datatype import DataTypeCategory
from structures.engines.indextype import SQLIndexType, StandardIndexType

from windows.components import BaseDataViewCtrl
from windows.components.popup import PopupColumnDatatype, PopupColumnDefault, PopupCheckList, PopupChoice, PopupCalendar, PopupCalendarTime
from windows.components.renders import PopupRenderer, LengthSetRender, TimeRenderer, FloatRenderer, IntegerRenderer, TextRenderer

from windows.main import CURRENT_SESSION, CURRENT_TABLE, CURRENT_DATABASE
from windows.main.table import NEW_TABLE


class _SQLiteTableColumnsDataViewCtrl:
    def __init__(self, dataview):
        dataview.AppendToggleColumn(_(u"Allow NULL"), 4, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_check_render = TextRenderer()
        column = wx.dataview.DataViewColumn(_(u"Check"), column_check_render, 5, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        column_default_renderer = PopupRenderer(PopupColumnDefault)
        column = wx.dataview.DataViewColumn(_(u"Default"), column_default_renderer, 6, width=200, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        choice_virtuality_renderer = wx.dataview.DataViewChoiceRenderer(["", "VIRTUAL", "STORED"], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Virtuality"), choice_virtuality_renderer, 7, width=-1, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        dataview.AppendTextColumn(_(u"Expression"), 8, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_collation_renderer = PopupRenderer(PopupChoice)
        column_collation_renderer.on_open = lambda popup: popup.set_choices([""] + [c for c in CURRENT_SESSION.get_value().context.COLLATIONS])
        column = wx.dataview.DataViewColumn(_(u"Collation"), column_collation_renderer, 9, width=-1, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        # dataview.AppendTextColumn(_(u"Comments"), 11, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)


class _MariaDBMySQLTableColumnsDataViewCtrl:
    def __init__(self, dataview):
        dataview.AppendToggleColumn(_(u"Unsigned"), 4, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        dataview.AppendToggleColumn(_(u"Allow NULL"), 5, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        dataview.AppendToggleColumn(_(u"Zerofill"), 6, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_default_renderer = PopupRenderer(PopupColumnDefault)
        column = wx.dataview.DataViewColumn(_(u"Default"), column_default_renderer, 7, width=200, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        choice_virtuality_renderer = wx.dataview.DataViewChoiceRenderer(["", "VIRTUAL", "STORED"], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Virtuality"), choice_virtuality_renderer, 8, width=-1, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        dataview.AppendTextColumn(_(u"Expression"), 9, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_collation_renderer = PopupRenderer(PopupChoice)
        column_collation_renderer.on_open = lambda popup: popup.set_choices([""] + [c for c in CURRENT_SESSION.get_value().context.COLLATIONS])
        column = wx.dataview.DataViewColumn(_(u"Collation"), column_collation_renderer, 10, width=-1, align=wx.ALIGN_LEFT)
        dataview.AppendColumn(column)

        dataview.AppendTextColumn(_(u"Comments"), 11, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)


class TableColumnsDataViewCtrl(BaseDataViewCtrl):
    on_column_insert: Callable[[wx.Event], None]
    on_column_delete: Callable[[wx.Event], None]
    on_column_move_up: Callable[[wx.Event], None]
    on_column_move_down: Callable[[wx.Event], None]

    insert_column_index: Callable[[wx.Event, SQLIndexType], Optional[bool]]
    append_column_index: Callable[[wx.Event, SQLIndex], Optional[bool]]

    on_finish_editing: Callable[[...], Optional[bool]] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column0 = wx.dataview.DataViewColumn(_(u"#"), wx.dataview.DataViewIconTextRenderer(align=wx.ALIGN_LEFT), 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)

        column1_render = TextRenderer()
        column1 = wx.dataview.DataViewColumn(_(u"Name"), column1_render, 1, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)

        column2_renderer = PopupRenderer(PopupColumnDatatype)
        column2 = wx.dataview.DataViewColumn(_(u"Data type"), column2_renderer, 2, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        column3_renderer = LengthSetRender()
        column3 = wx.dataview.DataViewColumn(_(u"Length/Set"), column3_renderer, 3, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        self._current_column: Optional[int] = None
        self._current_dataview: Optional[int] = None

        CURRENT_SESSION.subscribe(self._load_session)

    def _load_session(self, session: Session):
        if not self._current_dataview:
            if session.engine == SessionEngine.SQLITE:
                self._current_dataview = _SQLiteTableColumnsDataViewCtrl(self)
            elif session.engine in [SessionEngine.MYSQL, SessionEngine.MARIADB]:
                self._current_dataview = _MariaDBMySQLTableColumnsDataViewCtrl(self)

    def _on_context_menu(self, event):
        from icons import BitmapList

        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value() or NEW_TABLE.get_value()

        selected = self.GetSelection()
        model = self.GetModel()
        # row = model.GetRow(selected)
        column = model.get_data_by_item(selected)

        menu = wx.Menu()

        add_item = wx.MenuItem(menu, wx.ID_ANY, _("Add column\tCTRL+INS"), wx.EmptyString, wx.ITEM_NORMAL)
        add_item.SetBitmap(BitmapList.ADD)
        menu.Append(add_item)

        self.Bind(wx.EVT_MENU, lambda e : wx.CallAfter(self.on_column_insert, e), add_item)

        delete_item = wx.MenuItem(menu, wx.ID_ANY, _("Remove column\tCTRL+DEL"), wx.EmptyString, wx.ITEM_NORMAL)
        delete_item.SetBitmap(BitmapList.DELETE)
        # delete_item.Enable(selected.IsOk())
        menu.Append(delete_item)
        menu.Enable(delete_item.GetId(), selected.IsOk())

        self.Bind(wx.EVT_MENU, self.on_column_delete, delete_item)

        move_up_item = wx.MenuItem(menu, wx.ID_ANY, _("Move up\tCTRL+UP"), wx.EmptyString, wx.ITEM_NORMAL)
        move_up_item.SetBitmap(BitmapList.ARROW_UP)
        menu.Append(move_up_item)
        menu.Enable(move_up_item.GetId(), selected.IsOk())

        self.Bind(wx.EVT_MENU, self.on_column_move_up, move_up_item)

        move_down_item = wx.MenuItem(menu, wx.ID_ANY, _("Move down\tCTRL+D"), wx.EmptyString, wx.ITEM_NORMAL)
        move_down_item.SetBitmap(BitmapList.ARROW_DOWN)
        menu.Append(move_down_item)
        menu.Enable(move_down_item.GetId(), selected.IsOk())

        self.Bind(wx.EVT_MENU, self.on_column_move_down, move_down_item)

        menu.AppendSeparator()

        create_index_menu = wx.Menu()

        for index_type in session.context.INDEXTYPE.get_all():
            item = wx.MenuItem(create_index_menu, wx.ID_ANY, index_type.name, wx.EmptyString, wx.ITEM_NORMAL)
            item.SetBitmap(index_type.bitmap)
            create_index_menu.Append(item)

            if index_type.name == "PRIMARY" and len([pk for pk in list(table.indexes) if pk.type == StandardIndexType.PRIMARY]) > 0:
                # primary index already exists
                create_index_menu.Enable(item.GetId(), False)
            else:
                create_index_menu.Enable(item.GetId(), selected.IsOk())
                self.Bind(wx.EVT_MENU, lambda e, it=index_type: self.insert_column_index(e, it), item)

        menu.AppendSubMenu(create_index_menu, _("Create new index"))

        append_index_menu = wx.Menu()
        for index in list(table.indexes):
            if column.name not in index.columns:
                item = wx.MenuItem(append_index_menu, wx.ID_ANY, index.name, wx.EmptyString, wx.ITEM_NORMAL)
                item.SetBitmap(index.type.bitmap)
                append_index_menu.Append(item)

                if not index.type.enable_append:
                    append_index_menu.Enable(item.GetId(), False)

                else:
                    self.Bind(wx.EVT_MENU, lambda e, idx=index: self.append_column_index(e, idx), item)

        menu.AppendSubMenu(append_index_menu, _("Append to index"))

        self.PopupMenu(menu)


class TableIndexesDataViewCtrl(BaseDataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_render_column0 = wx.dataview.DataViewIconTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Name"), icon_render_column0, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Column(s)/Expression"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendTextColumn(_(u"Condition"), 2, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)


class TableConstraintDataViewCtrl(BaseDataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column0 = wx.dataview.DataViewIconTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column0 = wx.dataview.DataViewColumn(_(u"Type"), column0, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)

        self.AppendTextColumn(_(u"Name"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        self.AppendTextColumn(_(u"Expression"), 2, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)


class TableForeignKeysDataViewCtrl(BaseDataViewCtrl):
    on_foreign_key_insert: Callable[[wx.Event], None]
    on_foreign_key_delete: Callable[[wx.Event], None]
    on_foreign_key_update: Callable[[wx.Event], None]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column0_render = wx.dataview.DataViewIconTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column0 = wx.dataview.DataViewColumn(_(u"Name"), column0_render, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        column0.SetMinWidth(250)
        self.AppendColumn(column0)

        column1_render = PopupRenderer(PopupCheckList)
        column1_render.on_open = lambda popup: popup.set_choices([c.name for c in list((CURRENT_TABLE.get_value() or NEW_TABLE.get_value()).columns)])
        column1 = wx.dataview.DataViewColumn(_(u"Column(s)"), column1_render, 1, width=150, flags=wx.dataview.DATAVIEW_COL_RESIZABLE, align=wx.ALIGN_LEFT)
        column1.SetMinWidth(150)
        self.AppendColumn(column1)

        column2_renderer = PopupRenderer(PopupChoice)
        column2_renderer.on_open = lambda popup: popup.set_choices([t.name for t in list(CURRENT_DATABASE.get_value().tables)])
        column2 = wx.dataview.DataViewColumn(_(u"Reference table"), column2_renderer, 2, width=wx.COL_WIDTH_AUTOSIZE, flags=wx.dataview.DATAVIEW_COL_RESIZABLE, align=wx.ALIGN_LEFT)
        column2.SetMinWidth(140)
        self.AppendColumn(column2)

        column3_render = PopupRenderer(PopupCheckList)
        column3_render.on_open = lambda popup: popup.set_choices(self._load_table_columns(popup, column2_renderer))
        column3 = wx.dataview.DataViewColumn(_(u"Reference column(s)"), column3_render, 3, width=200, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
        column3.SetMinWidth(200)
        self.AppendColumn(column3)

        column4_render = PopupRenderer(PopupChoice)
        column4_render.on_open = lambda popup: popup.set_choices(["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"])
        column4 = wx.dataview.DataViewColumn(_(u"On UPDATE"), column4_render, 4, width=100, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
        column4.SetMinWidth(100)
        self.AppendColumn(column4)

        column5_render = PopupRenderer(PopupChoice)
        column5_render.on_open = lambda popup: popup.set_choices(["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"])
        column5 = wx.dataview.DataViewColumn(_(u"On DELETE"), column5_render, 5, width=100, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
        column5.SetMinWidth(100)
        self.AppendColumn(column5)

        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

    def _on_context_menu(self, event):
        from icons import BitmapList

        selected = self.GetSelection()
        model = self.GetModel()
        row = model.GetRow(selected)
        foreign_key = model.data[row]

        menu = wx.Menu()

        add_item = wx.MenuItem(menu, wx.ID_ANY, _("Add foreign key"), wx.EmptyString, wx.ITEM_NORMAL)
        add_item.SetBitmap(BitmapList.ADD)
        menu.Append(add_item)

        self.Bind(wx.EVT_MENU, self.on_foreign_key_insert, add_item)

        delete_item = wx.MenuItem(menu, wx.ID_ANY, _("Remove foreign key"), wx.EmptyString, wx.ITEM_NORMAL)
        delete_item.SetBitmap(BitmapList.DELETE)
        menu.Append(delete_item)
        menu.Enable(delete_item.GetId(), selected.IsOk())

        self.Bind(wx.EVT_MENU, self.on_foreign_key_delete, delete_item)

        # Forse non necessario, dato che editing è già disponibile
        # update_item = wx.MenuItem(menu, wx.ID_ANY, _("Update foreign key"), wx.EmptyString, wx.ITEM_NORMAL)
        # menu.Append(update_item)
        # self.Bind(wx.EVT_MENU, self.on_foreign_key_update, update_item)

        self.PopupMenu(menu)

    def _load_table_columns(self, popup, column2_render: PopupRenderer) -> List[str]:
        value = column2_render.GetValue()
        if value:
            table = next((t for t in list(CURRENT_DATABASE.get_value().tables) if t.name == value), None)
            if table:
                return [c.name for c in list(table.columns)]

        return []


class TableRecordsDataViewCtrl(BaseDataViewCtrl):
    on_record_insert: Callable[[...], Optional[bool]]
    on_record_delete: Callable[[...], Optional[bool]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_TABLE.subscribe(self._load_table)

    def _get_column_renderer(self, column: SQLColumn) -> wx.dataview.DataViewRenderer:
        for foreign_key in column.table.foreign_keys:
            if column.name in foreign_key.columns:
                session = CURRENT_SESSION.get_value()
                database = CURRENT_DATABASE.get_value()

                records = []
                references = []
                if reference_table := next((table for table in database.tables if table.name == foreign_key.reference_table), None):
                    records = session.context.get_records(reference_table)

                for record in records:
                    reference = [str(record.values.get(reference_column)) for reference_column in foreign_key.reference_columns]

                    references.append(reference)

                choices = [f" ".join(reference) for reference in references]

                r = PopupRenderer(PopupChoice)
                r.on_open = lambda popup: popup.set_choices(choices)
                return r

        if column.datatype.name == 'ENUM':
            popoup_render = PopupRenderer(PopupChoice)
            popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return popoup_render

        elif column.datatype.name == 'SET':
            popoup_render = PopupRenderer(PopupCheckList)
            popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return popoup_render

        elif column.datatype.name == 'BOOLEAN':
            return wx.dataview.DataViewToggleRenderer(
                mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE, align=wx.ALIGN_CENTER)

        elif column.datatype.category == DataTypeCategory.INTEGER:
            return IntegerRenderer()

        elif column.datatype.category == DataTypeCategory.REAL:
            return FloatRenderer()

        elif column.datatype.name == 'DATE':
            popoup_render = PopupRenderer(PopupCalendar)
            # popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return popoup_render
        elif column.datatype.name == 'TIME':
            # popoup_render = PopupRenderer(PopupTime)
            # popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return TimeRenderer()

        elif column.datatype.name in ['DATETIME', 'TIMESTAMP']:
            popoup_render = PopupRenderer(PopupCalendarTime)
            # popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return popoup_render


        else:
            return TextRenderer()

    def _load_table(self, table: SQLTable):
        while self.GetColumnCount() > 0:
            self.DeleteColumn(self.GetColumn(0))

        if table is not None:
            for i, column in enumerate(table.columns):
                renderer = self._get_column_renderer(column)

                col = wx.dataview.DataViewColumn(column.name, renderer, i, width=self.calculate_column_width(column.name), flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
                self.AppendColumn(col)


class DatabaseTablesDataViewCtrl(BaseDataViewCtrl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
