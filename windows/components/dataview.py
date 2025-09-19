import os
from typing import Type, List, Self, Any, Callable

import wx
import wx.dataview

from gettext import gettext as _

from helpers.logger import logger
from models.session import Session, SessionEngine
from models.structures.charset import COLLATION_CHARSETS
from models.structures.database import SQLColumn, SQLTable
from models.structures.datatype import SQLDataType, DataTypeCategory

from windows.main import CURRENT_SESSION, CURRENT_TABLE


class BaseDataViewCustomRenderer(wx.dataview.DataViewCustomRenderer):
    def __init__(self, varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT):
        super().__init__(varianttype=varianttype, mode=mode, align=align)

        self._value = None

    def SetValue(self, value):
        self._value = value
        return True

    def GetValue(self):
        return self._value

    def GetSize(self):
        return wx.Size(-1, -1)

    def Render(self, rect, dc, state, default=""):
        value = self.GetValue()
        if not value:
            value = default

        self.RenderText(str(value), 0, rect, dc, state)
        return True


class BasePopup(wx.PopupTransientWindow):
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


class PopupColumnDefault(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)

        self.rb_no_default = wx.RadioButton(self, wx.ID_ANY, _(u"No default value"), wx.DefaultPosition, wx.DefaultSize,
                                            0)
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


class PopupColumnDatatype(BasePopup):
    session: Session

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
        self.session = session
        self.set_choices(self.session.datatype.get_all())

    def _on_select(self, event):
        item = event.GetItem()
        if item and item != self.tree_ctrl.GetRootItem():
            parent = self.tree_ctrl.GetItemParent(item)
            if parent != self.tree_ctrl.GetRootItem():  # Only leaf items
                self._value = self.session.datatype.get_by_name(self.tree_ctrl.GetItemText(item))

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


class PopupCheckList(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.choices = []
        self.check_list_box = wx.CheckListBox(self)
        self.sizer.Add(self.check_list_box, 0, wx.ALL | wx.EXPAND, 5)
        self.check_list_box.Bind(wx.EVT_CHECKLISTBOX, self._on_select)

    def open(self, value: str, position: wx.Point, size: wx.Size) -> Self:
        self.check_list_box.AppendItems(self.choices)
        self.check_list_box.SetCheckedStrings(value.split(','))
        #
        return super().open(value, position, size)

    def _on_select(self, event):
        self._value = ",".join(self.check_list_box.GetCheckedStrings())
        event.Skip()

    def set_choices(self, choices: List[str]) -> Self:
        self.choices = choices

        return self


class PopupRenderer(BaseDataViewCustomRenderer):
    on_open: Callable[[BasePopup], None] = lambda self, popup: None

    def __init__(self, popup_class: Type[BasePopup]):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

        self._value = ""
        self.popup_class = popup_class

    def Render(self, rect, dc, state):
        self.RenderText(self.popup_class.render(self._value), 0, rect, dc, state)

        return True

    def ActivateCell(self, rect, model, item, col, mouseEvent):
        view = self.GetView()

        position = view.ClientToScreen(wx.Point(rect.x, int(rect.y + view.CharHeight + (view.CharHeight / 2))))

        popup = self.popup_class(view)

        def _on_dismiss():
            new_value = popup.get_value()
            if new_value != self._value:
                self._value = new_value
                model.SetValue(self._value, item, col)

            popup.close()

        popup.OnDismiss = _on_dismiss
        self.on_open(popup)
        popup.open(self._value, position, wx.Size(width=view.Columns[col].Width, height=-1))

        return True


class IconRender(BaseDataViewCustomRenderer):

    def __init__(self):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_INERT, wx.ALIGN_LEFT)

    def Render(self, rect, dc, state):
        data = self.GetView().GetModel().data
        if not len(data):
            return False

        column: SQLColumn = data[int(self._value) - 1]

        icons = []
        x, y = rect.GetTopLeft()

        for index in column.indexes:
            if index.is_primary:
                icons.append(
                    wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_primary.png"), wx.BITMAP_TYPE_ANY))

            if index.is_unique:
                icons.append(
                    wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_unique.png"), wx.BITMAP_TYPE_ANY))

            if index.is_fulltext:
                icons.append(
                    wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_fulltext.png"), wx.BITMAP_TYPE_ANY))

            if index.is_spatial:
                icons.append(
                    wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_spatial.png"), wx.BITMAP_TYPE_ANY))

            if index.is_normal:
                icons.append(
                    wx.Bitmap(os.path.join(os.getcwd(), "icons", "16x16", "key_index.png"), wx.BITMAP_TYPE_ANY))

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


class EnumRenderer(wx.dataview.DataViewChoiceRenderer):
    def __init__(self, choices):
        super().__init__(choices, wx.dataview.DATAVIEW_CELL_EDITABLE, wx.ALIGN_LEFT)


class SetRenderer(BaseDataViewCustomRenderer):
    """Renderer for SET columns with single-selection"""

    def __init__(self, choices):
        super().__init__(varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.choices = choices

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, rect, value):
        listbox = wx.CheckListBox(parent, choices=self.choices, style=wx.LB_MULTIPLE)
        listbox.SetSize(rect.GetSize())

        if value:
            current_values = value.split(',')
            for i, choice in enumerate(self.choices):
                if choice in current_values:
                    listbox.Check(i)

        return listbox

    def GetValueFromEditorCtrl(self, editor):
        """Get comma-separated string of selected values"""
        if not editor:
            return ""

        selected = []

        if editor:  # Check if editor exists
            for i in range(editor.GetCount()):
                if editor.IsChecked(i):
                    selected.append(editor.GetString(i))
        return ','.join(selected)


class IntegerRenderer(BaseDataViewCustomRenderer):
    """Renderer for integer columns with validation"""

    def __init__(self):
        super().__init__(varianttype="long", mode=wx.dataview.DATAVIEW_CELL_EDITABLE)

    def Validate(self, value):
        """Validate integer input"""
        try:
            int(value)
            return True
        except ValueError:
            logger.error("Invalid integer value: %s", value)
            return False

    def CreateEditorCtrl(self, parent, rect, value):
        """Create text control with validator"""
        text_ctrl = wx.TextCtrl(parent, value=value, style=wx.TE_PROCESS_ENTER)
        text_ctrl.SetValidator(wx.TextValidator(wx.FILTER_DIGITS))
        text_ctrl.SetSize(rect.GetSize())
        return text_ctrl


class FloatRenderer(BaseDataViewCustomRenderer):

    def __init__(self):
        super().__init__(varianttype="double", mode=wx.dataview.DATAVIEW_CELL_EDITABLE)

    def Validate(self, value):
        """Validate integer input"""
        try:
            float(value)
            return True
        except ValueError:
            logger.error("Invalid float value: %s", value)
            return False

    def CreateEditorCtrl(self, parent, rect, value):
        """Create text control with validator"""
        text_ctrl = wx.TextCtrl(parent, value=value, style=wx.TE_PROCESS_ENTER)
        text_ctrl.SetValidator(wx.TextValidator(wx.FILTER_FLOAT))
        text_ctrl.SetSize(rect.GetSize())
        return text_ctrl


class DateRenderer(wx.dataview.DataViewDateRenderer):
    """Renderer for date columns"""

    def __init__(self):
        super().__init__(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)

        # self.SetOwner(self.GetView())


class DateTimeRenderer(BaseDataViewCustomRenderer):
    """Renderer for datetime columns"""

    def __init__(self):
        super().__init__(varianttype="datetime", mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

    def Render(self, rect, dc, state):
        """Render datetime value in locale format"""
        value = self.GetValue()
        if value:
            text = value.Format('%x %X')
            # dc.DrawText(text, rect.x, rect.y)

            self.RenderText(text, 0, rect, dc, state)

        return True

    def CreateEditorCtrl(self, parent, rect, value):
        """Create date and time picker control"""
        date_picker = wx.DatePickerCtrl(parent)
        time_picker = wx.TimePickerCtrl(parent)

        # Set current value if available
        if value:
            date_picker.SetValue(value)
            time_picker.SetTime(value)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(date_picker)
        sizer.Add(time_picker)

        panel = wx.Panel(parent)
        panel.SetSizer(sizer)
        panel.SetSize(rect.GetSize())

        return panel


class TimeRenderer(BaseDataViewCustomRenderer):
    """Renderer for time columns"""

    def __init__(self):
        super().__init__(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)

    def CreateEditorCtrl(self, parent, rect, value):
        """Create time picker control"""
        time_picker = wx.TimePickerCtrl(parent, style=wx.TP_DEFAULT)
        time_picker.SetSize(rect.GetSize())

        # Set current value if available
        if value:
            try:
                # Parse time string (HH:MM:SS)
                hours, minutes, seconds = map(int, value.split(':'))
                time_picker.SetTime(hours, minutes, seconds)
            except (ValueError, AttributeError):
                pass

        return time_picker

    def GetValueFromEditorCtrl(self, editor):
        """Get formatted time string"""
        hours, minutes, seconds = editor.GetTime()
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def Render(self, rect, dc, state):
        self.RenderText(self.GetValue(), 0, rect, dc, state)

        return True


class BooleanRenderer(BaseDataViewCustomRenderer):
    """Renderer for boolean columns"""

    def __init__(self):
        super().__init__(varianttype="bool", mode= wx.dataview.DATAVIEW_CELL_ACTIVATABLE, align=wx.ALIGN_CENTER)
        self.editor_ctrl = None

    def Render(self, rect, dc, state):
        # Draw checkbox box
        dc.SetPen(wx.Pen(wx.BLACK, 1))
        dc.SetBrush(wx.Brush(wx.WHITE))
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        if self.GetValue():
            # Draw checkmark
            dc.SetPen(wx.Pen(wx.BLACK, 2))
            dc.DrawLine(rect.x + 3, rect.y + rect.height // 2, rect.x + rect.width // 2 - 2, rect.y + rect.height - 3)
            dc.DrawLine(rect.x + rect.width // 2 - 2, rect.y + rect.height - 3, rect.x + rect.width - 3, rect.y + 3)
        return True

    def CreateEditorCtrl(self, parent, rect, value):
        """Create boolean picker control"""
        self.editor_ctrl = wx.CheckBox(parent)
        self.editor_ctrl.SetValue(value)
        self.editor_ctrl.SetSize(rect.GetSize())
        return self.editor_ctrl

    def GetEditorCtrl(self):
        """Get the editor control for disabling"""
        return self.editor_ctrl

    def GetValueFromEditorCtrl(self, editor):
        """Get boolean value from picker control"""
        return editor.GetValue()

    def Activate(self, *args, **kwargs):
        print(args, kwargs)
        print("Activate", not self.GetValue())
        self.SetValue(not self.GetValue())
        return True


class TableColumnsDataViewCtrl(wx.dataview.DataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_SESSION.subscribe(self._load_session)

        column_id_render = IconRender()
        column = wx.dataview.DataViewColumn(_(u"#"), column_id_render, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Name"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_datatype_renderer = PopupRenderer(PopupColumnDatatype)
        column = wx.dataview.DataViewColumn(_(u"Data type"), column_datatype_renderer, 2, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Length/Set"), 3, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        # column_unsigned_renderer = BooleanRenderer()
        # column = wx.dataview.DataViewColumn(_(u"Unsigned"), column_unsigned_renderer, 4, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_CENTER)
        # self.AppendColumn(column)

        self.AppendToggleColumn(_(u"Unsigned"), 4, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Allow NULL"), 5, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendToggleColumn(_(u"Zerofill"), 6, wx.dataview.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_default_renderer = PopupRenderer(PopupColumnDefault)
        column = wx.dataview.DataViewColumn(_(u"Default"), column_default_renderer, 7, width=200, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        choice_virtuality_renderer = wx.dataview.DataViewChoiceRenderer(["", "VIRTUAL", "STORED"], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Virtuality"), choice_virtuality_renderer, 8, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Expression"), 9, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_collation_renderer = wx.dataview.DataViewChoiceRenderer([""] + [c for c in COLLATION_CHARSETS.keys()], mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Collation"), column_collation_renderer, 10, width=-1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Comments"), 11, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

    def _load_session(self, session: Session):
        if session.datatype == SessionEngine.SQLITE:
            self.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(6).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(8).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)


class TableRecordsDataViewCtrl(wx.dataview.DataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_TABLE.subscribe(self._load_table)

    def _get_column_renderer(self, column: SQLColumn) -> wx.dataview.DataViewRenderer:
        if column.datatype.name == 'ENUM' and column.set:
            return EnumRenderer(column.set)

        elif column.datatype.name == 'SET' and column.set:
            popoup_render = PopupRenderer(PopupCheckList)
            popoup_render.on_open = lambda popup: popup.set_choices(column.set)
            return popoup_render

        elif column.datatype.name == 'BOOLEAN':
            return wx.dataview.DataViewToggleRenderer(mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE, align=wx.ALIGN_CENTER)
            # return BooleanRenderer()


        elif column.datatype.category == DataTypeCategory.INTEGER:
            return IntegerRenderer()

        elif column.datatype.category == DataTypeCategory.REAL:
            return FloatRenderer()

        elif column.datatype.name == 'DATE':
            return DateRenderer()

        elif column.datatype.name in ['DATETIME', 'TIMESTAMP']:
            return DateTimeRenderer()

        elif column.datatype.name == 'TIME':
            return TimeRenderer()
        else:
            return wx.dataview.DataViewTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)

    def _load_table(self, table: SQLTable):
        while self.GetColumnCount() > 0:
            self.DeleteColumn(self.GetColumn(0))

        if table is not None:
            for i, column in enumerate(table.columns):
                renderer = self._get_column_renderer(column)

                # print("index", i, "column", column.name, column.datatype.name, "renderer", renderer)

                col = wx.dataview.DataViewColumn(column.name, renderer, i, width=-1, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
                self.AppendColumn(col)
