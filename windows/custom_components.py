import os
from typing import Type, List

import wx
import wx.dataview

from gettext import gettext as _

from wx.dataview import DATAVIEW_CELL_EDITABLE

from models.session import Session, SessionEngine
from models.structures import StandardDataType
from models.structures.charset import COLLATION_CHARSETS
from models.structures.mariadb.datatype import MariaDBDataType
from models.structures.mysql.datatype import MySQLDataType
from models.structures.sqlite.datatype import SQLiteDataType
from windows.main import CURRENT_SESSION


class PopupColumnDefault(wx.PopupTransientWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer63 = wx.BoxSizer(wx.VERTICAL)

        self.rb_no_default = wx.RadioButton(self, wx.ID_ANY, _(u"No default value"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer63.Add(self.rb_no_default, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_expression = wx.RadioButton(self, wx.ID_ANY, _(u"Expression"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer63.Add(self.rb_expression, 0, wx.ALL | wx.EXPAND, 5)

        self.txt_expression = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE)
        bSizer63.Add(self.txt_expression, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_null = wx.RadioButton(self, wx.ID_ANY, _(u"NULL"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer63.Add(self.rb_null, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_auto_increment = wx.RadioButton(self, wx.ID_ANY, _(u"AUTO INCREMENT"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer63.Add(self.rb_auto_increment, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(bSizer63)
        self.Layout()
        bSizer63.Fit(self)


class DataViewChoiceRenderer(wx.dataview.DataViewCustomRenderer):

    def __init__(self, choices):
        super().__init__("string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.choices = choices
        self._value = ""

    def Render(self, rect, dc, state):
        self.RenderText(self._value, 0, rect, dc, state)

        return True

    def GetSize(self):
        w, h = self.GetTextExtent(self._value)
        return wx.Size(-1, -1)

    def SetValue(self, value):
        self._value = value
        return True

    def GetValue(self):
        return self._value

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, rect, value):
        choice = wx.Choice(
            parent,
            choices=self.choices,
            pos=rect.GetTopLeft(),
            size=rect.GetSize()
        )
        if self._value in self.choices:
            choice.SetStringSelection(self._value)
        return choice

    def GetValueFromEditorCtrl(self, editor):
        return editor.GetStringSelection()

    def set_choices(self, choices: List[str]):
        self.choices = choices


class DataViewPopupRenderer(wx.dataview.DataViewCustomRenderer):
    def __init__(self, popup: Type[wx.PopupTransientWindow]):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

        self.popup = popup
        self._value = ""

    def Render(self, rect, dc, state):
        text = "No default"

        if (value := self.GetValue()) != "":
            if value == "NULL":
                text = "NULL"
            elif value == "AUTO_INCREMENT":
                text = "AUTO_INCREMENT"
            else:
                text = value

        self.RenderText(text, 0, rect, dc, state)

        return True

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        self._value = value

        return True

    def GetSize(self):
        return wx.Size(-1, -1)

    def ActivateCell(self, rect, model, item, col, mouseEvent):
        view = self.GetView()

        popup = self.popup(parent=view)
        point_x_y = view.ClientToScreen(wx.Point(rect.x, rect.y + 17))
        popup.SetPosition(point_x_y)
        popup.SetSize(width=view.Columns[col].Width, height=-1)
        popup.Popup()

        if self._value != "":
            if self._value == "NULL":
                popup.rb_null.SetValue(True)
            elif self._value == "AUTO_INCREMENT":
                popup.rb_auto_increment.SetValue(True)
            else:
                popup.rb_expression.SetValue(True)
                popup.txt_expression.SetValue(self._value)
        else:
            popup.rb_no_default.SetValue(True)

        def onDismiss(*args, **kwargs):
            if popup.rb_no_default.GetValue():
                self._value = ""
            elif popup.rb_null.GetValue():
                self._value = "NULL"
            elif popup.rb_auto_increment.GetValue():
                self._value = "AUTO_INCREMENT"
            elif popup.rb_expression.GetValue():
                self._value = popup.txt_expression.GetValue()

            model.ChangeValue(self._value, item, col)

        popup.OnDismiss = onDismiss

        return True


class DataViewIconRender(wx.dataview.DataViewCustomRenderer):

    def __init__(self):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_INERT, wx.ALIGN_LEFT)
        self._value = None

    def SetValue(self, value):
        self._value = value
        return True

    def GetValue(self):
        return self._value

    def GetSize(self):
        return wx.Size(-1, -1)

    def Render(self, rect, dc, state):
        model = self.GetView().GetModel().data[int(self._value) - 1]

        icons = []
        x, y = rect.GetTopLeft()

        if model.primary_key:
            icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_ANY))

        for _ in range(model.index_summary.get("unique_index", 0)):
            icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_ANY))
        for _ in range(model.index_summary.get("normal_index", 0)):
            icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_ANY))
        for _ in range(model.index_summary.get("fulltext_index", 0)):
            icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_ANY))
        for _ in range(model.index_summary.get("spatial_index", 0)):
            icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_ANY))

        dc.DrawText(self._value, x, y)

        tw, th = dc.GetTextExtent(self._value)
        x += tw + 4

        spacing = 2
        for icon in icons:
            w, h = icon.GetSize()
            text_y = y + (th - h) // 2
            dc.DrawBitmap(icon, x, text_y, True)
            x += w + spacing

        return True


class ColumnDataViewCtrl(wx.dataview.DataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_SESSION.subscribe(self._load_session)

        icon_id_render = DataViewIconRender()
        column = wx.dataview.DataViewColumn(_(u"#"), icon_id_render, 0, width=40, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Name"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        datatype_renderer = DataViewChoiceRenderer([])
        column = wx.dataview.DataViewColumn(_(u"Data type"), datatype_renderer, 2, width=120, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Length/Set"), 3, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        self.AppendToggleColumn(_(u"Unsigned"), 4, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Allow NULL"), 5, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Zerofill"), 6, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)

        popup_default_renderer = DataViewPopupRenderer(PopupColumnDefault)
        column = wx.dataview.DataViewColumn(_(u"Default"), popup_default_renderer, 7, width=200, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        choice_virtuality_renderer = wx.dataview.DataViewChoiceRenderer(["", "VIRTUAL", "PERSISTED"], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Virtuality"), choice_virtuality_renderer, 8, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Expression"), 9, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        choice_collation_renderer = wx.dataview.DataViewChoiceRenderer([c for c in COLLATION_CHARSETS.keys()], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Collation"), choice_collation_renderer, 10, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Comments"), 11, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

    def _load_session(self, session: Session):
        self.engine_data_type = StandardDataType()
        if session.engine == SessionEngine.MYSQL:
            self.engine_data_type = MySQLDataType()
        elif session.engine == SessionEngine.MARIADB:
            self.engine_data_type = MariaDBDataType
        elif session.engine == SessionEngine.SQLITE:
            self.engine_data_type = SQLiteDataType()

            self.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(6).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(8).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)

        self.GetColumn(2).GetRenderer().set_choices([data_type.name for data_type in self.engine_data_type.get_all()])
