import os
from typing import Type, List, Self, Any, Callable, Dict, Optional

import wx
import wx.dataview

from gettext import gettext as _

from helpers.logger import logger
from models.structures.indextype import SQLIndexType, StandardIndexType
from models.session import Session, SessionEngine
from models.structures.charset import COLLATION_CHARSETS
from models.structures.database import SQLColumn, SQLTable, SQLIndex, SQLDatabase
from models.structures.datatype import SQLDataType, DataTypeCategory

from windows.main import CURRENT_SESSION, CURRENT_TABLE, CURRENT_DATABASE


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

    def RenderText(self, text, x, rect, dc, state):
        x, y = rect.GetTopLeft()

        # dc.DrawText(str(text), x, self.get_draw_x(rect))
        super().RenderText(str(text), 0, rect, dc, state)

        return True

    def get_draw_x(self, rect):
        rect_height = rect.GetHeight()
        chars_height = self.GetView().CharHeight
        print(rect, chars_height)

        return int((rect_height / 2) - (chars_height / 2))


class BasePopup(wx.PopupTransientWindow):
    """Base class for all DataView popup windows."""

    def __init__(self, parent):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._value = None
        self._initial = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetWindowStyle(wx.TRANSPARENT_WINDOW)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetSizer(self.sizer)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        return self

    def get_initial(self):
        return self._initial

    @staticmethod
    def render(value):
        return value

    def open(self, value: Any, position: wx.Point, size: wx.Size) -> Self:
        self._value = value
        self._initial = value

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
        groups: Dict[DataTypeCategory, List[str]] = {}

        root = self.tree_ctrl.GetRootItem()
        self.tree_ctrl.DeleteChildren(root)

        for choice in self.choices:
            groups.setdefault(choice.category, []).append(choice.name)

        dc = wx.ClientDC(self.tree_ctrl)
        max_width = 0
        selected = None

        for category, datatypes in groups.items():

            category_item = self.tree_ctrl.AppendItem(root, category.value.name)
            self.tree_ctrl.SetItemBold(category_item, True)

            max_width = max(max_width, dc.GetTextExtent(category.value.name)[0])

            for datatype in datatypes:
                datatype_item = self.tree_ctrl.AppendItem(category_item, datatype)
                self.tree_ctrl.SetItemTextColour(datatype_item, category.value.color)

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

        self.check_list_box.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        # self.check_list_box.Bind(wx.EVT_KEY_DOWN, self._on_char_hook)

    def open(self, value: str, position: wx.Point, size: wx.Size) -> Self:
        max_width = 0
        dc = wx.ClientDC(self.check_list_box)
        for choice in self.choices:
            max_width = max(max_width, dc.GetTextExtent(choice)[0])

        size = wx.Size(max(max_width + 100, size.width), -1)

        self.check_list_box.AppendItems(self.choices)

        super().open(value, position, size)

        if value := self.get_value():
            self.check_list_box.SetCheckedStrings(value.split(', '))

        if self.check_list_box.GetCount() > 0:
            self.check_list_box.SetSelection(0)

        wx.CallAfter(self.SetFocus)

        return self

    def _on_select(self, event):
        self._value = ", ".join(self.check_list_box.GetCheckedStrings())
        event.Skip()

    def _on_char_hook(self, event):
        key_code = event.GetKeyCode()

        print("PopupCheckList EVT_CHAR_HOOK key_code:", key_code, "ENTER:", wx.WXK_RETURN, "NUMPAD_ENTER:", wx.WXK_NUMPAD_ENTER)

        if key_code == wx.WXK_SPACE:
            selection = self.check_list_box.GetSelection()
            if selection != wx.NOT_FOUND:
                current_state = self.check_list_box.IsChecked(selection)
                self.check_list_box.Check(selection, not current_state)
                self._value = ", ".join(self.check_list_box.GetCheckedStrings())
                logger.debug(f"Space pressed, toggled item {selection}")
        elif key_code == wx.WXK_UP:
            current = self.check_list_box.GetSelection()
            if current > 0:
                self.check_list_box.SetSelection(current - 1)
                logger.debug(f"Up arrow, selected item {current - 1}")
        elif key_code == wx.WXK_DOWN:
            current = self.check_list_box.GetSelection()
            if current < self.check_list_box.GetCount() - 1:
                self.check_list_box.SetSelection(current + 1)
                logger.debug(f"Down arrow, selected item {current + 1}")
        elif key_code == wx.WXK_RETURN or key_code == wx.WXK_NUMPAD_ENTER:
            logger.debug("ENTER pressed, closing popup")
            self.close()
        elif key_code == wx.WXK_ESCAPE:
            logger.debug("ESC pressed, reverting to initial value")
            self.set_value(self.get_initial())
            self.close()
        else:
            print("Other key, skipping")
            event.Skip()

    def set_choices(self, choices: List[str]) -> Self:
        print("set_choices", choices)
        self.choices = choices

        return self


class PopupRenderer(BaseDataViewCustomRenderer):
    def __init__(self, popup_class: Type[BasePopup], on_open: Optional[Callable[[BasePopup], None]] = None):
        super().__init__("string", wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

        self._value = ""
        self.popup_class = popup_class
        self.on_open: Optional[Callable[[BasePopup], None]] = on_open

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

        if self.on_open:
            self.on_open(popup)

        popup.OnDismiss = _on_dismiss

        popup.open(self._value, position, wx.Size(width=view.Columns[col].Width, height=-1))

        return True


class ChoiceRenderer(wx.dataview.DataViewChoiceRenderer):
    def __init__(self, choices):
        super().__init__(choices, wx.dataview.DATAVIEW_CELL_EDITABLE, wx.ALIGN_LEFT)


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
        super().__init__(varianttype="bool", mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE, align=wx.ALIGN_CENTER)
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
    on_column_insert: Callable[[...], Optional[bool]]
    on_column_delete: Callable[[...], Optional[bool]]
    on_column_move_up: Callable[[...], Optional[bool]]
    on_column_move_down: Callable[[...], Optional[bool]]

    insert_column_index: Callable[[wx.Event, SQLIndexType], Optional[bool]]
    append_column_index: Callable[[wx.Event, SQLIndex], Optional[bool]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_SESSION.subscribe(self._load_session)

        column = wx.dataview.DataViewColumn(_(u"#"), wx.dataview.DataViewIconTextRenderer(align=wx.ALIGN_LEFT), 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Name"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

        column_datatype_renderer = PopupRenderer(PopupColumnDatatype)
        column = wx.dataview.DataViewColumn(_(u"Data type"), column_datatype_renderer, 2, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Length/Set"), 3, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)

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

        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

    def _load_session(self, session: Session):
        if session.datatype == SessionEngine.SQLITE:
            self.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(6).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
            self.GetColumn(8).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)

    def _on_context_menu(self, event):
        from icons import BitmapList

        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.GetSelection()
        model = self.GetModel()
        row = model.GetRow(selected)
        column = model.data[row]

        menu = wx.Menu()

        add_item = wx.MenuItem(menu, wx.ID_ANY, _("Add column\tCTRL+INS"), wx.EmptyString, wx.ITEM_NORMAL)
        add_item.SetBitmap(BitmapList.ADD)
        menu.Append(add_item)

        self.Bind(wx.EVT_MENU, self.on_column_insert, add_item)

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

        for index_type in session.indextype.get_all():
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


class TableRecordsDataViewCtrl(wx.dataview.DataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        CURRENT_TABLE.subscribe(self._load_table)

    def _get_column_renderer(self, column: SQLColumn) -> wx.dataview.DataViewRenderer:
        if column.datatype.name == 'ENUM' and column.set:
            return ChoiceRenderer(column.set)

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


class TableIndexesDataViewCtrl(wx.dataview.DataViewCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_render_column0 = wx.dataview.DataViewIconTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Name"), icon_render_column0, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column)

        self.AppendTextColumn(_(u"Column(s)/Expression"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)
        self.AppendTextColumn(_(u"Condition"), 2, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)


class TableForeignKeysDataViewCtrl(wx.dataview.DataViewCtrl):

    on_foreign_key_insert: Callable[[...], Optional[bool]]
    on_foreign_key_delete: Callable[[...], Optional[bool]]
    on_foreign_key_update: Callable[[...], Optional[bool]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_render_column0 = wx.dataview.DataViewIconTextRenderer(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
        column = wx.dataview.DataViewColumn(_(u"Name"), icon_render_column0, 0, width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_LEFT)
        column.SetMinWidth(250)
        self.AppendColumn(column)

        # Colonna 1: Column(s) - larghezza minima 150px
        popup_render_column_1 = PopupRenderer(PopupCheckList)
        popup_render_column_1.on_open = lambda popup: popup.set_choices([c.name for c in list(CURRENT_TABLE.get_value().columns)])
        column1 = wx.dataview.DataViewColumn(_(u"Column(s)"), popup_render_column_1, 1, width=150, flags=wx.dataview.DATAVIEW_COL_RESIZABLE, align=wx.ALIGN_LEFT)
        column1.SetMinWidth(150)
        self.AppendColumn(column1)

        # colonne 2-5 vengono caricate dopo il database
        CURRENT_DATABASE.subscribe(self._load_database)

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

    def _load_database(self, database: SQLDatabase) -> None:
        if not database:
            return

        if column_2 := self.GetColumn(2):
            self.DeleteColumn(column_2)

        tables = list(CURRENT_DATABASE.get_value().tables)
        select_render_column_2 = ChoiceRenderer([t.name for t in tables])
        column2 = wx.dataview.DataViewColumn(_(u"Reference table"), select_render_column_2, 2, width=wx.COL_WIDTH_AUTOSIZE, flags=wx.dataview.DATAVIEW_COL_RESIZABLE, align=wx.ALIGN_LEFT)
        column2.SetMinWidth(140)
        self.InsertColumn(2, column2)

        if column_3 := self.GetColumn(3):
            self.DeleteColumn(column_3)

        popup_render_column_3 = PopupRenderer(PopupCheckList)
        popup_render_column_3.on_open = lambda popup: self._load_reference_columns(popup, select_render_column_2)
        column3 = wx.dataview.DataViewColumn(_(u"Reference column(s)"), popup_render_column_3, 3, width=200, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
        column3.SetMinWidth(200)
        self.InsertColumn(3, column3)

        if column_4 := self.GetColumn(4):
            self.DeleteColumn(column_4)

        choice_render_column_4 = ChoiceRenderer(["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"])
        column4 = wx.dataview.DataViewColumn(_(u"On UPDATE"), choice_render_column_4, 4, width=100, flags=wx.dataview.DATAVIEW_COL_RESIZABLE)
        column4.SetMinWidth(100)
        self.InsertColumn(4, column4)

        if column_5 := self.GetColumn(5):
            self.DeleteColumn(column_5)

        choice_render_column_5 = ChoiceRenderer(["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"])
        column5 = wx.dataview.DataViewColumn(_(u"On DELETE"), choice_render_column_5, 5, width=100, align=wx.ALIGN_LEFT)
        column5.SetMinWidth(100)
        self.InsertColumn(5, column5)

    def _load_reference_columns(self, popup, choice_render: ChoiceRenderer) -> None:
        value = choice_render.GetValue()
        if value:
            table = next((t for t in list(CURRENT_DATABASE.get_value().tables) if t.name == value), None)
            if table:
                columns = [c.name for c in list(table.columns)]
                popup.set_choices(columns)
