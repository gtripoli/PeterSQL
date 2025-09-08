import os
from typing import Type, List, Self, Any

import wx
import wx.dataview

from gettext import gettext as _

from models.database import Column
from models.session import Session, SessionEngine
from models.structures import SQLDataType
from models.structures.charset import COLLATION_CHARSETS

from windows.main import CURRENT_SESSION


class BaseDataviewPopup(wx.PopupTransientWindow):
    """Base class for all DataView popup windows."""

    def __init__(self, parent):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._value = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetWindowStyle(wx.TRANSPARENT_WINDOW)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetSizer(self.sizer)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        return self

    @staticmethod
    def render(value):
        return value

    def open(self, value: Any, position: wx.Point, size: wx.Size) -> Self:
        self.set_value(value)

        self.SetPosition(position)
        self.SetMinSize(size)
        self.SetMaxSize(size)

        self.Layout()
        self.sizer.Fit(self)
        self.Fit()

        self.Popup()

        return self

    def close(self):
        self.Destroy()


class PopupColumnDefault(BaseDataviewPopup):
    def __init__(self, parent):
        super().__init__(parent)

        self.rb_no_default = wx.RadioButton(self, wx.ID_ANY, _(u"No default value"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_no_default.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_no_default, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_expression = wx.RadioButton(self, wx.ID_ANY, _(u"Expression"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_expression.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_expression, 0, wx.ALL | wx.EXPAND, 5)

        self.txt_expression = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE)
        self.txt_expression.Enable(False)
        self.txt_expression.Bind(wx.EVT_TEXT, self._on_expression_changed)
        self.sizer.Add(self.txt_expression, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_null = wx.RadioButton(self, wx.ID_ANY, _(u"NULL"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_null.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_null, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_auto_increment = wx.RadioButton(self, wx.ID_ANY, _(u"AUTO INCREMENT"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_auto_increment.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_auto_increment, 0, wx.ALL | wx.EXPAND, 5)

    def _on_radio_button(self, event):
        if self.rb_no_default.GetValue():
            self._value = None
        elif self.rb_null.GetValue():
            self._value = "NULL"
        elif self.rb_auto_increment.GetValue():
            self._value = "AUTO_INCREMENT"
        elif self.rb_expression.GetValue():
            self.txt_expression.Enable(True)
            self.txt_expression.SetFocus()
            self._value = ""

    def _on_expression_changed(self, event):
        """Handle expression text changes."""
        if self.rb_expression.GetValue():
            self._value = self.txt_expression.GetValue()

    @staticmethod
    def render(value):
        if not value:
            return "No default"
        return value

    def set_value(self, value):
        """Set the initial value and update UI accordingly."""
        super().set_value(value)

        if not value:
            self.rb_no_default.SetValue(True)
        elif value == "NULL":
            self.rb_null.SetValue(True)
        elif value == "AUTO_INCREMENT":
            self.rb_auto_increment.SetValue(True)
        else:
            self.rb_expression.SetValue(True)
            self.txt_expression.Enable(True)
            self.txt_expression.SetValue(value)
            self.txt_expression.SetFocus()

        return self


class PopupColumnDatatype(BaseDataviewPopup):
    """Popup for selecting column data types."""
    _session: Session

    def __init__(self, parent):
        super().__init__(parent)
        self.choices = []

        self.parent = parent
        self.tree_ctrl = None

        self.tree_ctrl = wx.TreeCtrl(self, style=wx.TR_HIDE_ROOT | wx.TR_NO_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT |
                                                 wx.TR_NO_LINES | wx.TR_SINGLE)

        self.tree_ctrl.AddRoot("Root")

        self.sizer.Add(self.tree_ctrl, 1, wx.ALL | wx.EXPAND, 0)

        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_select)
        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_COLLAPSING, lambda e: e.Veto())

        CURRENT_SESSION.subscribe(self._load_session, execute_immediately=True)

    def _load_session(self, session: Session):
        self._session = session
        self.set_choices(self._session.datatype.get_all())

    def _on_select(self, event):
        """Handle tree selection changes."""
        item = event.GetItem()
        if item and item != self.tree_ctrl.GetRootItem():
            parent = self.tree_ctrl.GetItemParent(item)
            if parent != self.tree_ctrl.GetRootItem():  # Only leaf items
                self._value = self._session.datatype.get_by_name(self.tree_ctrl.GetItemText(item))

                self.OnDismiss()

    def set_choices(self, choices: List[SQLDataType]) -> Self:
        self.choices = choices

        return self

    def open(self, value: Any, position: wx.Point, size: wx.Size) -> Self:
        groups = {}

        root = self.tree_ctrl.GetRootItem()
        self.tree_ctrl.DeleteChildren(root)

        for choice in self.choices:
            groups.setdefault(choice.category.value, []).append(choice.name)

        dc = wx.ClientDC(self.tree_ctrl)
        max_width = 0
        selected = None

        for category, datatypes in groups.items():

            category_item = self.tree_ctrl.AppendItem(root, category.name)
            self.tree_ctrl.SetItemBold(category_item, True)

            max_width = max(max_width, dc.GetTextExtent(category.name)[0])

            for datatype in datatypes:
                datatype_item = self.tree_ctrl.AppendItem(category_item, datatype)
                self.tree_ctrl.SetItemTextColour(datatype_item, category.color)

                max_width = max(max_width, dc.GetTextExtent(datatype)[0])

                if datatype == value:
                    selected = datatype_item

        self.tree_ctrl.ExpandAll()

        size = wx.Size(max(max_width + 100, size.width), 300)

        if selected is not None:
            self.tree_ctrl.SelectItem(selected)
            self.tree_ctrl.EnsureVisible(selected)

        return super().open(value, position, size)


class DataViewPopupRenderer(wx.dataview.DataViewCustomRenderer):
    def __init__(self, popup_class: Type[BaseDataviewPopup]):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

        self._value = ""
        self.popup_class = popup_class

    def Render(self, rect, dc, state):
        self.RenderText(self.popup_class.render(self._value), 0, rect, dc, state)

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

        position = view.ClientToScreen(wx.Point(rect.x, rect.y + view.CharHeight))

        popup = self.popup_class(view)

        def _on_dismiss():
            new_value = popup.get_value()
            if new_value != self._value:
                self._value = new_value
                model.SetValue(self._value, item, col)

            popup.close()

        popup.OnDismiss = _on_dismiss
        popup.open(self._value, position, wx.Size(width=view.Columns[col].Width, height=-1))

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
        data = self.GetView().GetModel().data
        if not len(data):
            return False

        if self._value is None:
            print("a problem")
            return False

        column: Column = data[int(self._value) - 1]

        icons = []
        x, y = rect.GetTopLeft()

        for index in column.indexes:
            if index.is_primary:
                icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_ANY))

            if index.is_unique:
                icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_ANY))

            if index.is_fulltext:
                icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_ANY))

            if index.is_spatial:
                icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_ANY))

            if index.is_normal:
                icons.append(wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_ANY))

        dc.DrawText(self._value, x, y)

        tw, th = dc.GetTextExtent(self._value)
        x += tw + 4

        spacing = 1
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

        datatype_renderer = DataViewPopupRenderer(PopupColumnDatatype)
        column = wx.dataview.DataViewColumn(_(u"Data type"), datatype_renderer, 2, width=120, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Length/Set"), 3, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        self.AppendToggleColumn(_(u"Unsigned"), 4, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Allow NULL"), 5, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Zerofill"), 6, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)

        popup_default_renderer = DataViewPopupRenderer(PopupColumnDefault)
        column = wx.dataview.DataViewColumn(_(u"Default"), popup_default_renderer, 7, width=200, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        choice_virtuality_renderer = wx.dataview.DataViewChoiceRenderer(["", "VIRTUAL", "STORED"], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Virtuality"), choice_virtuality_renderer, 8, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Expression"), 9, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        choice_collation_renderer = wx.dataview.DataViewChoiceRenderer([c for c in COLLATION_CHARSETS.keys()], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Collation"), choice_collation_renderer, 10, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Comments"), 11, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

    def _load_session(self, session: Session):
        if session.datatype == SessionEngine.SQLITE:
            self.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(6).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(8).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
